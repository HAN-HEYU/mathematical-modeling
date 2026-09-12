import importlib.util, json, time
from pathlib import Path
root=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('q4d',root/'solve_q4_2d.py'); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
out=[]
for nr,nz in [(24,48),(32,64)]:
 print(nr,nz,flush=True); t=time.time(); r=m.run(.5,nr=nr,nz=nz,rtol=3e-5,max_step=3600); r['case']=f'chi0.5_{nr}x{nz}'; out.append(r); print(r,flush=True)
(root/'results'/'q4_2d_shrink'/'fine_grid_reference.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
