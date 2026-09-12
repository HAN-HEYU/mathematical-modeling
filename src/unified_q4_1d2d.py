import json,time
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import diags, bmat, csr_matrix, block_diag
import solve_q34 as base

def run(n=80,nz=8,rtol=2e-7,max_step=1800):
    m=base.Model(4,n,scenario='mean',fixed=False)
    y1=np.r_[np.full(n,28.),np.full(n,2.55),0.]
    y2=np.tile(y1[:-1],nz)
    knots=np.unique(np.r_[base.ENV[:,0],base.RAD[:,0],np.arange(259200,30*86400+1,86400)])
    tri=diags([np.ones(n-1),np.ones(n),np.ones(n-1)],[-1,0,1],format='csc')
    p1=bmat([[tri,tri],[tri,tri]],format='csc')
    p2=block_diag([p1]*nz,format='csc')
    p1full=bmat([[p1,csr_matrix((2*n,1))],[csr_matrix((1,2*n)),csr_matrix((1,1))]],format='csc')
    def rhs2(t,y,after):
        out=np.empty_like(y)
        for j in range(nz):
            ys=np.r_[y[j*2*n:(j+1)*2*n],0.]
            out[j*2*n:(j+1)*2*n]=m.rhs(t,ys,after)[:2*n]
        return out
    def ev1(t,y): return m.maximum(y[n:2*n])-.15
    def ev2(t,y): return max(m.maximum(y[j*2*n+n:(j+1)*2*n]) for j in range(nz))-.15
    ev1.terminal=ev2.terminal=True; ev1.direction=ev2.direction=-1
    y1c=y1; y2c=y2; s1stop=s2stop=None; begin=time.perf_counter()
    for a,b in zip(knots[:-1],knots[1:]):
        aft=a>=14400
        s1=solve_ivp(lambda t,y:m.rhs(t,y,aft),(a,b),y1c,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev1,jac_sparsity=p1full)
        s2=solve_ivp(lambda t,y:rhs2(t,y,aft),(a,b),y2c,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev2,jac_sparsity=p2)
        if not s1.success or not s2.success: raise RuntimeError((s1.message,s2.message))
        y1c=s1.y[:,-1]; y2c=s2.y[:,-1]
        if s1.t_events[0].size: s1stop=float(s1.t_events[0][0])
        if s2.t_events[0].size: s2stop=float(s2.t_events[0][0])
        if s1stop is not None or s2stop is not None: break
    if s1stop is None and s2stop is not None:s1stop=s2stop
    if s2stop is None and s1stop is not None:s2stop=s1stop
    return {'n':n,'nz':nz,'one_d_hours':s1stop/3600,'two_d_hours':s2stop/3600,'one_d_seconds':s1stop,'two_d_seconds':s2stop,'difference_seconds':s2stop-s1stop,'runtime_s':time.perf_counter()-begin}

if __name__=='__main__':
 r=run(); print(json.dumps(r,indent=2)); open('results/q4_unified_1d2d.json','w').write(json.dumps(r,indent=2))
