"""Build and render a house release video from a spec.

    python3 -I release_video.py build  spec.json out_dir/          # validate, resolve timing, write bed + props
    python3 -I release_video.py still  spec.json out_dir/ 12.5 ...  # PNG stills at those seconds
    python3 -I release_video.py render spec.json out_dir/          # out_dir/video.mp4 (<= 100 MB)
    python3 -I release_video.py frame <img_w> <x0> <y0> <x1> <y1> [scroll]
        camera key that frames a laptop-screenshot region (px) with a margin, e.g. {"x": 1131, "y": 567, "zoom": 2.2}

Spec (paths relative to the spec file; times in seconds):
  {
    "fps": 60,
    "vo_manifest": "vo/vo-manifest.json",   # from voice/vo.py: [{"id", "text", "duration"}], wavs next to it
    "scenes": [
      {"kind": "cold_open", "beats": [{"text": "Every event used to\\nend at registration.", "vo": "c1"}, ...],
       "payoff": {"text": "Not anymore.", "vo": "c3"},
       "prop": {"src": "screens/email.png", "width": 940, "pile": {"label": "unread", "to": 7452}}},
      {"kind": "title", "kicker": "HIGHLEVEL", "headline": "Introducing the *Events' Attendee App*.",
       "laptop": {"src": "screens/a.png", "url": "app.gohighlevel.com/..."}, "vo": ["t1"]},
      {"kind": "chapter", "label": "Your app", "shots": [
        {"vo": ["s1"], "min": 6,
         "laptop": {"src": "...", "url": "...", "scroll": [[0, 0], [3, 900]], "swaps": [{"t": 2.1, "src": "..."}]},
         "phone": {"src": "...", "enter": 4.0},
         "focus": [[0, "laptop"], [4.2, "phone"]],
         "camera": [{"t": 0, "x": 960, "y": 540, "zoom": 1}, {"t": 2, "x": 1300, "y": 560, "zoom": 2.2}],
         "cursor": [[0.8, 900, 300], [2.0, 2165, 540, "click"]],     # laptop screenshot px
         "tap": [[5.0, 300, 420]]}]},                                 # phone screenshot px
      {"kind": "interstitial", "word": "Agenda", "kicker": "AD SHOWN ON", "vo": []},
      {"kind": "end", "tagline": "Your event, in every\\nattendee's *pocket*.", "subline": "...",
       "available": "Available now", "where": "Turn it on in Events → Attendee App",
       "product": "Events' Attendee App", "vo": ["e1", "e2"]}
    ]
  }
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bed  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
MAX_MB = 100
TARGET_MB = 60
LABEL_COLORS = ["#1a89f1", "#37ca37", "#f9b803"]  # chapter bar colours cycle blue, green, amber (film)

# timing rules (seconds), tuned against the Attendee App film
COLD_LEAD, COLD_HOLD, TURN, PAYOFF_TAIL = 0.35, 0.65, 0.35, 0.9
TITLE_LEAD, TITLE_TAIL, TITLE_MIN = 0.9, 0.8, 3.5
SHOT_LEAD, VO_GAP, SHOT_TAIL = 0.4, 0.35, 0.5
END_LEAD, END_TAIL, END_MIN = 0.9, 2.2, 6.5
INTER_MIN = 2.2

BAD_TEXT = re.compile(r"[<>]|/p\b|&[a-z]+;|\s{2,}|\b(lorem|ipsum|todo|tbd)\b", re.I)


class SpecError(ValueError):
    """The video spec is invalid; the message says what to fix."""


class Resolver:
    def __init__(self, spec_path: Path) -> None:
        self.base = spec_path.resolve().parent
        self.spec = json.loads(spec_path.read_text())
        self.problems: list[str] = []
        self.files: dict[str, Path] = {}  # public path -> source file
        self.vo_lines: dict[str, dict] = {}
        self.cues: list[dict] = []
        manifest = self.spec.get("vo_manifest")
        if manifest:
            mpath = self.base / manifest
            if not mpath.is_file():
                self.problems.append(f"vo_manifest not found: {manifest}")
            else:
                for line in json.loads(mpath.read_text()):
                    wav = mpath.parent / f"{line['id']}.wav"
                    if not wav.is_file():
                        self.problems.append(f"vo wav missing for '{line['id']}': {wav.name}")
                    self.vo_lines[line["id"]] = {**line, "wav": wav}

    # ---- helpers ----
    def text(self, where: str, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            self.problems.append(f"{where}: text required")
            return ""
        if BAD_TEXT.search(value.replace("\n", " ")):
            self.problems.append(f"{where}: suspicious text {value!r} (HTML residue, double space or placeholder)")
        return value

    def img(self, where: str, src: object) -> dict:
        if not isinstance(src, str) or not src:
            self.problems.append(f"{where}: image src required")
            return {"src": "", "w": 1, "h": 1}
        path = (self.base / src).resolve()
        if self.base not in path.parents:
            self.problems.append(f"{where}: image must live inside the spec folder: {src}")
            return {"src": "", "w": 1, "h": 1}
        if not path.is_file():
            self.problems.append(f"{where}: image not found: {src}")
            return {"src": "", "w": 1, "h": 1}
        rel = "media/" + path.relative_to(self.base).as_posix()
        self.files[rel] = path
        with Image.open(path) as im:
            w, h = im.size
        return {"src": rel, "w": w, "h": h}

    def say(self, where: str, ids: object, at: float, sub: bool = True) -> float:
        """Place VO lines back to back from `at`; returns the time after the last line (no trailing gap)."""
        if ids is None:
            return at
        if isinstance(ids, str):
            ids = [ids]
        t = at
        for i, vid in enumerate(ids):
            line = self.vo_lines.get(vid)
            if not line:
                self.problems.append(f"{where}: unknown vo id '{vid}'")
                continue
            if i:
                t += VO_GAP
            src = f"vo/{vid}.wav"
            self.files[src] = line["wav"]
            self.cues.append({"id": vid, "src": src, "text": line["text"], "at": round(t, 3), "dur": float(line["duration"]), "sub": sub})
            t += float(line["duration"])
        return t

    # ---- scenes ----
    def cold_open(self, s: dict, t0: float, i: int) -> dict:
        where = f"scenes[{i}] cold_open"
        t = t0 + COLD_LEAD
        beats = []
        for j, b in enumerate(s.get("beats") or []):
            beats.append({"text": self.text(f"{where}.beats[{j}]", b.get("text")), "at": round(t, 3)})
            t = self.say(f"{where}.beats[{j}]", b.get("vo"), t, sub=False) + b.get("hold", COLD_HOLD)
        if not beats:
            self.problems.append(f"{where}: needs at least one beat")
        p = s.get("payoff") or {}
        pay_at = t + TURN
        end = self.say(f"{where}.payoff", p.get("vo"), pay_at, sub=False) + PAYOFF_TAIL
        out = {"kind": "cold_open", "from": t0, "dur": round(end - t0, 3), "beats": beats,
               "payoff": {"text": self.text(f"{where}.payoff", p.get("text")), "at": round(pay_at, 3)}}
        if s.get("prop"):
            pr = s["prop"]
            out["prop"] = {"img": self.img(f"{where}.prop", pr.get("src")), "width": pr.get("width", 940)}
            if pr.get("pile"):
                pl = pr["pile"]
                items = [{"from": self.text(f"{where}.pile.items[{k}].from", it.get("from")), "subject": self.text(f"{where}.pile.items[{k}].subject", it.get("subject"))}
                         for k, it in enumerate(pl.get("items") or [])]
                if len(items) < 6:
                    self.problems.append(f"{where}.prop.pile: needs at least 6 items (fictional senders + subjects)")
                hero = pl.get("hero") or {}
                out["prop"]["pile"] = {"label": pl.get("label", "unread"), "to": int(pl.get("to", 1000)), "items": items,
                                       "hero": {"from": self.text(f"{where}.pile.hero.from", hero.get("from")), "subject": self.text(f"{where}.pile.hero.subject", hero.get("subject"))}}
        return out

    def title(self, s: dict, t0: float, i: int) -> dict:
        where = f"scenes[{i}] title"
        end = self.say(where, s.get("vo"), t0 + TITLE_LEAD) + TITLE_TAIL
        headline = self.text(f"{where}.headline", s.get("headline"))
        if headline.count("*") != 2:
            self.problems.append(f"{where}.headline: needs exactly one *italic* phrase")
        lap = s.get("laptop") or {}
        return {"kind": "title", "from": t0, "dur": round(max(TITLE_MIN, end - t0), 3), "kicker": s.get("kicker", "HIGHLEVEL"),
                "headline": headline, "laptop": {"img": self.img(f"{where}.laptop", lap.get("src")), "url": lap.get("url", "")}}

    def chapter(self, s: dict, t0: float, i: int, n_chapter: int) -> dict:
        where = f"scenes[{i}] chapter"
        shots, t = [], t0
        for j, sh in enumerate(s.get("shots") or []):
            w = f"{where}.shots[{j}]"
            vo_end = self.say(w, sh.get("vo"), t + sh.get("vo_at", SHOT_LEAD))
            dur = round(max(sh.get("min", 0), vo_end - t + SHOT_TAIL), 3)
            shot: dict = {"from": round(t, 3), "dur": dur, "camera": sh.get("camera") or []}
            for dev in ("laptop", "phone"):
                if sh.get(dev):
                    d = dict(sh[dev])
                    d["img"] = self.img(f"{w}.{dev}", d.pop("src", None))
                    d["swaps"] = [{"t": sw["t"], "img": self.img(f"{w}.{dev}.swaps", sw.get("src"))} for sw in d.get("swaps") or []]
                    shot[dev] = d
            for key in ("focus", "cursor", "tap"):
                if sh.get(key):
                    shot[key] = sh[key]
            self.check_times(w, sh, dur)
            shots.append(shot)
            t += dur
        if not shots:
            self.problems.append(f"{where}: needs at least one shot")
        return {"kind": "chapter", "from": t0, "dur": round(t - t0, 3), "label": self.text(f"{where}.label", s.get("label")),
                "color": s.get("color", LABEL_COLORS[n_chapter % 3]), "shots": shots}

    def check_times(self, where: str, sh: dict, dur: float) -> None:
        times = [k.get("t", 0) for k in sh.get("camera") or []] + [k[0] for k in sh.get("cursor") or []] + [k[0] for k in sh.get("tap") or []]
        times += [k[0] for k in sh.get("focus") or []]
        for dev in ("laptop", "phone"):
            d = sh.get(dev) or {}
            times += [sw["t"] for sw in d.get("swaps") or []] + [k[0] for k in d.get("scroll") or []]
            if d.get("enter") is not None:
                times.append(d["enter"])
        late = [x for x in times if x > dur + 1e-6]
        if late:
            self.problems.append(f"{where}: action at {max(late)}s is after the shot ends ({dur}s); raise 'min' or move it")

    def interstitial(self, s: dict, t0: float, i: int) -> dict:
        end = self.say(f"scenes[{i}] interstitial", s.get("vo"), t0 + 0.5) + 0.8
        return {"kind": "interstitial", "from": t0, "dur": round(max(INTER_MIN, s.get("min", 0), end - t0), 3),
                "word": self.text(f"scenes[{i}].word", s.get("word")), "kicker": s.get("kicker"), "sub": s.get("sub")}

    def end(self, s: dict, t0: float, i: int) -> dict:
        where = f"scenes[{i}] end"
        end = self.say(where, s.get("vo"), t0 + END_LEAD) + END_TAIL
        out = {"kind": "end", "from": t0, "dur": round(max(END_MIN, end - t0), 3)}
        for k in ("tagline", "subline", "available", "where", "product"):
            out[k] = self.text(f"{where}.{k}", s.get(k))
        return out

    def resolve(self) -> dict:
        scenes, t, n_chapter = [], 0.0, 0
        for i, s in enumerate(self.spec.get("scenes") or []):
            kind = s.get("kind")
            if kind == "cold_open":
                r = self.cold_open(s, t, i)
            elif kind == "title":
                r = self.title(s, t, i)
            elif kind == "chapter":
                r = self.chapter(s, t, i, n_chapter)
                n_chapter += 1
            elif kind == "interstitial":
                r = self.interstitial(s, t, i)
            elif kind == "end":
                r = self.end(s, t, i)
            else:
                self.problems.append(f"scenes[{i}]: unknown kind {kind!r}")
                continue
            scenes.append(r)
            t = round(t + r["dur"], 3)
        kinds = [s["kind"] for s in scenes]
        if kinds[:1] and kinds[0] != "cold_open":
            self.problems.append("first scene must be the cold_open (house structure)")
        if "title" not in kinds:
            self.problems.append("a title scene is required")
        if kinds[-1:] != ["end"]:
            self.problems.append("last scene must be the end card")
        if self.problems:
            raise SpecError("video spec has problems:\n  - " + "\n  - ".join(self.problems))
        fps = int(self.spec.get("fps", 60))
        return {"fps": fps, "width": 1920, "height": 1080, "total": t, "scenes": scenes, "vo": self.cues, "bed": "bed.wav"}


def build(spec_path: Path, out_dir: Path) -> dict:
    """Validate + resolve the spec, lay out the render's public dir, synthesize the bed. Returns props."""
    r = Resolver(spec_path)
    props = r.resolve()
    public = out_dir / "public"
    if public.exists():
        shutil.rmtree(public)
    (public / "fonts").mkdir(parents=True)
    for f in (PROJECT / "public" / "fonts").iterdir():
        shutil.copy2(f, public / "fonts" / f.name)
    for rel, src in r.files.items():
        dst = public / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    bed.write_bed(props, public / "bed.wav")
    (out_dir / "props.json").write_text(json.dumps(props, indent=2))
    return props


def remotion(args: list[str]) -> None:
    cmd = ["npx", "remotion", *args]
    res = subprocess.run(cmd, cwd=PROJECT, text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"remotion failed:\n{res.stdout[-2000:]}\n{res.stderr[-2000:]}")


def stills(out_dir: Path, seconds: list[float]) -> list[Path]:
    props = json.loads((out_dir / "props.json").read_text())
    outs = []
    for s in seconds:
        frame = min(int(round(s * props["fps"])), int(props["total"] * props["fps"]) - 1)
        out = out_dir / "stills" / f"t{s:07.2f}.png"
        remotion(["still", "src/index.ts", "Release", str(out.resolve()), f"--frame={frame}",
                  f"--props={(out_dir / 'props.json').resolve()}", f"--public-dir={(out_dir / 'public').resolve()}"])
        outs.append(out)
    if len(outs) > 1:  # one sheet to review every check frame at once
        sys.path.insert(0, str(PROJECT.parent / "scripts"))
        import tiles  # noqa: PLC0415
        tiles.sheet(out_dir / "stills" / "sheet.png", [str(o) for o in outs])
    return outs


def render(out_dir: Path) -> Path:
    out = (out_dir / "video.mp4").resolve()
    remotion(["render", "src/index.ts", "Release", str(out), "--codec=h264", "--crf=20", "--audio-codec=aac",
              f"--props={(out_dir / 'props.json').resolve()}", f"--public-dir={(out_dir / 'public').resolve()}"])
    # loudness to the film's level (-18 LUFS integrated, -1.5 dBTP); picture is copied untouched
    loud = out.with_name("video-loud.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "copy", "-af", "loudnorm=I=-18:TP=-1.5:LRA=7",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(loud)], check=True)
    os.replace(loud, out)
    mb = out.stat().st_size / 1e6
    if mb > MAX_MB:  # re-encode to the target size; release notes cap a video at 100 MB
        props = json.loads((out_dir / "props.json").read_text())
        kbps = int(TARGET_MB * 8000 / props["total"]) - 192
        small = out.with_name("video-small.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k",
                        "-bufsize", f"{2 * kbps}k", "-c:a", "aac", "-b:a", "192k", str(small)], check=True)
        os.replace(small, out)
    return out


# laptop viewport in world px (must match src/geometry.ts)
VIEWPORT_X, VIEWPORT_Y, VIEWPORT_W = 385, 282, 1151


def frame(img_w: float, x0: float, y0: float, x1: float, y1: float, scroll: float = 0.0, margin: float = 0.85) -> dict:
    """Camera key centring a laptop-screenshot region, zoomed so it fills `margin` of the frame (zoom 1..3)."""
    k = VIEWPORT_W / img_w
    cx = VIEWPORT_X + (x0 + x1) / 2 * k
    cy = VIEWPORT_Y + ((y0 + y1) / 2 - scroll) * k
    zoom = margin * min(1920 / max(1.0, (x1 - x0) * k), 1080 / max(1.0, (y1 - y0) * k))
    return {"x": round(cx), "y": round(cy), "zoom": round(min(3.0, max(1.0, zoom)), 2)}


def main(argv: list[str]) -> int:
    if len(argv) >= 7 and argv[1] == "frame":
        nums = [float(a) for a in argv[2:9]]
        print(json.dumps(frame(*nums)))
        return 0
    if len(argv) < 4 or argv[1] not in ("build", "still", "render"):
        print(__doc__)
        return 2
    spec, out_dir = Path(argv[2]), Path(argv[3])
    try:
        props = build(spec, out_dir)
        print(f"built: {props['total']:.2f}s, {len(props['scenes'])} scenes, {len(props['vo'])} VO lines")
        if argv[1] == "still":
            for p in stills(out_dir, [float(x) for x in argv[4:]]):
                print(p)
        elif argv[1] == "render":
            out = render(out_dir)
            print(f"{out} ({out.stat().st_size / 1e6:.1f} MB)")
    except (SpecError, RuntimeError, FileNotFoundError) as err:
        print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
