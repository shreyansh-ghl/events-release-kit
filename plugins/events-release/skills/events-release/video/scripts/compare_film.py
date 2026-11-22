"""Dev tool: side-by-side sheet of film frames vs template stills. Usage: compare_film.py film.mp4 stills_dir out.png film_t:ours_t ..."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def main(film: str, stills: str, out: str, pairs: list[str]) -> None:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for p in pairs:
            ft, ot = (float(x) for x in p.split(":"))
            fpng = Path(tmp) / f"f{ft}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ft), "-i", film, "-frames:v", "1", "-vf", "scale=960:540", str(fpng)], check=True)
            a = Image.open(fpng).convert("RGB")
            b = Image.open(Path(stills) / f"t{ot:07.2f}.png").convert("RGB").resize((960, 540))
            rows.append((a, b, ft, ot))
    sheet = Image.new("RGB", (1940, len(rows) * 560 + 10), "#777")
    d = ImageDraw.Draw(sheet)
    for i, (a, b, ft, ot) in enumerate(rows):
        sheet.paste(a, (5, 10 + i * 560))
        sheet.paste(b, (975, 10 + i * 560))
        d.text((12, 14 + i * 560), f"FILM {ft}s", fill="red")
        d.text((982, 14 + i * 560), f"TEMPLATE {ot}s", fill="red")
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
