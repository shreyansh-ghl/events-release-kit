"""Stitch Claude-in-Chrome zoom tiles into one sharp capture, and build contact sheets.

Chrome's plain screenshot is small JPEG; `zoom` on a region with save_to_disk=true and scale=1 returns a ~2x PNG.
Capture a page as tiles and stitch them here.

    python3 -I tiles.py stitch out.png tile1.png@0,0,514,392 tile2.png@514,0,514,392 ...
        Each tile is "<file>@x,y,w,h": the zoom region in page CSS px. For a long page, add window.scrollY to y
        (scroll with JS, read scrollY, zoom, repeat). Output scale = the tiles' own px-per-CSS-px.
    python3 -I tiles.py grid <viewport_w> <viewport_h> [cols] [rows]
        Prints the zoom regions to request (default 3x2) so tiles are small enough to come back at full resolution.
    python3 -I tiles.py sheet out.png img1 img2 ...   [--cols 3]
        Contact sheet for checkpoints (each image fitted into a 1000x625 cell).
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_tile(arg: str) -> tuple[Path, tuple[float, float, float, float]]:
    file, _, region = arg.rpartition("@")
    parts = [float(v) for v in region.split(",")]
    if not file or len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise ValueError(f"bad tile {arg!r}; expected file.png@x,y,w,h")
    return Path(file), (parts[0], parts[1], parts[2], parts[3])


def stitch(out: Path, tiles: list[str]) -> Path:
    parsed = [parse_tile(t) for t in tiles]
    images = [(Image.open(f).convert("RGB"), r) for f, r in parsed]
    scale = statistics.median(im.width / r[2] for im, r in images)
    x0 = min(r[0] for _, r in images)
    y0 = min(r[1] for _, r in images)
    w = max(r[0] + r[2] for _, r in images) - x0
    h = max(r[1] + r[3] for _, r in images) - y0
    canvas = Image.new("RGB", (round(w * scale), round(h * scale)), "white")
    for im, (x, y, rw, rh) in images:
        size = (round(rw * scale), round(rh * scale))
        if im.size != size:  # zoom output can be off by a pixel or capped; normalise to the common scale
            im = im.resize(size, Image.LANCZOS)
        canvas.paste(im, (round((x - x0) * scale), round((y - y0) * scale)))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, optimize=True)
    return out


def grid(vw: float, vh: float, cols: int = 3, rows: int = 2) -> list[tuple[int, int, int, int]]:
    tw, th = vw / cols, vh / rows
    regions = []
    for r in range(rows):
        for c in range(cols):
            x0, y0 = round(c * tw), round(r * th)
            regions.append((x0, y0, round((c + 1) * tw) - x0, round((r + 1) * th) - y0))
    return regions


def sheet(out: Path, files: list[str], cols: int = 3, labels: bool = True) -> Path:
    """Numbered contact sheet (labels on by default) for checkpoints A and B."""
    cw, ch, pad = 1000, 625, 24
    rows = max(1, -(-len(files) // cols))
    canvas = Image.new("RGB", (cols * (cw + pad) + pad, rows * (ch + pad + (40 if labels else 0)) + pad), "#d9d4cc")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(str(Path(__file__).resolve().parents[1] / "fonts" / "Inter-Variable.ttf"), 24)
    except OSError:
        font = ImageFont.load_default()
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((cw, ch))
        cx = pad + (i % cols) * (cw + pad)
        cy = pad + (i // cols) * (ch + pad + (40 if labels else 0))
        canvas.paste(im, (cx + (cw - im.width) // 2, cy + (ch - im.height) // 2))
        if labels:
            draw.text((cx, cy + ch + 8), f"{i + 1}. {Path(f).name}", fill="#171512", font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    try:
        if cmd == "stitch":
            print(stitch(Path(argv[2]), argv[3:]))
        elif cmd == "grid":
            nums = [float(a) for a in argv[2:4]] + [int(a) for a in argv[4:6]]
            for reg in grid(*nums):
                print(list(reg))
        elif cmd == "sheet":
            cols = int(argv[argv.index("--cols") + 1]) if "--cols" in argv else 3
            files = [a for i, a in enumerate(argv[3:], 3) if not a.startswith("--") and argv[i - 1] != "--cols"]
            print(sheet(Path(argv[2]), files, cols))
        else:
            print(__doc__)
            return 2
    except (ValueError, OSError) as err:
        print(f"tiles.py {cmd}: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
