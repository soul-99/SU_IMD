# Icon geometry

`source-artwork.png` is the original drawing. Everything else is generated from it.

    python3 trace.py     # measure the gear, fit one 60-degree sector -> geometry.py
    python3 render.py ..  # write every drawable, mipmap and the store icon
    python3 verify.py    # re-render in the source's coordinates and diff against it

`gen.py` holds the geometry itself: the key as rounded rectangles measured to sub-pixel
precision, the gear as the fitted sector rotated six times. `trace.py` only needs
re-running if the source artwork changes.

Needs `numpy`, `Pillow` and `cairosvg`. None of this runs during the Android build.
