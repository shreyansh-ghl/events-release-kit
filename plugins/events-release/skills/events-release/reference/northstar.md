# Northstar health check (every run, before capture)

All values come from `northstar/world.json`. Use the author's Chrome; they are signed in to staging.

1. Open `staging.builder_events_url`. The **Northstar Summit** row exists and shows Published.
   If the author isn't signed in, `run.py ask` them to sign in; never type credentials.
2. Open the event (`staging.event_id`). Dates are in the future. If they have passed, ask the author to approve moving
   them forward one year (same days and times), then do it and update `event.dates/start/end` in `world.json`.
3. Spot-check the data the shots will show: 8 speakers, 9 sessions, 6 exhibitors with logos, sponsors, both ads,
   ≥ 20 attendees, Jordan Blake registered (VIP). Missing or changed → tell the author what and offer to restore it
   from `world.json` (author approves each create).
4. If the surfaces include Client Portal or Mobile: open `staging.portal_url`; the Northstar Summit card shows
   "Registered" for Jordan. Mobile: the author signs in to the app as Jordan (`staging.persona`).
5. Feature data: if the feature needs data that isn't there (a coupon, a seat map, a workflow), propose the exact
   fictional records (names from the Northstar world), create them after a yes, and append them to `world.json`.
6. Never touch anything outside the Northstar sub-account. Brand art for new records: `scripts/northstar_brand.py`.
