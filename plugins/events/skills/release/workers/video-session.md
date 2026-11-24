# Video session (runs in parallel with the note session)

You make the narrated release video for one Events release. You are given `KIT` (the events-release skill folder) and
`RUN` (the run folder). Checkpoint A is already approved: the story, headline and screens are settled.

## Rules
- Work only inside `RUN/video/` and `RUN/video-spec.json`. Never edit `KIT`; if the template is wrong, report it.
- Never use a browser, never post, never message anyone. The main session talks to the author.
- Real UI only: use the captured screens in `RUN/shots/raw/`. If a moment has no screen, say it in the voice only.
- Tell a story, not a feature tour. Follow the journey in `RUN/shots/story.md` and the states in
  `RUN/shots/raw/motion/MANIFEST.md` in order. Each line narrates the click on screen under it. A line that only lists
  capabilities over a still screen ("Pick a layout: grid, list…") is the "reading pointers" feel the author rejected.
- Read `KIT/reference/guardrails.md` first. Tone: professional, warm, confident; no jokes.
- Progress: `python3 -I KIT/scripts/run.py session RUN video doing --step "<step>"` at each step below; `done` at the end
  (or `blocked --note "why"`).

## Read first
`RUN/brief.md` (facts, interview, story, checkpoint A notes) · `RUN/shots/story.md` (acts + click list) ·
`RUN/shots/raw/motion/MANIFEST.md` (every captured state, next click at px x,y) · `KIT/voice/directions.md` ·
`KIT/video/README.md` · `KIT/video/examples/repro/spec.json` (a full working spec) · `KIT/northstar/world.json`.

## 1. Script (step "script")
Write `RUN/video/vo-script.json`: `[{"id": "c1", "text": "...", "direction": "..."}]`, 30–120 s in total.
- **Cold open (ink):** two short beats that set up the journey: what the user already has, then what they need
  ("You've got the events." / "Now give them a home: one page on your site that lists them all."). From the brief,
  never invented. Avoid the stock pain + "Not anymore." turn; the author found it weak.
- **Title:** "Meet the Events' <Feature>, …" (one line). Headline on screen: `Introducing the *Events' <Feature>*.`
  (the film's wording; keep "the").
- **Chapters = the story's acts** (2–3), named for what the user does ("BUILD IT ONCE", "ADD AN EVENT", "YOUR
  VISITORS BOOK"), label ≤ 3 words in caps style. Each shot = one or a few real clicks + 1 line that says what that
  click does for the user ("Publish it the way you always do."). Land the payoff moment on its own line, over the
  before → after cut ("And it's already on your site, in date order."). Use spoken turns between acts ("Now plan your
  next event.").
- **End:** "The Events' <Feature>, from HighLevel. <payoff>." + the availability line. Availability (interview) =
  Everyone → "Available now."; rolling out, feature flag or specific plans → "Rolling out now.". The end card's
  `available` field says exactly the same words.
- Lines are 3–14 words; directions come from `KIT/voice/directions.md` (copy the closest one, adjust lightly).
- Say the product as "Events'" + the feature name. Claim only what the brief says.

**Stop here.** Mark `run.py session RUN video doing --step "script: waiting for go"` and report the script as a table:
id · text · direction · the motion states and clicks it plays over. The author approves the script before any voice
is made; you will be resumed with a go or with changes.

## 2. Voice (step "voice")
`python3 -I KIT/voice/vo.py script RUN/video/vo-script.json RUN/video/vo/` → wavs + `vo-manifest.json`.
It prints each line's pace and flags `PACE` outside 1.8–4.2 words/s. For a flagged line change the direction (or
tighten the text) in `vo-script.json` and regenerate only it: `vo.py script RUN/video/vo-script.json RUN/video/vo/ --only s2`.
The seed is fixed, so the same text + direction always gives the same take. Nobody can listen inside the session: say in
your report which lines the author should listen to (product names, unusual words).

## 3. Spec (step "spec")
Write `RUN/video-spec.json` (paths relative to `RUN`; format in `KIT/video/scripts/release_video.py`):
- `"vo_manifest": "video/vo/vo-manifest.json"`; screens as `shots/raw/motion/<state>.png` (the story frames, in
  MANIFEST order), plus `shots/raw/phone/<id>.png`. Use `shots/raw/web/` card captures only when a state has no motion
  frame.
- Clicks come from the MANIFEST: cursor to the listed px, `click`, then a `swaps` entry to the next state ~0.05 s later.
  Nudge a click point to the lower right of its button so the pointer doesn't cover the label. A drag is press → glide
  → press; a reload is a hard cut between two shots. Push in on the part of the screen that changed.
- Scenes in house order: `cold_open` → `title` → `chapter`… → (optional `interstitial`) → `end`.
- Cold open: `prop` is optional (a real captured screen of the old way). Use `pile` only for a "lost in the noise" story;
  its rows come from `world.json → inbox` (from + subject), the hero is the email/screen that got lost.
- Title laptop = the first chapter's first screen, so the push-in is continuous.
- Camera: `python3 -I KIT/video/scripts/release_video.py frame <img_w> <x0> <y0> <x1> <y1> [scroll]` gives the key that
  frames a region of a laptop screenshot. Frame the card or panel that holds the control, not the control alone
  (a toggle alone hits the 3.0 zoom cap; its card gives the film's ~2.1). Home framing is `{"x": 960, "y": 540, "zoom": 1}`; the phone-focus framing
  from the film is `{"x": 1255, "y": 525, "zoom": 1.32}`.
- Cursor and tap coordinates are screenshot pixels. Every click or tap must show its real result: a `swaps` screen
  ~0.05 s later (captured, never drawn). No captured result → no click/tap; let the camera and voice carry it.
  Hold each result ~1 s before the camera moves on.
- Screen text (headline, end card, pile hero) must match what the captured screens show (event name, dates).
- Shot `min` gives room for actions; every action time must be inside the shot (the build refuses otherwise).

## 4. Check frames (step "stills")
`python3 -I KIT/video/scripts/release_video.py still RUN/video-spec.json RUN/video/build <t> ...` with all times in one
call: each shot start +1 s, every click/tap, each chapter start +1 s (label visible), the end card +3 s. It also writes
`RUN/video/build/stills/sheet.png`; look at that first. Look at every still: text fits, the pointer/finger lands on
the target, the camera frames the action, no real names or staging junk. Fix the spec and repeat.

## 5. Render (step "render")
`python3 -I KIT/video/scripts/release_video.py render RUN/video-spec.json RUN/video/build` → copy
`RUN/video/build/video.mp4` to `RUN/video/video.mp4`; `run.py set RUN video_mb=<size>`. It must be < 100 MB
(the renderer re-encodes if needed).

## Report back (≤ 12 lines)
Length, size, chapters (label + one line each), the full VO script, anything you were unsure of (claims, missing
screens). Mark `run.py session RUN video done`.

## Change requests after checkpoint B
You may be resumed with a change ("shorter intro", "say X not Y"). Change only what was asked, regenerate only the
affected VO lines, re-check stills around the change, re-render, report what changed.
