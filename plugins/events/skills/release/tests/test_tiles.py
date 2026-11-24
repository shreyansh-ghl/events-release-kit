"""Behaviour tests for tile stitching and contact sheets."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tiles  # noqa: E402


def test_grid_covers_viewport_exactly() -> None:
    regions = tiles.grid(1542, 784)
    assert len(regions) == 6
    assert sum(w * h for _, _, w, h in regions) == 1542 * 784
    assert max(x + w for x, _, w, _ in regions) == 1542


def test_zoom_box_gives_corners_for_chrome_zoom() -> None:
    # Chrome's zoom action takes x0,y0,x1,y1; stitch takes x,y,w,h. Both must describe the same tile.
    regions = tiles.grid(1381, 828, 2, 2)
    assert [tiles.zoom_box(r) for r in regions] == [
        (0, 0, 690, 414), (690, 0, 1381, 414), (0, 414, 690, 828), (690, 414, 1381, 828)]


def test_patch_replaces_only_the_changed_tiles(tmp_path: Path) -> None:
    base = tmp_path / "before.png"
    Image.new("RGB", (400, 200), "white").save(base)  # a 200x100 CSS viewport at 2x
    tile = tmp_path / "toggle.png"
    Image.new("RGB", (200, 100), "red").save(tile)  # re-zoomed bottom-right quarter after a click
    out = tiles.patch(tmp_path / "after.png", base, [f"{tile}@100,50,100,50"])
    im = Image.open(out).convert("RGB")
    assert im.size == (400, 200)
    assert im.getpixel((10, 10)) == (255, 255, 255)
    assert im.getpixel((390, 190)) == (255, 0, 0)
    assert Image.open(base).convert("RGB").getpixel((390, 190)) == (255, 255, 255)  # the before frame is untouched


def test_stitch_places_tiles_at_2x(tmp_path: Path) -> None:
    files = []
    colours = ["red", "green", "blue", "yellow"]
    for i, (x, y) in enumerate([(0, 0), (100, 0), (0, 50), (100, 50)]):
        f = tmp_path / f"t{i}.png"
        Image.new("RGB", (200, 100), colours[i]).save(f)  # 2x of a 100x50 CSS region
        files.append(f"{f}@{x},{y},100,50")
    out = tiles.stitch(tmp_path / "out.png", files)
    im = Image.open(out).convert("RGB")
    assert im.size == (400, 200)
    assert im.getpixel((10, 10)) == (255, 0, 0)
    assert im.getpixel((390, 190)) == (255, 255, 0)


def test_stitch_stacks_scrolled_tiles(tmp_path: Path) -> None:
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGB", (200, 100), "red").save(a)
    Image.new("RGB", (200, 100), "blue").save(b)
    out = tiles.stitch(tmp_path / "long.png", [f"{a}@0,0,100,50", f"{b}@0,50,100,50"])  # second tile after scrollY=50
    assert Image.open(out).size == (200, 200)


def test_bad_tile_spec_is_rejected() -> None:
    with pytest.raises(ValueError):
        tiles.parse_tile("tile.png@0,0,100")


def test_sheet_numbers_every_image(tmp_path: Path) -> None:
    files = []
    for i in range(4):
        f = tmp_path / f"s{i}.png"
        Image.new("RGB", (3200, 2000), "white").save(f)
        files.append(str(f))
    out = tiles.sheet(tmp_path / "sheet.png", files, cols=2)
    assert Image.open(out).size[0] == 2 * 1024 + 24
