import os, math
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Ellipse, Rectangle, Circle, FancyArrowPatch, FancyBboxPatch,
    Arc, Polygon
)
from matplotlib.lines import Line2D

# -----------------------------
# Global publication style
# -----------------------------
FONT = 'Microsoft YaHei'
mpl.rcParams.update({
    'font.family': FONT,
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',  # keep text editable in the SVG
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

NAVY = '#17324D'
BLUE = '#2B6F9E'
PALE_BLUE = '#DCECF6'
PALE_BLUE2 = '#EEF6FA'
MOIST = '#1E78A7'
RED = '#C64B4B'
PALE_RED = '#FCE8E5'
GOLD = '#D18B36'
GREEN = '#3A837A'
GRAY = '#66737D'
LIGHT_GRAY = '#E8EDF0'
MID_GRAY = '#B9C5CC'

fig = plt.figure(figsize=(12.8, 4.7), facecolor='white')
gs = fig.add_gridspec(1, 3, width_ratios=[1.12, 1.18, 1.46], wspace=0.13,
                      left=0.025, right=0.985, top=0.87, bottom=0.12)

# helpers
def setup(ax, title):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')
    ax.text(0.03, 0.98, title, ha='left', va='top', fontsize=11.5,
            color=NAVY, fontweight='bold')
    ax.plot([0.03, 0.97], [0.925, 0.925], color=LIGHT_GRAY, lw=1.0)

def arrow(ax, xy1, xy2, color=NAVY, lw=1.5, ms=8, style='-|>', ls='-'):
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle=style,
                                 mutation_scale=ms, linewidth=lw,
                                 color=color, linestyle=ls,
                                 shrinkA=0, shrinkB=0))

def label_box(ax, x, y, text, fc='white', ec=LIGHT_GRAY, color=NAVY,
              fontsize=9.0, pad=0.15, radius=0.02, ha='center'):
    # width is estimated from character count; keeps layout stable without overlap
    w = max(0.16, min(0.84, 0.022*len(text) + 0.12))
    h = 0.075 if len(text) < 17 else 0.095
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
                    boxstyle=f'round,pad={pad},rounding_size={radius}',
                    facecolor=fc, edgecolor=ec, linewidth=0.8))
    ax.text(x, y, text, ha=ha, va='center', fontsize=fontsize, color=color)

# -----------------------------
# (a) physical object
# -----------------------------
ax = fig.add_subplot(gs[0, 0]); setup(ax, '(a) 物理对象')
# Main cylinder (slightly shaded body)
x0, x1, yc = 0.16, 0.84, 0.54
rx, ry = 0.085, 0.19
ax.add_patch(Rectangle((x0, yc-ry), x1-x0, 2*ry,
                       facecolor=PALE_BLUE, edgecolor=NAVY, linewidth=1.5))
ax.add_patch(Ellipse((x0, yc), 2*rx, 2*ry,
                     facecolor='#D2E7F2', edgecolor=NAVY, linewidth=1.5))
ax.add_patch(Ellipse((x1, yc), 2*rx, 2*ry,
                     facecolor='#C5DDEB', edgecolor=NAVY, linewidth=1.5))
# centerline
ax.plot([x0, x1], [yc, yc], color=MID_GRAY, lw=1.0, ls=(0,(4,3)))
# Radius dimension on left end
arrow(ax, (x0, yc), (x0, yc+ry), color=NAVY, lw=1.2, ms=7)
arrow(ax, (x0, yc+ry), (x0, yc), color=NAVY, lw=1.2, ms=7)
ax.text(x0-0.045, yc+0.105, 'R0', fontsize=10, color=NAVY, ha='right', va='center')
# Length dimension above
arrow(ax, (x0, 0.81), (x1, 0.81), color=NAVY, lw=1.15, ms=7)
arrow(ax, (x1, 0.81), (x0, 0.81), color=NAVY, lw=1.15, ms=7)
ax.text((x0+x1)/2, 0.846, 'L0', fontsize=10, color=NAVY, ha='center')
# ticks
ax.plot([x0, x0], [0.77, 0.84], color=NAVY, lw=1.0)
ax.plot([x1, x1], [0.77, 0.84], color=NAVY, lw=1.0)
# object annotation
label_box(ax, 0.50, 0.24, '均匀圆柱形药材', fc=PALE_BLUE2, ec='#B5D2E1', fontsize=9.2)
ax.text(0.50, 0.13, '初始半径 R0；初始长度 L0', ha='center', va='center',
        fontsize=8.8, color=GRAY)
ax.text(0.50, 0.065, '中心对称，外形随干燥过程变化', ha='center', va='center',
        fontsize=8.5, color=GRAY)

# -----------------------------
# (b) radial axisymmetric model
# -----------------------------
ax = fig.add_subplot(gs[0, 1]); setup(ax, '(b) 轴对称径向模型')
cx, cy = 0.50, 0.54
R = 0.29
# outer material and inner core rings
ax.add_patch(Circle((cx, cy), R, facecolor=PALE_BLUE, edgecolor=NAVY, linewidth=1.5))
ax.add_patch(Circle((cx, cy), 0.205, facecolor='#B9D8E8', edgecolor='#8DB9D0', linewidth=1.0))
ax.add_patch(Circle((cx, cy), 0.11, facecolor='#8DBBD0', edgecolor=BLUE, linewidth=1.0))
# radial coordinate and center
ax.plot([cx, cx+R+0.08], [cy, cy], color=GRAY, lw=1.0, ls=(0,(3,2)))
arrow(ax, (cx+0.015, cy), (cx+R+0.08, cy), color=GRAY, lw=1.0, ms=7)
ax.text(cx+R+0.095, cy+0.015, 'r', fontsize=9.5, color=GRAY, va='center')
ax.text(cx, cy+0.02, 'r = 0', fontsize=8.6, color=NAVY, ha='center')
ax.text(cx+R+0.015, cy-0.055, 'r = R(t)', fontsize=8.8, color=NAVY, ha='center')
# outward moisture arrows, four directions
for a in [25, 145, 205, 325]:
    a1, a2 = math.radians(a), math.radians(a)
    p1 = (cx + 0.14*math.cos(a1), cy + 0.14*math.sin(a1))
    p2 = (cx + 0.255*math.cos(a2), cy + 0.255*math.sin(a2))
    arrow(ax, p1, p2, color=MOIST, lw=1.5, ms=8)
# heat arrows on outer ring (short radial arrows)
for a in [65, 115, 245, 295]:
    aa = math.radians(a)
    p1 = (cx + 0.305*math.cos(aa), cy + 0.305*math.sin(aa))
    p2 = (cx + 0.255*math.cos(aa), cy + 0.255*math.sin(aa))
    arrow(ax, p1, p2, color=RED, lw=1.4, ms=8)
# labels
ax.text(0.50, 0.875, '热量由外向内传入', ha='center', va='center', color=RED, fontsize=8.8)
ax.text(0.50, 0.095, '水分由内部向表面迁移', ha='center', va='center', color=MOIST, fontsize=8.8)
# small legend
ax.add_line(Line2D([0.10,0.18],[0.19,0.19], color=RED, lw=2.0))
ax.text(0.20, 0.19, '热量', va='center', fontsize=8.4, color=RED)
ax.add_line(Line2D([0.32,0.40],[0.19,0.19], color=MOIST, lw=2.0))
ax.text(0.42, 0.19, '水分通量', va='center', fontsize=8.4, color=MOIST)
ax.text(0.50, 0.045, '二维扩展保留 r–z 轴对称性', ha='center', va='center',
        fontsize=8.2, color=GRAY)

# -----------------------------
# (c) external environment and boundary definitions
# -----------------------------
ax = fig.add_subplot(gs[0, 2]); setup(ax, '(c) 外界条件与边界定义')
# External environment box
ax.add_patch(FancyBboxPatch((0.04,0.34), 0.32, 0.48,
                            boxstyle='round,pad=0.012,rounding_size=0.015',
                            facecolor='#F8FAFB', edgecolor=MID_GRAY, linewidth=1.0))
ax.text(0.20, 0.765, '外界环境', ha='center', color=NAVY, fontsize=9.5, fontweight='bold')
ax.text(0.20, 0.66, 'T∞  环境温度', ha='center', color=RED, fontsize=8.8)
ax.text(0.20, 0.58, 'H∞  环境含湿状态', ha='center', color=MOIST, fontsize=8.8)
ax.text(0.20, 0.47, 'h、h_m：侧面换热/传质', ha='center', color=GRAY, fontsize=8.3)
ax.text(0.20, 0.39, 'h_e、h_m,e：端面换热/传质', ha='center', color=GRAY, fontsize=8.3)
# 2D r-z material domain
left, bottom, width, height = 0.50, 0.39, 0.36, 0.39
ax.add_patch(Rectangle((left,bottom), width,height, facecolor=PALE_BLUE,
                       edgecolor=NAVY, linewidth=1.5))
# boundary strips
ax.add_patch(Rectangle((left,bottom), 0.025,height, facecolor='#C3DFEC', edgecolor='none'))
ax.add_patch(Rectangle((left+width-0.025,bottom), 0.025,height, facecolor='#C3DFEC', edgecolor='none'))
ax.add_patch(Rectangle((left,bottom), width, 0.025, facecolor='#D7E8F1', edgecolor='none'))
ax.add_patch(Rectangle((left,bottom+height-0.025), width, 0.025, facecolor='#D7E8F1', edgecolor='none'))
# axis and surface labels
ax.plot([left+0.045,left+0.045],[bottom,bottom+height], color=GRAY, lw=1, ls=(0,(3,2)))
ax.text(left+0.045, bottom-0.045, 'r = 0', fontsize=8.2, color=GRAY, ha='center')
ax.text(left+width-0.015, bottom+height+0.035, 'r = R(t)', fontsize=8.4, color=NAVY, ha='right')
ax.text(left+width/2, bottom-0.07, 'z = -H(t)/2', fontsize=8.2, color=NAVY, ha='center')
ax.text(left+width/2, bottom+height+0.075, 'z = +H(t)/2', fontsize=8.2, color=NAVY, ha='center')
# arrows from environment to side and ends
arrow(ax, (0.39, 0.68), (left-0.01, 0.68), color=RED, lw=1.3, ms=7)
arrow(ax, (0.39, 0.56), (left-0.01, 0.56), color=MOIST, lw=1.3, ms=7)
arrow(ax, (0.68, 0.87), (0.68, bottom+height+0.01), color=RED, lw=1.3, ms=7)
arrow(ax, (0.78, 0.87), (0.78, bottom+height+0.01), color=MOIST, lw=1.3, ms=7)
ax.text(0.40, 0.72, '热量', color=RED, fontsize=8.2, ha='right')
ax.text(0.40, 0.51, '水分', color=MOIST, fontsize=8.2, ha='right')
ax.text(0.865, 0.67, '侧面边界\n(h, h_m)', color=NAVY, fontsize=8.0, ha='left', va='center')
ax.text(0.73, 0.90, '端面边界\n(h_e, h_m,e)', color=NAVY, fontsize=8.0, ha='center', va='bottom')
# condition strip at bottom
ax.add_patch(FancyBboxPatch((0.04,0.055), 0.92, 0.20,
                            boxstyle='round,pad=0.012,rounding_size=0.015',
                            facecolor='#F8FAFB', edgecolor=LIGHT_GRAY, linewidth=0.9))
ax.text(0.07, 0.205, '侧面：', fontsize=8.0, color=NAVY, ha='left', va='center', fontweight='bold')
ax.text(0.18, 0.205, '−k∂T/∂n = h(T_s−T∞)，  −D∂X/∂n = h_m(X_s−X∞)',
        fontsize=7.7, color=GRAY, ha='left', va='center')
ax.text(0.07, 0.125, '端面：', fontsize=8.0, color=NAVY, ha='left', va='center', fontweight='bold')
ax.text(0.18, 0.125, '−k∂T/∂n = h_e(T_s−T∞)，  −D∂X/∂n = h_m,e(X_s−X∞)',
        fontsize=7.7, color=GRAY, ha='left', va='center')

# Overall title
fig.suptitle('模型假设中的物理对象与边界描述', x=0.5, y=0.965,
             fontsize=15, fontweight='bold', color=NAVY)

out_dir = os.path.join(os.path.dirname(__file__))
base = os.path.join(out_dir, '模型假设_物理对象与边界描述')
fig.savefig(base + '.svg', bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.pdf', bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.png', dpi=600, bbox_inches='tight', pad_inches=0.08)
print(base + '.svg')
print(base + '.pdf')
print(base + '.png')

