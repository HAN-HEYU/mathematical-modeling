# Mathematical Modeling Competition Toolkit

一个面向数学建模比赛的 Python 3.11 仓库：保留干净的每问入口，集中管理参数、
数据路径、图表、指标、优化、敏感性分析、日志和复现信息。目标不是囤积算法，
而是让三名队员在比赛当天 clone 后能立即读数据、写模型、跑测试并生成论文素材。

## 1 分钟启动

```powershell
git clone https://github.com/HAN-HEYU/mathematical-modeling.git
cd mathematical-modeling
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/check_env.py --features data visualization excel optimization statistics graph image
python -m pytest -q
python -m src.q1
```

macOS/Linux 把激活命令换成 `source .venv/bin/activate`，其余命令相同。

## 目录约定

```text
data/
  raw/                 原始赛题附件，只读
  processed/           清洗后的中间数据，可重新生成
  external/            有出处的外部数据
src/
  config.py            全局路径、随机种子、容差、DPI
  data_io.py           XLSX/CSV/TXT 可靠读写
  metrics.py           RMSE/MAE/MAPE/R²/相对误差
  sensitivity.py       单因素敏感性分析与绘图
  visualization.py     统一论文图函数和 PNG/SVG/PDF 导出
  optimization.py      连续优化和随机搜索基线
  reproducibility.py   输入哈希、参数、环境与复现命令
  q1.py ... q5.py      每一问的可运行流水线模板
utils/plot_style.py    仓库自带的出版级绘图样式
scripts/               环境检查和复现清单命令
results/q*/            每问数值结果；日志在 results/logs/
figures/q*/            每问候选图；采用 raw/process/result 前缀
figures/final/         论文最终采用的图
notes/                 题意、假设、符号、模型说明、AI 使用记录
paper/                 摘要、参考文献和论文草稿
tests/                 通用函数与运行入口测试
```

生成文件默认不提交到 Git；各目录中的 `.gitkeep` 只负责保留骨架。

## 比赛当天工作流

1. 把原始 PDF、Excel、CSV、TXT 放进 `data/raw/`，不要原地修改。
2. 在 `notes/problem_analysis.md` 拆分子问题，在 `notes/symbols.md` 统一单位与符号。
3. 在 `src/config.py` 集中写题目参数、随机种子、容差和迭代上限。
4. 从 `src/q1.py` 开始，依次填充 `load_inputs → build_model → solve → validate`。
5. 清洗数据写入 `data/processed/`，结果写入 `results/q*/`，图写入 `figures/q*/`。
6. 每完成一个公共函数立即加测试，持续运行 `python -m pytest -q`。
7. 冻结模型后生成 `results/复现清单.json`，再把通过核验的图复制到 `figures/final/`。

详细的临场检查见 [`比赛当天清单.md`](比赛当天清单.md)。Codex 工作流见
[`SKILLS.md`](SKILLS.md)，产物使用边界见 [`使用指南.md`](使用指南.md)。

## 常用代码

### 可靠读取附件

```python
from src.data_io import load_csv, load_excel, load_txt

# 第一行是列名时明确写 header=0；第一行就是数据时写 header=None。
table = load_excel("data/raw/附件1.xlsx", header=0, expected_rows=1000)
samples = load_csv("data/raw/附件2.csv", expected_rows=500)
points = load_txt("data/raw/坐标.txt", header=None)
```

`expected_rows` 会在附件行数异常时立即报错，防止模型在错误数据上静默运行。

### 指标与敏感性分析

```python
from src.metrics import mae, r2, rmse
from src.sensitivity import one_factor_sensitivity, plot_sensitivity

score = {"RMSE": rmse(y_true, y_pred), "MAE": mae(y_true, y_pred), "R2": r2(y_true, y_pred)}
table = one_factor_sensitivity(
    lambda speed, radius: speed / radius,
    {"speed": 300.0, "radius": 20.0},
)
fig, ax = plot_sensitivity(table)
```

### 统一出图

```python
from src.visualization import plot_fit, save_figure, set_default_style

set_default_style(language="zh")
fig, ax = plot_fit(y_true, y_pred, unit="m")
paths = save_figure(fig, "figures/q1/result_q1_fit", formats=("png", "svg"), dpi=300)
```

默认采用固定物理尺寸和 `constrained_layout`，同时输出至少 300 DPI PNG 与可编辑
SVG。`tight=True` 会改变物理边界，只在不要求严格最终尺寸时使用。中文字体会按
Noto Sans CJK、思源黑体、微软雅黑、黑体的顺序自动选择。

### 连续优化

```python
import numpy as np
from src.optimization import minimize_continuous

result = minimize_continuous(
    lambda x: float((x[0] - 2) ** 2 + (x[1] + 1) ** 2),
    np.array([0.0, 0.0]),
    bounds=[(-5, 5), (-5, 5)],
)
assert result.success, result.message
```

### 生成复现清单

```powershell
python scripts/repro_manifest.py `
  --input data/raw/附件1.xlsx `
  --seed 42 `
  --parameters '{"tol": 1e-6, "max_iter": 10000}' `
  --command "python -m src.q1" `
  --package numpy --package scipy --package pandas `
  --overwrite
```

## 质量门禁

赛前完成标准：

- `python -m pip install -r requirements.txt` 成功；
- `python scripts/check_env.py ...` 返回 `"ok": true`；
- `python -m pytest -q` 全部通过且无警告；
- `python -m src.q1` 能完整经过加载、建模、求解、校验、保存、绘图入口；
- Excel 明确声明表头并核对预期行数；
- 正式图包含变量名和单位，PNG ≥ 300 DPI，并保留 SVG；
- 每个正式实验都有随机种子、输入 SHA-256、关键参数、依赖版本和唯一复现命令；
- GitHub Actions 在 push 和 pull request 时自动复跑环境检查与测试。

这里的代码、图表和论文内容都是参赛队伍的工作草稿。提交前必须人工核对公式、
数值、单位、图表、引用和当届官方规则，不应把 AI 产物未经复核直接提交。
