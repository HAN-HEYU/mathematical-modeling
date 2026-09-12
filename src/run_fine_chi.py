import importlib.util,json,time
from pathlib import Path
root=Path(__file__).resolve().parent; sp=importlib.util.spec_from_file_location('q4d',root/'solve_q4_2d.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
out=[]
for chi in (0.,1.):
 print('chi',chi,flush=True); r=m.run(chi,nr=24,nz=48,rtol=3e-5,max_step=3600); out.append(r); print(r,flush=True)
(root/'results'/'today_2d_comparisons'/'fine_grid_chi.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
