from __future__ import annotations

import csv
from pathlib import Path
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Deterministic publication figure; no generated-image content is used.
FONT = 'Microsoft YaHei'
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': [FONT, 'Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

HERE = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    HERE.parent / 'results' / 'sensitivity' / 'q3_sensitivity.csv',
    HERE.parent / 'github_repo' / 'results' / 'sensitivity' / 'q3_sensitivity.csv',
]
DATA_PATH = next((p for p in DATA_CANDIDATES if p.exists()), None)
if DATA_PATH is None:
    raise FileNotFoundError('q3_sensitivity.csv not found')

rows = {}
with DATA_PATH.open(encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        rows[row['case']] = row

case_order = ['D_0.8', 'hm_0.8', 'h_0.8', 'h_1.2', 'tail_last', 'hm_1.2', 'D_1.2']
label_map = {
    'D_0.8': '扩散系数 ×0.8',
    'hm_0.8': '传质系数 ×0.8',
    'h_0.8': '传热系数 ×0.8',
    'h_1.2': '传热系数 ×1.2',
    'tail_last': '末段环境延拓',
    'hm_1.2': '传质系数 ×1.2',
    'D_1.2': '扩散系数 ×1.2',
}
value_text_map = {
    'D_0.8': '+22.2%', 'hm_0.8': '+3.0%', 'h_0.8': '+0.034%',
    'h_1.2': '−0.023%', 'tail_last': '−0.5%',
    'hm_1.2': '−1.8%', 'D_1.2': '−14.7%',
}
values = [float(rows[c]['relative_percent']) for c in case_order]
labels = [label_map[c] for c in case_order]
texts = [value_text_map[c] for c in case_order]

NAVY = '#21364C'
TEXT = '#263747'
GRID = '#DCE4EA'
ROW = '#F7F9FB'
ZERO = '#465C6E'
POS = '#BF5C5E'
POS_DARK = '#9F4548'
NEG = '#4B82B2'
NEG_DARK = '#2E6796'

fig = plt.figure(figsize=(7.2, 4.35), facecolor='white')
gs = fig.add_gridspec(1, 2, width_ratios=[1.72, 0.90], wspace=0.24,
                      left=0.285, right=0.975, top=0.80, bottom=0.18)
main = fig.add_subplot(gs[0, 0])
zoom = fig.add_subplot(gs[0, 1])

# Main panel: full-range Cleveland dot plot.
y = list(range(len(labels)))[::-1]
for i, yi in enumerate(y):
    if i % 2 == 0:
        main.axhspan(yi - 0.46, yi + 0.46, color=ROW, zorder=0)
for x in (-20, -10, 10, 20):
    main.axvline(x, color=GRID, lw=0.8, zorder=0)
main.axvline(0, color=ZERO, lw=1.35, zorder=1)

for yi, val, case, txt in zip(y, values, case_order, texts):
    color = POS if val >= 0 else NEG
    edge = POS_DARK if val >= 0 else NEG_DARK
    main.plot([0, val], [yi, yi], color=color, lw=2.8,
              alpha=0.84, solid_capstyle='round', zorder=2)
    main.scatter([val], [yi], s=68, color=color, edgecolor='white',
                 linewidth=1.15, zorder=3)
    if abs(val) >= 1:
        if val > 0:
            main.text(val + 0.72, yi, txt, ha='left', va='center',
                      fontsize=9.7, color=edge, fontweight='bold')
        else:
            main.text(val - 0.72, yi, txt, ha='right', va='center',
                      fontsize=9.7, color=edge, fontweight='bold')

main.set_xlim(-24.2, 26.0)
main.set_ylim(-0.65, len(labels) - 0.35)
main.set_yticks(y)
main.set_yticklabels(labels, fontsize=9.7, color=TEXT)
main.set_xticks([-20, -10, 0, 10, 20])
main.set_xticklabels(['−20', '−10', '0', '10', '20'], fontsize=9.2, color='#5E6F7D')
main.set_xlabel('相对达标时间变化 (%)', fontsize=10.1, color=TEXT, labelpad=10)
main.tick_params(axis='y', length=0, pad=8)
main.tick_params(axis='x', length=3.3, width=0.7, color='#5E6F7D')
main.set_title('整体效应', loc='left', fontsize=10.8, color=NAVY,
               fontweight='bold', pad=10)

# Inset-like second panel: same values, magnified around zero.
zoom_indices = [2, 3, 4, 5]
zy = list(range(len(zoom_indices)))[::-1]
for i, yi in enumerate(zy):
    if i % 2 == 0:
        zoom.axhspan(yi - 0.46, yi + 0.46, color=ROW, zorder=0)
for x in (-2, -1, 1, 2):
    zoom.axvline(x, color=GRID, lw=0.8, zorder=0)
zoom.axvline(0, color=ZERO, lw=1.35, zorder=1)
for yi, idx in zip(zy, zoom_indices):
    val = values[idx]
    txt = texts[idx]
    color = POS if val >= 0 else NEG
    edge = POS_DARK if val >= 0 else NEG_DARK
    zoom.plot([0, val], [yi, yi], color=color, lw=2.8,
              alpha=0.84, solid_capstyle='round', zorder=2)
    zoom.scatter([val], [yi], s=68, color=color, edgecolor='white',
                 linewidth=1.15, zorder=3)
    if val >= 0:
        zoom.text(val + 0.10, yi, txt, ha='left', va='center', fontsize=9.0,
                  color=edge, fontweight='bold')
    else:
        zoom.text(val - 0.10, yi, txt, ha='right', va='center', fontsize=9.0,
                  color=edge, fontweight='bold')

zoom.set_xlim(-2.25, 0.65)
zoom.set_ylim(-0.65, len(zoom_indices) - 0.35)
zoom.set_yticks(zy)
zoom.set_yticklabels([])
zoom.set_xticks([-2, -1, 0])
zoom.set_xticklabels(['−2', '−1', '0'], fontsize=8.8, color='#5E6F7D')
zoom.set_xlabel('相对达标时间变化 (%)', fontsize=9.0, color=TEXT, labelpad=10)
zoom.tick_params(axis='y', length=0)
zoom.tick_params(axis='x', length=3.3, width=0.7, color='#5E6F7D')
zoom.set_title('零点附近局部放大', loc='left', fontsize=10.8, color=NAVY,
               fontweight='bold', pad=10)
zoom.text(0.0, 1.03, '对应主图第 3–6 项', transform=zoom.transAxes,
          ha='left', va='bottom', fontsize=8.1, color='#657684')

for ax in (main, zoom):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#AAB8C3')
    ax.spines['bottom'].set_color('#AAB8C3')
    ax.spines['left'].set_linewidth(0.7)
    ax.spines['bottom'].set_linewidth(0.7)

fig.suptitle('Q3 单因素情景灵敏度', fontsize=15.0, color=NAVY,
             fontweight='bold', y=0.945)
fig.text(0.285, 0.875, '点的位置表示相对达标时间变化；连接线以 0% 为共同基准',
         ha='left', va='center', fontsize=8.9, color='#657684')
handles = [
    Line2D([0], [0], color=POS, lw=2.8, marker='o', markersize=5.5,
           markerfacecolor=POS, markeredgecolor='white', label='达标时间增加'),
    Line2D([0], [0], color=NEG, lw=2.8, marker='o', markersize=5.5,
           markerfacecolor=NEG, markeredgecolor='white', label='达标时间减少'),
]
fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(0.975, 0.945),
           frameon=False, ncol=2, fontsize=8.3, handlelength=1.25,
           columnspacing=0.8, handletextpad=0.4)

out_dir = HERE
base = out_dir / 'Q3_单因素情景灵敏度_发散点图版_v2'
fig.savefig(str(base) + '.png', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(str(base) + '.tiff', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(str(base) + '.svg', bbox_inches='tight', pad_inches=0.08)
fig.savefig(str(base) + '.pdf', bbox_inches='tight', pad_inches=0.08)
print('source:', DATA_PATH)
for ext in ('png', 'tiff', 'svg', 'pdf'):
    print(base.with_suffix('.' + ext))
