"""Render every Northstar brand asset from house tokens.

Port of the in-page canvas helpers used to seed the Northstar staging sub-account
(22 Nov 2026), so a teammate can re-create the same art offline:

    python3 -I scripts/northstar_brand.py          # writes northstar/**

Outputs: logo-square, logo-200, favicon, cover (no year), portal image,
6 exhibitor logos, Harbor Payments home ad, Brightwave web + mobile page banners.
Exhibitor list comes from northstar/world.json.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
OUT = ROOT / "northstar"
WORLD = json.loads((OUT / "world.json").read_text())
TOKENS = json.loads((ROOT / "tokens.json").read_text())

NS = TOKENS["color"]["northstar"]
NAVY, NAVY_GRID, CORAL, MUTED = NS["navy"], NS["navy_grid"], NS["coral"], NS["muted"]
WHITE = "#ffffff"
LOGO_INK = "#14121f"
SS = 2  # supersample factor; every canvas is drawn at SS x then downscaled for smooth edges

WEIGHTS = {500: "Medium", 600: "SemiBold", 800: "ExtraBold", 900: "Black"}


class Canvas:
    """Tiny canvas-like wrapper: callers use final-pixel coordinates, drawing happens at SS x."""

    def __init__(self, w: int, h: int, bg: str) -> None:
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w * SS, h * SS), bg)
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts: list[tuple[float, float]], fill: str) -> None:
        self.d.polygon(self._p(pts), fill=fill)

    def rect(self, x: float, y: float, w: float, h: float, fill: str, radius: float = 0) -> None:
        box = [x * SS, y * SS, (x + w) * SS, (y + h) * SS]
        if radius:
            self.d.rounded_rectangle(box, radius=radius * SS, fill=fill)
        else:
            self.d.rectangle(box, fill=fill)

    def circle(self, cx: float, cy: float, r: float, fill: str | None = None,
               outline: str | None = None, width: float = 0) -> None:
        box = [(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS]
        self.d.ellipse(box, fill=fill, outline=outline, width=round(width * SS))

    def stroke(self, pts: list[tuple[float, float]], color: str, width: float, round_cap: bool = True) -> None:
        self.d.line(self._p(pts), fill=color, width=round(width * SS), joint="curve")
        if round_cap:
            for x, y in (pts[0], pts[-1]):
                self.circle(x, y, width / 2, fill=color)

    def arc(self, cx: float, cy: float, r: float, a0: float, a1: float, color: str, width: float) -> None:
        """Arc from a0 to a1 radians (canvas convention: clockwise from +x), round caps."""
        n = 48
        pts = [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
               for i in range(n + 1)]
        self.stroke(pts, color, width)

    def grid(self, step: int, color: str) -> None:
        for x in range(0, self.w, step):
            self.d.line([(x * SS, 0), (x * SS, self.h * SS)], fill=color, width=SS)
        for y in range(0, self.h, step):
            self.d.line([(0, y * SS), (self.w * SS, y * SS)], fill=color, width=SS)

    def text(self, x: float, y: float, s: str, size: float, weight: int, fill: str,
             anchor: str = "la", tracking: float = 0) -> float:
        """Draw text; anchor uses PIL codes (la=top, lm=middle, ls=baseline, mm=centre). Returns width."""
        font = inter(size * SS, weight)
        if not tracking:
            self.d.text((x * SS, y * SS), s, font=font, fill=fill, anchor=anchor)
            return self.d.textlength(s, font=font) / SS
        cx = x * SS
        for ch in s:
            self.d.text((cx, y * SS), ch, font=font, fill=fill, anchor=anchor)
            cx += self.d.textlength(ch, font=font) + tracking * SS
        return cx / SS - x

    def width(self, s: str, size: float, weight: int) -> float:
        return self.d.textlength(s, font=inter(size * SS, weight)) / SS

    def image(self) -> Image.Image:
        return self.im.resize((self.w, self.h), Image.LANCZOS)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image().save(path, optimize=True)
        return path


def inter(size: float, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / "Inter-Variable.ttf"), max(1, round(size)))
    font.set_variation_by_name(WEIGHTS[weight])
    return font


def bezier(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float],
           p3: tuple[float, float] | None = None, n: int = 40) -> list[tuple[float, float]]:
    """Sample a quadratic (3 points) or cubic (4 points) bezier."""
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        if p3 is None:
            out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
        else:
            out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                        u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


# ---------- Northstar mark, logo, cover, portal image ----------

def mark(c: Canvas, x: float, y: float, s: float, fg: str = WHITE) -> None:
    """Northstar 'N' mark with a coral tip; s = height in px."""
    w, t = s * 0.78, s * 0.2
    c.poly([(x, y + s), (x, y), (x + t, y), (x + w - t, y + s * 0.62), (x + w - t, y + s * 0.28),
            (x + w, y + s * 0.28), (x + w, y + s), (x + w - t, y + s), (x + t, y + s * 0.38), (x + t, y + s)], fg)
    c.poly([(x + w - t * 1.25, y + s * 0.28), (x + w - t / 2, y - s * 0.12), (x + w + t * 0.25, y + s * 0.28)], CORAL)


def triangle(c: Canvas, ax: float, ay: float, base: float, half: float, th: float) -> None:
    c.poly([(ax, ay), (ax + half, base), (ax + half - th, base), (ax, ay + th * 1.9),
            (ax - half + th, base), (ax - half, base)], CORAL)


def logo(n: int = 1024) -> Canvas:
    c = Canvas(n, n, NAVY)
    s = n * 0.46
    mark(c, (n - s * 0.78) / 2, (n - s) / 2 + s * 0.05, s)
    return c


def cover(title1: str = "NORTHSTAR", title2: str = "SUMMIT", sub: str = "AUSTIN, TX · OCT 26 – 29") -> Canvas:
    w, h = 2160, 1080
    c = Canvas(w, h, NAVY)
    c.grid(48, NAVY_GRID)
    triangle(c, w * 0.8, h * 0.14, h * 1.02, w * 0.19, w * 0.085)
    mark(c, w * 0.06, h * 0.12, h * 0.075)
    c.text(w * 0.06, h * 0.56, title1, 135, 900, WHITE)
    c.text(w * 0.06, h * 0.69, title2, 135, 900, CORAL)
    c.text(w * 0.062, h * 0.845, sub, 37, 600, MUTED, tracking=7)
    return c


def portal_image() -> Canvas:
    """Client-portal sign-in image v2 (triangle sits above the text, no overlap)."""
    w, h = 1600, 1800
    c = Canvas(w, h, NAVY)
    c.grid(48, NAVY_GRID)
    triangle(c, w * 0.62, h * 0.16, h * 0.60, w * 0.30, w * 0.12)
    mark(c, w * 0.09, h * 0.08, h * 0.06)
    c.text(w * 0.09, h * 0.68, "NORTHSTAR", 150, 900, WHITE)
    c.text(w * 0.09, h * 0.77, "COLLECTIVE", 150, 900, CORAL)
    c.text(w * 0.095, h * 0.88, "EVENTS · COURSES · COMMUNITY", 44, 600, MUTED, tracking=8)
    return c


# ---------- Exhibitor icons, logos, ads ----------

def icon(c: Canvas, x: float, y: float, s: float, color: str, shape: str) -> None:
    """Rounded-square exhibitor icon with a white glyph; glyphs are drawn on a 210px grid."""
    c.rect(x, y, s, s, color, radius=s * 0.23)
    k, lw = s / 210, s * 0.105
    cx, cy = x + s / 2, y + s / 2

    def P(dx: float, dy: float) -> tuple[float, float]:
        return (cx + dx * k, cy + dy * k)

    if shape == "wave":
        c.stroke(bezier(P(-70, 10), P(-35, -50), P(-5, 50), P(25, -5))
                 + bezier(P(25, -5), P(45, -40), P(60, -20), P(70, -10))[1:], WHITE, lw)
    elif shape == "anchor":
        c.arc(cx, cy + 5 * k, 55 * k, 0.15 * math.pi, 0.85 * math.pi, WHITE, lw)
        c.stroke([P(0, -60), P(0, 60)], WHITE, lw)
        c.circle(cx, cy - 62 * k, 14 * k, outline=WHITE, width=lw)
    elif shape == "pine":
        c.poly([P(0, -75), P(60, 30), P(-60, 30)], WHITE)
        c.rect(cx - 10 * k, cy + 30 * k, 20 * k, 40 * k, WHITE)
    elif shape == "loop":
        c.circle(cx - 28 * k, cy, 40 * k, outline=WHITE, width=lw)
        c.circle(cx + 28 * k, cy, 40 * k, outline=WHITE, width=lw)
    elif shape == "leaf":
        c.poly(bezier(P(-55, 55), P(-60, -60), P(60, -60)) + bezier(P(60, -60), P(55, 55), P(-55, 55))[1:], WHITE)
        c.stroke([P(-45, 45), P(40, -40)], color, 10 * k)


def exhibitor_logo(name: str, color: str, shape: str) -> Canvas:
    w, h = 1200, 600
    c = Canvas(w, h, WHITE)
    s, x = 210, 110
    icon(c, x, (h - s) / 2, s, color, shape)
    fs = 112
    while c.width(name, fs, 800) > w - x - s - 110 and fs > 40:
        fs -= 4
    c.text(x + s + 50, h / 2 + 4, name, fs, 800, LOGO_INK, anchor="lm")
    return c


def ad_home() -> Canvas:
    """Harbor Payments full-screen home ad (1080x1920)."""
    w, h = 1080, 1920
    c = Canvas(w, h, "#0f766e")
    c.circle(w * 0.95, h * 0.18, 520, fill="#115e59")
    c.rect(90, 140, 150, 150, WHITE, radius=150 * 0.23)
    icon(c, 90, 140, 150, "#0b5e57", "anchor")
    c.text(270, 215, "Harbor Payments", 64, 800, WHITE, anchor="lm")
    for i, line in enumerate(["Get paid", "on the", "spot."]):
        c.text(90, 900 + i * 170, line, 150, 800, WHITE, anchor="ls")
    for i, line in enumerate(["Tap to pay at your booth.", "Money lands the next morning."]):
        c.text(90, 1430 + i * 72, line, 52, 500, "#ccfbf1", anchor="ls")
    c.rect(90, 1640, 560, 130, WHITE, radius=65)
    c.text(140, 1725, "Visit Booth B-22", 52, 800, "#0f766e", anchor="ls")
    return c


def ad_banner(w: int, h: int) -> Canvas:
    """Brightwave CRM page banner; wide (>6:1) = web, otherwise mobile."""
    c = Canvas(w, h, "#eef4ff")
    c.rect(0, 0, round(h * 0.06), h, "#2563eb")
    s, pad = h * 0.56, h * 0.3
    icon(c, pad, (h - s) / 2, s, "#2563eb", "wave")
    wide = w / h > 6
    tx = pad + s + h * 0.22
    if wide:
        c.text(tx, h / 2, "Close more referrals with Brightwave CRM", h * 0.3, 800, LOGO_INK, anchor="lm")
        bw, bh = h * 2.6, h * 0.48
        bx, by = w - bw - h * 0.4, (h - bh) / 2
        c.rect(bx, by, bw, bh, "#2563eb", radius=bh / 2)
        c.text(bx + bw / 2, h / 2, "See it at Booth B-21", h * 0.2, 800, WHITE, anchor="mm")
    else:
        c.text(tx, h * 0.4, "Close more referrals", h * 0.2, 800, LOGO_INK, anchor="lm")
        c.text(tx, h * 0.68, "Brightwave CRM · Booth B-21", h * 0.15, 600, "#2563eb", anchor="lm")
    return c


def slug(name: str) -> str:
    return re.sub(r"[^a-z]+", "-", name.lower()).strip("-")


def render_all() -> list[Path]:
    big = logo()
    written = [big.save(OUT / "logo-square.png")]
    for size, name in ((200, "logo-200.png"), (64, "favicon-64.png")):
        path = OUT / name
        big.image().resize((size, size), Image.LANCZOS).save(path, optimize=True)
        written.append(path)
    written.append(cover().save(OUT / "cover-northstar-summit.png"))
    written.append(portal_image().save(OUT / "portal-image.png"))
    for ex in WORLD["exhibitors"]:
        written.append(exhibitor_logo(ex["name"], ex["color"], ex["mark"]).save(OUT / "logos" / f"{slug(ex['name'])}.png"))
    written.append(ad_home().save(OUT / "ads" / "harbor-payments-home.png"))
    written.append(ad_banner(2520, 180).save(OUT / "ads" / "brightwave-banner-web.png"))
    written.append(ad_banner(720, 180).save(OUT / "ads" / "brightwave-banner-mobile.png"))
    return written


if __name__ == "__main__":
    for p in render_all():
        print(p.relative_to(ROOT))
    sys.exit(0)
