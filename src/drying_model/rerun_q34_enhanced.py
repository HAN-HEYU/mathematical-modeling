from pathlib import Path
import json, numpy as np, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from solve_q34 import run
out=ROOT/'results'/'q34_enhanced'
out.mkdir(parents=True,exist_ok=True)
# diagnostic rerun: Q3 and full Q4 at moderate resolution, plus Q4 shrinkage-off control
runs={}
for label,q,fixed in [('Q3_main',3,False),('Q4_main',4,False),('Q4_shrinkage_off',4,True)]:
    m,ev,s=run(q,n=200,rtol=2e-8,max_step=600,fixed=fixed)
    runs[label]=s
# postprocess high-resolution existing Q4 trajectory for feasibility audits
z=np.load(ROOT/'q4_full_precision.npz',allow_pickle=True); d=z['data']; cols=list(z['columns'])
t=d[:,0]; C=d[:,1:22]; R=d[:,-1]
# Appendix-4 effective density; dry-density closure from initial wet density
C0=2.55; rhoe0=760+90*C0; rhod0=rhoe0/(1+C0)
rhos=1500.; rhow=1000.
rhod=rhod0*(0.02/ R)**2
phi=1-rhod[:,None]*(1/rhos + np.nan_to_num(C,nan=0)/rhow)
# values outside material are NaN in C and excluded
valid=np.isfinite(C)
minphi=float(np.nanmin(np.where(valid,phi,np.nan)))
# dry mass relative error under fixed length and uniform radial shrink closure
Md_ratio=(rhod/rhod0)*(R/0.02)**2
runs['Q4_main']['min_porosity_assumed']=minphi
runs['Q4_main']['dry_mass_rel_error_assumed']=float(np.max(np.abs(Md_ratio-1)))
runs['Q4_main']['porosity_assumptions']={'rho_s':rhos,'rho_w':rhow,'rho_d0':rhod0,'formula':'phi=1-rho_d(1/rho_s+C/rho_w), rho_d=rho_d0(R0/R)^2'}
# write
(ROOT/'results'/'q34_enhanced'/'enhanced_summary.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(runs,ensure_ascii=False,indent=2))
