# A题干燥过程数学建模项目

本目录整理了 A 题四问的可复现模型、输入数据、主结果、网格收敛、灵敏度分析和今天统一参数后完成的二维对比实验。

## 入口

- 方案与全部写作数据：[paper/drying_model/论文手_全方案与数据汇总.md](paper/drying_model/论文手_全方案与数据汇总.md)
- 主模型与方程：[notes/drying_model/四问模型总览.md](notes/drying_model/四问模型总览.md)
- 运行与复现说明：[src/drying_model/README.md](src/drying_model/README.md)

## 目录

- `data/raw/drying_A/`：题目 PDF 和附件原始数据。
- `src/drying_model/`：四问求解、网格收敛、灵敏度和二维对比代码。
- `results/drying_model/main/`：四问主结果数组。
- `results/drying_model/validation/`：守恒、边界、事件和算法校核。
- `results/drying_model/grid_convergence/`：问题一二的 N=200--6400 全序列，以及问题三四 N=100/200/400 事件时间收敛。
- `results/drying_model/sensitivity/`：灵敏度数据。
- `results/drying_model/today_2d_comparisons/`：今天修正后的问题四二维四组对比和 chi 情景。
- `paper/drying_model/`：面向论文写作的结果汇总。

## 关键口径

问题三主模型达标时间为 57.474077 h，问题四主模型为 51.092074 h。今天的二维对比是机制分析，不替代主模型；二维端面实验采用端面传质、端面换热系数 h_e=0。

旧版 51.532 h、57.64--57.65 h 和 131.266752 h 已作废，不应写入论文。

## 运行环境

依赖见根目录 `requirements.txt`。示例：

```powershell
pip install -r requirements.txt
python src/drying_model/solve_q1.py
```

部分结果文件体积较大，若只阅读论文数据，可直接查看 `paper/drying_model/论文手_全方案与数据汇总.md`。
