"""基础灵敏度分析：问题三固定尺寸、变物性主模型。

默认参数与 solve_q34.run 完全相同；本脚本只输出新文件，不改写 q34_validation.json
或附件3结果。采用 N=100 进行筛查，随后可用 N=400 对关键情形复核。
"""
from pathlib import Path
import csv, json, time
from solve_q34 import run, H, HM

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "q3_sensitivity"
OUT.mkdir(parents=True, exist_ok=True)

# Baseline is the published Q3 setting. Perturb one factor at a time.
cases = [
    ("baseline", dict(scenario="mean", dscale=1.0, hm=HM, hcoef=H)),
    ("D_0.8", dict(scenario="mean", dscale=0.8, hm=HM, hcoef=H)),
    ("D_1.2", dict(scenario="mean", dscale=1.2, hm=HM, hcoef=H)),
    ("hm_0.8", dict(scenario="mean", dscale=1.0, hm=0.8*HM, hcoef=H)),
    ("hm_1.2", dict(scenario="mean", dscale=1.0, hm=1.2*HM, hcoef=H)),
    ("h_0.8", dict(scenario="mean", dscale=1.0, hm=HM, hcoef=0.8*H)),
    ("h_1.2", dict(scenario="mean", dscale=1.0, hm=HM, hcoef=1.2*H)),
    # Annex-1 tail continuation: mean of late observations versus last observation.
    ("tail_last", dict(scenario="last", dscale=1.0, hm=HM, hcoef=H)),
]

rows=[]; t0=time.perf_counter()
for name, kw in cases:
    print(name, flush=True)
    _, _, st = run(3, n=100, rtol=1e-9, max_step=3600, **kw)
    st = dict(st); st["case"] = name
    rows.append(st)
base = next(x for x in rows if x["case"]=="baseline")
for x in rows:
    x["delta_h"] = x["hours"] - base["hours"]
    x["relative_percent"] = 100*x["delta_h"]/base["hours"]
    x["strict_pass"] = bool(x["maximum_after_1s"] < 0.15)

# Time integration check at the baseline (same space grid, tighter/looser max step).
time_cases=[("step_1800",1800), ("step_7200",7200)]
time_rows=[]
for name, ms in time_cases:
    print(name, flush=True)
    _,_,st=run(3,n=100,rtol=1e-9,max_step=ms,scenario="mean",dscale=1.0,hm=HM,hcoef=H)
    st=dict(st);st["case"]=name;st["delta_h"]=st["hours"]-base["hours"]
    st["relative_percent"]=100*st["delta_h"]/base["hours"]
    st["strict_pass"] = bool(st["maximum_after_1s"] < 0.15)
    time_rows.append(st)

report={
    "description":"问题三固定尺寸、变物性湿热耦合模型的基础单因素灵敏度分析；N=100筛查，主结果未修改。",
    "model":"solve_q34.run(q=3)",
    "baseline":{"N":100,"rtol":1e-9,"max_step":3600,"D_scale":1.0,"hm":HM,"hcoef":H,"tail":"late-observation mean"},
    "physical_sensitivity":rows,
    "time_step_check":time_rows,
    "runtime_s":time.perf_counter()-t0,
}
(OUT/"sensitivity_q3.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
with (OUT/"sensitivity_q3.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["case","D_scale","hm_m_s","h_W_m2K","scenario","hours","delta_h","relative_percent","mass_error","maximum_after_1s","strict_pass"])
    for x in rows+time_rows:
        w.writerow([x["case"],x.get("dscale",1),x.get("hm",HM),x.get("hcoef",H),x.get("scenario","mean"),f'{x["hours"]:.8f}',f'{x["delta_h"]:.8f}',f'{x["relative_percent"]:.5f}',f'{x["mass_error"]:.3e}',f'{x["maximum_after_1s"]:.12f}',x["strict_pass"]])

lines=["# 问题三基础灵敏度分析\n", "本文件由 `python sensitivity_q3.py` 生成。所有扰动均以问题三主模型为基准，默认结果文件未覆盖。\n", "\n## 单因素结果（N=100，BDF，rtol=1e-9）\n", "|情形|干燥时间/h|相对基准|最大值(续算1 s)|质量守恒误差|\n|---|---:|---:|---:|---:|\n"]
for x in rows:
    lines.append(f"|{x['case']}|{x['hours']:.5f}|{x['relative_percent']:+.3f}%|{x['maximum_after_1s']:.9f}|{x['mass_error']:.2e}|\n")
lines += ["\n## 时间步上限检查\n", "|设置|干燥时间/h|相对基准|\n|---|---:|---:|\n"]
for x in time_rows: lines.append(f"|{x['case']}|{x['hours']:.5f}|{x['relative_percent']:+.3f}%|\n")
lines += ["\n解释：D 是内部扩散能力，通常为最敏感因素；hm 直接控制表面脱水阻力；h 主要影响升温阶段，影响相对较小；尾部环境取值属于边界假设，需在论文中作为情景不确定性说明。质量守恒误差和严格达标检查均由求解器自动输出。\n"]
(OUT/"sensitivity_q3.md").write_text("".join(lines),encoding="utf-8")
print(json.dumps({"output":str(OUT),"baseline_hours":base["hours"],"n_cases":len(rows)+len(time_rows)},ensure_ascii=False))
