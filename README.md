# tapstudio-media

Instagram content for [@tapstudio.kg](https://www.instagram.com/tapstudio.kg/), made and scheduled automatically.

- `posts/<date>-<slug>/post.json` describes one post: date, caption, and slides (carousel) or scenes (reel).
- `pipeline/render.py` turns a post folder into Instagram-ready media: JPEG slides, or an MP4 reel plus a cover.
- The media is served by GitHub Pages, so Metricool can fetch it when it schedules the post.
- `pipeline/WEEKLY_JOB.md` is what the weekly Claude job follows every Sunday.
- `plan/calendar.md` lists the topics coming up.

Render locally:

```
python pipeline/render.py posts/2026-10-08-price-in-direct
```

Needs Python 3, ffmpeg, and Chrome or Edge.
