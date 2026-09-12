from pathlib import Path
import json,sys,time
sys.path.insert(0,'.')
from solve_q4_2d import run
out=[]
for grid in [(8,16),(12,24),(16,32)]:
 for chi in (0.,.5,1.):
  print('run',grid,chi,flush=True)
  out.append(run(chi,nr=grid[0],nz=grid[1],rtol=3e-5,max_step=3600))
# time test at 12x24 chi=.5
for rt,ms in [(1e-4,3600),(3e-5,3600),(3e-5,1800)]:
 print('time',rt,ms,flush=True); out.append(run(.5,nr=12,nz=24,rtol=rt,max_step=ms))
p=Path('results/q4_2d_shrink/verification.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False,indent=2))
