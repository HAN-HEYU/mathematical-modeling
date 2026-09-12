# A题模型代码

本目录直接保存 A 题模型代码。`solve_q1.py`、`solve_q2.py`、`solve_q34.py` 是四问主模型；`q3_unified_axisymmetric.py` 和 `q4_four_unified_cases.py` 是二维端面与收缩对照；`grid_refinement_q12.py` 与 `sensitivity_*.py` 用于网格收敛和灵敏度实验。

代码从 `data/raw/` 读取附件，生成结果写入 `results/generated/`；已经核定的结果位于 `results/` 下对应目录。旧版二维求解器不在主代码目录中。
