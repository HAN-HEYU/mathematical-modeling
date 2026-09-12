"""Real r-z Q3 finite volumes; same Kirchhoff radial flux as solve_q34.Model.

All cases retain axial neighbor diffusion. End heat and mass transfer switches
are independent. Every case locates its own event and saves its actual state.
No latent heat is included, consistent with the existing effective model.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import expi
from scipy.sparse import lil_matrix
from scipy.interpolate import RegularGridInterpolator
import solve_q34 as base

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / 'data' / 'raw' / 'drying_A'
OUT = ROOT / 'results' / 'drying_model' / 'q3_2d_endface'


def primitive(c):
    return c * np.exp(-.45 / c) + .45 * expi(-.45 / c)


def boundary_c(c, tc, ts, distance, hm, eq):
    if hm == 0:
        return c.copy()
    scale = 2.4e-3 * np.exp(-3850 / ((tc + ts) / 2 + 273.15)) / distance
    pc = primitive(c)
    lo, hi = np.minimum(c, eq), np.maximum(c, eq)
    linear = scale * np.exp(-.45 / c)
    x = (linear * c + hm * eq) / (linear + hm)
    for _ in range(60):
        f = scale * (pc - primitive(x)) - hm * (x - eq)
        active = np.abs(f) > 2e-21
        if not active.any():
            return x
        lo = np.where(active & (f > 0), x, lo)
        hi = np.where(active & (f <= 0), x, hi)
        new = x + f / (scale * np.exp(-.45 / x) + hm)
        new = np.where((new > lo) & (new < hi), new, (lo + hi) / 2)
        if np.max(np.where(active, np.abs(new - x), 0)) < 2e-14:
            return np.where(active, new, x)
        x = np.where(active, new, x)
    raise RuntimeError('Nonlinear Robin boundary root did not converge')


class Model2D:
    def __init__(self, nr, nz, end_hm=base.HM, end_h=base.H, shrink_radius=False):
        self.nr, self.nz = nr, nz
        self.end_hm, self.end_h = end_hm, end_h
        self.radial = base.Model(3, nr, fixed=not shrink_radius)
        self.shrink_radius = shrink_radius
        self.R, self.H = .02, .125
        self.x = self.radial.x
        self.z = (np.arange(nz) + .5) / nz
        self.a = self.radial.a
        self.weights = np.broadcast_to(2 * self.a[None, :] / nz, (nz, nr))
        self.nn = nr * nz

    def unpack(self, y):
        return y[:self.nn].reshape(self.nz, self.nr), y[self.nn:2*self.nn].reshape(self.nz, self.nr)

    def geom(self, t):
        return (self.radial.radius(t) if self.shrink_radius else self.R), self.H

    def fluxes(self, t, y, after):
        T, C = self.unpack(y)
        rho, cp, k, _ = self.radial.properties(T, C)
        te, ce = self.radial.environment(t, after)
        g = 2.4e-3 * np.exp(-3850 / (T + 273.15))
        p = primitive(C)
        # Physical radial and axial half-cell distances.
        R,H = self.geom(t)
        dr, dz = R / self.nr, H / self.nz
        tr = (k[:, -1] * T[:, -1] / (dr/2) + base.H * te) / (k[:, -1] / (dr/2) + base.H)
        cr = boundary_c(C[:, -1], T[:, -1], tr, dr/2, base.HM, ce)
        tz = (k[-1] * T[-1] / (dz/2) + self.end_h * te) / (k[-1] / (dz/2) + self.end_h)
        cz = boundary_c(C[-1], T[-1], tz, dz/2, self.end_hm, ce)
        ft = np.zeros((self.nz, self.nr+1)); fc = np.zeros_like(ft)
        zt = np.zeros((self.nz+1, self.nr)); zc = np.zeros_like(zt)
        faces = self.radial.faces[1:-1]
        ft[:, 1:-1] = faces * (2*k[:, :-1]*k[:, 1:]/(k[:, :-1]+k[:, 1:])) * np.diff(T, axis=1)*self.nr
        fc[:, 1:-1] = faces * (2*g[:, :-1]*g[:, 1:]/(g[:, :-1]+g[:, 1:])) * np.diff(p, axis=1)*self.nr
        ft[:, -1] = R * base.H * (te-tr)
        fc[:, -1] = R * base.HM * (ce-cr)
        zt[1:-1] = (2*k[:-1]*k[1:]/(k[:-1]+k[1:])) * np.diff(T, axis=0)*self.nz
        zc[1:-1] = (2*g[:-1]*g[1:]/(g[:-1]+g[1:])) * np.diff(p, axis=0)*self.nz
        zt[-1] = H * self.end_h * (te-tz)
        zc[-1] = H * self.end_hm * (ce-cz)
        return ft, fc, zt, zc, rho*cp, tr, cr, tz, cz

    def rhs(self, t, y, after):
        ft, fc, zt, zc, cap, *_ = self.fluxes(t, y, after)
        R,H = self.geom(t)
        dt = (np.diff(ft, axis=1)/(R**2*self.a) + np.diff(zt, axis=0)*self.nz/H**2)/cap
        dc = np.diff(fc, axis=1)/(R**2*self.a) + np.diff(zc, axis=0)*self.nz/H**2
        loss_side = -2*np.mean(fc[:, -1])/R**2
        loss_end = -2*np.dot(self.a, zc[-1])/H**2
        return np.r_[dt.ravel(), dc.ravel(), loss_side, loss_end]

    def maximum(self, y):
        _, C = self.unpack(y)
        axis = (9*C[:, 0]-C[:, 1])/8
        midplane = (9*C[0]-C[1])/8
        center = float((9*axis[0]-axis[1])/8)
        return max(float(C.max()), float(axis.max()), float(midplane.max()), center)

    def center(self, y):
        _, c = self.unpack(y)
        return float((81*c[0,0]-9*c[0,1]-9*c[1,0]+c[1,1])/64)

    def pattern(self):
        p = lil_matrix((2*self.nn+2, 2*self.nn+2), dtype=int)
        for j in range(self.nz):
            for i in range(self.nr):
                s = j*self.nr+i
                for jj, ii in ((j,i),(j,max(i-1,0)),(j,min(i+1,self.nr-1)),(max(j-1,0),i),(min(j+1,self.nz-1),i)):
                    u = jj*self.nr+ii
                    for off in (0,self.nn):
                        p[s, u+off] = 1; p[s+self.nn,u+off] = 1
                if i == self.nr-1:
                    p[2*self.nn,s] = 1; p[2*self.nn,s+self.nn] = 1
                if j == self.nz-1:
                    p[2*self.nn+1,s] = 1; p[2*self.nn+1,s+self.nn] = 1
        return p.tocsc()

    def table(self, t, y, radii, heights):
        # Symmetry traces reconstructed in both directions. End/side traces
        # use their own Robin roots. Do not invent the intersection value.
        _, C = self.unpack(y)
        *_, tr, cr, tz, cz = self.fluxes(t,y,t>=14400)
        c = np.zeros((self.nz+2, self.nr+2)); c[1:-1,1:-1] = C
        c[1:-1,0] = (9*C[:,0]-C[:,1])/8
        c[0,1:-1] = (9*C[0]-C[1])/8
        c[0,0] = self.center(y)
        c[1:-1,-1] = cr; c[-1,1:-1] = cz
        c[0,-1] = (9*cr[0]-cr[1])/8
        c[-1,0] = (9*cz[0]-cz[1])/8
        # Internal placeholder, excluded explicitly from exported samples.
        c[-1,-1] = (cz[-1]+cr[-1])/2
        R,H = self.geom(t)
        z = np.r_[0,self.z,1]*H; r = np.r_[0,self.x,1]*R
        f = RegularGridInterpolator((z,r),c)
        out = []
        for zz in heights:
            row=[]
            for rr in radii:
                row.append(None if abs(zz-self.H)<1e-12 and abs(rr-self.R)<1e-12 else float(f([[zz,rr]])[0]))
            out.append(row)
        return out


def reduction_check(nr=12,nz=6):
    m = Model2D(nr,nz,end_hm=0,end_h=0)
    T = 47 + 2*m.x**2; C = .12 + .5*(1-m.x**2)
    y = np.r_[np.tile(T,nz),np.tile(C,nz),0,0]
    d = m.rhs(50000,y,True)
    b = m.radial.rhs(50000,np.r_[T,C,0],True)
    errT = float(np.max(np.abs(d[:m.nn].reshape(nz,nr)-b[:nr])))
    errC = float(np.max(np.abs(d[m.nn:2*m.nn].reshape(nz,nr)-b[nr:2*nr])))
    assert max(errT,errC) < 1e-12
    return {'max_rhs_T_error':errT,'max_rhs_C_error':errC}


def run(nr=40,nz=32,end_hm=base.HM,end_h=base.H,rtol=1e-8,max_step=1800,label='open',shrink_radius=False):
    OUT.mkdir(parents=True,exist_ok=True)
    m = Model2D(nr,nz,end_hm,end_h,shrink_radius=shrink_radius)
    pat = m.pattern()
    y = np.r_[np.full(m.nn,28.),np.full(m.nn,2.55),0.,0.]
    knots = np.unique(np.r_[base.ENV[:,0],base.RAD[:,0] if shrink_radius else [],np.arange(21600,72*3600+1,21600)])
    def event(t,y): return m.maximum(y)-.15
    event.terminal=True; event.direction=-1
    begin=time.perf_counter(); snapshots=[]; masserr=0.; minC=2.55; minT=28.; maxT=28.; stop=None
    for a,b in zip(knots[:-1],knots[1:]):
        after=a>=14400
        s=solve_ivp(lambda t,y:m.rhs(t,y,after),(a,b),y,method='BDF',jac_sparsity=pat,
            rtol=rtol,atol=rtol*.001,max_step=max_step,first_step=min(.01,b-a),events=event)
        if not s.success: raise RuntimeError(s.message)
        means=m.weights.ravel() @ s.y[m.nn:2*m.nn]
        masserr=max(masserr,float(np.max(np.abs(means+s.y[-2]+s.y[-1]-2.55))))
        minC=min(minC,float(s.y[m.nn:2*m.nn].min()))
        minT=min(minT,float(s.y[:m.nn].min())); maxT=max(maxT,float(s.y[:m.nn].max()))
        y=s.y[:,-1]
        if b%21600==0 or s.t_events[0].size:
            snapshots.append({'time_h':float(s.t[-1]/3600),'C_mid':m.table(float(s.t[-1]),y,[0,.005,.01,.015,.02],[0])[0]})
        if s.t_events[0].size:
            stop=float(s.t_events[0][0]); y=s.y_events[0][0]; break
    if stop is None: raise RuntimeError('No independent threshold event by 72 h')
    post=solve_ivp(lambda t,y:m.rhs(t,y,True),(stop,stop+1),y,method='BDF',jac_sparsity=pat,
                  rtol=rtol,atol=rtol*.001,max_step=1)
    if not post.success: raise RuntimeError(post.message)
    T,C=m.unpack(y)
    heights=[0,.025,.05,.075,.1,.12,.125]; radii=[0,.005,.01,.015,.02]
    ans={'case':label,'nr':nr,'nz':nz,'rtol':rtol,'max_step':max_step,'end_h':end_h,'end_hm':end_hm,
         'seconds':stop,'hours':stop/3600,'center_C':m.center(y),'maximum_C':m.maximum(y),
         'maximum_after_1s':m.maximum(post.y[:,-1]),'mass_balance_error':masserr,'min_C':minC,
         'temperature_range':[minT,maxT],'axial_C_spread':float(np.ptp(C,axis=0).max()),
         'axial_increases':float(np.diff(C,axis=0).max()),'radial_increases':float(np.diff(C,axis=1).max()),
         'side_cumulative_loss':float(y[-2]),'end_cumulative_loss':float(y[-1]),
         'C_mean':float(np.sum(C*m.weights)),'r_cm':list(np.array(radii)*100),
         'z_from_midplane_cm':list(np.array(heights)*100),'C_table':m.table(stop,y,radii,heights),
         'midplane_time_series':snapshots,'runtime_s':time.perf_counter()-begin,
         'input_hashes':{name:hashlib.sha256((DATA_ROOT/name).read_bytes()).hexdigest() for name in ['附件1.xlsx']}}
    assert ans['maximum_after_1s']<.15 and minC>0 and masserr<1e-7
    np.savez_compressed(OUT/f'{label}_{nr}x{nz}.npz',time_s=stop,T=T,C=C,state=y,x=m.x,z=m.z)
    (OUT/f'{label}_{nr}x{nz}.json').write_text(json.dumps(ans,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:ans[k] for k in ['case','nr','nz','hours','center_C','maximum_after_1s','mass_balance_error','runtime_s']},ensure_ascii=False),flush=True)
    return ans


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--nr',type=int,default=40); ap.add_argument('--nz',type=int,default=32)
    ap.add_argument('--case',choices=['open','closed','mass_only'],default='open'); ap.add_argument('--rtol',type=float,default=1e-8)
    args=ap.parse_args(); print('reduction',reduction_check(),flush=True)
    run(args.nr,args.nz,0 if args.case=='closed' else base.HM,base.H if args.case=='open' else 0,args.rtol,label=args.case)
