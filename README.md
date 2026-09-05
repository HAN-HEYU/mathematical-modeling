# Mathematical Modeling

数学建模项目工作区，用于存放赛题附件、数据处理、模型代码、结果表、图表、笔记和论文草稿。

## 项目结构

```text
data/
  raw/          原始赛题附件，尽量不修改
  processed/    清洗、转换后的数据
  external/     额外收集的数据
src/
  q1.py ... q5.py       各题代码入口
  utils.py              通用工具函数
  models.py             数学模型/核心公式
  optimization.py        优化算法
  visualization.py       公共画图函数
notebooks/       探索和临时实验
results/         结果表与复现记录
figures/         论文图片和过程图片
notes/           题意分析、假设、符号表、AI 使用记录
paper/           摘要、参考文献、最终论文
tests/           最小单元测试
```

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

运行某一问：

```powershell
python -m src.q1
```

## 协作约定

- `data/raw/` 只放原始附件，原则上不直接修改。
- 中间数据写入 `data/processed/`，最终可引用结果写入 `results/final/`。
- 每一问的脚本优先输出到对应的 `results/q*/` 和 `figures/q*/`。
- 论文中采用的图表复制或导出到 `figures/final/`。
- 重要假设、符号和 AI 辅助过程分别记录在 `notes/assumptions.md`、`notes/symbols.md` 和 `notes/ai_log.md`。
- 论文草稿需人工核对和改写后再提交，最终格式以当届竞赛官方要求为准。
