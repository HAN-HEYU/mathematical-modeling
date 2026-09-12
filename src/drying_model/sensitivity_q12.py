"""问题一、二固定时段的基础单因素灵敏度分析。"""
from pathlib import Path
import csv, json, time, importlib
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'/'q12_sensitivity'; OUT.mkdir(parents=True,exist_ok=True)
q1=importlib.import_module('solve_q1'); q2=importlib.import_module('solve_q2')

def one_q1(case, fac, kind):
    q1.h=25.; q1.hm=8e-7
    q1.Dfun=lambda C: 7e-9*np.exp(-.89/np.maximum(C,1e-12))
    if kind=='D': q1.Dfun=lambda C: fac*7e-9*np.exp(-.89/np.maximum(C,1e-12))
    elif kind=='hm': q1.hm=fac*8e-7
    elif kind=='h': q1.h=fac*25.
    te=np.array([1.,300.,600.,900.,1200.,1500.,1800.])
    _,Ty,rc,Ts=q1.solve(400,'T',te); _,Cy,rc,Cs=q1.solve(400,'C',te)
    return dict(problem=1,case=case,final_time_s=1800.,center_T=float(Ty[0,-1]),surface_T=float(Ts[-1]),center_C=float(Cy[0,-1]),surface_C=float(Cs[-1]))

def one_q2(case, fac, kind):
    q2.h=25.; q2.hm=8e-7
    q2.Dval=lambda C,T: 2.4e-3*np.exp(-.45/np.maximum(C,1e-12))*np.exp(-3850/(np.maximum(T,-273.14)+273.15))
    if kind=='D': q2.Dval=lambda C,T: fac*2.4e-3*np.exp(-.45/np.maximum(C,1e-12))*np.exp(-3850/(np.maximum(T,-273.14)+273.15))
    elif kind=='hm': q2.hm=fac*8e-7
    elif kind=='h': q2.h=fac*25.
    te=np.array([1800.,3600.,5400.,7200.,9000.,10800.])
    _,Ty,Cy,rc,Ts,Cs=q2.solve(400,te)
    return dict(problem=2,case=case,final_time_s=10800.,center_T=float(Ty[0,-1]),surface_T=float(Ts[-1]),center_C=float(Cy[0,-1]),surface_C=float(Cs[-1]))

cases=[('baseline',1.0,'base'),('D_0.8',.8,'D'),('D_1.2',1.2,'D'),('hm_0.8',.8,'hm'),('hm_1.2',1.2,'hm'),('h_0.8',.8,'h'),('h_1.2',1.2,'h')]
rows=[]; t0=time.perf_counter()
for name,fac,kind in cases:
    print('Q1',name,flush=True); rows.append(one_q1(name,fac,kind))
for name,fac,kind in cases:
    print('Q2',name,flush=True); rows.append(one_q2(name,fac,kind))
for p in (1,2):
    b=next(x for x in rows if x['problem']==p and x['case']=='baseline')
    for x in [z for z in rows if z['problem']==p]:
        for key in ('center_T','surface_T','center_C','surface_C'):
            x['delta_'+key]=x[key]-b[key]
report={'description':'Q1/Q2基础单因素灵敏度；只输出诊断文件，不覆盖附件3或主结果。','grid':{'Q1_N':400,'Q2_N':400},'rows':rows,'runtime_s':time.perf_counter()-t0}
(OUT/'sensitivity_q12.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'sensitivity_q12.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['problem','case','final_time_s','center_T','surface_T','center_C','surface_C','d_center_T','d_surface_T','d_center_C','d_surface_C'])
    for x in rows: w.writerow([x['problem'],x['case'],x['final_time_s'],f"{x['center_T']:.8f}",f"{x['surface_T']:.8f}",f"{x['center_C']:.8f}",f"{x['surface_C']:.8f}",f"{x['delta_center_T']:.8g}",f"{x['delta_surface_T']:.8g}",f"{x['delta_center_C']:.8g}",f"{x['delta_surface_C']:.8g}"])
lines=['# 问题一、二基础灵敏度分析\n','参数扰动只用于诊断，未覆盖原始主结果。每次只改变一个因素，网格为 Q1/Q2 的 N=400。\n\n','|问题|情形|末时刻中心温度|末时刻表面温度|末时刻中心含水率|末时刻表面含水率|\n|---:|---|---:|---:|---:|---:|\n']
for x in rows: lines.append(f"|Q{x['problem']}|{x['case']}|{x['center_T']:.5f}|{x['surface_T']:.5f}|{x['center_C']:.5f}|{x['surface_C']:.5f}|\n")
lines.append('\n说明：Q1 的 D 为 7e-9 exp(-0.89/C)，Q2 的 D 为题设变物性表达式；D、h_m、h 分别表示内部扩散、表面传质和表面对流换热能力。\n')
(OUT/'sensitivity_q12.md').write_text(''.join(lines),encoding='utf-8')
print(json.dumps({'output':str(OUT),'rows':len(rows),'runtime_s':time.perf_counter()-t0},ensure_ascii=False))
