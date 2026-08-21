"""Measures the source artwork and emits the exact path geometry gen.py ships.

The gear is not a textbook involute or a ring of tangent circles — it is drawn art, and
every attempt to model it analytically was visibly off. So it is measured instead: the
silhouette's radius is sampled at sub-pixel precision every 0.25 degrees, averaged over
the six rotational copies and mirrored about the tooth axis (which is what makes the
result clean rather than wobbly), and one 60-degree sector is fitted with cubic Beziers.
The sector is cut at a notch minimum, where symmetry forces the tangent perpendicular to
the radius, so rotating it six times joins up smoothly with no extra constraints.

Outputs geometry.py, which gen.py imports. Needs numpy + Pillow; not part of the build.
"""
import math

import numpy as np
from PIL import Image

SRC = "src.png"
WHITE = np.array([255.0, 255.0, 255.0])
GEAR = np.array([165.0, 219.0, 185.0])
KEY = np.array([19.0, 167.0, 91.0])

img = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
H, W, _ = img.shape


def coverage(background, foreground):
    """Per-pixel fraction of `foreground` against `background`, from the anti-aliasing."""
    d = foreground - background
    return ((img - background) @ d) / float(d @ d)


# Silhouette: anything that is not the page. Gear and key both count.
silhouette = np.clip(np.maximum(coverage(WHITE, GEAR), coverage(WHITE, KEY)), 0.0, 1.5)


def sample(field, x, y):
    """Bilinear sample, so the boundary is located to a fraction of a pixel."""
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    if x0 < 0 or y0 < 0 or x0 + 1 >= W or y0 + 1 >= H:
        return 0.0
    fx, fy = x - x0, y - y0
    return (field[y0, x0] * (1 - fx) * (1 - fy) + field[y0, x0 + 1] * fx * (1 - fy) +
            field[y0 + 1, x0] * (1 - fx) * fy + field[y0 + 1, x0 + 1] * fx * fy)


def radius(field, cx, cy, ang, r_lo=150.0, r_hi=400.0):
    """Outermost crossing of the 0.5 contour along a ray, bisected to 0.01px."""
    ca, sa = math.cos(ang), math.sin(ang)
    prev_r, prev_v = r_lo, sample(field, cx + r_lo * ca, cy + r_lo * sa)
    hit = None
    r = r_lo + 0.5
    while r <= r_hi:
        v = sample(field, cx + r * ca, cy + r * sa)
        if prev_v >= 0.5 > v:
            hit = (prev_r, r)
        prev_r, prev_v = r, v
        r += 0.5
    if hit is None:
        return None
    lo, hi = hit
    for _ in range(30):
        mid = (lo + hi) / 2
        if sample(field, cx + mid * ca, cy + mid * sa) >= 0.5:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


N = 6
TOL = 0.5          # px, in the source PNG's own 1024-unit space
STEP = math.radians(0.25)
COUNT = int(round(2 * math.pi / STEP))
ANGLES = [k * STEP for k in range(COUNT)]


def profile(cx, cy):
    return [radius(silhouette, cx, cy, a) for a in ANGLES]


def asymmetry(cx, cy):
    """How far the profile is from having exact 6-fold symmetry about (cx, cy)."""
    r = profile(cx, cy)
    if any(v is None for v in r):
        return 1e9
    r = np.array(r)
    step = COUNT // N
    stack = np.stack([np.roll(r, -k * step) for k in range(N)])
    return float(stack.std(axis=0).mean())


def find_centre(cx, cy, span=6.0):
    """Coordinate descent. The drawn centre is not exactly the bounding-box centre."""
    best = asymmetry(cx, cy)
    while span >= 0.125:
        moved = False
        for dx, dy in ((span, 0), (-span, 0), (0, span), (0, -span)):
            score = asymmetry(cx + dx, cy + dy)
            if score < best - 1e-9:
                best, cx, cy, moved = score, cx + dx, cy + dy, True
        if not moved:
            span /= 2
    return cx, cy, best


# ---------------------------------------------------------------- Bezier fitting


def bezier(p, t):
    mt = 1 - t
    return (mt ** 3 * p[0] + 3 * mt * mt * t * p[1] + 3 * mt * t * t * p[2] + t ** 3 * p[3])


def chord_params(pts):
    d = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    return d / d[-1] if d[-1] > 0 else d


def fit_segment(pts, t, t0, t1):
    """Least-squares cubic through pts[0] and pts[-1] with tangents t0 and t1 fixed."""
    p0, p3 = pts[0], pts[-1]
    mt = 1 - t
    a1 = (3 * mt * mt * t)[:, None] * t0
    a2 = (3 * mt * t * t)[:, None] * t1
    rhs = pts - (mt ** 3)[:, None] * p0 - (t ** 3)[:, None] * p3
    m = np.array([[float((a1 * a1).sum()), float((a1 * a2).sum())],
                  [float((a1 * a2).sum()), float((a2 * a2).sum())]])
    v = np.array([float((a1 * rhs).sum()), float((a2 * rhs).sum())])
    det = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
    if abs(det) < 1e-12:
        d = np.linalg.norm(p3 - p0) / 3
        alpha = beta = d
    else:
        alpha = (v[0] * m[1, 1] - m[0, 1] * v[1]) / det
        beta = (m[0, 0] * v[1] - v[0] * m[1, 0]) / det
        d = np.linalg.norm(p3 - p0)
        if alpha <= 0 or beta <= 0 or alpha > 2 * d or beta > 2 * d:
            alpha = beta = d / 3
    return np.array([p0, p0 + alpha * t0, p3 + beta * t1, p3])


def max_error(pts, t, curve):
    err = 0.0
    worst = len(pts) // 2
    for i, (p, ti) in enumerate(zip(pts, t)):
        e = float(np.linalg.norm(bezier(curve, ti) - p))
        if e > err:
            err, worst = e, i
    return err, worst


def reparametrise(pts, t, curve):
    out = []
    for p, ti in zip(pts, t):
        d1 = 3 * ((1 - ti) ** 2 * (curve[1] - curve[0]) + 2 * (1 - ti) * ti *
                  (curve[2] - curve[1]) + ti * ti * (curve[3] - curve[2]))
        d2 = 6 * ((1 - ti) * (curve[2] - 2 * curve[1] + curve[0]) +
                  ti * (curve[3] - 2 * curve[2] + curve[1]))
        diff = bezier(curve, ti) - p
        den = float((d1 * d1).sum() + (diff * d2).sum())
        out.append(ti if abs(den) < 1e-12 else ti - float((diff * d1).sum()) / den)
    return np.clip(np.array(out), 0.0, 1.0)


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n else v


def fit_curve(pts, t0, t1, tol, depth=0):
    """Schneider's algorithm: fit, and split at the worst point if it does not converge."""
    if len(pts) < 3:
        d = np.linalg.norm(pts[-1] - pts[0]) / 3
        return [np.array([pts[0], pts[0] + d * t0, pts[-1] + d * t1, pts[-1]])]
    t = chord_params(pts)
    curve = fit_segment(pts, t, t0, t1)
    for _ in range(24):
        err, split = max_error(pts, t, curve)
        if err < tol:
            return [curve]
        t = reparametrise(pts, t, curve)
        curve = fit_segment(pts, t, t0, t1)
    err, split = max_error(pts, t, curve)
    if err < tol or depth > 12:
        return [curve]
    split = min(max(split, 2), len(pts) - 3)
    centre = unit(unit(pts[split] - pts[split - 1]) + unit(pts[split + 1] - pts[split]))
    return (fit_curve(pts[:split + 1], t0, -centre, tol, depth + 1) +
            fit_curve(pts[split:], centre, t1, tol, depth + 1))


# ---------------------------------------------------------------- run

def main():
    cx, cy, score = find_centre(511.5, 490.5)
    print(f"gear centre       : ({cx:.3f}, {cy:.3f})   6-fold residual {score:.3f}px")

    r = np.array(profile(cx, cy))
    step = COUNT // N
    r = np.stack([np.roll(r, -k * step) for k in range(N)]).mean(axis=0)

    # Mirror about the tooth axis. The axis is found by search rather than by taking the
    # profile's maximum: the crest is nearly flat, so argmax lands anywhere along it.
    axis = min(range(COUNT),
               key=lambda k: float(np.abs(r - np.roll(r[::-1], 2 * k + 1)).mean()))
    residual = float(np.abs(r - np.roll(r[::-1], 2 * axis + 1)).mean())
    print(f"tooth axis        : {axis * STEP * 180 / math.pi:.2f} deg"
          f"   mirror residual {residual:.3f}px")
    r = (r + np.roll(r[::-1], 2 * axis + 1)) / 2

    # Averaging twelve copies leaves about 0.45px of raster noise. A +/-1 degree box
    # blur takes that out; anything sharper than 1 degree here is not real.
    win = int(round(math.radians(1.0) / STEP)) | 1
    r = np.convolve(np.concatenate([r[-win:], r, r[:win]]),
                    np.ones(win) / win, mode="same")[win:-win]

    notch = int(np.argmin(r))
    r = np.roll(r, -notch)
    start = notch * STEP

    print(f"tooth crest / root: {r.max():.2f} / {r.min():.2f} px"
          f"   (root {100 * r.min() / r.max():.1f}% of crest)")

    sector = np.array([[cx + rad * math.cos(start + i * STEP),
                        cy + rad * math.sin(start + i * STEP)]
                       for i, rad in enumerate(r[:step + 1])])

    # At a symmetric minimum the tangent is perpendicular to the radius, so the six
    # rotated copies meet with matching tangents for free.
    def perp(ang):
        return np.array([-math.sin(ang), math.cos(ang)])

    curves = fit_curve(sector, perp(start), -perp(start + step * STEP), tol=TOL)
    worst = max(min(float(np.linalg.norm(bezier(c, t) - p))
                    for c in curves for t in np.linspace(0, 1, 200))
                for p in sector)
    print(f"sector fitted with: {len(curves)} cubic segments, worst deviation {worst:.3f}px")

    with open("geometry.py", "w") as fh:
        fh.write('"""Generated by trace.py from the source artwork. Do not edit by hand."""\n')
        fh.write(f"GEAR_CENTRE = ({float(cx)!r}, {float(cy)!r})\n")
        fh.write(f"GEAR_CREST = {float(r.max())!r}\n")
        fh.write(f"GEAR_SECTOR_START = {float(start)!r}\n")
        fh.write("GEAR_SECTOR = [\n")
        for c in curves:
            fh.write("    [%s],\n" % ", ".join(f"({float(p[0])!r}, {float(p[1])!r})" for p in c))
        fh.write("]\n")
    print("wrote geometry.py")


if __name__ == "__main__":
    main()
