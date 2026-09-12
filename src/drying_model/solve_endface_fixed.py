import numpy as np, json, time
from pathlib import Path
import openpyxl
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix
from scipy.optimize import brentq

ROOT=Path(__file__).resolve().parent
def read_xlsx(name):
    w=openpyxl.load_workbook(ROOT/'附件'/name,data_only=True)
    a=np.array(list(w.active.values)[1:],float); w.close(); return a
ENV=read_xlsx('附件1.xlsx'); R0=.02; H=.125; h=25.; hm=8e-7
TAIL=ENV[ENV[:,0]>=10800,1:].mean(axis=0)

class Fixed2D:
    def __init__(self,q,nr=12,nz=24,end_h=h,end_hm=hm):
        self.q=q; self.nr=nr; self.nz=nz; self.end_h=end_h; self.end_hm=end_hm
        self.x=(np.arange(nr)+.5)/nr; self.xf=np.arange(nr+1)/nr; self.dx=1/nr
        self.z=(np.arange(nz)+.5)/nz; self.zf=np.arange(nz+1)/nz; self.dz=1/nz
        self.ar=(self.xf[1:]**2-self.xf[:-1]**2)/2; self.az=np.full(nz,self.dz)
    def env(self,t,after):
        if after:return TAIL
        return np.array([np.interp(t,ENV[:,0],ENV[:,j]) for j in (1,2)])
    def props(self,T,C):
        if self.q==1:
            return np.full_like(C,820.),np.full_like(C,2600.),np.full_like(C,.36),7e-9*np.exp(-.89/C)
        rho=650+128*C; cp=1450+2736*C/(1+C); k=.21+.38*C/(1+C)
        D=2.4e-3*np.exp(-.45/C-3850/(T+273.15)); return rho,cp,k,D
    def rhs(self,t,y,after=False):
        nr,nz=self.nr,self.nz; nn=nr*nz
        T=y[:nn].reshape(nr,nz); C=y[nn:].reshape(nr,nz); ti,hi=self.env(t,after)
        rho,cp,k,D=self.props(T,C); cap=rho*cp
        ft=np.zeros((nr+1,nz)); fc=np.zeros_like(ft); fz=np.zeros((nr,nz+1)); cz=np.zeros_like(fz)
        kh=2*k[:-1]*k[1:]/(k[:-1]+k[1:]); Dh=2*D[:-1]*D[1:]/(D[:-1]+D[1:])
        ft[1:nr]=self.xf[1:nr,None]*kh*(T[1:]-T[:-1])/self.dx
        fc[1:nr]=self.xf[1:nr,None]*Dh*(C[1:]-C[:-1])/self.dx
        ks=k[-1]; Ds=D[-1]
        Ts=(2*nr*ks*T[-1]+R0*h*ti)/(2*nr*ks+R0*h)
        Cs=(2*nr*Ds*C[-1]+R0*hm*hi)/(2*nr*Ds+R0*hm)
        ft[-1]=R0*h*(ti-Ts); fc[-1]=R0*hm*(hi-Cs)
        khz=2*k[:,:-1]*k[:,1:]/(k[:,:-1]+k[:,1:]); Dhz=2*D[:,:-1]*D[:,1:]/(D[:,:-1]+D[:,1:])
        fz[:,1:nz]=khz*(T[:,1:]-T[:,:-1])/self.dz; cz[:,1:nz]=Dhz*(C[:,1:]-C[:,:-1])/self.dz
        kend=k[:,-1]; Dend=D[:,-1]
        Tz=(2*nz*kend*T[:,-1]+H*self.end_h*ti)/(2*nz*kend+H*self.end_h) if self.end_h>0 else T[:,-1]
        Cz=(2*nz*Dend*C[:,-1]+H*self.end_hm*hi)/(2*nz*Dend+H*self.end_hm) if self.end_hm>0 else C[:,-1]
        fz[:,-1]=H*self.end_h*(ti-Tz); cz[:,-1]=H*self.end_hm*(hi-Cz)
        dT=(np.diff(ft,axis=0)/(R0**2*self.ar[:,None])+np.diff(fz,axis=1)/(H**2*self.az[None,:]))/cap
        dC=np.diff(fc,axis=0)/(R0**2*self.ar[:,None])+np.diff(cz,axis=1)/(H**2*self.az[None,:])
        return np.r_[dT.ravel(),dC.ravel()]
    def maxC(self,y):
        nn=self.nr*self.nz; C=y[nn:].reshape(self.nr,self.nz)
        axis=(9*C[0]-C[1])/8
        return float(max(C.max(),axis.max()))
    def mid_profile(self,y):
        nn=self.nr*self.nz; C=y[nn:].reshape(self.nr,self.nz)
        # z=0 boundary is symmetry; reconstruct centerline r=0 from first cells
        c=(9*C[0,0]-C[1,0])/8
        return np.r_[c,C[:,0]]
    def profile_at_mid(self,y,t,rs):
        """Mid-plane C profile at requested physical radii (m), with Robin surface reconstruction."""
        nn=self.nr*self.nz; C=y[nn:].reshape(self.nr,self.nz)
        _,hi=self.env(t,t>=14400)
        D=self.props(y[:nn].reshape(self.nr,self.nz),C)[3]
        # center reconstruction, cell centers, and outer Robin surface
        cv=(9*C[0,0]-C[1,0])/8
        rc=(np.arange(self.nr)+.5)*R0/self.nr
        Ds=D[-1,0]; Cn=C[-1,0]
        Cs=(2*self.nr*Ds*Cn+R0*hm*hi)/(2*self.nr*Ds+R0*hm)
        xp=np.r_[0.,rc,R0]; vals=np.r_[cv,C[:,0],Cs]
        return np.interp(np.asarray(rs),xp,vals)
    def temperature_at_mid(self,y,t,rs):
        nn=self.nr*self.nz; T=y[:nn].reshape(self.nr,self.nz); C=y[nn:].reshape(self.nr,self.nz)
        ti,_=self.env(t,t>=14400)
        k=self.props(T,C)[2]
        tv=(9*T[0,0]-T[1,0])/8
        rc=(np.arange(self.nr)+.5)*R0/self.nr
        kn=k[-1,0]; Tn=T[-1,0]
        Ts=(2*self.nr*kn*Tn+R0*h*ti)/(2*self.nr*kn+R0*h)
        xp=np.r_[0.,rc,R0]; vals=np.r_[tv,T[:,0],Ts]
        return np.interp(np.asarray(rs),xp,vals)

def pattern(m):
    nr,nz=m.nr,m.nz; nn=nr*nz; p=lil_matrix((2*nn,2*nn),dtype=int)
    for i in range(nr):
      for j in range(nz):
        a=i*nz+j
        for ii,jj in ((i,j),(max(0,i-1),j),(min(nr-1,i+1),j),(i,max(0,j-1)),(i,min(nz-1,j+1))):
          b=ii*nz+jj; p[a,b]=p[a,nn+b]=p[nn+a,b]=p[nn+a,nn+b]=1
    return p.tocsc()

def run(q,tend,nr=12,nz=24,event=False,rtol=2e-6,max_step=1800,outputs=None,return_state=False,end_h=h,end_hm=hm):
    m=Fixed2D(q,nr,nz,end_h=end_h,end_hm=end_hm); nn=nr*nz; y=np.r_[np.full(nn,28.),np.full(nn,2.55)]
    knots=np.unique(np.r_[ENV[:,0], [tend]]) ; knots=knots[(knots>=0)&(knots<=tend)]
    if knots[0]!=0: knots=np.r_[0,knots]
    pat=pattern(m); snaps={}; stop=None; t0=time.perf_counter()
    def ev(t,y): return m.maxC(y)-.15
    ev.terminal=True; ev.direction=-1
    for a,b in zip(knots[:-1],knots[1:]):
        aft=a>=14400
        fun=lambda t,y:m.rhs(t,y,aft)
        sol=solve_ivp(fun,(a,b),y,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(60,b-a),events=ev if event else None,jac_sparsity=pat,dense_output=bool(outputs) or event)
        if not sol.success: raise RuntimeError(sol.message)
        if outputs:
            for tt in outputs:
                if a<=tt<=sol.t[-1]: snaps[float(tt)]=sol.sol(tt)
        y=sol.y[:,-1]
        if event and sol.t_events[0].size:
            stop=float(sol.t_events[0][0]); break
    if event:
        if stop is None: raise RuntimeError('no crossing')
        # event state from last segment dense output; if absent rerun tiny bracket
        ys=sol.sol(stop) if sol.sol is not None else y
        ans={'q':q,'seconds':stop,'hours':stop/3600,'maxC':m.maxC(ys),'runtime_s':time.perf_counter()-t0}
        if return_state: ans.update({'model':m,'state':ys})
        return ans
    return m,snaps,time.perf_counter()-t0

if __name__=='__main__':
    out=[]
    for q,tend in ((1,1800.),(2,10800.)):
        m,snaps,rt=run(q,tend,event=False,outputs=[100,300,600,900,1200,1500,1800] if q==1 else [1800,3600,5400,7200,9000,10800])
        vals={str(t):m.mid_profile(y).tolist() for t,y in snaps.items()}
        (ROOT/f'results/endface_q{q}_mid.json').write_text(json.dumps({'runtime_s':rt,'nr':m.nr,'nz':m.nz,'profiles':vals},ensure_ascii=False,indent=2),encoding='utf-8')
        print('Q',q,'runtime',rt,'profiles saved')
    for q in (2,):
        print('Q3',run(q,72*3600,event=True,nr=12,nz=24,rtol=2e-6,max_step=3600))
