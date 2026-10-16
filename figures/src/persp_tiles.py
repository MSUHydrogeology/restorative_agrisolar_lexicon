"""Shared engine for the perspective plates (the scale transect and the farming axis).

Each plate is a strip of six tiles. Each tile is a low view across flat ground
toward a horizon, the motif of the earlier hand-drawn plates, drawn in true
perspective with the rendering of the farming landscapes: furrows converge on the horizon,
panel tables recede in rows, and things shrink with distance.
World units are meters: x east, y north (away from the viewer), z up.
"""
import math, os, random
import numpy as np

W, X0, TW = 1104, 18.0, 178.0
HDR, TH = 42, 220
BAR_Y = HDR + TH

GRASS, PASTURE, HAY = "#b4cc86", "#a9c57a", "#bfd391"
CORN, SOY, STUBBLE = "#9fbc6a", "#cdd89c", "#d6cfa6"
YARD, ROAD, ROAD_EDGE, WATER = "#ddd8c9", "#efece2", "#b9b2a2", "#7fa9c4"
PANEL, PANEL_EDGE, PANEL_LIT = "#4f6276", "#33414f", "#b9c8d6"
FAR_GREEN = "#c7d6a6"


def shade(hexcol, k):
    c = [int(hexcol[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{min(255, int(v * k)):02x}" for v in c)


class PTile:
    """A view from (xc, -back, eye) looking north, fitted so the horizon sits near the
    top of tile i and the ground `front` meters wide fills the bottom edge."""

    def __init__(self, i, front, alpha_deg, horizon_px=40, xc=None, y_front=0.0):
        """front: ground width (m) seen across the bottom edge, which lies at y_front;
        alpha: how steeply the viewer looks down at that front edge. No stretching:
        one focal length both ways."""
        self.i, self.front, self.alpha, self.y_front = i, front, alpha_deg, y_front
        self.xc = front / 2 if xc is None else xc
        self.ground, self.objs = [], []
        a = math.radians(alpha_deg)
        th = a / 2                                          # aim halfway between horizon and front edge
        y_hor, y_bot = HDR + horizon_px, HDR + TH - 2
        self.F = (y_bot - y_hor) / (math.tan(a - th) + math.tan(th))
        D0 = front * self.F / TW                            # depth to the front edge along the view axis
        dist = D0 / math.cos(a - th)
        self.eye, self.back = dist * math.sin(a), dist * math.cos(a)
        ct, st = math.cos(th), math.sin(th)
        self.f = np.array([0.0, ct, -st]); self.u = np.array([0.0, st, ct]); self.r = np.array([1.0, 0.0, 0.0])
        self.C = np.array([self.xc, y_front - self.back, self.eye])
        self.cy = y_hor + self.F * math.tan(th)
        self.cx = X0 + i * TW + TW / 2
        self.y_hor = y_hor
        self.kx = 1.0

    @classmethod
    def fit(cls, i, alpha_deg, x, y, w_m, w_px, p=0.76):
        """A view in which the ground point (x, y) sits a fraction p of the way down from
        the horizon to the bottom edge, with w_m meters spanning w_px pixels there.
        This is how a plate places its subject above the foreground rather than on the edge."""
        unit = cls(i, 1.0, alpha_deg, xc=0.0)
        target = unit.y_hor + p * (HDR + TH - 2 - unit.y_hor)
        lo, hi = 0.0, 1e4
        for _ in range(80):
            u = (lo + hi) / 2
            if unit.P(0.0, u)[1] > target: lo = u
            else: hi = u
        front = unit.px_per_m(0.0, u) * w_m / w_px
        return cls(i, front, alpha_deg, xc=x, y_front=y - u * front)

    def width_at(self, y):
        """Ground width (m) the tile spans at distance y."""
        return TW / self.px_per_m(self.xc, y)

    def P(self, x, y, z=0.0):
        q = np.array([x, y, z]) - self.C
        d = q @ self.f
        return self.cx + self.kx * self.F * (q @ self.r) / d, self.cy - self.F * (q @ self.u) / d

    def dist(self, x, y, z=0.0):
        return (np.array([x, y, z]) - self.C) @ self.f

    def px_per_m(self, x, y, z=0.0):
        return self.kx * self.F / self.dist(x, y, z)

    # --- ground
    def poly(self, ring, fill, extra=""):
        pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.P(x, y) for x, y in ring))
        self.ground.append(f'<polygon points="{pts}" fill="{fill}" {extra}/>')

    def furrows(self, x0, y0, x1, y1, spacing, color="#5f7a3a", op=0.12):
        d = []
        for x in np.arange(x0 + spacing / 2, x1, spacing):
            a, b = self.P(x, y0), self.P(x, y1)
            d.append(f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}")
        self.ground.append(f'<path d="{" ".join(d)}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="0.7"/>')

    def furrows_ew(self, x0, y0, x1, y1, spacing, color="#5f7a3a", op=0.12):
        d = []
        for y in np.arange(y0 + spacing / 2, y1, spacing):
            a, b = self.P(x0, y), self.P(x1, y)
            d.append(f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}")
        self.ground.append(f'<path d="{" ".join(d)}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="0.7"/>')

    def field(self, x0, y0, x1, y1, fill, furrow=None):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill)
        if furrow:
            self.furrows(x0, y0, x1, y1, furrow)

    def road(self, x0, y0, x1, y1, w):
        if x0 == x1:
            ring = [(x0 - w / 2, y0), (x0 + w / 2, y0), (x1 + w / 2, y1), (x1 - w / 2, y1)]
        else:
            ring = [(x0, y0 - w / 2), (x1, y1 - w / 2), (x1, y1 + w / 2), (x0, y0 + w / 2)]
        self.poly(ring, ROAD, f'stroke="{ROAD_EDGE}" stroke-width="0.5"')

    def line(self, pts, stroke, width, extra=""):
        p = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.P(x, y) for x, y in pts))
        self.ground.append(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{width}" {extra}/>')

    # --- objects, painted far to near
    def obj(self, x, y, svg, z=0.0):
        self.objs.append((self.dist(x, y, z), svg))

    def tree(self, x, y, r=4.0, col="#7f9f55", edge="#5f7d3d"):
        s = self.px_per_m(x, y)
        rp = r * s
        if rp < 0.6:
            return
        bx, by = self.P(x, y, 0); tx, ty = self.P(x, y, 1.6 * r)
        svg = ""
        if rp > 1.8:
            svg += f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#6e5f45" stroke-width="{max(0.5, rp * 0.15):.2f}"/>'
        svg += f'<circle cx="{tx:.1f}" cy="{ty - rp * 0.5:.1f}" r="{rp:.1f}" fill="{col}" stroke="{edge}" stroke-width="{min(0.8, rp * 0.2):.2f}"/>'
        self.obj(x, y, svg)

    def building(self, x0, y0, w, d, h, wall, roof, gable=True, pv=False):
        """Walls facing the viewer (south) and west, roof ridge running east-west."""
        P = self.P
        X, Y = (x0, x0 + w), (y0, y0 + d)
        f = lambda pts: " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        if w * self.px_per_m(x0, y0) < 1.6:
            cx, cy = P(x0 + w / 2, y0, h / 2)
            self.obj(x0 + w / 2, y0, f'<rect x="{cx - 1:.1f}" y="{cy - 0.8:.1f}" width="2" height="1.6" fill="{wall}"/>')
            return
        sw = 0.7 if w * self.px_per_m(x0, y0) > 10 else 0.4
        rh = h + (d * 0.42 if gable else 0)
        parts = []
        side_x = X[0] if self.xc < X[0] else (X[1] if self.xc > X[1] else None)
        if side_x is not None:   # the end wall the viewer can see
            end = [P(side_x, Y[0], 0), P(side_x, Y[1], 0), P(side_x, Y[1], h)] + ([P(side_x, Y[0] + d / 2, rh)] if gable else []) + [P(side_x, Y[0], h)]
            parts.append(f'<polygon points="{f(end)}" fill="{shade(wall, 0.86)}" stroke="#5a564e" stroke-width="{sw}" stroke-linejoin="round"/>')
        if gable:
            back_roof = [P(X[0], Y[0] + d / 2, rh), P(X[1], Y[0] + d / 2, rh), P(X[1], Y[1], h), P(X[0], Y[1], h)]
            parts.append(f'<polygon points="{f(back_roof)}" fill="{shade(roof, 0.85)}" stroke="#5a564e" stroke-width="{sw}" stroke-linejoin="round"/>')
        parts.append(f'<polygon points="{f([P(X[0],Y[0],0),P(X[1],Y[0],0),P(X[1],Y[0],h),P(X[0],Y[0],h)])}" fill="{wall}" stroke="#5a564e" stroke-width="{sw}" stroke-linejoin="round"/>')
        if gable:
            roofp = [P(X[0], Y[0], h), P(X[1], Y[0], h), P(X[1], Y[0] + d / 2, rh), P(X[0], Y[0] + d / 2, rh)]
            parts.append(f'<polygon points="{f(roofp)}" fill="{roof}" stroke="#5a564e" stroke-width="{sw}" stroke-linejoin="round"/>')
            if pv:
                ix = w * 0.08
                q = lambda a, t: P(X[0] + ix + (w - 2 * ix) * a, Y[0] + (d / 2) * t, h + (rh - h) * t)
                lo, hi = 0.14, 0.88
                parts.append(f'<polygon points="{f([q(0,lo),q(1,lo),q(1,hi),q(0,hi)])}" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="0.9" stroke-linejoin="round"/>')
                g = ""
                for a in np.linspace(0, 1, 9)[1:-1]:
                    s0, s1 = q(a, lo), q(a, hi); g += f"M{s0[0]:.1f},{s0[1]:.1f} L{s1[0]:.1f},{s1[1]:.1f} "
                for tt in np.linspace(lo, hi, 4)[1:-1]:
                    s0, s1 = q(0, tt), q(1, tt); g += f"M{s0[0]:.1f},{s0[1]:.1f} L{s1[0]:.1f},{s1[1]:.1f} "
                parts.append(f'<path d="{g}" stroke="#8a9fb3" stroke-width="0.7" fill="none"/>')
                a, b = q(0, hi), q(1, hi)
                parts.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{PANEL_LIT}" stroke-width="1"/>')
        else:
            parts.append(f'<polygon points="{f([P(X[0],Y[0],h),P(X[1],Y[0],h),P(X[1],Y[1],h),P(X[0],Y[1],h)])}" fill="{roof}" stroke="#5a564e" stroke-width="{sw}" stroke-linejoin="round"/>')
        self.obj(x0 + w / 2, y0, "".join(parts))

    def silo(self, x, y, r=2.6, h=13.0):
        s = self.px_per_m(x, y)
        if r * s < 0.7:
            return
        cx, by = self.P(x, y, 0); _, ty = self.P(x, y, h); _, tip = self.P(x, y, h + r * 0.8)
        rx = r * s; ry = rx * 0.25
        self.obj(x, y, f'<path d="M{cx-rx:.1f},{by:.1f} L{cx-rx:.1f},{ty:.1f} L{cx:.1f},{tip:.1f} L{cx+rx:.1f},{ty:.1f} L{cx+rx:.1f},{by:.1f} A{rx:.1f},{ry:.1f} 0 0 1 {cx-rx:.1f},{by:.1f}Z" fill="#dcdfe1" stroke="#6b6e70" stroke-width="0.7" stroke-linejoin="round"/>')

    def animal(self, x, y, cow=False, z0=0.0):
        s = self.px_per_m(x, y, z0)
        rx, ry = ((1.3, 0.75) if cow else (0.75, 0.5))
        rx, ry = rx * s, ry * s
        if rx < 0.45:
            return
        cx, cy = self.P(x, y, z0 + (1.0 if cow else 0.6))
        leg = f'<path d="M{cx - rx*0.55:.1f},{cy + ry*0.6:.1f} v{ry*0.9:.1f} M{cx + rx*0.5:.1f},{cy + ry*0.6:.1f} v{ry*0.9:.1f}" stroke="#3d3a35" stroke-width="{max(0.4, rx*0.12):.2f}"/>' if rx > 2.5 else ""
        patch = f'<ellipse cx="{cx - rx*0.2:.1f}" cy="{cy - ry*0.1:.1f}" rx="{rx*0.35:.1f}" ry="{ry*0.45:.1f}" fill="#3d3a35"/>' if cow else ""
        self.obj(x, y, leg + f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="#ffffff" stroke="#3d3a35" stroke-width="{min(0.7, rx*0.15):.2f}"/>'
                       + patch + f'<circle cx="{cx + rx*0.95:.1f}" cy="{cy - ry*0.45:.1f}" r="{ry*0.55:.2f}" fill="#3d3a35"/>')

    def panel_row(self, xa, xb, y, w=3.2, h0=0.8, tilt=0.45, legs=True, z0=0.0):
        hz, hy = w * math.sin(tilt), w * math.cos(tilt)
        h0 = h0 + z0
        A, B = self.P(xa, y, h0), self.P(xb, y, h0)
        Bh, Ah = self.P(xb, y + hy, h0 + hz), self.P(xa, y + hy, h0 + hz)
        f = lambda pts: " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        face = abs(A[1] - Ah[1])
        svg = ""
        if face > 1.2:   # shadow on the ground behind the row
            sh = [self.P(xa, y + hy * 0.3, z0), self.P(xb, y + hy * 0.3, z0), self.P(xb, y + hy * 1.6, z0), self.P(xa, y + hy * 1.6, z0)]
            svg += f'<polygon points="{f(sh)}" fill="#2b3a24" fill-opacity="0.16"/>'
        if legs and face > 3:
            n = max(2, int((xb - xa) / 8))
            d = ""
            for k in range(n + 1):
                x = xa + (xb - xa) * k / n
                g, top = self.P(x, y + hy * 0.15, z0), self.P(x, y + hy * 0.15, h0)
                d += f"M{g[0]:.1f},{g[1]:.1f} L{top[0]:.1f},{top[1]:.1f} "
            svg += f'<path d="{d}" stroke="#56606a" stroke-width="{min(1.2, face * 0.12):.2f}"/>'
        svg += f'<polygon points="{f([A, B, Bh, Ah])}" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="{0.6 if face > 2 else 0.3}" stroke-linejoin="round"/>'
        if face > 4:   # module cells
            cells = int((xb - xa) / 2.0)
            step = max(1, cells // 40)
            g = f"M{(A[0]+Ah[0])/2:.1f},{(A[1]+Ah[1])/2:.1f} L{(B[0]+Bh[0])/2:.1f},{(B[1]+Bh[1])/2:.1f} "
            for k in range(step, cells, step):
                t = k / cells
                a = (A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t); b = (Ah[0] + (Bh[0] - Ah[0]) * t, Ah[1] + (Bh[1] - Ah[1]) * t)
                g += f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f} "
            svg += f'<path d="{g}" stroke="#7f95a9" stroke-width="0.5" fill="none"/>'
        if face > 1.5:
            svg += f'<line x1="{Ah[0]:.1f}" y1="{Ah[1]:.1f}" x2="{Bh[0]:.1f}" y2="{Bh[1]:.1f}" stroke="{PANEL_LIT}" stroke-width="{0.9 if face > 3 else 0.6}"/>'
        self.obj((xa + xb) / 2, y, svg, h0)

    def array(self, x0, y0, x1, y1, pitch=7.0, w=3.2, h0=0.8, tilt=0.45, min_px=2.6, z0=0.0):
        """Rows from the near edge back; far rows that would crowd closer than min_px are thinned."""
        self.array_in([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pitch, w, h0, tilt, min_px, z0)

    def array_in(self, ring, pitch=7.0, w=3.2, h0=0.8, tilt=0.45, min_px=2.6, z0=0.0):
        """Rows clipped to any outline: pivot corners, curving strips, odd fields."""
        ys_ = [p[1] for p in ring]
        y, last, n = min(ys_), None, len(ring)
        while y < max(ys_) - w * 0.4:
            yy = y + 0.01
            xs = []
            for k in range(n):
                (xa, ya), (xb, yb) = ring[k], ring[(k + 1) % n]
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            if last is None or abs(self.P(self.xc, y, z0)[1] - last) >= min_px:
                for a, b in zip(xs[0::2], xs[1::2]):
                    if b - a > 1.5:
                        self.panel_row(a, b, y, w, h0, tilt, z0=z0)
                last = self.P(self.xc, y, z0)[1]
            y += pitch

    def plateau(self, x0, y0, x1, y1, h, inset, top, side):
        """A flat-topped mound, such as a capped landfill: its near and end slopes and its top."""
        P, f = self.P, lambda pts: " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        tx0, ty0, tx1, ty1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
        faces = [[P(x0, y0), P(x1, y0), P(tx1, ty0, h), P(tx0, ty0, h)]]
        if self.xc < x0: faces.append([P(x0, y0), P(tx0, ty0, h), P(tx0, ty1, h), P(x0, y1)])
        if self.xc > x1: faces.append([P(x1, y0), P(tx1, ty0, h), P(tx1, ty1, h), P(x1, y1)])
        for fc in faces:
            self.ground.append(f'<polygon points="{f(fc)}" fill="{side}" stroke="{shade(side, 0.85)}" stroke-width="0.5"/>')
        self.ground.append(f'<polygon points="{f([P(tx0, ty0, h), P(tx1, ty0, h), P(tx1, ty1, h), P(tx0, ty1, h)])}" fill="{top}"/>')

    def water(self, ring):
        self.poly(ring, WATER, 'stroke="#6a94b0" stroke-width="0.6"')

    def creek(self, pts, width):
        """A stream of real width: a band along the centerline."""
        left, right = [], []
        for k, (x, y) in enumerate(pts):
            (xa, ya) = pts[max(0, k - 1)]; (xb, yb) = pts[min(len(pts) - 1, k + 1)]
            dx, dy = xb - xa, yb - ya; L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L * width / 2, dx / L * width / 2
            left.append((x + nx, y + ny)); right.append((x - nx, y - ny))
        self.water(left + right[::-1])

    def bale(self, x, y, r=0.8):
        s = self.px_per_m(x, y)
        if r * s < 0.8:
            return
        cx, cy = self.P(x, y, r)
        self.obj(x, y, f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r*s:.1f}" ry="{r*s*0.95:.1f}" fill="#d8bf73" stroke="#9c8443" stroke-width="0.6"/>'
                       f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r*s*0.45:.1f}" ry="{r*s*0.42:.1f}" fill="none" stroke="#b39a52" stroke-width="0.5"/>')

    def tower(self, x, y, h=30.0):
        s = self.px_per_m(x, y)
        if h * s < 3:
            return
        b1, b2 = self.P(x - 3, y), self.P(x + 3, y); t = self.P(x, y, h)
        a1, a2 = self.P(x - 5, y, h * 0.8), self.P(x + 5, y, h * 0.8)
        self.obj(x, y, f'<polyline points="{b1[0]:.1f},{b1[1]:.1f} {t[0]:.1f},{t[1]:.1f} {b2[0]:.1f},{b2[1]:.1f}" fill="none" stroke="#7d7a72" stroke-width="0.9"/>'
                       f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="#7d7a72" stroke-width="0.9"/>')

    def pole(self, x, y, h=10.0):
        b, t = self.P(x, y), self.P(x, y, h)
        a1, a2 = self.P(x - 1.2, y, h * 0.9), self.P(x + 1.2, y, h * 0.9)
        self.obj(x, y, f'<line x1="{b[0]:.1f}" y1="{b[1]:.1f}" x2="{t[0]:.1f}" y2="{t[1]:.1f}" stroke="#8a7f6a" stroke-width="0.9"/>'
                       f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="#8a7f6a" stroke-width="0.8"/>')

    def svg(self, sky=None, far=FAR_GREEN):
        sky = sky or getattr(self, "sky", "#e9f0f4")
        x = X0 + self.i * TW
        out = [f'<rect x="{x:.0f}" y="{HDR}" width="{TW:.0f}" height="{TH}" fill="{far}"/>',
               f'<rect x="{x:.0f}" y="{HDR}" width="{TW:.0f}" height="{self.y_hor - HDR:.1f}" fill="{sky}"/>']
        out += self.ground
        out += [s for _, s in sorted(self.objs, key=lambda o: -o[0])]
        # haze toward the horizon
        out.append(f'<rect x="{x:.0f}" y="{self.y_hor - 0.5:.1f}" width="{TW:.0f}" height="58" fill="url(#haze)"/>')
        return out


# ---------------------------------------------------------------- the countryside
Q = 804.7          # half a mile: the quarter-section road grid
HEDGE = "#8ea868"  # what shows between fields: fencerows and field edges


def countryside(t, palette, seed=1, cell=Q / 2, base=HEDGE, furrow_px=2.6):
    """Fields from the bottom edge to where they shrink into the haze, laid out in
    quarter sections the way they are surveyed: each 160 acres farmed whole, as two
    80s, or as four 40s. Furrows only where they would show."""
    rng = random.Random(seed)
    looks = {}
    near = t.y_front - 2                         # nothing behind the bottom edge, which may lie behind the viewer
    y = math.floor(near / Q) * Q
    while True:
        y1 = y + Q
        if t.P(t.xc, max(y, near))[1] - t.P(t.xc, y1)[1] < 0.6 or y > t.y_front + 200 * t.front:
            break
        hw = t.width_at(y1) * 0.62
        k0, k1 = math.floor((t.xc - hw) / Q), math.ceil((t.xc + hw) / Q)
        t.poly([(k0 * Q, max(y, near)), (k1 * Q, max(y, near)), (k1 * Q, y1), (k0 * Q, y1)], base)
        for k in range(k0, k1):
            x = k * Q
            r = random.Random(hash((seed, k, round(y / Q))))
            pattern = r.choice(["whole", "ns", "ew", "four", "four", "ns"])
            if pattern == "whole":
                parts = [(x, y, x + Q, y1, "ns")]
            elif pattern == "ns":
                parts = [(x, y, x + Q / 2, y1, "ns"), (x + Q / 2, y, x + Q, y1, "ns")]
            elif pattern == "ew":
                parts = [(x, y, x + Q, y + Q / 2, "ew"), (x, y + Q / 2, x + Q, y1, "ew")]
            else:
                parts = [(a, b, a + Q / 2, b + Q / 2, r.choice(["ns", "ns", "ew"])) for a in (x, x + Q / 2) for b in (y, y + Q / 2)]
            far = t.px_per_m(x, y) < 0.09
            if far and r.random() < 0.18:        # a woodlot in a back forty, seen as canopy
                a, b = (x, y) if r.random() < 0.5 else (x + Q / 2, y + Q / 2)
                parts = [p_ for p_ in parts if not (p_[0] <= a + 1 and p_[1] <= b + 1 and p_[2] >= a + Q / 2 - 1 and p_[3] >= b + Q / 2 - 1)]
                parts.append((a, b, a + Q / 2, b + Q / 2, "woods"))
            for (a, b, c, d, dirn) in parts:
                col = "#7e9a57" if dirn == "woods" else r.choice(palette)
                if d <= near:
                    continue
                b = max(b, near)
                m = max(1.5, (c - a) * 0.008)
                t.field(a + m, b + m, c - m, d - m, col)
                if col in (CORN, SOY):
                    sp = cell / 30
                    if dirn == "ns" and sp * t.px_per_m((a + c) / 2, b) > furrow_px:
                        t.furrows(a + m, b + m, c - m, d - m, sp)
                    elif dirn == "ew" and t.P(t.xc, b)[1] - t.P(t.xc, b + sp)[1] > furrow_px:
                        t.furrows_ew(a + m, b + m, c - m, d - m, sp)
            if far and r.random() < 0.45:        # a farmstead's yard trees by the road
                fx = x + r.uniform(0.1, 0.9) * Q
                t.poly([(fx, y + 12), (fx + 70, y + 12), (fx + 70, y + 70), (fx, y + 70)], "#6f8f4c")
        y = y1
    t.far_y = y


def road_grid(t, w, xs=None, ys=None, y_far=None, x_off=0.0, y_off=0.0):
    """County roads on the half-mile lines in view; pass xs or ys to keep only some."""
    y_far = y_far or getattr(t, "far_y", t.y_front + 40 * t.front)
    hw = t.width_at(y_far) * 0.62
    if ys is None:
        ys = [y_off + k * Q for k in range(math.floor((t.y_front - Q) / Q), math.ceil(y_far / Q))]
    if xs is None:
        xs = [x_off + k * Q for k in range(math.floor((t.xc - hw) / Q), math.ceil((t.xc + hw) / Q) + 1)]
    for y in ys:
        if t.y_front - 3 * w < y < y_far:
            hwy = t.width_at(y) * 0.7
            t.road(t.xc - hwy, y, t.xc + hwy, y, w)
    for x in xs:
        t.road(x, t.y_front - 3 * w, x, y_far, w)


def woodlot(t, x0, y0, x1, y1, seed=2, spacing=9.0, r=5.5):
    """A farm woodlot: a dark canopy floor, trees standing on it where they would show."""
    rng = random.Random(seed)
    t.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#7e9a57")
    if r * t.px_per_m((x0 + x1) / 2, y0) < 0.8:
        return
    sp = max(spacing, 1.4 / t.px_per_m((x0 + x1) / 2, y0))
    for y in np.arange(y0 + sp / 2, y1, sp):
        for x in np.arange(x0 + sp / 2, x1, sp):
            t.tree(x + rng.uniform(-sp, sp) * 0.3, y + rng.uniform(-sp, sp) * 0.3, max(r, sp * 0.62) * rng.uniform(0.85, 1.15),
                   rng.choice(["#6f9150", "#7f9f55", "#678a47"]), "#4f6b34")


def hedgerow(t, pts, spacing=11.0, r=4.2, seed=3):
    rng = random.Random(seed)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        L = math.hypot(xb - xa, yb - ya)
        for s in np.arange(0, L, spacing):
            if rng.random() < 0.8:
                f = s / L
                t.tree(xa + (xb - xa) * f + rng.uniform(-2, 2), ya + (yb - ya) * f + rng.uniform(-2, 2), r * rng.uniform(0.75, 1.2),
                       rng.choice(["#6f9150", "#7f9f55"]), "#557538")


def homestead(t, x, y, seed=4, barn="#b5523a", south=False):
    """A neighbor's place set back from the road: house, a barn or shed, a few trees.
    (x, y) is the middle of the yard's road edge; the yard runs north from it, or
    south when the place sits on the near side of the road."""
    rng = random.Random(seed)
    if south:
        y -= 50
    t.field(x - 30, y, x + 30, y + 46, YARD)
    t.building(x - 22, y + 10, 10, 8, 5, rng.choice(["#ffffff", "#f1ead8", "#e5e8ea"]), "#7c7a72")
    if barn:
        t.building(x - 2, y + 18, 20, 11, 6.5, barn, "#6e6b63")
    else:
        t.building(x - 2, y + 16, 22, 13, 5, "#d9d6cc", "#9ea3a6", gable=False)
    for k in range(rng.randint(4, 7)):
        t.tree(x + rng.uniform(-30, 30), y + rng.uniform(30, 48), rng.uniform(3.6, 5.2), rng.choice(["#6f9150", "#7f9f55"]), "#557538")


def fence(t, x0, y0, x1, y1, post=3.0, h=1.2):
    """A post-and-wire fence, for views close enough to see one."""
    L = math.hypot(x1 - x0, y1 - y0)
    a, b = t.P(x0, y0, h), t.P(x1, y1, h)
    d = f"M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f} "
    for s in np.arange(0, L + 0.01, post):
        f = s / L
        g, top = t.P(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f), t.P(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, h)
        d += f"M{g[0]:.1f},{g[1]:.1f} L{top[0]:.1f},{top[1]:.1f} "
    t.obj((x0 + x1) / 2, max(y0, y1), f'<path d="{d}" stroke="#8a7a60" stroke-width="0.6" fill="none"/>')


def town(t, x0, y0, x1, y1, block=110, seed=7):
    """Streets on a grid, yards and shade trees, roofs: at this distance a speckled patch."""
    rng = random.Random(seed)
    t.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#a3b884")
    for y in np.arange(y0, y1, block): t.poly([(x0, y - 3), (x1, y - 3), (x1, y + 3), (x0, y + 3)], "#d9d5c8")
    for x in np.arange(x0, x1, block): t.poly([(x - 3, y0), (x + 3, y0), (x + 3, y1), (x - 3, y1)], "#d9d5c8")
    for y in np.arange(y0 + 14, y1 - 14, block / 2):
        for x in np.arange(x0 + 12, x1 - 12, 30):
            u = rng.random()
            if u < 0.45:
                t.poly([(x, y), (x + 12, y), (x + 12, y + 10), (x, y + 10)], rng.choice(["#e9e6de", "#cfcac0", "#bdb6aa"]))
            elif u < 0.8:
                t.poly([(x, y), (x + 20, y), (x + 20, y + 20), (x, y + 20)], rng.choice(["#6f8f4c", "#7f9f55"]))

def farmstead(t, cx, cy):
    """The reference farm: house, red barn, silo, windbreak, seen from the south."""
    t.field(cx - 34, cy - 26, cx + 40, cy + 30, YARD)
    t.building(cx - 24, cy - 14, 10, 8, 5, "#ffffff", "#7c7a72")
    t.building(cx - 4, cy - 2, 24, 12, 6.5, "#b5523a", "#6e6b63")
    t.silo(cx + 25, cy + 4)
    for x in np.arange(cx - 34, cx + 40, 6):
        t.tree(x, cy + 34, 4.6, "#6f9150", "#557538")


def assemble(tiles, title, desc, left, center, right, bar, extra_style, fname, bar_h=98):
    h = BAR_Y + bar_h + 4
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img">',
           f'<title>{title}</title>', f'<desc>{desc}</desc>', '<style>',
           'text{font-family:"Helvetica Neue",Helvetica,"Segoe UI",Arial,sans-serif}',
           '.hd{font-size:14px;font-weight:700;letter-spacing:.14em;fill:#6f6d66}',
           '.sc{font-size:11.5px;font-style:italic;fill:#6f6d66}'] + extra_style + ['</style>',
           '<defs><linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef2ee" stop-opacity="0.95"/>'
           '<stop offset="1" stop-color="#eef2ee" stop-opacity="0"/></linearGradient></defs>',
           f'<rect width="{W}" height="{h}" fill="#ffffff"/>']
    out.append(f'<text class="hd" x="18" y="27">&#9664;</text><text class="hd" x="40" y="27">{left}</text>')
    lw = 40 + 12.2 * len(left) + 20
    out.append('<g stroke="#b4b2a9" stroke-width="1.2"><path d="' + " ".join(f"M{x},15 v11" for x in range(int(lw), 420, 30)) + '"/></g>')
    out.append(f'<text class="hd" x="552" y="27" text-anchor="middle">{center}</text>')
    rw = 1064 - 12.2 * len(right) - 20
    out.append('<g stroke="#b4b2a9" stroke-width="1.2"><path d="' + " ".join(f"M{x},15 v11" for x in range(686, int(rw), 30)) + '"/></g>')
    out.append(f'<text class="hd" x="1064" y="27" text-anchor="end">{right}</text><text class="hd" x="1086" y="27" text-anchor="end">&#9654;</text>')
    for t in tiles:
        x = X0 + t.i * TW
        out.append(f'<clipPath id="c{t.i}"><rect x="{x:.0f}" y="{HDR}" width="{TW:.0f}" height="{TH}"/></clipPath>')
        out.append(f'<g clip-path="url(#c{t.i})">' + "\n".join(t.svg()) + '</g>')
        if getattr(t, "label", None):
            out.append(f'<text class="sc" x="{x + 9:.0f}" y="{HDR + 15}">{t.label}</text>')
    for i, (col, lines) in enumerate(bar):
        x = X0 + i * TW
        out.append(f'<rect x="{x:.0f}" y="{BAR_Y}" width="{TW:.0f}" height="{bar_h}" fill="{col}"/>')
        out.append("".join(f'<text class="{cls}" x="{x + 11:.0f}" y="{BAR_Y + dy}">{txt}</text>' for cls, txt, dy in lines))
    out.append('<g stroke="#ffffff" stroke-width="1.5"><path d="' + " ".join(f"M{X0 + k * TW:.0f},{HDR} v{TH + bar_h}" for k in range(1, 6)) + '"/></g>')
    out.append('</svg>')
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", fname)
    open(dest, "w").write("\n".join(out))
    print(fname, len("\n".join(out)) // 1024, "KB")
