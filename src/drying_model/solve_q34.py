"""Q3/Q4: coupled radial finite volumes, moving material grid, threshold event.
Run: python solve_q34.py. Input files are never changed.
"""
from pathlib import Path
import json, time
import numpy as np
import openpyxl
from scipy.integrate import solve_ivp
from scipy.special import expi
from scipy.optimize import brentq
from scipy.sparse import diags, bmat, csr_matrix
from scipy.interpolate import PchipInterpolator

SCRIPT_DIR=Path(__file__).resolve().parent
PROJECT_ROOT=SCRIPT_DIR.parents[1]
DATA_ROOT=PROJECT_ROOT/'data'/'raw'/'drying_A'
RESULT_ROOT=PROJECT_ROOT/'results'/'drying_model'
def read(name):
    w=openpyxl.load_workbook(DATA_ROOT/name,data_only=True)
    a=np.array(list(w.active.values)[1:],float); w.close()
    assert np.isfinite(a).all() and np.all(np.diff(a[:,0])>0)
    return a
ENV=read('附件1.xlsx'); RAD=read('附件2.xlsx'); RAD[:,1]/=100
TAIL=ENV[ENV[:,0]>=10800,1:].mean(axis=0)
H=25.; HM=8e-7
# Interpolation is a controlled numerical choice.  The default remains the
# original piecewise-linear interpolation; comparison scripts can set this to
# ``pchip`` without changing the PDE or event logic.
INTERP_MODE='linear'
_ENV_PCHIP=tuple(PchipInterpolator(ENV[:,0],ENV[:,j]) for j in (1,2))
_RAD_PCHIP=PchipInterpolator(RAD[:,0],RAD[:,1])
def interp_series(x,xp,fp,pchip):
    return float(pchip(x)) if INTERP_MODE=='pchip' else float(np.interp(x,xp,fp))

class Model:
    def __init__(self,q,n,scenario='mean',fixed=False,hcoef=H,hm=HM,dscale=1.0):
        self.q=q;self.n=n;self.scenario=scenario;self.fixed=fixed
        self.hcoef=float(hcoef); self.hm=float(hm); self.dscale=float(dscale)
        self.x=(np.arange(n)+.5)/n;self.faces=np.arange(n+1)/n
        self.a=np.diff(self.faces**2)/2
    def radius(self,t):
        return .02 if self.q==3 or self.fixed else interp_series(t,RAD[:,0],RAD[:,1],_RAD_PCHIP)
    def properties(self,T,C):
        if np.any(C<=0) or np.any(T<=-273.15):
            raise ValueError('Nonphysical trial state; integration must be retried with smaller steps.')
        if self.q==3:
            return 650+128*C,1450+2736*C/(C+1),.21+.38*C/(C+1),self.dscale*2.4e-3*np.exp(-.45/C-3850/(T+273.15))
        return 760+90*C,1850+2150*C/(C+1),.12+.20*C/(C+1),self.dscale*4.2e-4*np.exp(-.30/C-3850/(T+273.15))
    def environment(self,t,after=False):
        if after:
            return TAIL if self.scenario=='mean' else (ENV[-1,1:] if self.scenario=='last' else np.array([50.,.05]))
        return np.array([interp_series(t,ENV[:,0],ENV[:,j],_ENV_PCHIP[j-1]) for j in (1,2)])
    def fluxes(self,t,y,after=False):
        n=self.n;T=y[:n];C=y[n:2*n];r=self.radius(t)
        rho,cp,k,d=self.properties(T,C); ti,hi=self.environment(t,after)
        kt=2*n*k[-1]/r
        ts=(kt*T[-1]+self.hcoef*ti)/(kt+self.hcoef)
        # Kirchhoff primitive: P'(C)=exp(-a/C). This integrates nonlinear
        # diffusivity across each face and gives a unique monotone boundary root.
        alpha=.45 if self.q==3 else .30
        prefactor=self.dscale*(2.4e-3 if self.q==3 else 4.2e-4)
        def primitive(c):return c*np.exp(-alpha/c)+alpha*expi(-alpha/c)
        p=primitive(C);g=prefactor*np.exp(-3850/(T+273.15))
        gs=prefactor*np.exp(-3850/((T[-1]+ts)/2+273.15))
        def boundary(c):return 2*n*gs/r*(p[-1]-primitive(c))-self.hm*(c-hi)
        cs=brentq(boundary,min(hi,C[-1]),max(hi,C[-1]),xtol=2e-14)
        ft=np.zeros(n+1);fc=ft.copy()
        ft[1:n]=self.faces[1:n]*(2*k[:-1]*k[1:]/(k[:-1]+k[1:]))*np.diff(T)*n
        fc[1:n]=self.faces[1:n]*(2*g[:-1]*g[1:]/(g[:-1]+g[1:]))*np.diff(p)*n
        ft[-1]=-r*self.hcoef*(ts-ti);fc[-1]=-r*self.hm*(cs-hi)
        return ft,fc,rho*cp,ts,cs,r
    def rhs(self,t,y,after=False):
        ft,fc,cap,ts,cs,r=self.fluxes(t,y,after)
        return np.r_[np.diff(ft)/(r*r*self.a*cap),np.diff(fc)/(r*r*self.a),-2*fc[-1]/(r*r)]
    def center(self,C):
        # Even quadratic through first two cell centers; used in event and output.
        return (9*C[0]-C[1])/8
    def maximum(self,C):
        return max(float(np.max(C)),float(self.center(C)))
    def output(self,t,y,radii):
        n=self.n;C=y[n:2*n];*_,ts,cs,r=self.fluxes(t,y,t>14400)
        x=np.r_[0,self.x,1];z=np.r_[self.center(C),C,cs]
        return [float(np.interp(v/r,x,z)) if v<=r+1e-12 else None for v in radii],float(cs),float(r)

def run(q,n=400,scenario='mean',rtol=1e-9,method='BDF',max_step=3600,fixed=False,hcoef=H,hm=HM,dscale=1.0):
    m=Model(q,n,scenario,fixed=fixed,hcoef=hcoef,hm=hm,dscale=dscale);tri=diags([np.ones(n-1),np.ones(n),np.ones(n-1)],[-1,0,1],format='csc')
    # Cumulative boundary loss depends only on the last T and C cells.
    # A dense auxiliary row would defeat sparse finite-difference coloring.
    zero=csr_matrix((n,1));row=csr_matrix(([1.],([0],[n-1])),shape=(1,n))
    pat=bmat([[tri,tri,zero],[tri,tri,zero],[row,row,csr_matrix((1,1))]],format='csc')
    y=np.r_[np.full(n,28.),np.full(n,2.55),0.]
    def event(t,y):return m.maximum(y[n:2*n])-.15
    event.terminal=True;event.direction=-1
    # Break at every environment knot; moving-radius knots also delimit intervals.
    knots=np.unique(np.r_[ENV[:,0],RAD[:,0] if q==4 else [],np.arange(259200,30*86400+1,86400)])
    segments=[]; stats={'min_C':2.55,'max_C':2.55,'min_T':28.,'max_T':28.,'mass_error':0.,'radial_increase':0.}
    begin=time.perf_counter()
    for a,b in zip(knots[:-1],knots[1:]):
        after=a>=14400
        fun=lambda t,y:m.rhs(t,y,after)
        sol=solve_ivp(fun,(a,b),y,method=method,rtol=rtol,atol=rtol*.001,
                      jac_sparsity=pat,events=event,dense_output=True,max_step=max_step,first_step=min(.01,b-a))
        if not sol.success:raise RuntimeError(sol.message)
        Y=sol.y;C=Y[n:2*n];T=Y[:n]
        stats['min_C']=min(stats['min_C'],float(C.min()));stats['max_C']=max(stats['max_C'],float(C.max()))
        stats['min_T']=min(stats['min_T'],float(T.min()));stats['max_T']=max(stats['max_T'],float(T.max()))
        stats['mass_error']=max(stats['mass_error'],float(np.max(np.abs(2*m.a@C+Y[-1]-2.55))))
        stats['radial_increase']=max(stats['radial_increase'],float(np.max(np.diff(C,axis=0))))
        segments.append((a,float(sol.t[-1]),sol.sol));y=Y[:,-1]
        if sol.t_events[0].size:
            stop=float(sol.t_events[0][0]);break
    else:raise RuntimeError('No crossing within 30 days; no result exported.')
    stats.update(seconds=stop,hours=stop/3600,radius_cm=m.radius(stop)*100,N=n,rtol=rtol,scenario=scenario,runtime=time.perf_counter()-begin,fixed_geometry=fixed,hcoef=m.hcoef,hm=m.hm,dscale=m.dscale)
    _,_,_,ts,cs,r=m.fluxes(stop,y,True)
    ti,hi=m.environment(stop,True);c=y[2*n-1];temp=y[n-1]
    _,_,k,_=m.properties(np.array([temp]),np.array([c]))
    alpha=.45 if q==3 else .30;pref=m.dscale*(2.4e-3 if q==3 else 4.2e-4)
    primitive=lambda c:c*np.exp(-alpha/c)+alpha*expi(-alpha/c)
    gs=pref*np.exp(-3850/((temp+ts)/2+273.15))
    stats['water_boundary_residual']=float(abs(2*n*gs/r*(primitive(c)-primitive(cs))-m.hm*(cs-hi)))
    stats['heat_boundary_residual']=float(abs(2*n*k[0]/r*(temp-ts)-m.hcoef*(ts-ti)))
    derivative=m.rhs(stop,y,True)[n:2*n];stats['crossing_slope']=float(m.center(derivative))
    # Verify strict inequality just after the crossing with a real continuation.
    post=solve_ivp(lambda t,y:m.rhs(t,y,True),(stop,stop+1),y,method=method,rtol=rtol,atol=rtol*.001,jac_sparsity=pat)
    stats['maximum_after_1s']=m.maximum(post.y[n:2*n,-1])
    # Physical audits for Q4: dry-mass closure and porosity feasibility.
    # These diagnostics do not alter the PDE because the supplied radius is observational.
    if q==4:
        rhoe0=760+90*2.55; rhod0=rhoe0/(1+2.55); rhos=1500.; rhow=1000.
        rr=m.radius(stop); rhod=rhod0*(0.02/rr)**2
        stats['dry_mass_relative_error']=float(abs((rhod/rhod0)*(rr/0.02)**2-1))
        stats['min_porosity_assumed']=float(1-rhod*(1/rhos+float(np.max(y[n:2*n]))/rhow))
        stats['porosity_audit_only']=True
    assert stats['min_C']>0 and stats['maximum_after_1s']<.15 and stats['mass_error']<1e-7
    def evaluate(t):
        ends=[s[1] for s in segments];idx=min(np.searchsorted(ends,t),len(segments)-1)
        return segments[idx][2](t)
    print(json.dumps({'q':q,**stats}),flush=True)
    return m,evaluate,stats

def export(m,evaluate,stats):
    q=m.q;stop=stats['seconds'];times=np.r_[np.arange(60,stop,60),stop];radii=np.arange(21)*.001
    path=DATA_ROOT/'附件3'/f'result{q}.xlsx';wb=openpyxl.load_workbook(path);ws=wb.worksheets[0]
    ws.delete_rows(1,ws.max_row)
    ws.append(['时间/s，距离/cm']+[round(r*100,1) for r in radii]+(['药材表面'] if q==4 else []))
    raw=[]
    for t in times:
        vals,cs,r=m.output(t,evaluate(t),radii);raw.append([t,*[np.nan if v is None else v for v in vals],cs,r])
        ws.append([float(t)]+[None if v is None else round(v,4) for v in vals]+([round(cs,4)] if q==4 else []))
    for row in ws.iter_rows(min_row=2):
        row[0].number_format='0.0000'
        for cell in row[1:]:cell.number_format='0.0000'
    ws.freeze_panes='B2';ws.column_dimensions['A'].width=24
    wb.save(path);wb.close()
    (RESULT_ROOT/'main').mkdir(parents=True,exist_ok=True)
    np.savez_compressed(RESULT_ROOT/'main'/f'q{q}_full_precision.npz',columns=np.array(['time_s']+[f'C_r{r*100:.1f}cm' for r in radii]+['C_surface','radius_m']),data=np.array(raw))
    paper=[]
    for t in np.r_[np.arange(21600,stop,21600),stop]:
        vals,cs,r=m.output(t,evaluate(t),np.arange(5)*.005)
        paper.append({'time_h':float(t/3600),'C':vals,'surface':cs,'radius_cm':r*100})
    return paper

if __name__=='__main__':
    all_results={}
    for q in (3,4):
        runs=[]
        # Main production solve uses the adaptive-BDF configuration.
        for n in (100,200,400):
            m,ev,s=run(q,n);runs.append(s)
        all_results[str(q)]={'runs':runs,'paper':export(m,ev,s)}
    (RESULT_ROOT/'validation').mkdir(parents=True,exist_ok=True)
    (RESULT_ROOT/'validation'/'q34_validation.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2),encoding='utf-8')
