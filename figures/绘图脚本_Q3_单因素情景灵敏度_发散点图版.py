import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

FONT = 'Microsoft YaHei'
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': [FONT, 'Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

# Exact values from results/sensitivity/q3_sensitivity.csv.
labels = [
    '扩散系数 ×0.8',
    '传质系数 ×0.8',
    '传热系数 ×0.8',
    '传热系数 ×1.2',
    '末段环境延拓',
    '传质系数 ×1.2',
    '扩散系数 ×1.2',
]
values = [22.21005, 2.95156, 0.03430, -0.02268, -0.53002, -1.80812, -14.66569]
value_text = ['+22.2%', '+3.0%', '+0.034%', '−0.023%', '−0.5%', '−1.8%', '−14.7%']

NAVY = '#20364D'
TEXT = '#263746'
GRID = '#DCE4EA'
POS = '#C35F61'
POS_DARK = '#9D4145'
NEG = '#4F83B2'
NEG_DARK = '#2F6797'
ROW = '#F7F9FB'
ZERO = '#42586B'

fig = plt.figure(figsize=(7.2, 4.35), facecolor='white')
gs = fig.add_gridspec(1, 2, width_ratios=[1.72, 0.9], wspace=0.23,
                      left=0.285, right=0.975, top=0.80, bottom=0.18)
ax = fig.add_subplot(gs[0, 0])
zoom = fig.add_subplot(gs[0, 1])

# -------- Main full-range dot plot --------
y = list(range(len(labels)))[::-1]
for i, yi in enumerate(y):
    if i % 2 == 0:
        ax.axhspan(yi-0.46, yi+0.46, color=ROW, zorder=0)
for x in [-20, -10, 10, 20]:
    ax.axvline(x, color=GRID, lw=0.85, zorder=0)
ax.axvline(0, color=ZERO, lw=1.4, zorder=1)

for yi, val, txt in zip(y, values, value_text):
    color = POS if val >= 0 else NEG
    edge = POS_DARK if val >= 0 else NEG_DARK
    # Thin connector from the common reference (zero) to the estimate.
    ax.plot([0, val], [yi, yi], color=color, lw=3.0,
            solid_capstyle='round', alpha=0.84, zorder=2)
    ax.scatter([val], [yi], s=75, color=color, edgecolor='white',
               linewidth=1.15, zorder=3)
    # Direct labels for the large effects; the near-zero effects are repeated in the inset.
    if abs(val) >= 1.0:
        if val > 0:
            ax.text(val+0.72, yi, txt, ha='left', va='center', fontsize=10.0,
                    color=edge, fontweight='bold', zorder=4)
        else:
            ax.text(val-0.72, yi, txt, ha='right', va='center', fontsize=10.0,
                    color=edge, fontweight='bold', zorder=4)

ax.set_xlim(-24.2, 26.0)
ax.set_ylim(-0.65, len(labels)-0.35)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=10.0, color=TEXT)
ax.set_xticks([-20, -10, 0, 10, 20])
ax.set_xticklabels(['−20', '−10', '0', '10', '20'], fontsize=9.5, color='#5E6F7D')
ax.set_xlabel('相对达标时间变化（%）', fontsize=10.8, color=TEXT, labelpad=11)
ax.tick_params(axis='y', length=0, pad=9)
ax.tick_params(axis='x', length=3.5, width=0.75, color='#5E6F7D')
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color('#AAB8C3')
ax.spines['bottom'].set_color('#AAB8C3')
ax.spines['left'].set_linewidth(0.75)
ax.spines['bottom'].set_linewidth(0.75)
ax.set_title('整体效应', loc='left', fontsize=11.2, color=NAVY,
             fontweight='bold', pad=12)

# -------- Near-zero zoom plot --------
zoom_labels = ['h ×0.8', 'h ×1.2', '末段延拓', 'h_m ×1.2']
zoom_values = [values[i] for i in [2, 3, 4, 5]]
zoom_texts = [value_text[i] for i in [2, 3, 4, 5]]
zy = list(range(len(zoom_labels)))[::-1]
for i, yi in enumerate(zy):
    if i % 2 == 0:
        zoom.axhspan(yi-0.46, yi+0.46, color=ROW, zorder=0)
for x in [-2, -1, 1, 2]:
    zoom.axvline(x, color=GRID, lw=0.85, zorder=0)
zoom.axvline(0, color=ZERO, lw=1.4, zorder=1)
for yi, val, txt in zip(zy, zoom_values, zoom_texts):
    color = POS if val >= 0 else NEG
    edge = POS_DARK if val >= 0 else NEG_DARK
    zoom.plot([0, val], [yi, yi], color=color, lw=3.0,
              solid_capstyle='round', alpha=0.84, zorder=2)
    zoom.scatter([val], [yi], s=75, color=color, edgecolor='white',
                 linewidth=1.15, zorder=3)
    if val >= 0:
        zoom.text(val+0.10, yi, txt, ha='left', va='center', fontsize=9.3,
                  color=edge, fontweight='bold', zorder=4)
    else:
        zoom.text(val-0.10, yi, txt, ha='right', va='center', fontsize=9.3,
                  color=edge, fontweight='bold', zorder=4)
zoom.set_xlim(-2.25, 0.65)
zoom.set_ylim(-0.65, len(zoom_labels)-0.35)
zoom.set_yticks(zy)
zoom.set_yticklabels([])
zoom.set_xticks([-2, -1, 0])
zoom.set_xticklabels(['−2', '−1', '0'], fontsize=9.0, color='#5E6F7D')
zoom.set_xlabel('相对达标时间变化（%）', fontsize=9.5, color=TEXT, labelpad=11)
zoom.yaxis.tick_right()
zoom.tick_params(axis='y', length=0, pad=8, labelleft=False, labelright=True)
zoom.tick_params(axis='x', length=3.5, width=0.75, color='#5E6F7D')
for spine in ['top', 'right']:
    zoom.spines[spine].set_visible(False)
zoom.spines['left'].set_color('#AAB8C3')
zoom.spines['bottom'].set_color('#AAB8C3')
zoom.spines['left'].set_linewidth(0.75)
zoom.spines['bottom'].set_linewidth(0.75)
zoom.set_title('零点附近局部放大', loc='left', fontsize=11.2, color=NAVY,
               fontweight='bold', pad=12)

# Main title, subtitle, and compact legend.
fig.suptitle('Q3 单因素情景灵敏度', fontsize=16.0, color=NAVY,
             fontweight='bold', y=0.945)
fig.text(0.285, 0.875, '点的位置表示相对达标时间变化；连接线以 0% 为共同基准',
         ha='left', va='center', fontsize=9.6, color='#657684')
handles = [
    Line2D([0], [0], color=POS, lw=3.0, marker='o', markersize=6,
           markerfacecolor=POS, markeredgecolor='white', label='达标时间增加'),
    Line2D([0], [0], color=NEG, lw=3.0, marker='o', markersize=6,
           markerfacecolor=NEG, markeredgecolor='white', label='达标时间减少'),
]
fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(0.97, 0.948),
           frameon=False, ncol=2, fontsize=9.1, handlelength=1.3,
           columnspacing=1.0, handletextpad=0.45)

out_dir = os.path.dirname(__file__)
base = os.path.join(out_dir, 'Q3_单因素情景灵敏度_发散点图版')
fig.savefig(base + '.png', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.tiff', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.svg', bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.pdf', bbox_inches='tight', pad_inches=0.08)
print(base + '.png')
print(base + '.tiff')
print(base + '.svg')
print(base + '.pdf')






