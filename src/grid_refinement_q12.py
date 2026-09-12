"""Bounded grid study of existing Q1/Q2 spatial operators; no original outputs overwritten.
Run: python grid_refinement_q12.py --grids 200 400 800 1600 3200
Outputs are sampled each second at all 21 required radii. All solves restart at
environment knots so nonsmooth forcing does not confound spatial convergence.
"""
from pathlib import Path
import argparse, csv, hashlib, json, os, platform, time
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.sparse import diags, bmat

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
import solve_q1 as q1
import solve_q2 as q2

OUT = ROOT / 'results' / 'grid_convergence' / 'q12'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def integrate(q, n, rtol=2e-10, atol=1e-12, max_step=5., end=None):
    end = end or (1800 if q == 1 else 10800)
    radii = np.arange(21) * .001
    tri = diags([np.ones(n-1), np.ones(n), np.ones(n-1)], [-1, 0, 1], format='csc')
    if q == 1:
        rhsT, rc, _, _ = q1.make_rhs(n, 'T')
        rhsC, _, _, _ = q1.make_rhs(n, 'C')
        systems = [(rhsT, np.full(n, 28.), tri), (rhsC, np.full(n, 2.55), tri)]
    else:
        rhs, rc = q2.make_rhs(n)
        systems = [(rhs, np.r_[np.full(n, 28.), np.full(n, 2.55)], bmat([[tri, tri], [tri, tri]], format='csc'))]
    times = np.arange(1., end+1)
    Tout = np.empty((end, 21)); Cout = np.empty_like(Tout)
    knots = np.unique(np.r_[0., q1.t[(q1.t > 0) & (q1.t < end)], float(end)])
    stats = dict(q=q, N=n, rtol=rtol, atol=atol, max_step_s=max_step,
                 end_s=end, nfev=0, min_C=2.55, max_C=2.55, min_T=28., max_T=28.)
    start = time.perf_counter()
    d = .02 / (2*n)
    for sysindex, (rhs, state, pat) in enumerate(systems):
        for a, b in zip(knots[:-1], knots[1:]):
            tt = times[(times > a) & (times <= b)]
            sol = solve_ivp(rhs, (a,b), state, method='BDF', rtol=rtol, atol=atol,
                            max_step=max_step, jac_sparsity=pat, dense_output=True)
            assert sol.success, sol.message
            assert np.isfinite(sol.y).all()
            state = sol.y[:, -1]
            Y = sol.sol(tt)
            stats['nfev'] += sol.nfev
            te = np.interp(tt, q1.t, q1.Tenv); he = np.interp(tt, q1.t, q1.Henv)
            idx = tt.astype(int)-1
            if q == 1:
                if sysindex == 0:
                    T = Y; Ts = ((q1.k/d)*T[-1]+q1.h*te)/(q1.k/d+q1.h)
                    Tout[idx] = q1.sample(T, rc, Ts, radii)
                    stats['min_T'] = min(stats['min_T'], float(sol.y.min()), float(Ts.min()))
                    stats['max_T'] = max(stats['max_T'], float(sol.y.max()), float(Ts.max()))
                else:
                    C = Y; KC = q1.Dfun(C[-1])/d; Cs = (KC*C[-1]+q1.hm*he)/(KC+q1.hm)
                    Cout[idx] = q1.sample(C, rc, Cs, radii)
                    stats['min_C'] = min(stats['min_C'], float(sol.y.min()), float(Cs.min()))
                    stats['max_C'] = max(stats['max_C'], float(sol.y.max()), float(Cs.max()))
            else:
                T, C = Y[:n], Y[n:]
                KT = q2.kval(C[-1])/d; KC = q2.Dval(C[-1],T[-1])/d
                Ts = (KT*T[-1]+q2.h*te)/(KT+q2.h)
                Cs = (KC*C[-1]+q2.hm*he)/(KC+q2.hm)
                Tout[idx] = q2.sample(T,rc,Ts,radii); Cout[idx] = q2.sample(C,rc,Cs,radii)
                stats['min_T'] = min(stats['min_T'],float(sol.y[:n].min()),float(Ts.min()))
                stats['max_T'] = max(stats['max_T'],float(sol.y[:n].max()),float(Ts.max()))
                stats['min_C'] = min(stats['min_C'],float(sol.y[n:].min()),float(Cs.min()))
                stats['max_C'] = max(stats['max_C'],float(sol.y[n:].max()),float(Cs.max()))
    assert stats['min_C'] > 0 and np.isfinite(Tout).all() and np.isfinite(Cout).all()
    stats['runtime_s'] = time.perf_counter()-start
    return times, radii, Tout, Cout, stats

def compare(a, b, times, radii):
    d = np.abs(a-b); ix = np.unravel_index(np.argmax(d),d.shape)
    return dict(max_abs=float(d[ix]), time_s=float(times[ix[0]]), radius_cm=float(radii[ix[1]]*100),
                rms=float(np.sqrt(np.mean(d*d))), surface_max=float(d[:,-1].max()),
                nonsurface_max=float(d[:,:-1].max()),
                rounded4_different=int(np.count_nonzero(np.round(a,4)!=np.round(b,4))),total=int(d.size))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--grids',nargs='+',type=int,default=[200,400,800,1600,3200])
    ap.add_argument('--questions',nargs='+',type=int,default=[1,2]); ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--tight-check',action='store_true'); args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    assert len(q1.t)==241 and q1.t[0]==0 and q1.t[-1]==14400 and np.all(np.diff(q1.t)==60)
    assert np.array_equal(q1.t,q2.te) and np.array_equal(q1.Tenv,q2.Tenv) and np.array_equal(q1.Henv,q2.Henv)
    for q in args.questions:
        for n in args.grids:
            label='smoke' if args.smoke else 'strict'
            dest=OUT/f'q{q}_N{n}_{label}.npz'
            if not dest.exists():
                tt,rs,T,C,stats=integrate(q,n,end=120 if args.smoke else None)
                np.savez_compressed(dest,time=tt,r=rs,T=T,C=C,stats=json.dumps(stats))
            else: stats=json.loads(str(np.load(dest)['stats']))
            print(json.dumps(stats),flush=True)
        if args.tight_check and not args.smoke:
            n=max(args.grids);dest=OUT/f'q{q}_N{n}_tighter.npz'
            if not dest.exists():
                tt,rs,T,C,stats=integrate(q,n,rtol=2e-11,atol=1e-13,max_step=2.5)
                np.savez_compressed(dest,time=tt,r=rs,T=T,C=C,stats=json.dumps(stats))
            else: stats=json.loads(str(np.load(dest)['stats']))
            print(json.dumps(stats),flush=True)
    if args.smoke: return
    report={'method':'Original spatial RHS and original surface/center sampling; BDF restarted at all 60 s environment knots.',
            'scope':'Q1 1..1800 s; Q2 1..10800 s; radii 0..2 cm every 0.1 cm',
            'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
            'sha256':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'附件/附件1.xlsx',ROOT/'solve_q1.py',ROOT/'solve_q2.py',Path(__file__)]},
            'comparisons':[],'runs':[]}
    terminal=[]
    for q in args.questions:
        data={n:np.load(OUT/f'q{q}_N{n}_strict.npz') for n in args.grids}
        pairs=[('grid',a,b,data[a],data[b]) for a,b in zip(args.grids[:-1],args.grids[1:])]
        delivered=3200 if q==1 else 800
        original=ROOT/f'q{q}_solution_N{delivered}.npz'
        if delivered in data and original.exists():
            pairs.append(('original_vs_strict_same_grid',delivered,delivered,np.load(original),data[delivered]))
        for n in args.grids:
            tight=OUT/f'q{q}_N{n}_tighter.npz'
            if tight.exists(): pairs.append(('time',n,n,data[n],np.load(tight)))
        for kind,n1,n2,a,b in pairs:
            assert np.array_equal(a['time'],b['time']) and np.allclose(a['r'],b['r'],atol=1e-14,rtol=0)
            for field in ['T','C']:
                report['comparisons'].append(dict(q=q,kind=kind,field=field,N_from=n1,N_to=n2,**compare(a[field],b[field],b['time'],b['r'])))
        for n,a in data.items():
            report['runs'].append(json.loads(str(a['stats'])))
            for field in ['T','C']:
                for col in [0,5,10,15,20]: terminal.append(dict(q=q,N=n,field=field,time_s=float(a['time'][-1]),radius_cm=float(a['r'][col]*100),value=float(a[field][-1,col])))
    (OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,rows in [('comparisons.csv',report['comparisons']),('terminal_values.csv',terminal),('runs.csv',report['runs'])]:
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(report['comparisons'],ensure_ascii=False),flush=True)

if __name__=='__main__': main()
