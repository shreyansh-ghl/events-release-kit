# Post the review thread (after the author says "post it")

1. Chrome, the author's own Slack tab → channel `#events-core-internal`.
2. Paste the text from `RUN/note/review-post.md` into the composer. For each @mention, type `@` + the first letters and
   pick the person/group from Slack's own dropdown (a pasted "@name" does not notify anyone).
3. Attach the images from `RUN/shots/final/` in order, then `RUN/video/video.mp4` (≤ 10 files total).
4. Wait until every upload finishes, check the composer matches the approved pack, then send. "Post it" is the one
   approval; if anything differs from what was approved at checkpoint B, stop and ask instead.
5. Copy the message link (hover → ⋯ → Copy link), report it, `run.py set RUN post_url=<link>`.
Never post from a bot, never to another channel, never edit someone else's message.
