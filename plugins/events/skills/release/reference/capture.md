# Capture + cards

## 1. Shot plan (`RUN/shots/plan.json`)
Plan before capturing; the post holds ≤ 9 images, so plan cards first, then what the video needs.

```json
[
  {"id": "hero", "surface": "builder", "use": ["card", "video"], "what": "Coupon list with three codes",
   "url": "https://staging.gohighlevel.com/v2/location/.../memberships/events/...", "steps": ["Open Tickets tab", "Click Coupons"]},
  {"id": "p1", "surface": "mobile", "use": ["card"], "what": "Checkout with coupon applied",
   "how": "App as Jordan → Northstar Summit → Get tickets → VIP → Apply code NORTHSTAR20"}
]
```
- Card order: hero (`layout: hero`, browser frame) first, then 2–8 section cards (`layout: side`).
- Video screens come from the story plan below, not from the card list. A screen can still serve a card.

## 2. Video: one story, every click real
A video that narrates features over still screens feels like "reading pointers". What lands: **one concrete journey**
in 2–3 acts, where every step is a real click and the screen really changes. Plan it before capturing anything.

1. **Pick the journey.** Follow one record through the feature, end to end, and find the payoff moment: the thing that
   happens without anyone doing it by hand. Events in funnels: build the page once → publish a *new* event → it is on
   the site, in date order, with no page edit → a visitor gets tickets there.
2. **Write the click list** in `RUN/shots/story.md`: per act, the ordered states. Each state = what is on screen + the
   click (target) that leads to the next state. Include the "before" of every change (the empty slot, the purple
   button, the Draft badge), because the cut from before to after is the motion.
3. **Seed the change, don't fake it.** If the payoff needs something new to appear, create it in Northstar as a draft
   (author's yes first) and publish it on camera. If a step needs a clean start (an element already on the page),
   remove it and rebuild it on camera (author's yes first).
4. **Capture every state** with the steps in §3 into `RUN/shots/raw/motion/NN-<state>.png`, in order. Click for real,
   wait for the result, park the cursor, capture. When only part of the screen changed, re-zoom just those tiles and
   `tiles.py patch` them onto the previous state, so before/after stay a real pair.
5. **Log each state** in `RUN/shots/raw/motion/MANIFEST.md`: `- NN-<state>.png: what it shows; next click <target> at
   px x,y` (screenshot px of the 2x frame = CSS px × 2). The video session builds its cursor and swaps from this file.
6. **Show the storyboard** at checkpoint A: `tiles.py sheet RUN/qa/story-board.png <key states> --cols 4`.

What can't move: a held drag is drawn as press → glide → press; a page reload is a hard cut; the browser URL bar can't
change mid-shot. Say these in the plan, don't hide them.

## 3. Web capture (Builder, public page, Client Portal)
1. Navigate in the author's Chrome to the plan's URL; follow the steps. Read-only outside Northstar; Cancel dialogs.
   Size the window so the viewport is the laptop template's 1.668:1 (1381×828 CSS): `resize_window` to width 1381;
   check `innerWidth/innerHeight` with JS. A fullscreen window ignores the resize: open the page in a tab of the
   resized window instead. Every capture of one run uses the same viewport.
2. Clean the frame: hide dev overlays and staging-only menu items with in-page CSS (display only); park the cursor in
   a corner (`hover` at the bottom-right); let images finish loading (soft covers mean wait and re-zoom).
3. `python3 -I KIT/scripts/tiles.py grid 1381 828 2 2` prints each tile as `zoom x0,y0,x1,y1` (pass that to the zoom
   action) and `stitch @x,y,w,h` (pass that to stitch/patch).
4. For each region: `computer zoom` with `save_to_disk: true`, `scale: 1`. Keep the returned paths. A half-screen tile
   comes back below 2x; keep tiles at a quarter of the viewport or smaller.
5. `python3 -I KIT/scripts/tiles.py stitch RUN/shots/raw/<web|motion>/<id>.png <path>@x,y,w,h ...` → 2762×1656.
6. Long page (video scroll): `window.scrollTo(0, Y)`, read `scrollY`, zoom tiles with y + scrollY, repeat, stitch once.
7. Look at the result. Any real name, brand or staging junk → don't use it; fix the data in Northstar or reframe.

## 4. Mobile capture (the author's phone)
Write `RUN/shots/phone-shotlist.md`: numbered, one line of exact taps per shot, signed in as Jordan Blake. Show it in
chat, then `run.py ask RUN "Send phone shots p1–pN to shots/raw/phone"`. The author AirDrops iPhone screenshots
(full screen, portrait) and saves them as `p1.png`, `p2.png` … in `RUN/shots/raw/phone/`. Check each is portrait at
≈ 2.17 : 1 and shows the right screen; clear the ask when all are in.

## 5. Cards
One spec per card in `RUN/shots/specs/NN-<id>.json`, rendered with
`python3 -I KIT/cards/render_card.py RUN/shots/specs/NN-<id>.json RUN/shots/final/NN-<id>.png`.
- Hero: kicker `NEW IN HIGHLEVEL EVENTS`, dot `blue`, headline with exactly one `*italic*` phrase, one-line subhead,
  `frame.url` = the real path with the Northstar domain (`members.northstarcollective.com/...` for the portal).
- Sections: kicker `0N · TOPIC`, dots cycle green → amber → blue, headline `"Line one\n*line two*."` (≤ 2 lines),
  subhead ≤ 3 lines, optional `bullets`; stage = `phones` (1–3, captions in caps) or `layers` for overlaps/tilts.
- The renderer refuses broken copy and overflow; fix the text, don't fight the check.
- `run.py set RUN shots=<count>`.
