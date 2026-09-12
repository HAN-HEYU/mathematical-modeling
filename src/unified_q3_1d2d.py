import json, time
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import block_diag
import solve_q34 as base

def run_unified(n=80,nz=8,rtol=2e-7,max_step=1800):
    # Same radial Model, fluxes, interpolation, tolerances and event logic as q3 1-D.
    m=base.Model(3,n,scenario='mean',fixed=False)
    # q=3 in base.Model has fixed radius; use Appendix-3 properties.
    y1=np.r_[np.full(n,28.),np.full(n,2.55),0.]
    y2=np.tile(y1[:-1],nz)  # independent axial slices; no axial flux
    knots=np.unique(np.r_[base.ENV[:,0],np.arange(259200,30*86400+1,86400)])
    stop1=None; stop2=None; begin=time.perf_counter()
    def rhs1(t,y,after): return m.rhs(t,y,after)
    def rhs2(t,y,after):
        out=np.empty_like(y)
        for j in range(nz):
            ys=np.r_[y[j*2*n:(j+1)*2*n],0.]
            out[j*2*n:(j+1)*2*n]=m.rhs(t,ys,after)[:2*n]
        return out
    def ev1(t,y): return m.maximum(y[n:2*n])-.15
    def ev2(t,y): return max(m.maximum(y[j*2*n+n:(j+1)*2*n]) for j in range(nz))-.15
    ev1.terminal=ev2.terminal=True; ev1.direction=ev2.direction=-1
    # sparse block pattern for the replicated 2-D slices
    tri=base.diags([np.ones(n-1),np.ones(n),np.ones(n-1)],[-1,0,1],format='csc')
    p1=base.bmat([[tri,tri],[tri,tri]],format='csc')
    p2=block_diag([p1]*nz,format='csc')
    y1c=y1.copy(); y2c=y2.copy()
    for a,b in zip(knots[:-1],knots[1:]):
        aft=a>=14400
        s1=solve_ivp(lambda t,y:rhs1(t,y,aft),(a,b),y1c,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev1,jac_sparsity=base.bmat([[p1,base.csr_matrix((2*n,1))],[base.csr_matrix((1,2*n)),base.csr_matrix((1,1))]],format='csc'))
        s2=solve_ivp(lambda t,y:rhs2(t,y,aft),(a,b),y2c,method='BDF',rtol=rtol,atol=rtol*1e-3,max_step=max_step,first_step=min(.01,b-a),events=ev2,jac_sparsity=p2)
        if not s1.success or not s2.success: raise RuntimeError((s1.message,s2.message))
        y1c=s1.y[:,-1]; y2c=s2.y[:,-1]
        if s1.t_events[0].size: stop1=float(s1.t_events[0][0]); break
        if s2.t_events[0].size: stop2=float(s2.t_events[0][0]); break
    # Never fabricate the missing event. This legacy sliced experiment is
    # superseded by q3_unified_axisymmetric.py, which retains axial coupling.
    if stop1 is None or stop2 is None:
        raise RuntimeError('Legacy run did not independently locate both events; use q3_unified_axisymmetric.py')
    return {'n':n,'nz':nz,'one_d_hours':stop1/3600,'two_d_hours':stop2/3600,'one_d_seconds':stop1,'two_d_seconds':stop2,'difference_seconds':stop2-stop1,'runtime_s':time.perf_counter()-begin}

if __name__=='__main__':
    r=run_unified(); print(json.dumps(r,indent=2)); open('results/q3_unified_1d2d.json','w').write(json.dumps(r,indent=2))
