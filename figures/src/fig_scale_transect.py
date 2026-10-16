"""The scale transect zones (@fig-scale-transect): six low views across farmland.

Generates figures/fig_scale_transect.svg. Six views across flat farmland,
one per zone, each looking north toward a horizon over the same kind of
countryside: county roads on the half-mile lines, fields in 40s and 80s,
farmsteads along the roads, woodlots, and water. Each array sits above a strip
of foreground, and the ground in view grows from a barn roof (A0) to blocks
of quarter sections (A5) while the tile stays the same size; the same farm,
with its red barn and silo, recedes from the foreground to a speck.

Edit here and rerun with `python3 figures/src/fig_scale_transect.py`.
"""
import math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from persp_tiles import *

random.seed(3)
PAL = (CORN, SOY, HAY, CORN, SOY, PASTURE, CORN)
GRAVEL, UNDER = "#e3ddcc", "#c2cf98"      # farm lanes; the mown ground under the panels

def riparian(t, pts, r, seed=5, every=1):
    rng = random.Random(seed)
    for (x, y) in pts[::every]:
        for off in (-1, 1):
            if rng.random() < 0.75:
                t.tree(x + rng.uniform(-r, r), y + off * r * rng.uniform(1.6, 2.6), r * rng.uniform(0.8, 1.15))

def poles(t, y, x0, x1, step, h=10.0):
    for x in np.arange(x0, x1, step):
        t.pole(x, y, h)

def label(t, y):
    w = t.width_at(y)
    t.label = f"about {w / 1000:.1f} km across" if w >= 1000 else f"about {int(round(w, -1 if w < 300 else -1))} m across"

tiles = []

# A0 -- rooftop: the array is the barn roof; the yard in front, a pond, the road behind
t = PTile.fit(0, 40, x=13, y=30, w_m=26, w_px=104, p=0.80)
countryside(t, PAL, seed=10)
t.field(-60, t.y_front - 10, 90, 120, GRASS)
t.field(40, 52, 90, 120, PASTURE)
t.poly([(-36, 18), (29, 18), (29, 50), (-36, 50)], YARD)
t.water([(58 + 12 * math.cos(a), 78 + 5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)])
road_grid(t, 7, xs=[-180], ys=[150, 150 + Q])
poles(t, 142, -200, 300, 45)
t.poly([(-60, 22), (-36, 22), (-36, 27), (-60, 27)], GRAVEL)
t.building(0, 30, 26, 13, 7, "#b5523a", "#6e6b63", pv=True)
t.silo(-6, 38, 2.4, 13)
t.building(30, 31, 9, 8, 4.6, "#ffffff", "#7c7a72")
t.building(-26, 44, 18, 12, 5, "#d9d6cc", "#9ea3a6", gable=False)
for k in range(4): t.bale(19 + k * 1.9, 24.5)
fence(t, 29, 18, 29, 50)
fence(t, 40, 50, 90, 50)
for x in (-40, -30, 48, 70, 84): t.tree(x, 100 + random.uniform(-6, 6), 4.6, "#6f9150", "#557538")
homestead(t, -70, 170, seed=21)
woodlot(t, 120, 420, 420, 700, seed=22)
hedgerow(t, [(-400, 560), (40, 560)], seed=23)
label(t, 30)
tiles.append(t)

# A1 -- farmstead: three rows in the paddock, a driveway off the road, a farm pond behind
t = PTile.fit(1, 38, x=72, y=36, w_m=150, w_px=178, p=0.74)
countryside(t, PAL, seed=11)
t.field(-4, 14, 150, 104, PASTURE)
t.water([(118 + 15 * math.cos(a), 118 + 6 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)])
road_grid(t, 7, xs=[-300, -300 + Q], ys=[0, Q, 2 * Q])
poles(t, -7, -200, 400, 50)
t.poly([(20, 3.5), (27, 3.5), (27, 34), (20, 34)], GRAVEL)                  # driveway
farmstead(t, 30, 60)
t.array(86, 36, 136, 64, pitch=7.0, w=3.0, h0=2.0, tilt=0.38)
for x0, y0, x1, y1 in [(74, 14, 150, 14), (74, 14, 74, 30), (150, 14, 150, 104)]: fence(t, x0, y0, x1, y1)
for _ in range(8): t.animal(random.uniform(80, 145), random.uniform(17, 31), cow=True)
homestead(t, 300, -8, seed=24, barn=None, south=True)
hedgerow(t, [(-300, 402), (500, 402)], seed=25)
woodlot(t, -250, 520, 60, 780, seed=26)
homestead(t, 260, Q + 8, seed=27)
label(t, 36)
tiles.append(t)

# A2 -- commercial: the array takes the corner of a corn field at the crossroads; a creek behind
t = PTile.fit(2, 36, x=70, y=30, w_m=250, w_px=178, p=0.72)
countryside(t, PAL, seed=12)
t.field(4, 4, 402, 402, CORN, furrow=9)
t.field(24, 24, 156, 136, UNDER)
ck = [(x, 330 + 32 * math.sin(x / 80)) for x in np.linspace(-900, 1400, 120)]
t.creek(ck, 6)
road_grid(t, 7, xs=[0, Q], ys=[0, Q, 2 * Q])
poles(t, -7, -300, 600, 55)
t.array(30, 30, 150, 130, pitch=7.0)
farmstead(t, -90, 150)
t.poly([(-6, 142), (-56, 142), (-56, 148), (-6, 148)], GRAVEL)
homestead(t, 210, -6, seed=28, south=True)
riparian(t, ck, 5, every=2)
woodlot(t, -420, 360, -150, 560, seed=29)
homestead(t, 300, Q + 6, seed=30, barn=None)
hedgerow(t, [(402, 4), (402, 402)], seed=31)
label(t, 30)
tiles.append(t)

# A3 -- community: about 25 acres at the crossroads behind a sown border, the line it ties into, a stream beyond
t = PTile.fit(3, 34, x=210, y=40, w_m=520, w_px=178, p=0.73)
countryside(t, PAL, seed=13)
t.field(4, 4, Q - 4, Q - 4, SOY, furrow=12)
t.field(24, 24, 396, 336, "#c9cf8e")
t.field(40, 40, 380, 320, UNDER)
ck = [(x, 610 + 70 * math.sin(x / 260)) for x in np.linspace(-2500, 3200, 120)]
t.creek(ck, 9)
woodlot(t, 470, 480, Q - 8, Q - 8, seed=32)
road_grid(t, 8, ys=[0, Q, 2 * Q])
poles(t, -9, -600, 1200, 70)
t.array(40, 40, 380, 320, pitch=7.0)
for y in np.arange(110, 560, 90): t.building(-34, y, 11, 9, 5, "#ffffff", "#8a8379")      # houses along the road
for y in np.arange(140, 560, 120): t.building(-48, y + 30, 14, 10, 4, "#d9d6cc", "#9ea3a6", gable=False)
farmstead(t, 470, 330)
riparian(t, ck, 7, every=2)
homestead(t, -380, 10, seed=33)
homestead(t, 420, -10, seed=34, south=True, barn=None)
homestead(t, 200, Q + 8, seed=35)
label(t, 40)
tiles.append(t)

# A4 -- utility: a quarter section between the half-mile roads, a substation by the road, a river beyond
t = PTile.fit(4, 32, x=402, y=30, w_m=930, w_px=178, p=0.75)
countryside(t, PAL, seed=14)
t.field(14, 14, Q - 14, Q - 14, UNDER)
rv = [(x, 1500 + 190 * math.sin(x / 800)) for x in np.linspace(-14000, 16000, 160)]
t.creek(rv, 34)
woodlot(t, -700, 220, -360, 560, seed=36)
road_grid(t, 12)
t.array(30, 30, Q - 30, Q - 30, pitch=7.0)
t.field(640, -80, 740, -26, "#d9d6cc")
t.building(650, -72, 80, 40, 6, "#e8e6e0", "#a9a59b", gable=False)                     # substation
for k in range(6): t.tower(690 + 0 * k, -150 - 380 * k * 0, 34) if k == 0 else t.tower(690 + 420 * k, -110, 34)
t.tower(690, -210, 34)
riparian(t, rv, 14, every=1)
farmstead(t, -70, 420)
for x, y, s_, b in [(1150, 20, 37, None), (-420, Q + 20, 38, "#b5523a"), (560, Q + 20, 39, None), (1400, Q + 20, 40, "#b5523a"), (300, -12, 41, "#b5523a")]:
    homestead(t, x, y, seed=s_, barn=b, south=(y < 0))
label(t, 30)
tiles.append(t)

# A5 -- complex: quarter section after quarter section, one the assembly did not get, a town and a lake
t = PTile.fit(5, 30, x=1380, y=20, w_m=3800, w_px=178, p=0.76)
countryside(t, PAL, seed=15)
woodlot(t, 2 * Q + 420, Q + 420, 3 * Q - 30, 2 * Q - 30, seed=42)
for kx in range(4):
    for ky in range(4):
        if (kx, ky) != (2, 1):
            t.field(kx * Q + 20, ky * Q + 20, (kx + 1) * Q - 20, (ky + 1) * Q - 20, UNDER)
road_grid(t, 22)
t.water([(-900 + 3000 * math.cos(a) + 400 * math.sin(3 * a), 5600 + 1200 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 80)])
for kx in range(4):
    for ky in range(4):
        if (kx, ky) != (2, 1):
            t.array(kx * Q + 40, ky * Q + 40, (kx + 1) * Q - 40, (ky + 1) * Q - 40, pitch=7.0)
farmstead(t, 2 * Q + 200, Q + 160)
town(t, -Q + 40, Q + 30, -30, 2 * Q - 30)              # a small town across the road west of the arrays
for k in range(3): t.silo(-120 + k * 16, Q + 50, 7, 40)
t.building(3 * Q + 300, -120, 140, 90, 8, "#e8e6e0", "#a9a59b", gable=False)            # substation
for k in range(1, 6): t.tower(3 * Q + 370 - 900 * k, -260, 44)
for x, y, s_ in [(-600, -10, 43), (800, -10, 44), (2000, -10, 45), (-900, 30, 46)]:
    homestead(t, x, y, seed=s_, south=(y < 0))
label(t, 20)
tiles.append(t)

DESC = ("Six low views across flat farmland, one per zone of the scale transect, each looking north toward a horizon over the same kind of countryside: "
        "county roads on the half-mile lines, fields in forties and eighties, farmsteads along the roads, woodlots, and water. "
        "The ground in view grows from zone to zone while each tile stays the same size, and each array sits above a strip of foreground. "
        "A0 Rooftop, about 45 meters across: panels on the south slope of a barn roof, no ground taken, with the yard in front and a pond behind. "
        "A1 Farmstead, about 150 meters across: three rows in the paddock beside the barn, with cattle, a driveway off the road, and a farm pond. "
        "A2 Commercial, about 250 meters across: the corn keeps the field and the array takes the corner at the crossroads, with a creek behind. "
        "A3 Community, about 500 meters across: some 25 acres of panels behind a sown border at the crossroads, the distribution line along the road, houses along the side road, and a stream beyond. "
        "A4 Utility, about 900 meters across: a quarter section of panels between the half-mile roads, a substation and transmission line by the road, and a river beyond. "
        "A5 Complex, about 3.8 kilometers across: panels filling quarter section after quarter section, one the assembly did not get, where a farm still stands, with a substation, a small town with its elevator, woodlots, and a lake beyond. "
        "The same farm, a white house, a red barn, and a silo behind a windbreak, appears in each view.")
BAR = [("#5f5e5a", [("cd0", "A0", 24), ("nm", "ROOFTOP", 43), ("ca0", "any capacity", 66), ("ac0", "no ground taken", 86)]),
       ("#4C6636", [("cd", "A1", 24), ("nm", "FARMSTEAD", 43), ("ca", "&lt;100 kW", 66), ("ac", "under ~1 acre", 86)]),
       ("#435C2F", [("cd", "A2", 24), ("nm", "COMMERCIAL", 43), ("ca", "100 kW – 1 MW", 66), ("ac", "~0.5–8 acres", 86)]),
       ("#3A5228", [("cd", "A3", 24), ("nm", "COMMUNITY", 43), ("ca", "1 – 5 MW", 66), ("ac", "~6–30 acres", 86)]),
       ("#314821", [("cd", "A4", 24), ("nm", "UTILITY", 43), ("ca", "5 – 50 MW", 66), ("ac", "~30–300 acres", 86)]),
       ("#283E1A", [("cd", "A5", 24), ("nm", "COMPLEX", 43), ("ca", "50 MW +", 66), ("ac", "~300–10,000+ acres", 86)])]
STYLE = ['.cd{font-size:21px;font-weight:700;fill:#ffffff}.cd0{font-size:21px;font-weight:700;fill:#f2f1ec}',
         '.nm{font-size:14.5px;font-weight:700;letter-spacing:.03em;fill:#ffffff}',
         '.ca{font-size:15px;fill:#eef3e8}.ca0{font-size:15px;fill:#f2f1ec}',
         '.ac{font-size:14px;fill:#d3dfc6}.ac0{font-size:14px;fill:#dcdad2}']
assemble(tiles, "Scale transect zones", DESC, "SMALL", "SCALE TRANSECT", "LARGE", BAR, STYLE, "fig_scale_transect.svg")
