import numpy as np, json, time
from pathlib import Path
import openpyxl
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix
from scipy.interpolate import PchipInterpolator
ROOT=Path(__file__).resolve().parent

def read(name):
 w=openpyxl.load_workbook(ROOT/'附件'/name,data_only=True); a=np.array(list(w.active.values)[1:],float); w.close(); return a
ENV=read('附件1.xlsx'); RAD=read('附件2.xlsx'); RAD[:,1]/=100
R0=.02; H0=.125; hcoef=25.; hm=8e-7
TAIL=ENV[ENV[:,0]>=10800,1:].mean(axis=0)
Rdot_data=np.gradient(RAD[:,1],RAD[:,0])
INTERP_MODE='linear'
_ENV_PCHIP=tuple(PchipInterpolator(ENV[:,0],ENV[:,j]) for j in (1,2))
_RAD_PCHIP=PchipInterpolator(RAD[:,0],RAD[:,1])
_RAD_DERIV=_RAD_PCHIP.derivative()
def interp_series(x,xp,fp,pchip):
 return float(pchip(x)) if INTERP_MODE=='pchip' else float(np.interp(x,xp,fp))

class Axisym2D:
 def __init__(self,nr=20,nz=40,chi=0.0,hcoef_=hcoef,hm_=hm,dscale=1.0,end_h=None,end_hm=None,fixed_radius=False):
  self.nr,self.nz,self.chi=nr,nz,chi
  self.hcoef,self.hm,self.dscale=hcoef_,hm_,dscale
  self.fixed_radius=fixed_radius
  self.end_h=self.hcoef if end_h is None else end_h
  self.end_hm=self.hm if end_hm is None else end_hm
  self.x=(np.arange(nr)+.5)/nr; self.xf=np.arange(nr+1)/nr; self.dx=1/nr
  self.z=(np.arange(nz)+.5)/nz; self.zf=np.arange(nz+1)/nz; self.dz=1/nz
  self.ar=(self.xf[1:]**2-self.xf[:-1]**2)/2; self.az=np.full(nz,self.dz)
 def geom(self,t):
  R=.02 if self.fixed_radius else (interp_series(t,RAD[:,0],RAD[:,1],_RAD_PCHIP) if t<=RAD[-1,0] else float(RAD[-1,1]))
  rd=float(_RAD_DERIV(t)) if INTERP_MODE=='pchip' and t<=RAD[-1,0] else (float(np.interp(t,RAD[:,0],Rdot_data)) if t<=RAD[-1,0] else 0.)
  s=R/R0; Hlen=H0*(1-self.chi*(1-s)); hd=self.chi*rd/R if R>0 else 0.
  return R,rd,Hlen,hd
 def env(self,t,after=True):
  if after:return TAIL
  return np.array([interp_series(t,ENV[:,0],ENV[:,j],_ENV_PCHIP[j-1]) for j in (1,2)])
 def props(self,T,C):
  if np.any(C<=0) or np.any(T<=-273): raise ValueError
  rho=760+90*C; cp=1850+2150*C/(1+C); k=.12+.20*C/(1+C)
  D=self.dscale*4.2e-4*np.exp(-.30/C-3850/(T+273.15)); return rho,cp,k,D
 def rhs(self,t,y,after=True):
  nr,nz=self.nr,self.nz; nn=nr*nz; T=y[:nn].reshape(nr,nz); C=y[nn:2*nn].reshape(nr,nz); R,rd,Hlen,hd=self.geom(t); ti,hi=self.env(t,after)
  rho,cp,k,D=self.props(T,C); cap=rho*cp
  # heat flux arrays: radial faces nr+1,nz; axial faces nr,nz+1
  ft=np.zeros((nr+1,nz)); fc=np.zeros_like(ft)
  fz=np.zeros((nr,nz+1)); cz=np.zeros_like(fz)
  # interior radial
  kh=2*k[:-1,:]*k[1:,:]/(k[:-1,:]+k[1:,:]); Dh=2*D[:-1,:]*D[1:,:]/(D[:-1,:]+D[1:,:])
  ft[1:nr,:]=self.xf[1:nr,None]*kh*(T[1:,:]-T[:-1,:])/self.dx
  fc[1:nr,:]=self.xf[1:nr,None]*Dh*(C[1:,:]-C[:-1,:])/self.dx
  # radial boundaries center symmetry, side Robin
  ks=k[-1,:]; Ds=D[-1,:]
  Ts=(2*nr*ks*T[-1,:]+R*self.hcoef*ti)/(2*nr*ks+R*self.hcoef)
  Cs=(2*nr*Ds*C[-1,:]+R*self.hm*hi)/(2*nr*Ds+R*self.hm)
  ft[-1,:]=R*self.hcoef*(ti-Ts); fc[-1,:]=R*self.hm*(hi-Cs)
  # axial interior and end boundary
  khz=2*k[:,:-1]*k[:,1:]/(k[:,:-1]+k[:,1:]); Dhz=2*D[:,:-1]*D[:,1:]/(D[:,:-1]+D[:,1:])
  fz[:,1:nz]=khz*(T[:,1:]-T[:,:-1])/self.dz
  cz[:,1:nz]=Dhz*(C[:,1:]-C[:,:-1])/self.dz
  kend=k[:,-1]; Dend=D[:,-1]
  Tz=(2*nz*kend*T[:,-1]+Hlen*self.end_h*ti)/(2*nz*kend+Hlen*self.end_h) if self.end_h>0 else T[:,-1]
  Cz=(2*nz*Dend*C[:,-1]+Hlen*self.end_hm*hi)/(2*nz*Dend+Hlen*self.end_hm) if self.end_hm>0 else C[:,-1]
  # Use the instance parameters at the end face as well as at the side face.
  # This is essential for a consistent h/h_m sensitivity experiment.
  fz[:,-1]=Hlen*self.end_h*(ti-Tz); cz[:,-1]=Hlen*self.end_hm*(hi-Cz)
  # divergence
  dT=(np.diff(ft,axis=0)/(R*R*self.ar[:,None]) + np.diff(fz,axis=1)/(Hlen*Hlen*self.az[None,:]))/cap
  dC=(np.diff(fc,axis=0)/(R*R*self.ar[:,None]) + np.diff(cz,axis=1)/(Hlen*Hlen*self.az[None,:]))
  # For the half-cylinder normalized material volume, the outward boundary
  # flux gives the dry-basis water-loss rate used by the conservation audit.
  W=np.sum(self.ar[:,None]*self.az[None,:])
  loss_rate=-(fc[-1,:].sum()*self.dz/(R*R)+np.sum(cz[:,-1]*self.ar)/(Hlen*Hlen))/W
  # In material (body-following) coordinates the uniform shrinkage velocity
  # is already absorbed by the coordinate map; only R(t), H(t) scaling remains.
  return np.r_[dT.ravel(),dC.ravel(),loss_rate]
 def maxC(self,y):
  n=self.nr*self.nz; C=y[n:2*n].reshape(self.nr,self.nz)
  # Reconstruct the symmetry-axis value from the first two cell centers.
  axis=(9*C[0,:]-C[1,:])/8 if self.nr >= 2 else C[0,:]
  return float(max(C.max(), axis.max()))

def run(chi,nr=20,nz=40,rtol=3e-6,max_step=1800,hcoef_=hcoef,hm_=hm,dscale=1.0,end_h=None,end_hm=None,fixed_radius=False):
 m=Axisym2D(nr,nz,chi,hcoef_,hm_,dscale,end_h=end_h,end_hm=end_hm,fixed_radius=fixed_radius); nn=nr*nz; y=np.r_[np.full(nn,28.),np.full(nn,2.55),0.]; knots=np.unique(np.r_[ENV[:,0],RAD[:,0] if not fixed_radius else [],np.arange(259200,30*86400+1,86400)])
 # Five-point spatial stencil plus local T-C coupling, duplicated for T and C blocks.
 pat=lil_matrix((2*nn+1,2*nn+1),dtype=int)
 for i in range(nr):
  for j in range(nz):
   p=i*nz+j
   for ii,jj in ((i,j),(max(0,i-1),j),(min(nr-1,i+1),j),(i,max(0,j-1)),(i,min(nz-1,j+1))):
    q=ii*nz+jj
    # Variable properties make both equations depend on neighboring T and C.
    pat[p,q]=1; pat[p,nn+q]=1
    pat[nn+p,nn+q]=1; pat[nn+p,q]=1
   pat[2*nn,p]=1; pat[2*nn,nn+p]=1
 pat=pat.tocsc()
 def ev(t,y): return m.maxC(y)-.15
 ev.terminal=True; ev.direction=-1; begin=time.perf_counter(); segs=[]; maxerr=0; stop=None
 for a,b in zip(knots[:-1],knots[1:]):
  aft=a>=14400
  sol=solve_ivp(lambda t,y:m.rhs(t,y,aft),(a,b),y,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(60.,b-a),events=ev,dense_output=True,jac_sparsity=pat)
  if not sol.success: raise RuntimeError(sol.message)
  y=sol.y[:,-1]; segs.append((a,sol.t[-1],sol.sol));
  if sol.t_events[0].size:
   stop=float(sol.t_events[0][0]); break
  # manually event from dense output; use solve event in next version
  vals=sol.y[nr*nz:2*nr*nz]
  if vals.max()<=.15:
   # locate crossing by rerunning segment event if crossing occurred; likely final step
   lo=max(a,sol.t[max(0,np.where(vals.max(axis=0)>0.15)[0][-1])]) if np.any(vals.max(axis=0)>0.15) else a
   # simpler rerun full interval with event from prior state impossible; detect interpolate
  # check previous segment crossing via endpoint only
  if m.maxC(y)<=.15:
   # binary on stored dense output for first crossing in segment
   s=segs[-1]; aa=float(a); bb=float(sol.t[-1]);
   # find bracket by sample
   grid=np.linspace(aa,bb,80); gv=[m.maxC(s[2](tt))-.15 for tt in grid]
   for i in range(len(grid)-1):
    if gv[i]>=0 and gv[i+1]<=0:
      from scipy.optimize import brentq
      stop=brentq(lambda tt:m.maxC(s[2](tt))-.15,grid[i],grid[i+1]); break
   if stop is not None: break
 if stop is None: raise RuntimeError('no crossing')
 # evaluate crossing state and +1s continuation
 ystar=segs[-1][2](stop); post=solve_ivp(lambda t,y:m.rhs(t,y,True),(stop,stop+1),ystar,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=1)
 yp=post.y[:,-1]; maxafter=m.maxC(yp)
 # integrated water mass using normalized volume: 2? half domain z; ratio to initial average
 C=ystar[nn:2*nn].reshape(nr,nz); avg=float(np.sum(C*m.ar[:,None]*m.az[None,:])/np.sum(m.ar[:,None]*m.az[None,:]))
 loss=float(ystar[-1]); mass_error=abs(avg+loss-2.55)
 Hlen=m.geom(stop)[2]; R=m.geom(stop)[0]
 return {'chi':chi,'nr':nr,'nz':nz,'seconds':float(stop),'hours':float(stop/3600),'max_after_1s':maxafter,'mean_C_at_cross':avg,'cumulative_loss':loss,'mass_balance_error':mass_error,'R_cm':R*100,'H_half_cm':Hlen*100,'runtime_s':time.perf_counter()-begin,'rtol':rtol,'max_step':max_step,'hcoef':hcoef_,'hm':hm_,'dscale':dscale}

if __name__=='__main__':
 out=[]
 for chi in (0.,.5,1.):
  print('running chi',chi,flush=True); out.append(run(chi,nr=8,nz=16,rtol=1e-4,max_step=3600))
 d=ROOT/'results'/'q4_2d_shrink'; d.mkdir(parents=True,exist_ok=True)
 (d/'summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))

