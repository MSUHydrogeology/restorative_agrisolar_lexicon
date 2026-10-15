"""Block diagrams of farm landscapes with arrays placed by farming-axis position.

Generates three figures, one per region, from the same drawing engine:
  midwest  figures/fig_farming_landscape.svg       (Figure 4.2, rolling corn and soybean ground)
  west     figures/fig_farming_landscape_west.svg  (an irrigated valley below dry foothills)
  east     figures/fig_farming_landscape_east.svg  (a dairy valley with hedgerows and woods)
Edit here and rerun with `python3 figures/src/fig_farming_landscape.py [region ...]`
rather than editing the SVGs; with no argument all three are drawn.

World units: x east, y north, z up. One unit ~ 30 m horizontally; relief and
panel sizes are exaggerated for legibility.
"""
import math, os, random, re, sys
import numpy as np
import contourpy

W, SCENE_H, BAND_H = 1104, 600, 102
H = SCENE_H + BAND_H
XMAX, YMAX, ZBASE = 120.0, 84.0, -3.2

# ---------------------------------------------------------------- terrain
def ys(x):           # stream centerline
    return 34 + 6 * math.sin((x + 8) / 16)

def wx(y):           # grassed waterway thalweg
    return 80 + 2.2 * math.sin(y / 6.5)

def sig(t):
    return 1 / (1 + math.exp(-t))

def mound(x, y):     # closed landfill
    cx, cy, hx, hy = 106, 57, 7.5, 5.0
    return 1.7 * sig((hx - abs(x - cx)) / 1.1) * sig((hy - abs(y - cy)) / 1.1)

def zf_midwest(x, y):
    d = y - ys(x)
    side = 1.0 if d > 0 else 0.85
    z = 4.4 * side * math.tanh(abs(d) / 10)
    z += 0.35 * math.sin(x / 9.0) * math.cos(y / 11.0) * min(1, abs(d) / 8)
    if d > 0:
        z -= 0.9 * math.exp(-((x - wx(y)) / 3.4) ** 2) * math.tanh(d / 8) * (1 - sig((y - 72) / 1.5))
    z += 1.5 * math.exp(-((x - 33) ** 2 + (y - 63) ** 2) / 34)
    z += mound(x, y)
    return z

TERRAIN = zf_midwest
def zf(x, y):
    return TERRAIN(x, y)


# ---------------------------------------------------------------- camera
T = np.array([60.0, 40.0, 0.0])
az = math.radians(214)        # camera sits to the SSW of the target
el = math.radians(33)
dist = 150
C = T + dist * np.array([math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)])
f = T - C; f /= np.linalg.norm(f)
r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r)
u = np.cross(r, f)

def raw(p):
    q = np.asarray(p, float) - C
    zc = q @ f
    return (q @ r) / zc, (q @ u) / zc, zc

# fit the block (top corners and base corners) into the scene area
corners = [(x, y, z) for x in (0, XMAX) for y in (0, YMAX) for z in (ZBASE, 6.0)]
pr = [raw(c) for c in corners]
minx, maxx = min(p[0] for p in pr), max(p[0] for p in pr)
miny, maxy = min(p[1] for p in pr), max(p[1] for p in pr)
FOC = min((W - 24) / (maxx - minx), (SCENE_H - 16) / (maxy - miny))
OX = (W - FOC * (maxx + minx)) / 2
OY = (SCENE_H + FOC * (maxy + miny)) / 2 + 2

def P(x, y, z=None):
    if z is None:
        z = zf(x, y)
    a, b, zc = raw((x, y, z))
    return OX + FOC * a, OY - FOC * b, zc

def depth(x, y, z=0):
    return raw((x, y, z))[2]

def pts(seq):
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in seq)

# ---------------------------------------------------------------- svg buffers
out = []
def add(s): out.append(s)

def drape_ring(ring, step=0.6, lift=0.0):
    """Densify a closed world ring and project it on the terrain."""
    res = []
    n = len(ring)
    for i in range(n):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        for j in range(k):
            t = j / k
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            res.append(P(x, y, zf(x, y) + lift)[:2])
    return res

def drape_line(line, step=0.6, lift=0.0):
    res = []
    for i in range(len(line) - 1):
        (x0, y0), (x1, y1) = line[i], line[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(L / step))
        for j in range(k):
            t = j / k
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            res.append(P(x, y, zf(x, y) + lift)[:2])
    x, y = line[-1]
    res.append(P(x, y, zf(x, y) + lift)[:2])
    return res

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def band(x0, x1, lo, hi, step=1.0):
    """Ring between two functions of x."""
    xs = list(np.arange(x0, x1, step)) + [x1]
    return [(x, lo(x)) for x in xs] + [(x, hi(x)) for x in reversed(xs)]

def poly(ring, fill, extra="", step=0.6, lift=0.0):
    add(f'<polygon points="{pts(drape_ring(ring, step, lift))}" fill="{fill}" {extra}/>')

# ---------------------------------------------------------------- palette
SC = {0: "#0d3452", 1: "#1c4c73", 2: "#2f6b96", 3: "#5f5e5a", 4: "#6a4a91", 5: "#46295f"}
GRASS, PASTURE, HAY = "#b4cc86", "#a9c57a", "#bfd391"
CORN, SOY = "#9fbc6a", "#cdd89c"
PRAIRIE = "#c4bc85"
YARD, TOWN = "#ddd8c9", "#e2ded4"
ROAD, ROAD_EDGE = "#f2efe6", "#b9b2a2"
WATER = "#7fa9c4"

# ---------------------------------------------------------------- block sides
def side_faces():
    # south face (y = 0) and west face (x = 0) are the ones the camera sees
    for face in ("south", "west"):
        if face == "south":
            top = [(x, 0.0) for x in np.arange(0, XMAX + 0.01, 0.5)]
        else:
            top = [(0.0, y) for y in np.arange(0, YMAX + 0.01, 0.5)]
        tp = [P(x, y)[:2] for x, y in top]
        a = top[0]; b = top[-1]
        base = [P(b[0], b[1], ZBASE)[:2], P(a[0], a[1], ZBASE)[:2]]
        add(f'<polygon points="{pts(tp + base)}" fill="#cbb89a" stroke="#8a7a62" stroke-width="0.9" stroke-linejoin="round"/>')
        # topsoil layer
        top2 = [P(x, y, zf(x, y) - 0.55)[:2] for x, y in reversed(top)]
        add(f'<polygon points="{pts(tp + top2)}" fill="#8c7356"/>')
        # a lower stratum line
        mid = [P(x, y, ZBASE + 1.2 + 0.25 * math.sin((x + y) / 7))[:2] for x, y in top]
        add(f'<polyline points="{pts(mid)}" fill="none" stroke="#b09c7c" stroke-width="0.9"/>')
    # front vertical edge line
    add(f'<line x1="{P(0,0)[0]:.1f}" y1="{P(0,0)[1]:.1f}" x2="{P(0,0,ZBASE)[0]:.1f}" y2="{P(0,0,ZBASE)[1]:.1f}" stroke="#8a7a62" stroke-width="0.9"/>')

ground = rect(0, 0, XMAX, YMAX)

# ---------------------------------------------------------------- shared helpers
def road(ring):
    poly(ring, ROAD, f'stroke="{ROAD_EDGE}" stroke-width="0.6"', 0.8, 0.03)

def hl_ring(code, ring):
    hl.append((code, ring))
    poly(ring, SC[code], 'fill-opacity="0.20"', 0.6, 0.04)

def tower(x, y, hgt=4.2):
    z = zf(x, y)
    b1 = P(x - 0.5, y, z)[:2]; b2 = P(x + 0.5, y, z)[:2]; t = P(x, y, z + hgt)[:2]
    a1 = P(x - 0.9, y, z + hgt * 0.82)[:2]; a2 = P(x + 0.9, y, z + hgt * 0.82)[:2]
    obj(x, y, f'<polyline points="{pts([b1, t, b2])}" fill="none" stroke="#7d7a72" stroke-width="0.9"/>'
              f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="#7d7a72" stroke-width="0.9"/>')
    return P(x - 0.9, y, z + hgt * 0.82)[:2], P(x + 0.9, y, z + hgt * 0.82)[:2]

def water_tower(x, y):
    z = zf(x, y)
    l1 = P(x - 0.6, y, z)[:2]; l2 = P(x + 0.6, y, z)[:2]; top = P(x, y, z + 4.2)[:2]
    c = P(x, y, z + 4.9)
    rad = FOC * 1.1 / c[2]
    obj(x, y, f'<polyline points="{pts([l1, top, l2])}" fill="none" stroke="#7d8a92" stroke-width="1.1"/>'
              f'<ellipse cx="{c[0]:.1f}" cy="{c[1]:.1f}" rx="{rad:.1f}" ry="{rad*0.62:.1f}" fill="#dfe6ea" stroke="#7d8a92" stroke-width="0.9"/>')


def crop_rows(ring, kind):
    xs = [p[0] for p in ring]; ys_ = [p[1] for p in ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys_), max(ys_)
    from matplotlib.path import Path
    path = Path(ring)
    lines = []
    if kind == "ew":
        for y in np.arange(y0 + 0.7, y1, 0.9):
            seg = [(x, y) for x in np.arange(x0, x1 + 0.01, 2.0) if path.contains_point((x, y))]
            if len(seg) > 2:
                lines.append(seg)
    else:
        for x in np.arange(x0 + 0.7, x1, 0.9):
            seg = [(x, y) for y in np.arange(y0, y1 + 0.01, 2.0) if path.contains_point((x, y))]
            if len(seg) > 2:
                lines.append(seg)
    d = " ".join("M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in (P(x, y)[:2] for x, y in s)) for s in lines)
    add(f'<path d="{d}" fill="none" stroke="#5f7a3a" stroke-opacity="0.18" stroke-width="0.6"/>')

# ---------------------------------------------------------------- hillshade
def hillshade(step=2.4):
    L = np.array([-0.55, 0.45, 0.70]); L /= np.linalg.norm(L)
    cells = {}
    for x in np.arange(0, XMAX, step):
        for y in np.arange(0, YMAX, step):
            cx, cy = x + step / 2, y + step / 2
            e = 0.3
            gx = (zf(cx + e, cy) - zf(cx - e, cy)) / (2 * e)
            gy = (zf(cx, cy + e) - zf(cx, cy - e)) / (2 * e)
            n = np.array([-gx, -gy, 1.0]); n /= np.linalg.norm(n)
            s = n @ L - L[2]
            if abs(s) < 0.02:
                continue
            q = round(min(0.30, abs(s) * 1.3), 2)
            col = "#ffffff" if s > 0 else "#2a3a1c"
            ring = [P(x, y)[:2], P(x + step, y)[:2], P(x + step, y + step)[:2], P(x, y + step)[:2]]
            cells.setdefault((col, q), []).append(ring)
    for (col, q), rings in cells.items():
        d = " ".join("M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in rg) + "Z" for rg in rings)
        add(f'<path d="{d}" fill="{col}" fill-opacity="{q}"/>')

def contours():
    gx = np.arange(0, XMAX + 0.01, 0.5); gy = np.arange(0, YMAX + 0.01, 0.5)
    Z = np.array([[zf(x, y) for x in gx] for y in gy])
    gen = contourpy.contour_generator(gx, gy, Z)
    for lev in np.arange(0.6, 6.4, 0.6):
        for line in gen.lines(lev):
            if len(line) < 4:
                continue
            p = [P(x, y, lev)[:2] for x, y in line[::2]]
            add(f'<polyline points="{pts(p)}" fill="none" stroke="#4c5e33" stroke-opacity="0.16" stroke-width="0.7"/>')

# ---------------------------------------------------------------- objects
objs = []   # (depth, svg)

def obj(x, y, svg):
    objs.append((depth(x, y, zf(x, y)), svg))

def tree(x, y, r=1.0, col="#7f9f55", edge="#5f7d3d"):
    z = zf(x, y)
    bx, by, zc = P(x, y, z)
    tx, ty, _ = P(x, y, z + 1.3 * r)
    rad = FOC * 0.85 * r / zc
    obj(x, y, f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#6e5f45" stroke-width="{max(0.6, rad*0.18):.2f}"/>'
              f'<circle cx="{tx:.1f}" cy="{ty - rad*0.5:.1f}" r="{rad:.1f}" fill="{col}" stroke="{edge}" stroke-width="0.7"/>')

def boxb(x0, y0, w, d, h, wall, roof, gable=True, z0=None):
    """A building with walls and a gable roof; ridge runs east-west."""
    z = zf(x0 + w / 2, y0 + d / 2) if z0 is None else z0
    X = [x0, x0 + w]; Y = [y0, y0 + d]
    def p(x, y, zz): return P(x, y, z + zz)[:2]
    parts = []
    # visible walls: south (y0) and west (x0)
    parts.append(f'<polygon points="{pts([p(X[0],Y[0],0),p(X[1],Y[0],0),p(X[1],Y[0],h),p(X[0],Y[0],h)])}" fill="{wall}" stroke="#5a564e" stroke-width="0.7" stroke-linejoin="round"/>')
    rh = h + (d * 0.45 if gable else 0)
    west = [p(X[0], Y[0], 0), p(X[0], Y[1], 0), p(X[0], Y[1], h), p(X[0], Y[0] + d / 2, rh) if gable else p(X[0], Y[1], h), p(X[0], Y[0], h)]
    parts.append(f'<polygon points="{pts(west)}" fill="{shade(wall, 0.86)}" stroke="#5a564e" stroke-width="0.7" stroke-linejoin="round"/>')
    if gable:
        parts.append(f'<polygon points="{pts([p(X[0],Y[0],h),p(X[1],Y[0],h),p(X[1],Y[0]+d/2,rh),p(X[0],Y[0]+d/2,rh)])}" fill="{roof}" stroke="#5a564e" stroke-width="0.7" stroke-linejoin="round"/>')
    else:
        parts.append(f'<polygon points="{pts([p(X[0],Y[0],h),p(X[1],Y[0],h),p(X[1],Y[1],h),p(X[0],Y[1],h)])}" fill="{roof}" stroke="#5a564e" stroke-width="0.7" stroke-linejoin="round"/>')
    obj(x0 + w / 2, y0, "".join(parts))

def shade(hexcol, k):
    c = [int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(v * k):02x}" for v in c)

def bin_(x, y, rr=0.9, h=1.6, col="#c9ccce"):
    z = zf(x, y)
    l, _, zc = P(x - rr, y, z); rt, _, _ = P(x + rr, y, z)
    cx, cy, _ = P(x, y, z); _, ty, _ = P(x, y, z + h)
    rx = (rt - l) / 2; ry = rx * 0.38
    _, tip, _ = P(x, y, z + h + rr * 0.6)
    obj(x, y + 0.01, f'<path d="M{cx-rx:.1f},{cy:.1f} L{cx-rx:.1f},{ty:.1f} L{cx:.1f},{tip:.1f} L{cx+rx:.1f},{ty:.1f} L{cx+rx:.1f},{cy:.1f} A{rx:.1f},{ry:.1f} 0 0 1 {cx-rx:.1f},{cy:.1f}Z" fill="{col}" stroke="#6b6e70" stroke-width="0.7" stroke-linejoin="round"/>')

def sheep(x, y):
    z = zf(x, y)
    cx, cy, zc = P(x, y, z + 0.18)
    s = FOC / zc
    obj(x, y, f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{0.42*s:.2f}" ry="{0.26*s:.2f}" fill="#ffffff" stroke="#4a4740" stroke-width="0.5"/>'
              f'<circle cx="{cx+0.38*s:.1f}" cy="{cy-0.14*s:.1f}" r="{0.13*s:.2f}" fill="#4a4740"/>')

def panel_row(xa, ya, xb, yb, w=0.62, h0=0.28, tilt=0.42, shadow=True):
    """Row whose low (south) edge runs from A to B; it rises toward the north."""
    za, zb = zf(xa, ya), zf(xb, yb)
    dx, dy = xb - xa, yb - ya
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L          # left normal of A->B; with A west of B this points north
    hx, hy = nx * w * math.cos(tilt), ny * w * math.cos(tilt)
    hz = w * math.sin(tilt)
    A = P(xa, ya, za + h0)[:2]; B = P(xb, yb, zb + h0)[:2]
    Bh = P(xb + hx, yb + hy, zb + h0 + hz)[:2]; Ah = P(xa + hx, ya + hy, za + h0 + hz)[:2]
    svg = ""
    if shadow:
        sh = [P(xa + nx * 0.2, ya + ny * 0.2, za + 0.02)[:2], P(xb + nx * 0.2, yb + ny * 0.2, zb + 0.02)[:2],
              P(xb + nx * 1.05, yb + ny * 1.05, zf(xb + nx * 1.05, yb + ny * 1.05) + 0.02)[:2],
              P(xa + nx * 1.05, ya + ny * 1.05, zf(xa + nx * 1.05, ya + ny * 1.05) + 0.02)[:2]]
        svg += f'<polygon points="{pts(sh)}" fill="#2b3a24" fill-opacity="0.22"/>'
    svg += f'<polygon points="{pts([A, B, Bh, Ah])}" fill="#3e5468" stroke="#24323e" stroke-width="0.5" stroke-linejoin="round"/>'
    svg += f'<line x1="{Ah[0]:.1f}" y1="{Ah[1]:.1f}" x2="{Bh[0]:.1f}" y2="{Bh[1]:.1f}" stroke="#9fb3c4" stroke-width="0.6"/>'
    obj((xa + xb) / 2, (ya + yb) / 2 + 0.3, svg)

def array_block(x0, y0, x1, y1, pitch=1.15, seg=None, skip=None):
    for y in np.arange(y0, y1, pitch):
        if seg:
            xs = list(np.arange(x0, x1, seg)) + [x1]
            for a, b in zip(xs[:-1], xs[1:]):
                if b - a > 0.6 and not (skip and skip(a, b, y)):
                    panel_row(a, y, b - 0.25, y)
        else:
            if not (skip and skip(x0, x1, y)):
                panel_row(x0, y, x1, y)

# ---------------------------------------------------------------- highlights
hl = []   # (code, ring)

# ================================================================= midwest
def fields_midwest():
    fields = []  # (ring, fill, rows: None|'ew'|'ns')
    S_LO = lambda x: ys(x) - 4.2
    N_LO = lambda x: ys(x) + 4.0

    # whole ground first

    # south-west block
    fields += [
        (rect(1.5, 6.4, 14, 15), YARD, None),                         # farmstead A
        (band(1.5, 28, lambda x: 15, S_LO), PASTURE, None),           # pasture (S1)
        (band(29, 58.8, lambda x: 9.6, S_LO), CORN, "ew"),            # corn with prairie strips
        (rect(14.5, 6.4, 28, 15), SOY, "ew"),
    ]
    # south-east block
    fields += [
        (band(61.2, 84, lambda x: 23.5, S_LO), CORN, "ew"),
        (rect(61.2, 6.4, 84, 23), GRASS, None),                       # S2 array ground
        (band(85, 118.5, lambda x: 25.5, S_LO), SOY, "ew"),
        (rect(85, 6.4, 107, 25), GRASS, None),                        # S3 array ground
    ]
    # north-west block
    fields += [
        (band(1.5, 20, N_LO, lambda x: 61), HAY, None),
        (rect(1.5, 61.5, 20, 73.8), YARD, None),                      # farmstead C
        (band(21, 58.8, N_LO, lambda x: 73.8), CORN, "ns"),
    ]
    # north-east block
    fields += [
        (band(61.2, 96, N_LO, lambda x: 73.8), SOY, "ns"),
        (band(97, 118.5, N_LO, lambda x: 49.5), HAY, None),
        (rect(97, 50, 118.5, 64.5), GRASS, None),                     # landfill cap
        (rect(97, 65, 118.5, 73.8), CORN, "ew"),
    ]
    # beyond the north road
    fields += [
        (rect(1.5, 76.4, 40, YMAX), SOY, "ew"),
        (rect(41, 76.4, 84, YMAX), CORN, "ew"),
        (rect(85, 76.4, 118.5, YMAX), TOWN, None),
    ]
    return fields

def draw_midwest():
    fields = fields_midwest()
    side_faces()
    poly(ground, GRASS)
    for ring, fill, rows in fields:
        poly(ring, fill)
    # prairie strips on the contour in the corn field
    strip_lo1 = lambda x: ys(x) - 10.4; strip_hi1 = lambda x: ys(x) - 7.4
    strip_lo2 = lambda x: ys(x) - 17.0; strip_hi2 = lambda x: ys(x) - 15.2
    poly(band(29.4, 58.4, strip_lo1, strip_hi1, 0.5), PRAIRIE)
    poly(band(29.4, 58.4, strip_lo2, strip_hi2, 0.5), PRAIRIE)
    # eroded knoll: subsoil showing through on the crest
    poly([(33 + 4.6 * math.cos(t) + 0.6 * math.sin(3 * t), 63 + 3.4 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)], "#d9cfa6")
    # grassed waterway
    ww = [(wx(y) - 1.5, y) for y in np.arange(ys(80) + 3, 73.6, 0.8)]
    ww += [(wx(y) + 1.5, y) for y in reversed(np.arange(ys(80) + 3, 73.6, 0.8))]
    poly(ww, "#a5c677")
    # riparian corridor
    poly(band(0, XMAX, lambda x: ys(x) - 3.6, lambda x: ys(x) + 3.4, 0.8), "#a2bf75")

    for ring, fill, rows in fields:
        if rows:
            crop_rows(ring, rows)
    hillshade()
    contours()

    # stream
    st = [(x, ys(x)) for x in np.arange(0, XMAX + 0.01, 0.6)]
    add(f'<polyline points="{pts(drape_line(st, 0.6, 0.02))}" fill="none" stroke="{WATER}" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>')
    # waterway thalweg (dry, faint)
    add(f'<polyline points="{pts(drape_line([(wx(y), y) for y in np.arange(ys(80)+2, 73.4, 0.8)], 0.8, 0.02))}" fill="none" stroke="#7f9f5a" stroke-width="0.8" stroke-dasharray="2 2"/>')

    # roads
    road(rect(0, 4.8, XMAX, 6.0))
    road(rect(0, 74.6, XMAX, 75.8))
    road(rect(59.6, 0, 60.8, YMAX))
    for yy in np.arange(77, 84, 2.2):
        road(rect(85, yy, 118.5, yy + 0.5))

    # highlight tints (before objects)

    hl_ring(1, rect(8.5, 17.0, 26.5, 26.2))                                   # pasture array
    hl_ring(5, band(29.6, 58.2, lambda x: ys(x) - 11.0, lambda x: ys(x) - 6.8, 0.5))   # strip array
    hl_ring(4, rect(29.8, 6.3, 58.4, 9.2))                                    # road-edge rows
    hl_ring(2, rect(62.0, 7.0, 83.2, 22.5))                                   # cropland now grazed
    hl_ring(3, rect(86.0, 7.0, 106.2, 24.4))                                  # ordinary field taken
    hl_ring(4, [(28.2, 59.4), (38.2, 59.4), (38.2, 66.8), (28.2, 66.8)])      # eroded knoll
    hl_ring(5, [(wx(y) - 5.6, y) for y in np.arange(ys(80) + 4.2, 71.0, 0.8)] +
               [(wx(y) + 5.6, y) for y in reversed(np.arange(ys(80) + 4.2, 71.0, 0.8))])  # waterway
    hl_ring(0, rect(98.8, 51.6, 113.6, 62.6))                                 # landfill

    # ----- objects
    # farmstead A
    boxb(4.0, 9.0, 3.2, 2.2, 1.5, "#ffffff", "#7c7a72")
    boxb(8.4, 11.2, 4.2, 2.8, 2.0, "#b5523a", "#6e6b63")
    bin_(12.6, 8.6); bin_(13.6, 9.8, 0.75, 1.3)
    for y in np.arange(7, 16, 1.2): tree(2.2, y, 0.9, "#6f9150", "#557538")
    for x in np.arange(3, 14, 1.3): tree(x, 15.6, 0.95, "#6f9150", "#557538")
    # farmstead C
    boxb(5.0, 64.0, 3.4, 2.4, 1.5, "#ffffff", "#7c7a72")
    boxb(10.0, 66.0, 4.6, 3.0, 2.1, "#b5523a", "#6e6b63")
    bin_(15.6, 64.2); bin_(16.8, 65.4, 0.75, 1.3)
    for y in np.arange(62, 74, 1.2): tree(2.2, y, 0.9, "#6f9150", "#557538")
    for x in np.arange(3, 19, 1.3): tree(x, 73.2, 0.95, "#6f9150", "#557538")
    # farmstead B (east), with its windbreak
    boxb(112.0, 28.0, 3.0, 2.2, 1.5, "#ffffff", "#7c7a72")
    bin_(110.0, 29.0, 0.8, 1.4)
    for x in np.arange(108, 118.5, 1.3): tree(x, 31.5, 0.9, "#6f9150", "#557538")

    # riparian trees
    for x in np.arange(1, XMAX, 1.5):
        for off in (-2.6, 2.4):
            if random.random() < 0.62 and not (57.5 < x < 63):
                tree(x + random.uniform(-0.4, 0.4), ys(x) + off + random.uniform(-0.6, 0.6), random.uniform(0.75, 1.05))

    # S1: sheep pasture, array kept as pasture
    array_block(9.5, 18.0, 25.5, 25.6, 1.25)
    for _ in range(16): sheep(random.uniform(9, 26), random.uniform(17.5, 26))
    # S5: rows in the lower prairie strip, on the contour
    for x in np.arange(30.2, 57.6, 1.6):
        for off in (-10.2, -8.6):
            panel_row(x, ys(x) + off, x + 1.35, ys(x + 1.35) + off, w=0.55)
    # S4: rows along the road edge
    for y in (6.8, 7.9):
        for x in np.arange(30.4, 57.8, 3.0):
            panel_row(x, y, x + 2.7, y, w=0.55)
    # S2: grazed array on former cropland
    array_block(62.8, 8.0, 82.6, 22.2, 1.2, seg=4.0)
    for _ in range(20): sheep(random.uniform(63, 82.5), random.uniform(7.6, 22.4))
    # S3: ordinary field, mown; substation and line
    array_block(86.8, 7.8, 105.6, 24.0, 1.15, seg=4.6)
    poly(rect(108.4, 7.4, 113.6, 12.0), "#cfccc4", 'stroke="#8a867c" stroke-width="0.7"', 0.6, 0.03)
    boxb(109.2, 8.4, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    boxb(111.4, 8.4, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    boxb(109.8, 10.4, 2.4, 0.9, 0.7, "#e8e6e0", "#a9a59b", gable=False)
    t1 = tower(119.0, 9.8)
    t2 = tower(114.6, 9.8, 3.2)
    add_lines = [(t1[0], t2[1]), (t1[1], t2[1])]
    # S4: knoll
    array_block(29.4, 60.4, 37.2, 66.2, 1.1, seg=2.6)
    # S5: waterway shoulders
    for y in np.arange(ys(80) + 5.0, 70.4, 1.1):
        c = wx(y)
        panel_row(c - 5.0, y, c - 2.0, y, w=0.55)
        panel_row(c + 2.0, y, c + 5.0, y, w=0.55)
    # S0: landfill cap, grazed
    array_block(99.8, 52.4, 112.8, 62.0, 1.15, seg=3.3)
    for _ in range(14): sheep(random.uniform(99.5, 113), random.uniform(51.8, 62.4))
    # town: houses, trees, water tower
    for i, yy in enumerate(np.arange(76.6, 83.4, 2.2)):
        for x in np.arange(86 + (i % 2) * 1.4, 118, 2.9):
            if random.random() < 0.8:
                boxb(x, yy + 0.65, 1.3, 1.0, 0.75, random.choice(["#ffffff", "#f1ebe0", "#e6e1d6"]), "#8a8379")
            if random.random() < 0.5:
                tree(x + 1.9, yy + 1.4, 0.75)
    water_tower(101, 81)
    # trees on landfill margins and a woodlot at the far west
    for x in np.arange(97.5, 118, 1.6): tree(x, 64.6, 0.8)
    for _ in range(26): tree(random.uniform(2, 14), random.uniform(78, 83.5), random.uniform(0.8, 1.1), "#6f9150", "#557538")
    CHIP = {  # code, anchor (world), chip offset (px)
        "pasture": (1, (17.5, 26.0), (-28, -40), "Pasture"),
        "strip": (5, (40.0, ys(40) - 7.0), (0, -46), "Prairie strip"),
        "road": (4, (44.0, 6.3), (34, 40), "Road edge"),
        "grazed": (2, (72.0, 22.4), (0, -40), "Grazed cropland"),
        "ordinary": (3, (96.0, 24.4), (6, -42), "Whole field"),
        "knoll": (4, (33.2, 66.8), (-6, -36), "Eroded knoll"),
        "waterway": (5, (wx(70.6), 70.8), (0, -36), "Waterway"),
        "landfill": (0, (106.2, 62.6), (-40, -30), "Landfill"),
    }
    title = "The farming axis across a working landscape"
    desc = 'A block diagram of rolling farmland cut by a stream, with three farmsteads, a section-road grid, a substation, and a small town with a water tower. Arrays sit in eight places, each outlined in the color of its farming-axis position. S0: a closed landfill cap at the town edge, grazed under the array. S1: a sheep pasture that stays a pasture under the rows. S2: a corn field turned to grazing under an array. S3: a whole ordinary field taken beside the substation and mown. S4: two rows along a road edge, and a small array on an eroded knoll. S5: rows on the shoulders of a grassed waterway in a soybean field, and rows set in a prairie strip on the contour above the stream.'
    return add_lines, CHIP, title, desc, "fig_farming_landscape.svg"

# ================================================================= west
# An irrigated valley floor below dry foothills: a working center pivot with
# arrays in its dry corners, a retired pivot field under panels, a canal along
# the foot of the hills, oak rangeland above it, and a small town on the fan.
def wash_x(y):       # sandy wash coming down out of the hills
    return 84 + 3 * math.sin(y / 7)

def pit(x, y):       # reclaimed gravel pit on the fan, flat-floored
    return 0.9 * sig((5.2 - abs(x - 73)) / 0.8) * sig((4.0 - abs(y - 53)) / 0.8)

def zf_west(x, y):
    z = 0.2 + 0.012 * y
    z += 4.1 * sig((y - 57) / 4.5) * (0.80 + 0.20 * math.sin(x / 10.5 + 0.8))
    z += 0.55 * math.sin(x / 6.2) * math.cos(y / 5.3) * sig((y - 60) / 3)
    z -= 1.3 * math.exp(-((x - wash_x(y)) / 2.2) ** 2) * sig((y - 49) / 3)
    z -= pit(x, y)
    return z

def circle_ring(cx, cy, rad, n=90):
    return [(cx + rad * math.cos(t), cy + rad * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]

def pivot_arm(cx, cy, rad, ang, h=0.8):
    tw = np.linspace(0, 1, 7)
    top = [P(cx + t * rad * math.cos(ang), cy + t * rad * math.sin(ang),
             zf(cx + t * rad * math.cos(ang), cy + t * rad * math.sin(ang)) + h)[:2] for t in tw]
    legs = ""
    for t, (tx, ty) in zip(tw[1:], top[1:]):
        gx, gy = cx + t * rad * math.cos(ang), cy + t * rad * math.sin(ang)
        bx, by = P(gx, gy)[:2]
        legs += f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#7d7a72" stroke-width="0.8"/>'
    obj(cx + rad * 0.5 * math.cos(ang), cy + rad * 0.5 * math.sin(ang),
        legs + f'<polyline points="{pts(top)}" fill="none" stroke="#6b6860" stroke-width="1.3"/>')

def draw_west():
    IRRIG, ALFALFA, STUBBLE = "#a3c46c", "#b2cc7a", "#d8cca2"
    FALLOW, RANGE, GRAVEL, WASH = "#d6c39b", "#d8c98e", "#d9d3c2", "#e3d8bd"
    VINE = "#b9c584"
    side_faces()
    poly(ground, RANGE)
    poly(rect(0, 0, XMAX, 46.0), STUBBLE)
    # fields on the valley floor
    pc, pr = (31.0, 25.2), 18.2                    # working pivot
    rc, rr = (80.1, 25.2), 18.2                    # retired pivot
    poly(rect(12.0, 6.4, 50.0, 44.0), STUBBLE)
    poly(circle_ring(*pc, pr), IRRIG)
    poly(rect(61.2, 6.4, 99.0, 44.0), FALLOW)
    poly(rect(1.5, 16.2, 11.4, 44.0), VINE)        # vineyard
    poly(rect(50.6, 6.4, 58.8, 44.0), "#c9c79a")   # almond orchard floor
    poly(rect(1.5, 6.4, 11.4, 15.6), YARD)         # ranch yard
    poly(rect(100.4, 6.4, 118.5, 23.0), STUBBLE)   # field taken whole
    poly(rect(100.4, 29.6, 118.5, 44.0), ALFALFA)  # alfalfa, now grazed
    poly(rect(105.6, 23.8, 113.8, 28.6), "#cfccc4", 'stroke="#8a867c" stroke-width="0.7"', 0.6, 0.03)  # substation
    # the wash, the pit floor, the town
    wash = [(wash_x(yy) - 1.6, yy) for yy in np.arange(44.0, YMAX + 0.01, 0.8)]
    wash += [(wash_x(yy) + 1.6, yy) for yy in reversed(np.arange(44.0, YMAX + 0.01, 0.8))]
    poly(wash, WASH)
    poly(rect(68.4, 49.6, 77.6, 56.4), GRAVEL)
    poly(rect(92.0, 47.6, 118.5, 56.8), TOWN)
    crop_rows(rect(1.5, 16.2, 11.4, 44.0), "ew")
    crop_rows(rect(100.4, 29.6, 118.5, 44.0), "ns")
    # faint wheel tracks of the old pivot under the retired field
    for k in (0.45, 0.72, 0.98):
        add(f'<polygon points="{pts(drape_ring(circle_ring(*rc, rr * k), 0.8, 0.03))}" fill="none" stroke="#b9a57d" stroke-width="0.7" stroke-dasharray="3 3"/>')
    for k in (0.35, 0.62, 0.9):
        add(f'<polygon points="{pts(drape_ring(circle_ring(*pc, pr * k), 0.8, 0.03))}" fill="none" stroke="#7f9f4a" stroke-opacity="0.5" stroke-width="0.7"/>')
    hillshade()
    contours()
    # canal along the foot of the hills
    poly(rect(0, 45.4, XMAX, 47.0), "#d7d3c8", 'stroke="#a9a397" stroke-width="0.6"', 0.8, 0.03)
    poly(rect(0, 45.8, XMAX, 46.6), WATER, "", 0.8, 0.05)
    add(f'<polyline points="{pts(drape_line([(wash_x(yy), yy) for yy in np.arange(47.0, YMAX, 0.8)], 0.8, 0.02))}" fill="none" stroke="#c9b48c" stroke-width="0.9" stroke-dasharray="2 2"/>')
    road(rect(0, 4.8, XMAX, 6.0))
    road(rect(59.6, 0, 60.8, 45.0))
    road(rect(0, 44.4, XMAX, 45.2))
    for yy in np.arange(48.4, 56.0, 2.4):
        road(rect(92.0, yy, 118.5, yy + 0.5))

    hl_ring(1, rect(1.0, 16.6, 11.9, 43.6))                                   # vineyard canopy
    hl_ring(4, [(12.4, 6.6), (24.0, 6.6), (14.6, 15.8), (12.4, 18.6)])        # pivot corner, west
    hl_ring(4, [(38.0, 6.6), (49.6, 6.6), (49.6, 18.6), (47.4, 15.8)])        # pivot corner, east
    hl_ring(5, rect(62.4, 7.4, 97.8, 43.0))                                   # retired pivot field
    hl_ring(3, rect(101.2, 7.2, 117.8, 22.4))                                 # field taken whole
    hl_ring(2, rect(101.2, 30.4, 117.8, 43.4))                                # alfalfa, now grazed
    hl_ring(1, rect(21.4, 59.0, 41.6, 68.6))                                  # rangeland
    hl_ring(0, rect(68.8, 50.0, 77.2, 56.0))                                  # gravel pit

    # ranch: house, metal shed, hay stack, a row of shade trees
    boxb(3.0, 8.6, 3.0, 2.2, 1.3, "#efe9dc", "#8b6d55")
    boxb(7.0, 10.6, 3.6, 3.0, 1.6, "#c9ccce", "#9aa0a3", gable=False)
    boxb(3.4, 12.8, 2.2, 1.2, 0.8, "#d9c27a", "#cdb46a", gable=False)
    for xx in np.arange(1.8, 11.2, 1.6): tree(xx, 15.8, 0.8, "#7c9a52", "#5d7a3c")
    # vineyard under a canopy of panels, carried above each vine row
    for yy in np.arange(17.4, 40.0, 2.1):
        # the vines: a trellised hedge, drawn as overlapping leaf clumps on the near side
        leaves = ""
        for xx in np.arange(2.0, 11.0, 0.42):
            lx, ly, zc = P(xx, yy - 0.15, zf(xx, yy - 0.15) + 0.45)
            rad = FOC * 0.36 / zc
            leaves += f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{rad:.1f}" fill="#6f9142" stroke="#557331" stroke-width="0.5"/>'
        obj(6.5, yy - 0.2, leaves)
        # the canopy carried above the row on posts
        for xx in (2.2, 6.5, 10.8):
            b = P(xx, yy + 0.25)[:2]; t = P(xx, yy + 0.25, zf(xx, yy + 0.25) + 1.15)[:2]
            obj(xx, yy + 0.24, f'<line x1="{b[0]:.1f}" y1="{b[1]:.1f}" x2="{t[0]:.1f}" y2="{t[1]:.1f}" stroke="#6b6860" stroke-width="0.8"/>')
        panel_row(1.9, yy + 0.25, 11.0, yy + 0.25, w=0.62, h0=1.15, shadow=False)
    # working pivot: arm, and arrays filling its two south corners
    pivot_arm(*pc, pr, math.radians(52))
    def outside(a, b, yy, c=pc, rad=pr):
        return any(math.hypot(px - c[0], yy - c[1]) < rad + 0.7 for px in (a, b, (a + b) / 2))
    for yy in np.arange(7.2, 18.0, 1.1):
        for xa in np.arange(12.6, 23.4, 2.4):
            if not outside(xa, xa + 2.1, yy): panel_row(xa, yy, xa + 2.1, yy, w=0.55)
        for xa in np.arange(38.4, 49.4, 2.4):
            if not outside(xa, min(xa + 2.1, 49.4), yy): panel_row(xa, yy, min(xa + 2.1, 49.4), yy, w=0.55)
    # almond orchard east of the pivot
    for yy in np.arange(7.4, 43.6, 1.1):
        for xx in np.arange(51.2, 58.6, 1.2):
            tree(xx, yy, 0.42, "#7f9a4c", "#5f7a34")
    # retired pivot field: the pumping ended, the panels went in
    array_block(63.2, 8.2, 97.2, 42.4, 1.2, seg=4.2)
    # field taken whole beside the substation; transmission runs east
    array_block(101.8, 7.8, 117.4, 22.0, 1.15, seg=3.9)
    boxb(106.4, 24.6, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    boxb(108.8, 24.6, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    boxb(111.2, 25.6, 1.8, 0.9, 0.7, "#e8e6e0", "#a9a59b", gable=False)
    t1 = tower(119.0, 26.2)
    t2 = tower(115.0, 26.2, 3.2)
    add_lines = [(t1[0], t2[1]), (t1[1], t2[1])]
    # alfalfa field now grazed under the array
    array_block(101.8, 31.0, 117.4, 43.0, 1.2, seg=3.9)
    for _ in range(18): sheep(random.uniform(101.6, 117.6), random.uniform(30.6, 43.4))
    # cottonwoods along the wash on the valley floor and up into the hills
    for yy in np.arange(47.5, YMAX, 1.4):
        if random.random() < 0.7:
            tree(wash_x(yy) + random.choice((-2.4, 2.4)) + random.uniform(-0.4, 0.4), yy, random.uniform(0.8, 1.05), "#8aa65a", "#67833f")
    # gravel pit: panels on the old pit floor, grazed
    array_block(69.2, 50.4, 76.8, 55.6, 1.1, seg=2.5)
    for _ in range(8): sheep(random.uniform(69, 77), random.uniform(50.2, 55.8))
    # rangeland array on the foothills, grazed as it was
    array_block(22.0, 59.6, 41.0, 68.0, 1.25, seg=3.8)
    for _ in range(14): sheep(random.uniform(21.8, 41.2), random.uniform(59.2, 68.4))
    # blue-oak savanna on the hills
    for _ in range(70):
        xx, yy = random.uniform(1, 119), random.uniform(57, 83.5)
        if 20.6 < xx < 42.2 and 58.4 < yy < 69.2: continue
        if abs(xx - wash_x(yy)) < 3.2: continue
        tree(xx, yy, random.uniform(0.7, 1.0), "#8f9f5c", "#6c7b3f")
    # second ranch below the hills
    boxb(48.0, 49.0, 3.0, 2.2, 1.3, "#efe9dc", "#8b6d55")
    boxb(52.4, 49.6, 3.8, 3.0, 1.7, "#a85a3c", "#6e6b63")
    for xx in np.arange(46.6, 57.0, 1.6): tree(xx, 54.6, 0.85, "#7c9a52", "#5d7a3c")
    # town on the fan, below the hills
    for i, yy in enumerate(np.arange(48.4, 56.0, 2.4)):
        for xx in np.arange(93 + (i % 2) * 1.4, 118, 2.9):
            if random.random() < 0.8:
                boxb(xx, yy + 0.65, 1.3, 1.0, 0.75, random.choice(["#ffffff", "#f1ebe0", "#efe1cf"]), "#9a7f68")
            if random.random() < 0.45:
                tree(xx + 1.9, yy + 1.4, 0.7, "#8aa65a", "#67833f")
    water_tower(95.0, 57.6)

    CHIP = {
        "vineyard": (1, (6.4, 43.6), (-2, -44), "Vineyard"),
        "corner": (4, (18.0, 12.0), (-10, 48), "Pivot corners"),
        "retired": (5, (84.0, 43.0), (34, -34), "Retired field"),
        "ordinary": (3, (109.0, 22.4), (-34, 30), "Whole field"),
        "grazed": (2, (109.0, 43.4), (8, -40), "Grazed alfalfa"),
        "range": (1, (31.4, 68.6), (0, -38), "Rangeland"),
        "pit": (0, (73.0, 56.0), (-56, -32), "Gravel pit"),
    }
    title = "The farming axis across an irrigated western valley"
    desc = ("A block diagram of a flat irrigated valley below dry, oak-dotted foothills, with a canal along the foot of the hills, "
            "a sandy wash coming down out of them, two ranches, a substation, and a small town on the fan. Arrays sit in eight places, "
            "each outlined in the color of its farming-axis position. S0: a reclaimed gravel pit, grazed under the panels. "
            "S1: a vineyard under a canopy of panels, and rangeland on the foothills grazed as it was. S2: an alfalfa field turned to grazing under an array. "
            "S3: a whole field taken beside the substation. S4: arrays in the two dry corners of a working center pivot. "
            "S5: a retired irrigated field, its old pivot tracks still faintly visible, under a large array.")
    return add_lines, CHIP, title, desc, "fig_farming_landscape_west.svg"

# ================================================================= east
# A dairy valley: a creek on the valley floor, hay and pasture on the slopes,
# hedgerows between small fields, a village with a steeple, and woods on the ridge.
def ys_e(x):         # creek centerline
    return 26 + 3.5 * math.sin((x + 6) / 17)

def quarry(x, y):    # reclaimed quarry cut into the hillside
    return 1.2 * sig((6.2 - abs(x - 104)) / 0.8) * sig((4.2 - abs(y - 57)) / 0.8)

def zf_east(x, y):
    d = y - ys_e(x)
    if d > 0:
        z = 0.5 + 1.8 * math.tanh(d / 11) + 3.1 * sig((y - 56) / 6)
    else:
        z = 0.5 + 0.9 * math.tanh(-d / 9)
    z += 0.5 * math.sin(x / 8.0) * math.cos(y / 7.0) * sig((y - 36) / 5)
    z -= quarry(x, y)
    return z

def cow(x, y):
    z = zf(x, y)
    cx, cy, zc = P(x, y, z + 0.22)
    s_ = FOC / zc
    obj(x, y, f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{0.55*s_:.2f}" ry="{0.30*s_:.2f}" fill="#ffffff" stroke="#3d3a35" stroke-width="0.5"/>'
              f'<ellipse cx="{cx-0.12*s_:.1f}" cy="{cy-0.04*s_:.1f}" rx="{0.2*s_:.2f}" ry="{0.14*s_:.2f}" fill="#3d3a35"/>'
              f'<circle cx="{cx+0.5*s_:.1f}" cy="{cy-0.14*s_:.1f}" r="{0.15*s_:.2f}" fill="#3d3a35"/>')

def hedgerow(x0, y0, x1, y1, step=1.1, col="#6f9150", edge="#557538"):
    L = math.hypot(x1 - x0, y1 - y0)
    for t in np.arange(0, 1.0001, step / L):
        tree(x0 + (x1 - x0) * t + random.uniform(-0.2, 0.2), y0 + (y1 - y0) * t + random.uniform(-0.2, 0.2),
             random.uniform(0.7, 0.95), col, edge)

def draw_east():
    HAYE, PAST, CORNE = "#bcd28c", "#a7c476", "#a2bd6c"
    BRUSH, QUARRY, WOODS = "#b9bb86", "#d6d1c0", "#8fae66"
    side_faces()
    poly(ground, HAYE)
    lo = lambda x: ys_e(x) - 3.0          # south edge of the creek buffer
    hi = lambda x: ys_e(x) + 3.0          # north edge
    vr = lambda x: ys_e(x) + 6.8          # valley road
    # south of the creek
    poly(band(1.5, 36.0, lambda x: 6.4, lo), "#c8c38c")          # creekside field (S5), now in perennial meadow
    poly(band(37.0, 58.8, lambda x: 6.4, lo), CORNE)             # corn, still cropped
    poly(band(61.2, 86.0, lambda x: 6.4, lo), HAYE)              # hay field taken (S3)
    poly(band(87.0, 118.5, lambda x: 6.4, lo), PAST)             # pasture
    # valley slopes north of the road
    poly(rect(1.5, 36.4, 36.0, 55.0), PAST)                      # hill pasture (S1)
    poly(rect(62.0, 36.4, 85.0, 47.6), HAYE)                     # silage field now hay (S2)
    poly(rect(38.0, 36.4, 58.8, 47.6), YARD)                     # dairy
    poly(rect(88.0, 33.6, 118.5, 48.6), TOWN)                    # village
    poly(rect(28.4, 55.6, 50.0, 66.6), BRUSH)                    # old field gone to brush (S4)
    poly(rect(97.0, 52.4, 111.0, 61.6), QUARRY)                  # reclaimed quarry (S0)
    poly(rect(0, 67.0, XMAX, YMAX), WOODS)                       # wooded ridge
    poly(band(0, XMAX, lambda x: ys_e(x) - 3.0, lambda x: ys_e(x) + 3.0, 0.8), "#9fbe73")   # riparian strip
    crop_rows(band(37.0, 58.8, lambda x: 6.4, lo), "ew")
    crop_rows(rect(62.0, 36.4, 85.0, 47.6), "ns")
    hillshade()
    contours()
    st = [(x, ys_e(x)) for x in np.arange(0, XMAX + 0.01, 0.6)]
    add(f'<polyline points="{pts(drape_line(st, 0.6, 0.02))}" fill="none" stroke="{WATER}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>')
    road(rect(0, 4.8, XMAX, 6.0))
    road(band(0, XMAX, lambda x: vr(x) - 0.6, lambda x: vr(x) + 0.6, 0.8))
    road(rect(59.6, 0, 60.8, 66.0))
    for yy in np.arange(35.6, 48.0, 2.6):
        road(rect(88.0, yy, 118.5, yy + 0.5))
    # stone walls along field edges on the slope
    for seg in [((1.5, 55.2), (50.4, 55.2)), ((36.4, 36.4), (36.4, 55.2)), ((50.4, 55.2), (50.4, 66.8)), ((62.0, 48.0), (85.4, 48.0))]:
        add(f'<polyline points="{pts(drape_line(list(seg), 0.6, 0.06))}" fill="none" stroke="#9c978b" stroke-width="1.6" stroke-dasharray="1.2 1.4"/>')

    hl_ring(5, band(2.4, 35.2, lambda x: 7.4, lambda x: ys_e(x) - 3.6, 0.8))   # creekside field
    hl_ring(3, band(62.0, 85.2, lambda x: 7.2, lambda x: ys_e(x) - 3.6, 0.8))  # hay field taken
    hl_ring(1, rect(8.6, 41.6, 28.6, 54.0))                                     # hill pasture
    hl_ring(1, rect(44.6, 37.0, 51.0, 41.0))                                    # heifer yard
    hl_ring(2, rect(62.8, 37.0, 84.4, 47.0))                                    # silage field, now hay
    hl_ring(4, rect(31.0, 57.2, 47.6, 65.4))                                    # old field
    hl_ring(0, rect(98.0, 53.2, 110.0, 60.8))                                   # quarry

    # S5: perennial cover and panels on the creekside field that used to wash into the creek
    array_block(3.4, 8.2, 34.2, 19.6, 1.2, seg=3.8)
    # corn still cropped beside it; S3: a hay field taken whole, substation and line
    array_block(63.0, 8.0, 84.2, 20.2, 1.15, seg=4.1)
    poly(rect(88.4, 7.4, 93.6, 11.6), "#cfccc4", 'stroke="#8a867c" stroke-width="0.7"', 0.6, 0.03)
    boxb(89.2, 8.2, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    boxb(91.4, 8.2, 1.2, 0.9, 0.9, "#e8e6e0", "#a9a59b", gable=False)
    t1 = tower(119.0, 9.4)
    t2 = tower(95.4, 9.4, 3.2)
    add_lines = [(t1[0], t2[1]), (t1[1], t2[1])]
    # dairy: long barn, house, two silos, heifer yard under a small array
    boxb(39.6, 41.6, 6.4, 3.0, 1.9, "#b5523a", "#6e6b63")
    boxb(52.4, 42.6, 3.0, 2.4, 1.6, "#ffffff", "#7c7a72")
    bin_(47.2, 43.6, 0.85, 4.2, "#d9dcde"); bin_(48.8, 43.6, 0.85, 3.8, "#d9dcde")
    for xx in np.arange(38.6, 58.4, 1.3): tree(xx, 47.4, 0.85, "#6f9150", "#557538")
    array_block(45.2, 37.6, 50.6, 40.6, 1.0, seg=2.6)
    for _ in range(6): cow(random.uniform(45.0, 50.8), random.uniform(37.2, 40.8))
    # S2: silage field turned to hay under the array, a few round bales
    array_block(63.4, 37.6, 84.0, 46.6, 1.2, seg=4.0)
    # S1: hill pasture, still grazed
    array_block(9.6, 42.6, 27.6, 53.2, 1.25, seg=3.6)
    for _ in range(16): sheep(random.uniform(9.4, 28.0), random.uniform(42.2, 53.6))
    # S4: old field going to brush, panels among the shrubs
    array_block(32.0, 58.2, 46.6, 64.6, 1.15, seg=3.6)
    for _ in range(40):
        xx, yy = random.uniform(28.8, 49.6), random.uniform(55.8, 66.4)
        tree(xx, yy, random.uniform(0.35, 0.6), "#9aa866", "#768446")
    # S0: reclaimed quarry floor, panels and sheep
    array_block(98.8, 54.0, 109.2, 60.0, 1.1, seg=2.6)
    for _ in range(9): sheep(random.uniform(98.6, 109.4), random.uniform(53.8, 60.2))
    # hedgerows between fields, riparian trees, woods on the ridge
    hedgerow(36.6, 6.6, 36.6, ys_e(36.6) - 3.2)
    hedgerow(86.5, 6.6, 86.5, ys_e(86.5) - 3.2)
    hedgerow(1.5, 36.0, 1.5, 55.0)
    hedgerow(61.6, 48.4, 85.4, 48.4)
    hedgerow(51.0, 55.6, 51.0, 66.6)
    for x in np.arange(1, XMAX, 1.4):
        for off in (-2.3, 2.2):
            if random.random() < 0.6 and not (57.5 < x < 63):
                tree(x + random.uniform(-0.4, 0.4), ys_e(x) + off + random.uniform(-0.5, 0.5), random.uniform(0.75, 1.05))
    for _ in range(170):
        xx, yy = random.uniform(0.6, 119.4), random.uniform(67.4, 83.6)
        tree(xx, yy, random.uniform(0.85, 1.15), random.choice(["#6f9150", "#7f9f55", "#5f8446"]), "#4d6a35")
    # village: houses, maples, a church with a steeple
    for i, yy in enumerate(np.arange(35.6, 48.0, 2.6)):
        for xx in np.arange(89 + (i % 2) * 1.4, 118, 2.9):
            if 100.0 < xx < 106.0 and 40.0 < yy < 46.0: continue
            if random.random() < 0.8:
                boxb(xx, yy + 0.65, 1.3, 1.0, 0.8, random.choice(["#ffffff", "#f1ebe0", "#e6e1d6"]), "#7c7a72")
            if random.random() < 0.55:
                tree(xx + 1.9, yy + 1.4, 0.8)
    boxb(101.6, 42.0, 3.2, 1.8, 1.5, "#ffffff", "#7c7a72")
    boxb(100.4, 42.4, 1.1, 1.1, 3.6, "#ffffff", "#7c7a72")

    CHIP = {
        "creek": (5, (18.0, 19.8), (-10, 46), "Creekside field"),
        "hayfield": (3, (74.0, 20.4), (10, 44), "Hay field"),
        "pasture": (1, (18.6, 54.0), (-10, -40), "Hill pasture"),
        "heifer": (1, (47.8, 41.0), (46, -30), "Heifer yard"),
        "silage": (2, (73.6, 47.0), (0, -42), "Hayed field"),
        "brush": (4, (39.2, 65.4), (0, -34), "Old field"),
        "quarry": (0, (104.0, 60.8), (0, -34), "Quarry"),
    }
    title = "The farming axis across an eastern dairy valley"
    desc = ("A block diagram of a dairy valley with a creek on its floor, small fields of hay, corn, and pasture divided by hedgerows "
            "and stone walls, a dairy farm with a barn and two silos, a village with a church steeple, and woods along the ridge. "
            "Arrays sit in seven places, each outlined in the color of its farming-axis position. S0: a reclaimed quarry in the hillside, "
            "grazed under the panels. S1: a hillside sheep pasture that stays a pasture, and a heifer yard shaded by a small array beside the barn. "
            "S2: a silage-corn field turned to hay under an array. S3: a whole hay field taken beside the substation. "
            "S4: an old field going to brush on the upper slope. S5: a creekside field that used to wash into the creek, now in perennial cover under panels.")
    return add_lines, CHIP, title, desc, "fig_farming_landscape_east.svg"

# ================================================================= finishing
def finish(add_lines, CHIP, title, desc, fname):
    for dpt, svg in sorted(objs, key=lambda o: -o[0]):
        add(svg)
    for a, b in add_lines:
        add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#8d8a82" stroke-width="0.6"/>')
    # transmission line runs off the east edge

    # outlines over everything, then chips
    for code, ring in hl:
        d = pts(drape_ring(ring, 0.6, 0.05))
        add(f'<polygon points="{d}" fill="none" stroke="#ffffff" stroke-width="3.6" stroke-opacity="0.9" stroke-linejoin="round"/>')
        add(f'<polygon points="{d}" fill="none" stroke="{SC[code]}" stroke-width="1.8" stroke-linejoin="round"/>')

    for key, (code, (ax, ay), (ox, oy), label) in CHIP.items():
        a = P(ax, ay, zf(ax, ay) + 0.4)
        cx, cy = a[0] + ox, a[1] + oy
        wl = 6.9 * len(label)                      # Helvetica Neue semibold at 13px
        w = 9 + 20 + 7 + wl + 10
        x0 = cx - w / 2
        add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{cx:.1f}" y2="{cy:.1f}" stroke="{SC[code]}" stroke-width="1.4"/>')
        add(f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4" fill="{SC[code]}" stroke="#ffffff" stroke-width="1"/>')
        add(f'<rect x="{x0:.1f}" y="{cy-12:.1f}" width="{w:.1f}" height="24" rx="3" fill="{SC[code]}" stroke="#ffffff" stroke-width="1.4"/>')
        add(f'<text x="{x0+9:.1f}" y="{cy+5.4:.1f}"><tspan class="chip">S{code}</tspan><tspan class="lab" x="{x0+36:.1f}">{label}</tspan></text>')

    xs, ys_ = [], []
    for frag in out:
        for m in re.finditer(r'points="([^"]+)"', frag):
            for p in m.group(1).split():
                a, b = p.split(","); xs.append(float(a)); ys_.append(float(b))
        for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"', frag):
            x, y, w_, h_ = map(float, m.groups()); xs += [x, x + w_]; ys_ += [y, y + h_]
    M = 10
    vx, vy = math.floor(min(xs)) - M, max(0, math.floor(min(ys_)) - M)
    vw, vh = math.ceil(max(xs)) + M - vx, math.ceil(max(ys_)) + M - vy
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" viewBox="{vx} {vy} {vw} {vh}" role="img">',
           f'<title>{title}</title>',
           f'<desc>{desc}</desc>',
           '<style>',
           'text{font-family:"Helvetica Neue",Helvetica,"Segoe UI",Arial,sans-serif}',
           '.chip{font-size:14px;font-weight:700;fill:#ffffff}',
           '.lab{font-size:13px;font-weight:600;fill:#ffffff}',
           '</style>',
           f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="#ffffff"/>']
    svg += out + ['</svg>']
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", fname), "w").write("\n".join(svg))
    print(fname, len("\n".join(svg)) // 1024, "KB")

REGIONS = {"midwest": (zf_midwest, draw_midwest), "west": (zf_west, draw_west), "east": (zf_east, draw_east)}

def render(region):
    global TERRAIN
    random.seed(7)
    out.clear(); objs.clear(); hl.clear()
    TERRAIN, draw = REGIONS[region]
    finish(*draw())

if __name__ == "__main__":
    for region in (sys.argv[1:] or list(REGIONS)):
        render(region)
