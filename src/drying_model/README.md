# 模型代码说明

代码按四问分组保存。核心入口：`solve_q1.py`、`solve_q2.py`、`solve_q34.py`；二维和端面对照：`q3_unified_axisymmetric.py`、`q4_four_unified_cases.py`、`solve_q4_2d.py`；网格收敛和灵敏度：`grid_refinement_q12.py`、`sensitivity_*.py`。

脚本会从仓库的 `data/raw/drying_A/` 读取输入，主模型生成表格写入 `results/drying_model/generated/`，不会覆盖原始附件。已保存的正式结果和对照结果位于 `results/drying_model/`。

从仓库根目录运行，例如：

```powershell
pip install -r requirements.txt
python src/drying_model/solve_q1.py
```
