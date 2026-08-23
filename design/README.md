# Icon geometry

`source-artwork.png` is the original drawing. Everything else is generated from it.

    python3 trace.py            # measure the gear, fit one 60-degree sector -> geometry.py
    python3 render.py ..        # write every drawable, mipmap and the store icon
    python3 verify.py           # re-render in the source's coordinates and diff against it

`gen.py` holds the geometry itself: the key as rounded rectangles measured to sub-pixel
precision, the gear as the fitted sector rotated six times. `trace.py` only needs re-running
if the source artwork changes.

## The sibling icons

The Services manager and Revert to default icons are the *same gear*, lifted from the
launcher icon rather than redrawn, with the key swapped for a different glyph. Each script
normalises the gear back to the width it was authored at (38.3823) before doing anything, so
they can be re-run at any time without compounding.

    python3 build_icons.py      # Services manager: gear + Android head
    python3 build_tile.py       # its Quick Settings tile, as a knockout
    python3 build_revert.py     # Revert to default: gear + revert arrow with a tick
    python3 scale_app_icons.py  # scale every 108-viewport drawing about its centre
    python3 build_legacy_png.py # the pre-26 PNG mipmaps, from those vectors

`scale_app_icons.py` takes a growth factor (default 1.35) measured from the authored size,
not from the file's current state — running it twice is a no-op. `build_revert.py` takes the
same factor and must be given the same one.

Two constraints the scripts assert rather than trust:

* **The glyph must not overhang the gear.** The gear's rim is a wave — 20.6 units out at a
  tooth, 15.2 in a valley — and a revert arrow's C sweeps past every valley, so the valleys
  cap its radius. An overhang is nearly invisible on the coloured icon but cuts a notch out
  of the gear on the Quick Settings tile, where the glyph is a hole rather than a colour.
* **A ring must stay a C, never a closed O.** A closed one gains an interior ring, which the
  knockout renders as a filled disc sitting in the middle of the arrow.

Tile icons are built with real boolean unions rather than an even-odd fill: even-odd punches
overlapping subpaths back to solid, which would put bright wedges across the shapes.

Needs `numpy`, `Pillow`, `cairosvg`, `shapely` and `svgpathtools`. None of this runs during
the Android build.
