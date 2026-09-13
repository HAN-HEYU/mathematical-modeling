import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D

FONT = 'Microsoft YaHei'
mpl.rcParams.update({
    'font.family': FONT,
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
TEXT = '#22313F'
GRID = '#D9E1E7'
POS = '#C25B5A'
POS_DARK = '#A74646'
NEG = '#4E83B1'
NEG_DARK = '#2F6797'
PALE = '#F7F9FB'

fig, ax = plt.subplots(figsize=(10.8, 5.9), facecolor='white')
fig.subplots_adjust(left=0.255, right=0.965, top=0.82, bottom=0.18)

# Alternating row bands for readability.
y = list(range(len(labels)))[::-1]
for i, yi in enumerate(y):
    if i % 2 == 0:
        ax.axhspan(yi - 0.46, yi + 0.46, color=PALE, zorder=0)

# Vertical grid and zero baseline.
for x in [-20, -10, 10, 20]:
    ax.axvline(x, color=GRID, lw=0.95, zorder=0)
ax.axvline(0, color=NAVY, lw=1.55, zorder=3)

# Rounded bars with exact signed lengths.
bar_h = 0.62
for yi, val, txt in zip(y, values, value_text):
    color = POS if val >= 0 else NEG
    edge = POS_DARK if val >= 0 else NEG_DARK
    left = min(0, val)
    width = abs(val)
    # use a standard rectangle for very short bars so they remain visible
    ax.barh(yi, width, left=left, height=bar_h, color=color,
            edgecolor='none', alpha=0.96, zorder=2)
    # Add a small end tick for the two near-zero effects.
    if abs(val) < 0.06:
        ax.plot([val, val], [yi - bar_h/2, yi + bar_h/2], color=edge, lw=2.4, zorder=4)

    # Place labels outside for large bars and near the zero line for tiny bars.
    if abs(val) >= 3:
        if val > 0:
            xtext, ha, col = val + 0.7, 'left', TEXT
        else:
            xtext, ha, col = val + 0.7, 'left', 'white'
        ax.text(xtext, yi, txt, va='center', ha=ha, fontsize=10.2,
                color=col, fontweight='bold', zorder=5)
    elif val > 0:
        ax.text(0.75, yi, txt, va='center', ha='left', fontsize=9.7,
                color=TEXT, fontweight='bold', zorder=5)
    else:
        ax.text(-0.75, yi, txt, va='center', ha='right', fontsize=9.7,
                color='#687887', fontweight='bold', zorder=5)

# Axes and labels.
ax.set_xlim(-20.8, 26.5)
ax.set_ylim(-0.72, len(labels)-0.28)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=10.5, color=TEXT)
ax.set_xticks([-20, -10, 0, 10, 20])
ax.set_xticklabels(['−20', '−10', '0', '10', '20'], fontsize=10, color='#526372')
ax.set_xlabel('相对达标时间变化（%）', fontsize=11.5, color=TEXT, labelpad=13)
ax.tick_params(axis='y', length=0, pad=10)
ax.tick_params(axis='x', length=4, width=0.8, color='#526372')
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color('#AAB8C3')
ax.spines['bottom'].set_color('#AAB8C3')
ax.spines['left'].set_linewidth(0.8)
ax.spines['bottom'].set_linewidth(0.8)

# Title and a restrained subtitle-like cue.
fig.suptitle('Q3 单因素情景灵敏度', fontsize=15.5, color=NAVY,
             fontweight='bold', y=0.935)
fig.text(0.255, 0.875, '正值：达标时间延长　　负值：达标时间缩短',
         ha='left', va='center', fontsize=9.5, color='#687887')

# Compact legend with data semantics only.
handles = [
    Line2D([0],[0], color=POS, lw=8, solid_capstyle='round', label='时间增加'),
    Line2D([0],[0], color=NEG, lw=8, solid_capstyle='round', label='时间减少'),
]
ax.legend(handles=handles, loc='upper right', bbox_to_anchor=(1.0, 1.155),
          frameon=False, ncol=2, fontsize=9.2, handlelength=1.2,
          columnspacing=1.3, handletextpad=0.5)

out_dir = os.path.dirname(__file__)
base = os.path.join(out_dir, 'Q3_单因素情景灵敏度_论文版')
fig.savefig(base + '.png', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.svg', bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.pdf', bbox_inches='tight', pad_inches=0.08)
print(base + '.png')
print(base + '.svg')
print(base + '.pdf')
