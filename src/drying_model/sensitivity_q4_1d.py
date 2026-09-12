"""问题四一维随体坐标主模型的单因素灵敏度分析。"""
from pathlib import Path
import csv, json, time
from solve_q34 import run, H, HM

OUT = Path("results/q4_1d_sensitivity")
OUT.mkdir(parents=True, exist_ok=True)
CASES = [
    ("baseline", {}), ("D_0.8", {"dscale": .8}), ("D_1.2", {"dscale": 1.2}),
    ("hm_0.8", {"hm": .8 * HM}), ("hm_1.2", {"hm": 1.2 * HM}),
    ("h_0.8", {"hcoef": .8 * H}), ("h_1.2", {"hcoef": 1.2 * H}),
]

rows = []
t0 = time.perf_counter()
for name, kw in CASES:
    print(name, flush=True)
    _, _, stats = run(4, n=200, rtol=2e-8, max_step=3600,
                      scenario="mean", **kw)
    stats = dict(stats)
    stats["case"] = name
    rows.append(stats)
base = rows[0]
for row in rows:
    row["delta_h"] = row["hours"] - base["hours"]
    row["relative_percent"] = 100 * row["delta_h"] / base["hours"]
    row["strict_pass"] = row["maximum_after_1s"] < .15

report = {
    "description": "问题四一维随体坐标主模型单因素灵敏度；不改变主结果。",
    "model": "solve_q34.run(q=4), fixed=False",
    "baseline": {"N": 200, "rtol": 2e-8, "max_step": 3600,
                 "tail": "late-observation mean", "h": H, "hm": HM},
    "physical_sensitivity": rows,
    "runtime_s": time.perf_counter() - t0,
}
(OUT / "q4_1d_sensitivity.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "q4_1d_sensitivity.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["case", "D_scale", "hm_m_s", "h_W_m2K", "hours",
                     "delta_h", "relative_percent", "mass_error",
                     "maximum_after_1s", "strict_pass"])
    for row in rows:
        writer.writerow([row["case"], row["dscale"], row["hm"], row["hcoef"],
                         f'{row["hours"]:.8f}', f'{row["delta_h"]:.8f}',
                         f'{row["relative_percent"]:.5f}',
                         f'{row["mass_error"]:.3e}',
                         f'{row["maximum_after_1s"]:.12f}', row["strict_pass"]])
lines = [
    "# 问题四一维主模型灵敏度分析（修正版）\n\n",
    "固定附录4物性、附件2半径和一维随体坐标模型，仅作单因素诊断，不覆盖主结果。",
    "基准为 N=200、BDF、rtol=2e-8、最大步长3600 s；每次只改变一个参数20%。\n\n",
    "|情形|达标时间/h|相对基准|质量守恒误差|事件后1 s最大含水率|\n|---|---:|---:|---:|---:|\n",
]
for row in rows:
    lines.append(f'|{row["case"]}|{row["hours"]:.5f}|{row["relative_percent"]:+.3f}%|'
                 f'{row["mass_error"]:.2e}|{row["maximum_after_1s"]:.9f}|\n')
lines.append("\n解释：本表只说明当前主模型在指定参数范围内的响应，不是参数置信区间。"
             "结论按达标时间指标给出，不推广到所有状态量。\n")
(OUT / "q4_1d_sensitivity.md").write_text("".join(lines), encoding="utf-8")
print(json.dumps({"baseline_hours": base["hours"],
                  "runtime_s": time.perf_counter() - t0}, ensure_ascii=False))

