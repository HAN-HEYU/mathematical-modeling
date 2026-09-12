import numpy as np, openpyxl, os, time, shutil
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
DATA_ROOT=PROJECT_ROOT/'data'/'raw'
from scipy.integrate import solve_ivp
OUTPUT_XLSX=PROJECT_ROOT/'results'/'generated'/'result2.xlsx'
OUTPUT_XLSX.parent.mkdir(parents=True,exist_ok=True)
if not OUTPUT_XLSX.exists(): shutil.copy2(DATA_ROOT/'result2.xlsx', OUTPUT_XLSX)
from scipy.sparse import diags, bmat

R=0.02; h=25.; hm=8e-7; T0=28.; C0=2.55
# environment
wb0=openpyxl.load_workbook(str(DATA_ROOT/'附件1.xlsx'),data_only=True); ws0=wb0[wb0.sheetnames[0]]
te=[]; Tenv=[]; Henv=[]
for row in ws0.iter_rows(min_row=2,values_only=True):
    if row[0] is not None: te.append(float(row[0])); Tenv.append(float(row[1])); Henv.append(float(row[2]))
te=np.asarray(te); Tenv=np.asarray(Tenv); Henv=np.asarray(Henv)

def env(tt,a): return np.interp(tt,te,a)
def rho(C): return 650+128*C
def cp(C): return 1450+2736*C/(C+1)
def kval(C): return .21+.38*C/(C+1)
def Dval(C,T): return 2.4e-3*np.exp(-.45/np.maximum(C,1e-12))*np.exp(-3850/(np.maximum(T,-273.14)+273.15))

def make_rhs(N):
 dr=R/N; rc=(np.arange(N)+.5)*dr; rf=np.arange(N+1)*dr; A=.5*(rf[1:]**2-rf[:-1]**2); d=.5*dr
 def rhs(t,y):
  T=y[:N]; C=y[N:]; Ti=float(env(t,Tenv)); Hi=float(env(t,Henv));
  rr=rho(C); cc=cp(C); kk=kval(C); DD=Dval(C,T)
  FT=np.empty(N+1); FC=np.empty(N+1); FT[0]=0; FC[0]=0
  kf=2*kk[:-1]*kk[1:]/np.maximum(kk[:-1]+kk[1:],1e-300)
  df=2*DD[:-1]*DD[1:]/np.maximum(DD[:-1]+DD[1:],1e-300)
  FT[1:N]=rf[1:N]*kf*(T[1:]-T[:-1])/dr
  FC[1:N]=rf[1:N]*df*(C[1:]-C[:-1])/dr
  KT=kk[-1]/d; Ts=(KT*T[-1]+h*Ti)/(KT+h); FT[N]=-R*h*(Ts-Ti)
  KC=DD[-1]/d; Cs=(KC*C[-1]+hm*Hi)/(KC+hm); FC[N]=-R*hm*(Cs-Hi)
  return np.r_[(FT[1:]-FT[:-1])/(A*rr*cc),(FC[1:]-FC[:-1])/A]
 return rhs,rc

def solve(N,t_eval):
 rhs,rc=make_rhs(N); dr=R/N; N2=2*N; tri=diags([np.ones(N-1),np.ones(N),np.ones(N-1)],[-1,0,1],shape=(N,N),format='csc'); pat=bmat([[tri,tri],[tri,tri]],format='csc')
 y0=np.r_[np.full(N,T0),np.full(N,C0)]
 sol=solve_ivp(rhs,(0,float(t_eval[-1])),y0,t_eval=t_eval,method='BDF',rtol=2e-6,atol=np.r_[np.full(N,1e-8),np.full(N,1e-10)],jac_sparsity=pat,max_step=60.)
 if not sol.success: raise RuntimeError(sol.message)
 T=sol.y[:N]; C=sol.y[N:]; Ts=[]; Cs=[]
 for j,tt in enumerate(sol.t):
  Ti=float(env(tt,Tenv)); Hi=float(env(tt,Henv)); kk=kval(C[:,j]); DD=Dval(C[:,j],T[:,j]);
  KT=kk[-1]/(dr/2); Ts.append((KT*T[-1,j]+h*Ti)/(KT+h)); KC=DD[-1]/(dr/2); Cs.append((KC*C[-1,j]+hm*Hi)/(KC+hm))
 return sol.t,T,C,rc,np.asarray(Ts),np.asarray(Cs)

def sample(Y,rc,surf,rs):
 out=np.empty((Y.shape[1],len(rs))); x=np.r_[0.,rc,R]
 for j in range(Y.shape[1]): out[j]=np.interp(rs,x,np.r_[Y[0,j],Y[:,j],surf[j]])
 return out

if __name__=='__main__':
 t_eval=np.arange(1.,10801.); rs=np.arange(0.,R+1e-12,.001); N=800
 t0=time.time(); tt,T,C,rc,Ts,Cs=solve(N,t_eval); print('runtime',time.time()-t0,'T',T.min(),T.max(),'C',C.min(),C.max(),'surface',Ts[-1],Cs[-1])
 To=sample(T,rc,Ts,rs); Co=sample(C,rc,Cs,rs)
 wb=openpyxl.load_workbook(str(OUTPUT_XLSX))
 for sname,data in [('温度',To),('水分浓度',Co)]:
  ws=wb[sname]
  for row in ws.iter_rows():
   for cell in row: cell.value=None
  ws.cell(1,1).value='时间\\到药材中心的距离'
  for j,r in enumerate(rs,2): ws.cell(1,j).value=round(r*100,10)
  for i,tv in enumerate(t_eval,2):
   ws.cell(i,1).value=int(tv)
   for j,v in enumerate(data[i-2],2): ws.cell(i,j).value=round(float(v),4)
 wb.save(str(OUTPUT_XLSX))
 np.savez('q2_solution_N800.npz',time=tt,r=rs,T=To,C=Co)
 for hour in [.5,1,1.5,2,2.5,3]:
  j=int(hour*3600)-1; print(hour, 'T',*[f'{v:.6f}' for v in To[j,[0,5,10,15,20]]]); print(hour,'C',*[f'{v:.6f}' for v in Co[j,[0,5,10,15,20]]])
