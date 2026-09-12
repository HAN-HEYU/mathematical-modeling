"""Q4 material-coordinate finite volumes using the main model's radial flux.

Case 1: 1D radial shrinkage, no end flux.
Case 2: 2D radial and axial shrinkage, no end flux.
Case 3: 2D radial shrinkage, fixed length, end-face mass transfer only.
Case 4: 2D radial and axial shrinkage, end-face mass transfer only.
No explicit latent heat is included, consistent with the main effective model.
"""
import argparse, json, time
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import expi
from scipy.sparse import lil_matrix
from scipy.interpolate import RegularGridInterpolator
import solve_q34 as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'today_2d_comparisons'
Hhalf=.125; hcoef=25.; hm=8e-7; R0=.02; Ltot=.25

def P(c):
    a=.30
    return c*np.exp(-a/c)+a*expi(-a/c)

def boundary_c(c, tc, ts, distance, transfer, eq):
    if transfer == 0:
        return c.copy()
    scale = 4.2e-4*np.exp(-3850/((tc+ts)/2+273.15))/distance
    pc=P(c); lo=np.minimum(c,eq); hi=np.maximum(c,eq)
    linear=scale*np.exp(-.30/c)
    x=(linear*c+transfer*eq)/(linear+transfer)
    for _ in range(60):
        f=scale*(pc-P(x))-transfer*(x-eq)
        active=np.abs(f)>2e-21
        if not active.any(): return x
        lo=np.where(active & (f>0),x,lo)
        hi=np.where(active & (f<=0),x,hi)
        new=x+f/(scale*np.exp(-.30/x)+transfer)
        new=np.where((new>lo)&(new<hi),new,(lo+hi)/2)
        if np.max(np.where(active,np.abs(new-x),0))<2e-14:
            return np.where(active,new,x)
        x=np.where(active,new,x)
    raise RuntimeError('Q4 nonlinear Robin boundary root did not converge')

class TwoD:
    def __init__(self,nr,nz,fixed=True,chi=0.,end_hm=0.,end_h=0.):
        self.nr,self.nz=nr,nz; self.fixed=fixed; self.chi=chi
        self.end_hm=end_hm; self.end_h=end_h
        self.m=base.Model(4,nr,fixed=fixed)
        self.x=(np.arange(nr)+.5)/nr
        self.xf=np.arange(nr+1)/nr
        self.z=(np.arange(nz)+.5)/nz
        self.dx=1/nr; self.dz=1/nz
        self.a=np.diff(self.xf**2)/2; self.nn=nr*nz
        self.weights=np.broadcast_to(2*self.a[None,:]/nz,(nz,nr))
    def geom(self,t):
        R=self.m.radius(t); s=R/R0
        H=Hhalf*(1-self.chi*(1-s))
        return R,H
    def env(self,t,after):
        return self.m.environment(t,after)
    def unpack(self,y):
        return y[:self.nn].reshape(self.nz,self.nr),y[self.nn:2*self.nn].reshape(self.nz,self.nr)
    def fluxes(self,t,y,after):
        T,C=self.unpack(y)
        R,H=self.geom(t); te,ce=self.env(t,after)
        rho,cp,k,d=self.m.properties(T,C); cap=rho*cp
        g=.00042*np.exp(-3850/(T+273.15)); p=P(C)
        dr=R/self.nr; dz=H/self.nz
        ts=(2*self.nr*k[:,-1]*T[:,-1]+R*hcoef*te)/(2*self.nr*k[:,-1]+R*hcoef)
        xs=boundary_c(C[:,-1],T[:,-1],ts,dr/2,hm,ce)
        th=(2*self.nz*k[-1]*T[-1]+H*self.end_h*te)/(2*self.nz*k[-1]+H*self.end_h) if self.end_h>0 else T[-1]
        ch=boundary_c(C[-1],T[-1],th,dz/2,self.end_hm,ce)
        ft=np.zeros((self.nz,self.nr+1)); fc=np.zeros_like(ft)
        zt=np.zeros((self.nz+1,self.nr)); zc=np.zeros_like(zt)
        kh=2*k[:,:-1]*k[:,1:]/(k[:,:-1]+k[:,1:])
        gh=2*g[:,:-1]*g[:,1:]/(g[:,:-1]+g[:,1:])
        ft[:,1:-1]=self.xf[1:-1]*kh*np.diff(T,axis=1)*self.nr
        fc[:,1:-1]=self.xf[1:-1]*gh*np.diff(p,axis=1)*self.nr
        ft[:,-1]=R*hcoef*(te-ts); fc[:,-1]=R*hm*(ce-xs)
        khz=2*k[:-1]*k[1:]/(k[:-1]+k[1:]); ghz=2*g[:-1]*g[1:]/(g[:-1]+g[1:])
        zt[1:-1]=khz*np.diff(T,axis=0)*self.nz
        zc[1:-1]=ghz*np.diff(p,axis=0)*self.nz
        zt[-1]=H*self.end_h*(te-th); zc[-1]=H*self.end_hm*(ce-ch)
        return ft,fc,zt,zc,cap,ts,xs,th,ch
    def rhs(self,t,y,after):
        ft,fc,zt,zc,cap,*_=self.fluxes(t,y,after); R,H=self.geom(t)
        dt=(np.diff(ft,axis=1)/(R*R*self.a)+np.diff(zt,axis=0)*self.nz/(H*H))/cap
        dc=np.diff(fc,axis=1)/(R*R*self.a)+np.diff(zc,axis=0)*self.nz/(H*H)
        return np.r_[dt.ravel(),dc.ravel(),-2*np.mean(fc[:,-1])/R**2,-2*np.dot(self.a,zc[-1])/H**2]
    def maximum(self,y):
        _,C=self.unpack(y); axis=(9*C[:,0]-C[:,1])/8; mid=(9*C[0]-C[1])/8
        center=(9*axis[0]-axis[1])/8
        return max(float(C.max()),float(axis.max()),float(mid.max()),float(center))
    def center(self,y):
        _,C=self.unpack(y)
        return float((81*C[0,0]-9*C[0,1]-9*C[1,0]+C[1,1])/64)
    def pattern(self):
        p=lil_matrix((2*self.nn+2,2*self.nn+2),dtype=int)
        for j in range(self.nz):
            for i in range(self.nr):
                s=j*self.nr+i
                for jj,ii in ((j,i),(j,max(0,i-1)),(j,min(self.nr-1,i+1)),(max(0,j-1),i),(min(self.nz-1,j+1),i)):
                    u=jj*self.nr+ii
                    for o in (0,self.nn): p[s,u+o]=p[s+self.nn,u+o]=1
                if i==self.nr-1: p[2*self.nn,s]=p[2*self.nn,s+self.nn]=1
                if j==self.nz-1: p[2*self.nn+1,s]=p[2*self.nn+1,s+self.nn]=1
        return p.tocsc()
    def terminal_table(self,t,y):
        _,C=self.unpack(y); ft,fc,zt,zc,cap,ts,xs,th,ch=self.fluxes(t,y,t>=14400)
        A=np.zeros((self.nz+2,self.nr+2)); A[1:-1,1:-1]=C
        A[1:-1,0]=(9*C[:,0]-C[:,1])/8; A[0,1:-1]=(9*C[0]-C[1])/8
        A[1:-1,-1]=xs; A[-1,1:-1]=ch
        A[0,0]=(81*C[0,0]-9*C[0,1]-9*C[1,0]+C[1,1])/64
        A[0,-1]=(9*xs[0]-xs[1])/8; A[-1,0]=(9*ch[0]-ch[1])/8; A[-1,-1]=(ch[-1]+xs[-1])/2
        R,H=self.geom(t)
        z=np.r_[0,self.z,1]*H; r=np.r_[0,self.x,1]*R
        f=RegularGridInterpolator((z,r),A,bounds_error=True)
        rs=list(R*np.array([0,.25,.5,.75,1])); hs=list(H*np.array([0,.2,.4,.6,.8,.96,1]))
        table=[]
        for zz in hs:
            row=[]
            for rr in rs:
                row.append(None if abs(zz-H)<1e-12 and abs(rr-R)<1e-12 else float(f([[zz,rr]])[0]))
            table.append(row)
        return table,rs,hs

def run2d(label,fixed,chi,end_hm,end_h,nr=40,nz=32,rtol=1e-7,max_step=1800,method='BDF'):
    OUT.mkdir(parents=True,exist_ok=True)
    m=TwoD(nr,nz,fixed,chi,end_hm,end_h); y=np.r_[np.full(m.nn,28.),np.full(m.nn,2.55),0.,0.]
    pat=m.pattern(); knots=np.unique(np.r_[base.ENV[:,0],base.RAD[:,0] if not fixed else [],np.arange(259200,30*86400+1,86400)])
    def ev(t,y): return m.maximum(y)-.15
    ev.terminal=True; ev.direction=-1; begin=time.perf_counter(); stop=None
    masserr=0.; minC=2.55
    for a,b in zip(knots[:-1],knots[1:]):
        s=solve_ivp(lambda t,y:m.rhs(t,y,a>=14400),(a,b),y,method=method,rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev,jac_sparsity=pat)
        if not s.success: raise RuntimeError(s.message)
        means=m.weights.ravel() @ s.y[m.nn:2*m.nn]
        masserr=max(masserr,float(np.max(np.abs(means+s.y[-2]+s.y[-1]-2.55))))
        minC=min(minC,float(s.y[m.nn:2*m.nn].min()))
        y=s.y[:,-1]
        if s.t_events[0].size: stop=float(s.t_events[0][0]); y=s.y_events[0][0]; break
    if stop is None: raise RuntimeError('no event')
    post=solve_ivp(lambda t,y:m.rhs(t,y,True),(stop,stop+1),y,method=method,rtol=rtol,atol=rtol*1e-3,max_step=1,jac_sparsity=pat)
    if not post.success: raise RuntimeError(post.message)
    tab,rs,hs=m.terminal_table(stop,y); _,C=m.unpack(y)
    out={'case':label,'nr':nr,'nz':nz,'fixed_radius':fixed,'chi':chi,'end_hm':end_hm,'end_h':end_h,'seconds':float(stop),'hours':float(stop/3600),'center_C':m.maximum(y),'maximum_after_1s':m.maximum(post.y[:,-1]),'mass_balance_error':float(abs(np.sum(m.weights*C)+y[-2]+y[-1]-2.55)),'axial_C_spread':float(np.ptp(C,axis=0).max()),'r_cm':rs,'z_from_midplane_cm':hs,'C_table':tab,'runtime_s':time.perf_counter()-begin}
    out.update(center_C=m.center(y),maximum_C=m.maximum(y),mass_balance_error=masserr,min_C=minC,
               r_cm=list(np.array(rs)*100),z_from_midplane_cm=list(np.array(hs)*100),
               radius_cm=m.geom(stop)[0]*100,length_cm=m.geom(stop)[1]*200,
               C_mean=float(np.sum(m.weights*C)),side_cumulative_loss=float(y[-2]),end_cumulative_loss=float(y[-1]),
               rtol=rtol,max_step=max_step,method=method)
    assert minC>0 and masserr<1e-7 and out['maximum_after_1s']<.15
    np.savez_compressed(OUT/f'{label}_{nr}x{nz}.npz',time_s=stop,state=y,C=C,T=m.unpack(y)[0],x=m.x,z=m.z)
    OUT.mkdir(parents=True,exist_ok=True); (OUT/f'{label}_{nr}x{nz}.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8'); print(json.dumps({k:out[k] for k in ['case','hours','maximum_after_1s','mass_balance_error','axial_C_spread','runtime_s']},ensure_ascii=False),flush=True); return out

def run1d_end_equiv(n=80,rtol=1e-8,max_step=1800):
    m=base.Model(4,n,fixed=True); y=np.r_[np.full(n,28.),np.full(n,2.55),0.]; knots=np.unique(np.r_[base.ENV[:,0],np.arange(259200,30*86400+1,86400)])
    def fun(t,y,after):
        d=m.rhs(t,y,after); _,hi=m.environment(t,after); C=y[n:2*n]; sink=2*hm/Ltot*(hi-C); d[n:2*n]+=sink; d[-1]+=2*hm/Ltot*(float(C.mean())-hi); return d
    def ev(t,y): return m.maximum(y[n:2*n])-.15
    ev.terminal=True; ev.direction=-1; begin=time.perf_counter(); stop=None
    for a,b in zip(knots[:-1],knots[1:]):
        s=solve_ivp(lambda t,y:fun(t,y,a>=14400),(a,b),y,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev)
        if not s.success: raise RuntimeError(s.message)
        y=s.y[:,-1]
        if s.t_events[0].size: stop=float(s.t_events[0][0]); y=s.y_events[0][0]; break
    post=solve_ivp(lambda t,y:fun(t,y,True),(stop,stop+1),y,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=1)
    vals=m.output(stop,y,[0,.005,.01,.015,.02])[0]
    out={'case':'1d_endface_equiv','n':n,'seconds':float(stop),'hours':float(stop/3600),'center_C':m.maximum(y[n:2*n]),'maximum_after_1s':m.maximum(post.y[n:2*n,-1]),'r_cm':[0,.5,1,1.5,2],'C_radial_at_event':vals,'runtime_s':time.perf_counter()-begin,'equivalent_sink':'2 hm/L (Ceq-C)'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'1d_endface_equiv.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False),flush=True); return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--nr',type=int,default=40); ap.add_argument('--nz',type=int,default=32); ap.add_argument('--high',action='store_true'); args=ap.parse_args(); nr,nz=(80,64) if args.high else (args.nr,args.nz)
    _,_,s=base.run(4,n=nr,scenario='mean',rtol=1e-8,max_step=1800,fixed=False); OUT.mkdir(parents=True,exist_ok=True); (OUT/'1d_shrink.json').write_text(json.dumps(s,indent=2),encoding='utf-8'); print('1d_shrink',json.dumps(s),flush=True)
    run2d('2d_shrink_both_noend',fixed=False,chi=1.,end_hm=0.,end_h=0.,nr=nr,nz=nz,rtol=1e-7)
    run2d('case3_verified_mass_only',fixed=False,chi=0.,end_hm=hm,end_h=0.,nr=nr,nz=nz,rtol=1e-8)
    run2d('2d_shrink_both_endface',fixed=False,chi=1.,end_hm=hm,end_h=0.,nr=nr,nz=nz,rtol=1e-7)
