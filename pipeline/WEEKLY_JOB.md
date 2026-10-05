# Weekly job: make, schedule and report on @tapstudio.kg posts

Runs every Sunday. Work in `C:\Users\doktu\code\tapstudio-media`. If that folder is missing, run
`gh repo clone dokturbekov-a-auca-2022/tapstudio-media C:\Users\doktu\code\tapstudio-media` first.
Start with `git pull`.

- Metricool brand: `6929381` (Instagram only, timezone `Asia/Bishkek`)
- Media base URL: `https://dokturbekov-a-auca-2022.github.io/tapstudio-media/`
- Plan doc (Claude Doc): https://claude.ai/code/artifact/b024cc69-a31a-4f6f-9aee-f0cdc7fa2866

The owner chose this setup: posts are scheduled to publish automatically, and the owner gets a preview
they can cancel from Metricool's planner. Keep it that way unless they say otherwise.

## 1. Report on last week

1. Pull Metricool for last Monday 00:00 to Sunday 23:59 (Bishkek time): `IGEV01` (followers, last value),
   `IGEV43` (followers gained), `IGEV06` (reach), `IGEV37` (posts). For each reel, pull `IGRE02`, `IGRE03`,
   `IGRE11` (reach) and `IGRE23` (views). For each carousel or image post, pull `IGPO02`, `IGPO03`, `IGPO14` and `IGPO12`.
2. Call `getScheduledPosts` for last week. A post that is still listed after its time didn't publish.
   Report it, and don't reschedule it on your own.
3. Write `reports/<sunday date>.md`, which stays local because `reports/` is gitignored. If the docs tools are available,
   also fill that week's column in the plan doc's "Weekly numbers" table (rows: Posts published, Average reach per reel,
   Followers gained). Leave the other rows to the owner.

## 2. Write next week's posts

1. Read `plan/calendar.md` and take the rows dated next Monday to Sunday. If there are none, add 4 rows for the
   standard slots: Tue 19:00 reel, Wed 19:00 carousel, Thu 19:00 reel, Sat 12:00 reel. Use this content mix:
   site reviews 40%, problems of businesses that sell only through Instagram 25%, process 20%, proof and offers 15%.
   Don't repeat a topic from the last 4 weeks, and lean toward hooks like those of the best-reaching reels in the report.
2. For each row, create `posts/<date>-<slug>/post.json` modelled on the existing posts. Available layouts:
   - carousel slides: `cover`, `point` (`num`, `title`, `body`), `cta`
   - reel scenes: `hook`, `point`, `chat` (`messages` from client, shop or divider), `page` (phone landing mockup with
     `rows`), `beforeafter` (`before` and `after` lists), `cta`
   - `*word*` makes a word brand blue
3. Rules for every post:
   - Russian, the studio's «мы» voice, plain and specific. Don't use gendered first-person verbs (the owner's gender
     isn't known).
   - End with «Напишите «РАЗБОР» в Директ». Use 4 hashtags, always including #сайтыбишкек #бизнесбишкек #сайтдлябизнеса.
   - No invented statistics, results, clients or testimonials. Any made-up business is labelled «Концепт».
   - A real business's site or profile only if it's listed in `plan/permissions.md`.
   - Prices only if `plan/prices.md` exists, and only as written there.
   - No `___` and no `[brackets]` anywhere. `render.py` refuses those.
   - 2–10 slides per carousel. Reels of 5–7 scenes, about 15–25 seconds.

## 3. Render and check

1. Run `python pipeline/render.py posts/<id> ...` for the new posts.
2. Look at every slide and every reel cover with the Read tool. For each reel, pull 2 frames with
   `ffmpeg -ss <t> -i reel.mp4 -frames:v 1 .preview/<name>.jpg` and look at those too.
   Fix any text that runs off the edge, overlaps something or is hard to read, then render again.

## 4. Publish the media

1. `git add posts plan && git commit -m "Posts for week of <monday>" && git push`
2. Wait until every media URL (`<base>/posts/<id>/<file>`) returns HTTP 200. GitHub Pages takes about 1–2 minutes.

## 5. Schedule in Metricool

Use `createScheduledPost` with `blogId` `6929381`. The `date` is the post's `publish_at` with `+06:00`.

Carousel `info`:
```json
{"autoPublish": true, "draft": false, "descendants": [], "firstCommentText": "", "hasNotReadNotes": false,
 "media": ["<base>/posts/<id>/slide-01.jpg", "..."], "mediaAltText": [],
 "providers": [{"network": "instagram"}],
 "publicationDate": {"dateTime": "<publish_at>", "timezone": "Asia/Bishkek"},
 "shortener": false, "smartLinkData": {"ids": []}, "text": "<caption>",
 "instagramData": {"type": "POST"}}
```

Reel `info`: the same, except `"media": ["<base>/posts/<id>/reel.mp4"]`,
`"videoThumbnailUrl": "<base>/posts/<id>/cover.jpg"`, and `"instagramData": {"type": "REEL", "showReelOnFeed": true}`.

Save the returned id, uuid and planner URL into the post's `post.json` under `"metricool"`. Set the row's status
in `plan/calendar.md` to `scheduled`, then commit and push.

## 6. Send the preview

Send the owner one message with PushNotification, if that tool is available. Otherwise put it in the run summary.
It should list, for each post: day and time, topic, and the link to its cover or first slide. Then add:
«Не нравится пост — удалите его в планировщике Metricool до публикации.»
Also say what failed or was skipped, and why.

## 7. Leads for the week (only if a browser tool is available)

Find 10 businesses in Bishkek, on 2GIS or Google Maps, with no website or a weak one. Good fits are flower shops, beauty
salons, dental clinics, cafés, furniture and clothing stores. For each one, write a personal first message, following the
"Outreach kit" templates in the plan doc, and mention one specific thing you saw. Save the list to `leads/<sunday date>.md`,
which stays local because it's gitignored. Never send messages yourself: the owner sends them.

## If something breaks

Leave anything that isn't ready unscheduled. Never publish a post you haven't looked at. Say exactly what went wrong
in the preview message.
