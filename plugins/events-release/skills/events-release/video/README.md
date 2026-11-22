# Events release video (house template)

Remotion template for every Events release video: cold open on ink, title card, chapters over real
captured screens, end card. Same look, voice and music bed no matter who on the team runs it.

```bash
npm install                                                   # once (Remotion 4.0.535, pinned)
python3 -I scripts/release_video.py build  spec.json out/     # validate + resolve timing + music bed
python3 -I scripts/release_video.py still  spec.json out/ 4.6 16.8
python3 -I scripts/release_video.py render spec.json out/     # out/video.mp4, 1080p60, -18 LUFS, <= 100 MB
```

- **Spec format:** docstring of `scripts/release_video.py`; full example in `examples/repro/spec.json`
  (rebuilds the Attendee App film's opening, first chapter and end card; the result is `examples/repro/template-repro.mp4`).
- **Voice:** `voice/vo.py script ...` writes the wavs + `vo-manifest.json` the spec points at.
- **Timing comes from the voice:** each scene/shot lasts as long as its VO lines plus fixed lead/tail;
  camera, cursor, tap, swap and phone-enter times are seconds from the shot start and must fit inside it.
- **Screens are captured, never redrawn.** Laptop screenshots are page captures at any width (the browser bar is
  drawn by the template); phone screenshots are full-screen app captures.
- **Music + effects** (`scripts/bed.py`): synthesized locally from the film's soundtrack, ducked under the voice.

| Path | What |
|---|---|
| `src/scenes/` | ColdOpen (pain line, inbox pile, "Not anymore."), TitleCard, Chapter, Interstitial, EndCard |
| `src/components/` | Laptop, Phone, Hand (Finger + Pointer), Overlays (Subtitles + ChapterLabel), HighLevelMark, Grain, Serif |
| `src/geometry.ts` | World layout measured from the film; camera keys use these coordinates |
| `scripts/` | spec resolver + render, music bed, film comparison tool |
| `tests/` | `uvx --with pillow pytest tests -q` |
