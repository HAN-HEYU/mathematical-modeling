import numpy as np, openpyxl, os, time, shutil
from pathlib import Path
from scipy.integrate import solve_ivp
from scipy.sparse import diags

PROJECT_ROOT=Path(__file__).resolve().parents[1]
DATA_ROOT=PROJECT_ROOT/'data'/'raw'
input_xlsx=str(DATA_ROOT/'附件1.xlsx')
out_xlsx=str(PROJECT_ROOT/'results'/'generated'/'result1.xlsx')
os.makedirs(os.path.dirname(out_xlsx), exist_ok=True)
if not os.path.exists(out_xlsx): shutil.copy2(DATA_ROOT/'result1.xlsx', out_xlsx)
# read environment
wb=openpyxl.load_workbook(input_xlsx,data_only=True)
ws=wb[wb.sheetnames[0]]
t=[]; Tenv=[]; Henv=[]
for row in ws.iter_rows(min_row=2,values_only=True):
    if row[0] is None: continue
    t.append(float(row[0])); Tenv.append(float(row[1])); Henv.append(float(row[2]))
t=np.array(t); Tenv=np.array(Tenv); Henv=np.array(Henv)

R=0.02; rho=820.; cp=2600.; k=0.36; h=25.; hm=8e-7
T0=28.; C0=2.55

def env_interp(tt, arr):
    return np.interp(tt,t,arr)

def Dfun(C):
    # Solver trial states should remain positive; protect only to avoid NaN in failed trial.
    return 7e-9*np.exp(-0.89/np.maximum(C,1e-12))


def make_rhs(N, kind):
    dr=R/N
    rc=(np.arange(N)+0.5)*dr
    rf=np.arange(N+1)*dr
    A=0.5*(rf[1:]**2-rf[:-1]**2)
    # tridiagonal sparsity
    if kind=='T':
        def rhs(tt,y):
            te=float(env_interp(tt,Tenv))
            F=np.empty(N+1)
            F[0]=0.0
            F[1:N]=rf[1:N]*k*(y[1:]-y[:-1])/dr
            K=k/(0.5*dr)
            Ts=(K*y[-1]+h*te)/(K+h)
            F[N]=-R*h*(Ts-te)
            return (F[1:]-F[:-1])/(rho*cp*A)
    else:
        def rhs(tt,y):
            he=float(env_interp(tt,Henv))
            D=Dfun(y)
            F=np.empty(N+1)
            F[0]=0.0
            # harmonic mean; positive states
            Dh=2*D[:-1]*D[1:]/np.maximum(D[:-1]+D[1:],1e-300)
            F[1:N]=rf[1:N]*Dh*(y[1:]-y[:-1])/dr
            # Half-cell resistance; D evaluated at the adjacent cell as
            # the finite-volume face coefficient (consistent as dr -> 0).
            K=D[-1]/(0.5*dr)
            Cs=(K*y[-1]+hm*he)/(K+hm)
            F[N]=-R*hm*(Cs-he)
            return (F[1:]-F[:-1])/A
    return rhs,rc,rf,A

def solve(N, kind, t_eval):
    rhs,rc,rf,A=make_rhs(N,kind)
    y0=np.full(N,T0 if kind=='T' else C0)
    # Constant-band Jacobian pattern (boundary nonlinearities are still local)
    pat=diags([np.ones(N-1),np.ones(N),np.ones(N-1)],[-1,0,1],shape=(N,N),format='csc')
    sol=solve_ivp(rhs,(0,float(t_eval[-1])),y0,t_eval=t_eval,method='BDF',rtol=2e-7,atol=1e-9 if kind=='T' else 1e-10,jac_sparsity=pat,max_step=30.0)
    if not sol.success: raise RuntimeError(sol.message)
    # reconstruct surface for each time
    surf=[]
    for j,tt in enumerate(sol.t):
        env=float(env_interp(tt,Tenv if kind=='T' else Henv))
        if kind=='T':
            K=k/(0.5*(R/N)); surf.append((K*sol.y[-1,j]+h*env)/(K+h))
        else:
            D=Dfun(sol.y[-1,j]); K=D/(0.5*(R/N)); surf.append((K*sol.y[-1,j]+hm*env)/(K+hm))
    return sol.t,sol.y,rc,np.array(surf)

def sample(sol_y,rc,surf,rs):
    # values at r=0, interior radii, and R via piecewise linear reconstruction
    N=sol_y.shape[0]; nt=sol_y.shape[1]
    out=np.empty((nt,len(rs)))
    x=np.r_[0.0,rc,R]
    for j in range(nt):
        y=np.r_[sol_y[0,j],sol_y[:,j],surf[j]]
        out[j]=np.interp(rs,x,y)
    return out

if __name__=='__main__':
    t_eval=np.arange(1,1801,dtype=float)
    rs=np.arange(0,0.0200001,0.001)
    # N=3200 is used for the delivered table; N=100/200/400/800 are
    # convenient coarser levels for the convergence check.
    N_final=3200
    t0=time.time(); tt,Ty,rc,Ts=solve(N_final,'T',t_eval); print('T done',time.time()-t0,Ty.min(),Ty.max(),Ts[-1])
    t0=time.time(); tc,Cy,rc,Cs=solve(N_final,'C',t_eval); print('C done',time.time()-t0,Cy.min(),Cy.max(),Cs[-1])
    Tout=sample(Ty,rc,Ts,rs); Cout=sample(Cy,rc,Cs,rs)
    # write template, preserving styles where possible
    wb=openpyxl.load_workbook(out_xlsx)
    # use first two sheets
    for sname,data in [('温度',Tout),('水分浓度',Cout)]:
        ws=wb[sname]
        # clear existing values except style by setting None in existing range
        for row in ws.iter_rows():
            for cell in row: cell.value=None
        ws.cell(1,1).value='时间\\到药材中心的距离'
        for j,rval in enumerate(rs, start=2): ws.cell(1,j).value=round(rval*100,10)
        for i,tv in enumerate(t_eval,start=2):
            ws.cell(i,1).value=int(tv)
            for j,val in enumerate(data[i-2],start=2): ws.cell(i,j).value=round(float(val),4)
    wb.save(out_xlsx)
    # save unrounded arrays for audit
    np.savez('q1_solution_N3200.npz',time=t_eval,r=rs,T=Tout,C=Cout)
    # paper table print
    wanted=[100,300,600,900,1200,1500,1800]
    idx=[x-1 for x in wanted]
    print('T table'); print(np.round(Tout[idx][:,[0,5,10,15,20]],6))
    print('C table'); print(np.round(Cout[idx][:,[0,5,10,15,20]],6))
