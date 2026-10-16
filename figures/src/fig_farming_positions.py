"""The farming axis positions (@fig-farming-positions): six low views across farmland.

Generates figures/fig_farming_positions.svg. Six views over the same kind
of countryside as the scale transect, each at the scale its kind of array is
usually built at, from a close look at sheep under the rows (S1) to the dry
corners of a center pivot (S4). Each array sits above a strip of foreground.
The sky in each view carries the position's tint, blue at the sharing end,
neutral at S3, purple at the sparing end.

Edit here and rerun with `python3 figures/src/fig_farming_positions.py`.
"""
import math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from persp_tiles import *

random.seed(9)
SKY = {0: "#cfe1f0", 1: "#d6e6f2", 2: "#e1edf5", 3: "#ecebe5", 4: "#e9e1f1", 5: "#e3d8ee"}
PRAIRIE, MADE, SCRUB, GRAVEL = "#cbbf86", "#cfcbbb", "#b9bb86", "#e3ddcc"

def aisles(y0, y1, pitch, w=2.8):
    return [y + w * 0.9 + (pitch - w * 0.9) / 2 for y in np.arange(y0, y1, pitch)]

def water_tower(t, x, y, h=30):
    b1, b2 = t.P(x - 3, y), t.P(x + 3, y); top = t.P(x, y, h); c = t.P(x, y, h + 4)
    r = 6 * t.px_per_m(x, y)
    t.obj(x, y, f'<polyline points="{b1[0]:.1f},{b1[1]:.1f} {top[0]:.1f},{top[1]:.1f} {b2[0]:.1f},{b2[1]:.1f}" fill="none" stroke="#7d8a92" stroke-width="1"/>'
                f'<ellipse cx="{c[0]:.1f}" cy="{c[1]:.1f}" rx="{r:.1f}" ry="{r*0.62:.1f}" fill="#dfe6ea" stroke="#7d8a92" stroke-width="0.8"/>')

def pivot(t, cx, cy, r, crop="#a3c46c", arm=0.9):
    """A center-pivot circle: the watered crop, the wheel tracks, the arm."""
    t.poly([(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 80)], crop)
    for k in (0.35, 0.65, 0.95):
        pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in (t.P(cx + r * k * math.cos(q), cy + r * k * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 80)))
        t.ground.append(f'<polygon points="{pts}" fill="none" stroke="#7f9f4a" stroke-opacity="0.5" stroke-width="0.6"/>')
    if arm is not None:
        pts = [t.P(cx + r * k * math.cos(arm), cy + r * k * math.sin(arm), 3.5) for k in np.linspace(0, 1, 8)]
        t.obj(cx + r * 0.5 * math.cos(arm), cy + r * 0.5 * math.sin(arm), f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="#6b6860" stroke-width="1.1"/>')

FARM = (CORN, SOY, HAY, CORN, SOY, PASTURE)
tiles = []

# S0 -- created agriculture: a capped landfill at the edge of town, grazed under the panels
t = PTile.fit(0, 34, x=100, y=26, w_m=190, w_px=178, p=0.78); t.sky = SKY[0]
countryside(t, FARM, seed=20)
t.field(-500, t.y_front - 5, 700, 330, GRASS)
town(t, -700, 520, 360, 1500, block=120, seed=8)
for k in range(5): t.building(232 + (k % 2) * 80, 60 + k * 70, 60, 36, 9, "#e6e2d8", "#a9a59b", gable=False)   # warehouses
for k in range(4): t.building(-330 + k * 80, 360, 60, 36, 8, "#e6e2d8", "#a9a59b", gable=False)
t.water([(150 + 26 * math.cos(a), 3 + 7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)])   # the stormwater pond
road_grid(t, 9, xs=[-Q / 2], ys=[-Q / 2 + 330, 330])
t.poly([(204, 20), (212, 20), (212, 330), (204, 330)], "#e3ddcc")                                     # the access road
t.plateau(0, 26, 200, 210, 10, 20, "#b9c58f", "#a6b47e")
t.array(26, 50, 174, 186, pitch=7.0, z0=10)
for _ in range(36): t.animal(random.uniform(30, 170), random.choice(aisles(50, 100, 7.0)), z0=10)
for x in (14, 186): t.pole(x, 30, 1.6)                                                               # gas vents
fence(t, -80, 14, 230, 14, post=5)
water_tower(t, 300, 640)
t.label = "about 190 m across"
tiles.append(t)

# S1 -- primary agriculture: up close, the flock still grazing the pasture under the rows
t = PTile.fit(1, 31, x=16, y=16, w_m=40, w_px=178, p=0.72); t.sky = SKY[1]
countryside(t, (PASTURE, HAY, PASTURE, CORN), seed=21)
t.field(-200, t.y_front - 2, 220, 140, PASTURE)
t.array(-12, 16, 44, 72, pitch=7.0, w=2.8, h0=2.2)
fence(t, -30, 9, 60, 9, post=2.5)
for y in [12.5] + aisles(16, 50, 7.0):
    for _ in range(3): t.animal(random.uniform(-4, 36), y + random.uniform(-0.4, 0.8))
for _ in range(5): t.animal(random.uniform(-6, 34), random.uniform(3, 7))
t.water([(30 + 1.6 * math.cos(a), 5 + 0.7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24)])   # the stock tank
hedgerow(t, [(-260, 150), (260, 150)], spacing=8, seed=22)
homestead(t, -120, 260, seed=23)
woodlot(t, 60, 330, 260, 460, seed=24)
t.label = "about 40 m across"
tiles.append(t)

# S2 -- secondary agriculture: the corn field cut for hay now, bales in the aisles, hives along a flowering edge
t = PTile.fit(2, 32, x=45, y=30, w_m=105, w_px=178, p=0.74); t.sky = SKY[2]
countryside(t, (CORN, SOY, CORN, SOY, HAY), seed=25)
t.field(-150, 10, 260, 170, HAY)
t.field(-150, t.y_front - 2, 260, 10, "#c9c79a")
for _ in range(90): t.tree(random.uniform(-40, 130), random.uniform(t.y_front, 9), random.uniform(0.25, 0.4), random.choice(["#e0c25a", "#b98bc4", "#d9884f"]), "#8d7a3a")
for k in range(8): t.building(4 + k * 3.2, 14, 0.9, 0.6, 0.8, "#ffffff", "#e6e1d6", gable=False)   # beehives
t.poly([(-150, 11), (260, 11), (260, 14), (-150, 14)], "#e3ddcc")                                  # the lane along the edge
t.array(2, 30, 88, 150, pitch=11.0)
for y in [24] + aisles(30, 150, 11.0)[:6]:
    for _ in range(3): t.bale(random.uniform(6, 84), y + random.uniform(-0.6, 0.6))
hedgerow(t, [(-300, 185), (300, 185)], seed=26)
farmstead(t, 180, 300)
woodlot(t, -320, 260, -60, 420, seed=27)
t.label = "about 100 m across"
tiles.append(t)

# S3 -- ordinary-land siting: a whole forty taken at the crossroads, mown, the farm beyond
t = PTile.fit(3, 30, x=200, y=26, w_m=520, w_px=178, p=0.74); t.sky = SKY[3]
countryside(t, (SOY, CORN, CORN, SOY), seed=28)
t.field(-Q + 4, t.y_front - 2, -4, -4, CORN, furrow=12)
t.field(4, 4, 398, 398, "#c4d39a")
t.field(406, 4, Q - 4, 398, SOY, furrow=12)
ck = [(x, 660 + 50 * math.sin(x / 220)) for x in np.linspace(-3000, 3600, 120)]
t.creek(ck, 7)
road_grid(t, 8)
for x in np.arange(-600, 1200, 70): t.pole(x, -9)
t.array(20, 20, 382, 382, pitch=7.0)
farmstead(t, 560, 470)
for (x, y) in ck[::3]:
    if random.random() < 0.6: t.tree(x, y + random.uniform(-14, 14), 6)
homestead(t, -280, -8, seed=29, south=True)
homestead(t, 300, Q + 10, seed=30, barn=None)
woodlot(t, -380, 420, -60, 760, seed=31)
t.label = "about 520 m across"
tiles.append(t)

# S4 -- low-productivity siting: the dry corners of a center pivot, the circle still farmed
t = PTile.fit(4, 40, x=402, y=20, w_m=860, w_px=178, p=0.80); t.sky = SKY[4]
countryside(t, FARM, seed=32)
t.field(6, 6, Q - 6, Q - 6, "#d6cfa6")
for (qx, qy) in [(-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (0, 2), (-2, 2), (1, 2)]:
    pivot(t, qx * Q + Q / 2, qy * Q + Q / 2, 380, crop=random.choice(["#a3c46c", "#b2cc7c", "#c9d796"]), arm=random.uniform(0, 6))
c, r = (Q / 2, Q / 2), 386
pivot(t, c[0], c[1], r, arm=0.9)
road_grid(t, 11)
arc = lambda q0, q1: [(c[0] + (r + 8) * math.cos(q), c[1] + (r + 8) * math.sin(q)) for q in np.linspace(q0, q1, 18)]
for (cx_, cy_), q0 in [((16, 16), math.pi), ((Q - 16, 16), 1.5 * math.pi), ((Q - 16, Q - 16), 0), ((16, Q - 16), 0.5 * math.pi)]:
    t.array_in([(cx_, cy_)] + arc(q0, q0 + math.pi / 2), pitch=7.0)
t.water([(Q + 140 + 40 * math.cos(a), -110 + 16 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)])   # an irrigation pond
homestead(t, Q + 260, -10, seed=33, south=True)
homestead(t, -240, Q + 12, seed=34, barn=None)
t.label = "about 860 m across"
tiles.append(t)

# S5 -- impaired-land siting: a prairie strip along the creek the field used to wash into, panels following it
t = PTile.fit(5, 38, x=260, y=190, w_m=330, w_px=178, p=0.80); t.sky = SKY[5]
countryside(t, FARM, seed=35)
ck = lambda x: 360 + 60 * math.sin(x / 140)
t.field(-1500, t.y_front - 2, 2700, 500, CORN, furrow=14)
band_ = [(x, ck(x) - 196) for x in np.linspace(-1500, 2700, 90)] + [(x, ck(x) + 60) for x in np.linspace(2700, -1500, 90)]
t.poly(band_, PRAIRIE)
t.creek([(x, ck(x)) for x in np.linspace(-1500, 2700, 160)], 9)
t.water([(820 + 70 * math.cos(a), ck(820) + 34 + 22 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 30)])   # a restored wetland
road_grid(t, 8, ys=[0, Q, 2 * Q], xs=[-Q, Q])
for x in np.linspace(-1500, 2700, 160):
    for off in (-10, 10):
        if random.random() < 0.65: t.tree(x + random.uniform(-5, 5), ck(x) + off, 5)
t.array_in([(x, ck(x) - 186) for x in np.linspace(-120, 640, 70)] + [(x, ck(x) - 26) for x in np.linspace(640, -120, 70)], pitch=7.0)
farmstead(t, -360, 120)
homestead(t, 1000, Q + 10, seed=36)
woodlot(t, 1100, 520, 1500, 760, seed=37)
t.label = "about 330 m across"
tiles.append(t)

DESC = ("Six low views across farmland, one per position on the farming axis, each at the scale its kind of array is usually built at and each set above a strip of foreground, "
        "with the sky in each tinted from blue at the sharing end to purple at the sparing end. "
        "S0 Created agriculture, about 190 meters across: panels on a capped landfill at the edge of town, grazed by sheep, with a stormwater pond in front and warehouses, a water tower, and the town beyond. "
        "S1 Primary agriculture, about 40 meters across: up close, sheep grazing the pasture in front of, between, and under the rows, with a stock tank and a fence. "
        "S2 Secondary agriculture, about 100 meters across: a former corn field cut for hay, round bales in the aisles, and beehives along a flowering edge by the farm lane. "
        "S3 Ordinary-land siting, about 520 meters across: a whole forty at the crossroads taken and mown, the distribution line along the road, a creek and the farm beyond. "
        "S4 Low-productivity siting, about 860 meters across: arrays in the four dry corners of a center pivot whose circle is still farmed, among the neighbors' pivots, with an irrigation pond. "
        "S5 Impaired-land siting, about 330 meters across: panels following a prairie strip along the creek the field used to wash into, with corn still farmed in front.")
SC = {0: "#0d3452", 1: "#1c4c73", 2: "#2f6b96", 3: "#5f5e5a", 4: "#6a4a91", 5: "#46295f"}
TXT = {"b": ("#f1f6fa", "#c9dbe8"), "n": ("#f2f1ec", "#dcdad2"), "p": ("#eee8f5", "#ddd3ea")}
ROWS = [(0, "CREATED", "AGRICULTURE", "a use that was not there", "grazing on made ground", "b"),
        (1, "PRIMARY", "AGRICULTURE", "the prior use, continued", "crops, vines, pasture", "b"),
        (2, "SECONDARY", "AGRICULTURE", "farmed, less intensively", "grazing, hay, hives", "b"),
        (3, "ORDINARY-LAND", "SITING", "an ordinary field, taken", "a whole field, mown", "n"),
        (4, "LOW-PRODUCTIVITY", "SITING", "idled or underproducing", "poor hay, brightfields", "p"),
        (5, "IMPAIRED-LAND", "SITING", "ground carrying a burden", "prairie on retired fields", "p")]
BAR = [(SC[c], [("cd", f"S{c}", 24), ("nm", n1, 42), ("nm", n2, 57), (f"ca ca-{k}", ca, 76), (f"ac ac-{k}", ac, 92)]) for c, n1, n2, ca, ac, k in ROWS]
STYLE = ['.cd{font-size:21px;font-weight:700;fill:#ffffff}', '.nm{font-size:13px;font-weight:700;letter-spacing:.02em;fill:#ffffff}',
         '.ca{font-size:12.5px}.ac{font-size:12px}'] + [f'.ca-{k}{{fill:{a}}}.ac-{k}{{fill:{b}}}' for k, (a, b) in TXT.items()]
assemble(tiles, "Farming axis positions", DESC, "LAND SHARING", "FARMING AXIS", "LAND SPARING", BAR, STYLE,
         "fig_farming_positions.svg", bar_h=102)
