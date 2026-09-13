import os, math
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, FancyBboxPatch, FancyArrowPatch, Arc, Polygon, Circle

FONT = 'Microsoft YaHei'
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': [FONT, 'Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

NAVY = '#263B4D'
STEEL = '#778692'
STEEL_LIGHT = '#DCE3E7'
WARM = '#F3E4D1'
WARM_DARK = '#B88E60'
WOOD = '#C99A6A'
WOOD_DARK = '#8F6948'
AIR = '#D8794D'
BLUE = '#4B86A8'
WHITE = '#FFFFFF'

fig, ax = plt.subplots(figsize=(8.6, 4.7), facecolor='white')
ax.set_xlim(0, 10); ax.set_ylim(0, 5.8); ax.axis('off')

# Soft background panel for a clean scene-figure appearance.
ax.add_patch(FancyBboxPatch((0.25, 0.35), 9.5, 4.95,
                            boxstyle='round,pad=0.02,rounding_size=0.08',
                            facecolor='#FAFBFC', edgecolor='#D5DDE2', linewidth=1.0))

# Oven outer housing / cutaway.
ax.add_patch(FancyBboxPatch((0.75, 0.8), 8.35, 4.0,
                            boxstyle='round,pad=0.04,rounding_size=0.16',
                            facecolor='#EEF2F4', edgecolor=NAVY, linewidth=1.6))
# inner chamber
ax.add_patch(Rectangle((1.05, 1.1), 7.75, 3.35,
                       facecolor='#F9FAFA', edgecolor=STEEL, linewidth=1.0))
# back wall subtle panel
ax.add_patch(Rectangle((1.28, 1.35), 7.30, 2.80,
                       facecolor='#F4F6F7', edgecolor='#D1D9DE', linewidth=0.8))

# Side guide rails.
for y in [1.55, 2.25, 2.95, 3.65]:
    ax.plot([1.10, 1.48], [y, y], color=STEEL, lw=1.2)
    ax.plot([8.38, 8.70], [y, y], color=STEEL, lw=1.2)

# Fan housing on back wall.
fcx, fcy = 7.55, 3.63
ax.add_patch(Circle((fcx, fcy), 0.43, facecolor='#E7ECEF', edgecolor=NAVY, linewidth=1.1))
ax.add_patch(Circle((fcx, fcy), 0.30, facecolor='#C8D2D8', edgecolor=STEEL, linewidth=0.9))
ax.add_patch(Circle((fcx, fcy), 0.075, facecolor=NAVY, edgecolor='none'))
for ang in [0, 90, 180, 270]:
    a = math.radians(ang)
    x1 = fcx + 0.08*math.cos(a); y1 = fcy + 0.08*math.sin(a)
    x2 = fcx + 0.28*math.cos(a+0.34); y2 = fcy + 0.28*math.sin(a+0.34)
    ax.plot([x1, x2], [y1, y2], color=NAVY, lw=2.0, solid_capstyle='round')

# Perforated tray in perspective.
tray_top = [(1.12, 2.08), (8.70, 2.08), (8.42, 1.55), (1.38, 1.55)]
ax.add_patch(Polygon(tray_top, closed=True, facecolor='#DDE5E9', edgecolor=NAVY, linewidth=1.15))
# front lip
ax.add_patch(Polygon([(1.38,1.55),(8.42,1.55),(8.42,1.32),(1.38,1.32)],
                     closed=True, facecolor='#C9D3D9', edgecolor=NAVY, linewidth=1.0))
# perforations
for row in range(3):
    yy = 1.68 + row*0.14
    for col in range(15):
        xx = 1.62 + col*0.46 + (0.20 if row % 2 else 0)
        if xx < 8.12:
            ax.add_patch(Ellipse((xx, yy), 0.095, 0.045,
                                 facecolor='#7D8A92', edgecolor='none', alpha=0.75))

# Cylindrical medicinal material on tray, slightly angled.
# Shadow
ax.add_patch(Ellipse((5.05, 2.14), 5.65, 0.16, facecolor='#9EAAB0', alpha=0.22, edgecolor='none'))
# body as a tapered polygon
body = [(2.65,2.18),(7.62,2.03),(7.78,2.23),(2.77,2.39)]
ax.add_patch(Polygon(body, closed=True, facecolor=WOOD, edgecolor=WOOD_DARK, linewidth=1.2))
# end caps
ax.add_patch(Ellipse((2.70,2.285), 0.30, 0.37, angle=-2,
                     facecolor='#D3A779', edgecolor=WOOD_DARK, linewidth=1.15))
ax.add_patch(Ellipse((7.68,2.13), 0.38, 0.43, angle=-2,
                     facecolor='#B78252', edgecolor=WOOD_DARK, linewidth=1.15))
# restrained longitudinal texture
for off in [0.0, 0.06, 0.12]:
    xs = [2.78, 3.65, 4.65, 5.62, 6.62, 7.50]
    ys = [2.30+off, 2.27+off, 2.25+off, 2.22+off, 2.18+off, 2.15+off]
    ax.plot(xs, ys, color='#A87850', lw=0.8, alpha=0.50)
# cuticle rings near end
for dx in [0.04, 0.10, 0.16]:
    ax.add_patch(Arc((2.70+dx,2.285), 0.25, 0.31, angle=-2,
                     theta1=80, theta2=280, color='#9B704E', lw=0.75, alpha=0.65))

# Heat-flow and moisture-flow arrows in the chamber.
for start, end in [((2.0, 3.55), (3.75, 2.72)), ((3.4, 3.55), (4.8, 2.75)), ((6.3, 3.45), (6.15, 2.72))]:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=12,
                                 color=AIR, linewidth=1.5, alpha=0.82,
                                 connectionstyle='arc3,rad=-0.12'))
for start, end in [((3.15, 2.50), (2.45, 3.18)), ((5.25, 2.40), (5.85, 3.12))]:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=11,
                                 color=BLUE, linewidth=1.4, alpha=0.78,
                                 connectionstyle='arc3,rad=0.16'))

# Minimal labels, kept outside the object where possible.
ax.text(1.08, 5.08, '热风干燥场景', fontsize=15, fontweight='bold', color=NAVY, ha='left')
ax.text(7.55, 4.28, '热风循环', fontsize=10.2, color=NAVY, ha='center')
ax.text(8.95, 3.65, '风机', fontsize=9.8, color=NAVY, ha='left', va='center')
ax.text(4.95, 1.05, '托盘', fontsize=9.8, color=STEEL, ha='center')
ax.text(5.15, 2.70, '圆柱形药材', fontsize=10.0, color=WOOD_DARK, ha='center')
# Compact legend.
ax.add_patch(FancyArrowPatch((1.35,0.58),(1.82,0.58), arrowstyle='-|>', mutation_scale=9,
                             color=AIR, linewidth=1.4))
ax.text(1.92,0.58,'热风', va='center', fontsize=9.0, color=AIR)
ax.add_patch(FancyArrowPatch((2.65,0.58),(3.12,0.58), arrowstyle='-|>', mutation_scale=9,
                             color=BLUE, linewidth=1.4))
ax.text(3.22,0.58,'水分逸出', va='center', fontsize=9.0, color=BLUE)

out_dir = os.path.dirname(__file__)
base = os.path.join(out_dir, '问题重述_热风干燥场景_简约版')
fig.savefig(base + '.png', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.tiff', dpi=600, bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.svg', bbox_inches='tight', pad_inches=0.08)
fig.savefig(base + '.pdf', bbox_inches='tight', pad_inches=0.08)
print(base + '.png')
print(base + '.tiff')
print(base + '.svg')
print(base + '.pdf')
