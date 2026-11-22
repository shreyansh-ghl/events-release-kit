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
- Video screens: for each chapter, the before/after laptop captures (any page height; tall pages can scroll) and
  phone screens. A screen can serve a card and the video.

## 2. Web capture (Builder, public page, Client Portal)
1. Navigate in the author's Chrome to the plan's URL; follow the steps. Read-only outside Northstar; Cancel dialogs.
2. Clean the frame: hide dev overlays with in-page CSS; park the cursor in a corner (`hover` at the bottom-right).
3. Get the viewport size (`window.innerWidth/innerHeight` via JS), then `python3 -I KIT/scripts/tiles.py grid W H`.
4. For each region: `computer zoom` with `save_to_disk: true`, `scale: 1`. Keep the returned paths.
5. `python3 -I KIT/scripts/tiles.py stitch RUN/shots/raw/web/<id>.png <path>@x,y,w,h ...` → ~2x capture.
6. Long page (video scroll): `window.scrollTo(0, Y)`, read `scrollY`, zoom tiles with y + scrollY, repeat, stitch once.
7. Look at the result. Any real name, brand or staging junk → don't use it; fix the data in Northstar or reframe.

## 3. Mobile capture (the author's phone)
Write `RUN/shots/phone-shotlist.md`: numbered, one line of exact taps per shot, signed in as Jordan Blake. Show it in
chat, then `run.py ask RUN "Send phone shots p1–pN to shots/raw/phone"`. The author AirDrops iPhone screenshots
(full screen, portrait) and saves them as `p1.png`, `p2.png` … in `RUN/shots/raw/phone/`. Check each is portrait at
≈ 2.17 : 1 and shows the right screen; clear the ask when all are in.

## 4. Cards
One spec per card in `RUN/shots/specs/NN-<id>.json`, rendered with
`python3 -I KIT/cards/render_card.py RUN/shots/specs/NN-<id>.json RUN/shots/final/NN-<id>.png`.
- Hero: kicker `NEW IN HIGHLEVEL EVENTS`, dot `blue`, headline with exactly one `*italic*` phrase, one-line subhead,
  `frame.url` = the real path with the Northstar domain (`members.northstarcollective.com/...` for the portal).
- Sections: kicker `0N · TOPIC`, dots cycle green → amber → blue, headline `"Line one\n*line two*."` (≤ 2 lines),
  subhead ≤ 3 lines, optional `bullets`; stage = `phones` (1–3, captions in caps) or `layers` for overlaps/tilts.
- The renderer refuses broken copy and overflow; fix the text, don't fight the check.
- `run.py set RUN shots=<count>`.
