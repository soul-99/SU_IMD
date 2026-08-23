#!/usr/bin/env python3
"""Grow the app icon's artwork inside its 108-unit viewport, and bring the sibling icons with it.

The gear was drawn small: 38.4 units of the 72-unit safe zone, so a launcher showed it with
a wide white margin. This scales the drawing about the viewport centre without touching the
viewport itself, which is the only way to change how big the art reads — the adaptive-icon
mask always shows the middle 72 units, whatever is in them.

Idempotent on purpose. Each file is first normalised back to the width it had when this was
written, then scaled by GROW, so running it twice does not compound.
"""
import math
import pathlib
import re
import sys

CX = CY = 54.0
GROW = float(sys.argv[1]) if len(sys.argv) > 1 else 1.35
# Paths resolve from this script's own location, so it runs from anywhere.
REPO = pathlib.Path(__file__).resolve().parent.parent
RES = REPO / 'app/src/main/res'

# Width of each drawing when it was first authored, so the scale is measured from a fixed
# point rather than from whatever the file happens to hold now.
CANON_WIDTH = {
    'ic_launcher_foreground': 38.3823,
    'ic_launcher_monochrome': 38.3823,
    'ic_services_foreground': 38.3823,
    'ic_services_monochrome': 38.3823,
    # The splash icon is a separate copy of the same drawing. Left behind, it would show a
    # visibly smaller gear than the launcher icon that had just been tapped.
    'ic_splash': 38.3823,
}

# Parameter layout per SVG path command: how many numbers, and which of them are
# coordinates. An arc is the awkward one — its first two numbers are radii, then a rotation
# and two flags that must survive untouched, and only the last pair is a point.
ARGS = {'M': 2, 'L': 2, 'T': 2, 'C': 6, 'S': 4, 'Q': 4, 'H': 1, 'V': 1, 'A': 7, 'Z': 0}

NUM = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')


def transform_path(d, k, origin=(CX, CY)):
    """Uniformly scale an absolute SVG path about a point, command by command."""
    out = []
    i = 0
    cmd = None

    def sx(v):
        return origin[0] + (float(v) - origin[0]) * k

    def sy(v):
        return origin[1] + (float(v) - origin[1]) * k

    while i < len(d):
        ch = d[i]

        if ch.isalpha():
            cmd = ch
            assert cmd in ARGS, f'unhandled path command {cmd!r}'
            assert cmd.isupper(), f'relative command {cmd!r}; this only handles absolute paths'
            out.append(cmd)
            i += 1

            continue

        if not (ch.isdigit() or ch in '-+.'):
            i += 1

            continue

        n = ARGS[cmd]
        nums = []

        for _ in range(n):
            m = NUM.match(d, i)
            assert m, f'expected {n} numbers after {cmd} at offset {i}'
            nums.append(m.group())
            i = m.end()

            while i < len(d) and d[i] in ', \t\n':
                i += 1

        if cmd == 'H':
            vals = [sx(nums[0])]
        elif cmd == 'V':
            vals = [sy(nums[0])]
        elif cmd == 'A':
            vals = [float(nums[0]) * k, float(nums[1]) * k, float(nums[2]),
                    float(nums[3]), float(nums[4]), sx(nums[5]), sy(nums[6])]
        else:
            vals = [sx(v) if j % 2 == 0 else sy(v) for j, v in enumerate(nums)]

        out.append(','.join(
            f'{v:g}' if cmd == 'A' and j in (3, 4) else f'{v:.4f}'.rstrip('0').rstrip('.')
            for j, v in enumerate(vals)
        ))

    return ''.join(
        tok if tok.isalpha() else (tok if out[j - 1].isalpha() else ' ' + tok)
        for j, tok in enumerate(out)
    )


def path_bbox(d, steps=400):
    """Bounding box by sampling — good enough to measure a scale factor from."""
    from svgpathtools import parse_path

    p = parse_path(d)
    pts = [p.point(i / steps) for i in range(steps + 1)]

    return (min(c.real for c in pts), min(c.imag for c in pts),
            max(c.real for c in pts), max(c.imag for c in pts))


def drawing_bbox(xml):
    boxes = [path_bbox(d) for d in re.findall(r'pathData="([^"]+)"', xml)]

    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


for name, canon in CANON_WIDTH.items():
    f = RES / 'drawable' / f'{name}.xml'
    xml = f.read_text()
    before = drawing_bbox(xml)
    k = GROW * canon / (before[2] - before[0])
    scaled = re.sub(r'pathData="([^"]+)"',
                    lambda m: f'pathData="{transform_path(m.group(1), k)}"', xml)
    after = drawing_bbox(scaled)
    f.write_text(scaled)
    print(f'{name:26} {before[2] - before[0]:6.2f} -> {after[2] - after[0]:6.2f} '
          f'(x{k:.4f})  height {after[3] - after[1]:.2f}  '
          f'safe-zone fill {(after[2] - after[0]) / 72:.0%}')
