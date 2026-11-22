"""Side-by-side + text-band diff of a rendered card against a reference card (dev tool)."""
from __future__ import annotations

import sys
from PIL import Image


def bands(path: str, box: tuple[int, int, int, int], thr: int = 450) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    im = Image.open(path).convert("RGB").crop(box)
    px, (w, h) = im.load(), im.size
    rows = [y for y in range(h) if any(sum(px[x, y]) < thr for x in range(0, w, 2))]
    if not rows:
        return []
    groups, s, p = [], rows[0], rows[0]
    for r in rows[1:]:
        if r - p > 3:
            groups.append((s, p))
            s = r
        p = r
    groups.append((s, p))
    out = []
    for a, b in groups:
        cols = [x for x in range(w) if any(sum(px[x, y]) < thr for y in range(a, b + 1, 2))]
        out.append(((a + box[1], b + box[1]), (min(cols) + box[0], max(cols) + box[0])))
    return out


def main(ref: str, ours: str, sheet: str, box: str) -> None:
    b = tuple(int(v) for v in box.split(","))
    for name, p in (("ref ", ref), ("ours", ours)):
        print(name, bands(p, b))
    a, o = Image.open(ref).convert("RGB"), Image.open(ours).convert("RGB")
    s = Image.new("RGB", (3200, 4000))
    s.paste(a, (0, 0))
    s.paste(o, (0, 2000))
    s.resize((1600, 2000)).save(sheet)


if __name__ == "__main__":
    main(*sys.argv[1:5])
