#!/usr/bin/env python3
"""Render a TAP Studio post folder (post.json) into Instagram-ready media.

Carousels -> slide-01.jpg ... (1080x1350, JPEG: the Instagram API takes JPEG only)
Reels     -> reel.mp4 (1080x1920, H.264 + AAC, 30 fps) and cover.jpg

Usage:
    python pipeline/render.py posts/2026-10-07-mobile-mistakes [more post dirs...]

Text markup inside post.json strings:
    *word*  -> brand-blue accent
    \n      -> line break
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# abspath, not resolve(): resolve() can follow Windows app-container redirects to a different folder
ROOT = Path(os.path.abspath(__file__)).parent.parent

BG = "#0a0b10"
BLUE = "#096df9"
CREAM = "#f2efe8"
MUTED = "#c3c7d3"
QUIET = "#7d8193"
LINE = "#262938"
CARD = "#141621"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
]

# Seconds each reel scene stays on screen, by layout.
SCENE_SECONDS = {"hook": 2.6, "point": 3.2, "chat": 2.8, "page": 3.4, "beforeafter": 3.6, "cta": 3.4}
FADE = 0.35

PLACEHOLDER = re.compile(r"___|\[[^\]]*\]")


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.isfile(c) or shutil.which(c):
            return c if os.path.isfile(c) else shutil.which(c)
    sys.exit("Chrome or Edge not found")


def rich(text):
    """Escape, then turn *x* into accent spans and newlines into <br>."""
    t = html.escape(text or "")
    t = re.sub(r"\*(.+?)\*", r'<span class="accent">\1</span>', t)
    # keep a number with the next word and a dash with the word before it
    t = re.sub(r"(?<![\w&#;])(\d+) ", r"\1&nbsp;", t)
    t = t.replace(" —", "&nbsp;—")
    return t.replace("\n", "<br>")


def fit(text, sizes):
    """Pick a font size from [(max_chars, px), ...] by plain-text length."""
    n = len(re.sub(r"[*\n]", "", text or ""))
    for limit, px in sizes:
        if n <= limit:
            return px
    return sizes[-1][1]


LOGO = f"""<div class="logo"><svg width="46" height="52" viewBox="0 0 46 52">
<rect x="0" y="0" width="46" height="12" fill="#fff"/><rect x="16" y="0" width="14" height="40" fill="#fff"/>
<rect x="8" y="44" width="30" height="8" fill="{BLUE}"/></svg><span>TAP СТУДИЯ</span></div>"""

BASE_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=block');
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: {BG}; }}
body {{ position: relative; overflow: hidden; color: #fff; font-family: 'Manrope', 'Segoe UI', Arial, sans-serif; }}
.accent {{ color: {BLUE}; }}
.logo {{ display: flex; align-items: center; gap: 18px; font-weight: 800; font-size: 26px; letter-spacing: .1em; }}
.ring {{ position: absolute; border-radius: 50%; border: 56px solid {BLUE}; }}
.dot {{ position: absolute; border-radius: 50%; background: {BLUE}; }}
.kicker {{ color: {BLUE}; font-weight: 800; font-size: 30px; letter-spacing: .14em; text-transform: uppercase; }}
.title {{ font-weight: 800; line-height: 1.04; text-transform: uppercase; letter-spacing: -.005em; }}
.body {{ font-weight: 500; color: {MUTED}; line-height: 1.38; }}
.rule {{ height: 2px; background: {LINE}; }}
.pill {{ display: inline-block; background: {CREAM}; color: {BG}; font-weight: 800; border-radius: 999px; letter-spacing: .03em; text-transform: uppercase; }}
.tag {{ display: inline-block; border: 2px solid {LINE}; color: {QUIET}; border-radius: 999px; font-weight: 700; }}
.num {{ font-weight: 800; line-height: .9; color: {BLUE}; }}
.foot {{ display: flex; justify-content: space-between; align-items: center; color: {QUIET}; font-weight: 700; font-size: 28px; }}
"""


# ---------- carousel slides (1080 x 1350) ----------

def slide_html(s, index, total):
    layout = s.get("layout", "point")
    foot = f'<div class="foot"><span>@tapstudio.kg</span><span>{index}/{total}</span></div>'
    if layout == "cover":
        size = fit(s["title"], [(28, 104), (44, 90), (64, 78), (999, 68)])
        inner = f"""
<div class="ring" style="width:470px;height:470px;top:-150px;right:-150px"></div>
<div class="dot" style="width:210px;height:210px;top:-20px;right:-20px"></div>
<div class="frame">{LOGO}
  <div style="margin-top:auto">
    {f'<div class="kicker" style="margin-bottom:34px">{rich(s.get("kicker"))}</div>' if s.get("kicker") else ""}
    <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
    {f'<div class="rule" style="margin:56px 0 40px"></div><div class="body" style="font-size:40px">{rich(s.get("body"))}</div>' if s.get("body") else ""}
  </div>
  <div style="margin-top:64px;display:flex;justify-content:space-between;align-items:center">
    <span class="pill" style="font-size:28px;padding:22px 40px">{rich(s.get("button", "Листайте →"))}</span>
    <span style="color:{QUIET};font-weight:700;font-size:28px">{index}/{total}</span>
  </div>
</div>"""
    elif layout == "cta":
        size = fit(s["title"], [(30, 96), (50, 82), (999, 70)])
        inner = f"""
<div class="ring" style="width:420px;height:420px;top:-170px;right:-170px"></div>
<div class="frame">{LOGO}
  <div style="margin:auto 0">
    <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
    {f'<div class="body" style="font-size:42px;margin-top:40px;max-width:820px">{rich(s.get("body"))}</div>' if s.get("body") else ""}
    <div style="margin-top:64px"><span class="pill" style="font-size:34px;padding:28px 52px">{rich(s.get("button", "Напишите «РАЗБОР»"))}</span></div>
  </div>
  {foot}
</div>"""
    else:  # point
        size = fit(s["title"], [(22, 84), (38, 72), (999, 62)])
        inner = f"""
<div class="frame">{LOGO}
  <div style="margin:auto 0">
    {f'<div class="num" style="font-size:230px;margin-bottom:40px">{html.escape(s["num"])}</div>' if s.get("num") else ""}
    <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
    <div class="rule" style="margin:48px 0 44px;width:180px;background:{BLUE};height:6px"></div>
    <div class="body" style="font-size:44px;max-width:880px">{rich(s.get("body"))}</div>
  </div>
  {foot}
</div>"""
    css = BASE_CSS + ".frame { position:absolute; inset:0; padding:92px 88px 84px; display:flex; flex-direction:column; }"
    return page(1080, 1350, css, inner)


# ---------- reel scenes (1080 x 1920) ----------
# Instagram covers roughly the top 220 px and bottom 380 px of a reel with UI,
# so everything important sits between y=260 and y=1540.

def phone(inner, height=None):
    h = f"height:{height}px;" if height else ""
    return f"""<div style="width:780px;{h}margin:0 auto;background:{CARD};border:2px solid {LINE};
border-radius:64px;padding:44px 40px;overflow:hidden;position:relative">{inner}</div>"""


def chat_html(s):
    msgs = []
    for m in s.get("messages", []):
        kind = m.get("from", "client")
        if kind == "divider":
            msgs.append(f'<div style="text-align:center;margin:30px 0"><span class="tag" style="font-size:26px;padding:10px 26px;color:{CREAM};border-color:{BLUE}">{rich(m["text"])}</span></div>')
            continue
        mine = kind == "shop"
        bubble_bg = BLUE if mine else "#23263a"
        align = "flex-end" if mine else "flex-start"
        msgs.append(f"""<div style="display:flex;justify-content:{align};margin:18px 0">
<div style="max-width:560px;background:{bubble_bg};border-radius:34px;padding:24px 32px;font-size:34px;font-weight:600;line-height:1.3">{rich(m["text"])}
<div style="font-size:22px;color:{'#cfe0ff' if mine else QUIET};margin-top:8px;text-align:right">{html.escape(m.get("time", ""))}</div></div></div>""")
    header = f"""<div style="display:flex;align-items:center;gap:22px;padding-bottom:28px;border-bottom:2px solid {LINE};margin-bottom:20px">
<div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#3a3f57,#23263a)"></div>
<div><div style="font-size:32px;font-weight:800">{html.escape(s.get("contact", "client"))}</div>
<div style="font-size:24px;color:{QUIET}">Instagram Direct</div></div></div>"""
    return phone(header + "".join(msgs), height=s.get("phone_height"))


def page_mock_html(s):
    rows = "".join(
        f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:24px 0;border-bottom:2px solid {LINE};font-size:32px;font-weight:700">
<span>{rich(r[0])}</span><span style="color:{BLUE}">{rich(r[1])}</span></div>""" for r in s.get("rows", []))
    inner = f"""<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:44px">
<span style="font-weight:800;font-size:32px">{rich(s.get("brand", "Лепесток"))}</span>
<span class="tag" style="font-size:22px;padding:8px 20px">Концепт</span></div>
<div style="font-weight:800;font-size:52px;line-height:1.1;text-transform:uppercase">{rich(s.get("headline", ""))}</div>
<div style="font-size:28px;color:{MUTED};margin:20px 0 26px">{rich(s.get("sub", ""))}</div>
{rows}
<div style="margin-top:40px;background:{BLUE};border-radius:999px;text-align:center;padding:30px;font-weight:800;font-size:32px;text-transform:uppercase">{rich(s.get("cta", "Заказать в WhatsApp"))}</div>"""
    return phone(inner, height=s.get("phone_height"))


def scene_html(s):
    layout = s.get("layout", "point")
    caption = ""
    if s.get("title") and layout in ("chat", "page", "beforeafter"):
        size = fit(s["title"], [(30, 64), (999, 54)])
        caption = f'<div class="title" style="font-size:{size}px;margin-bottom:56px;text-align:center">{rich(s["title"])}</div>'
    if layout == "hook":
        size = fit(s["title"], [(26, 118), (42, 102), (64, 88), (999, 76)])
        body = f"""
<div class="ring" style="width:560px;height:560px;top:120px;right:-240px"></div>
<div class="dot" style="width:240px;height:240px;top:280px;right:-80px"></div>
<div class="stage">
  {f'<div class="kicker" style="margin-bottom:40px">{rich(s.get("kicker"))}</div>' if s.get("kicker") else ""}
  <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
  {f'<div class="body" style="font-size:46px;margin-top:48px">{rich(s.get("body"))}</div>' if s.get("body") else ""}
</div>"""
    elif layout == "point":
        size = fit(s["title"], [(24, 96), (44, 82), (999, 70)])
        body = f"""<div class="stage">
  {f'<div class="num" style="font-size:260px;margin-bottom:44px">{html.escape(s["num"])}</div>' if s.get("num") else ""}
  <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
  {f'<div class="rule" style="margin:52px 0 48px;width:200px;background:{BLUE};height:7px"></div><div class="body" style="font-size:48px">{rich(s.get("body"))}</div>' if s.get("body") else ""}
</div>"""
    elif layout == "chat":
        body = f'<div class="stage" style="align-items:stretch">{caption}{chat_html(s)}</div>'
    elif layout == "page":
        body = f'<div class="stage" style="align-items:stretch">{caption}{page_mock_html(s)}</div>'
    elif layout == "beforeafter":
        def col(label, items, good):
            color = BLUE if good else "#5a5f75"
            li = "".join(f'<div style="padding:22px 0;border-bottom:2px solid {LINE};font-size:34px;font-weight:600;line-height:1.3">{rich(i)}</div>' for i in items)
            return f"""<div style="flex:1;background:{CARD};border:3px solid {color};border-radius:44px;padding:40px 36px">
<div style="font-weight:800;font-size:36px;letter-spacing:.12em;color:{color};margin-bottom:12px">{label}</div>{li}</div>"""
        body = f"""<div class="stage" style="align-items:stretch">{caption}
<div style="display:flex;gap:28px">{col("ДО", s.get("before", []), False)}{col("ПОСЛЕ", s.get("after", []), True)}</div></div>"""
    else:  # cta
        size = fit(s["title"], [(30, 100), (52, 84), (999, 72)])
        body = f"""
<div class="ring" style="width:620px;height:620px;bottom:180px;left:-300px"></div>
<div class="stage">
  <div class="title" style="font-size:{size}px">{rich(s["title"])}</div>
  {f'<div class="body" style="font-size:46px;margin-top:44px">{rich(s.get("body"))}</div>' if s.get("body") else ""}
  <div style="margin-top:72px"><span class="pill" style="font-size:40px;padding:34px 60px">{rich(s.get("button", "Напишите «РАЗБОР»"))}</span></div>
  <div style="margin-top:44px;color:{QUIET};font-weight:700;font-size:34px">@tapstudio.kg</div>
</div>"""
    top = f'<div style="position:absolute;top:150px;left:90px">{LOGO}</div>'
    css = BASE_CSS + """.stage { position:absolute; left:90px; right:90px; top:280px; bottom:420px;
display:flex; flex-direction:column; justify-content:center; }"""
    return page(1080, 1920, css, top + body)


def page(w, h, css, inner):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}
body {{ width:{w}px; height:{h}px; }}</style></head><body>{inner}</body></html>"""


# ---------- rendering ----------

def screenshot(chrome, html_text, w, h, out_png, tmp):
    src = Path(tmp) / (out_png.stem + ".html")
    src.write_text(html_text, encoding="utf-8")
    profile = Path(tmp) / "chrome-profile"
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--force-device-scale-factor=1", f"--user-data-dir={profile}",
           f"--window-size={w},{h}", "--virtual-time-budget=8000",
           f"--screenshot={out_png}", src.as_uri()]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not out_png.exists():
        sys.exit(f"screenshot failed: {out_png}")


def to_jpg(png, jpg):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(png), "-q:v", "2", str(jpg)], check=True)


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ("rendered", "metricool"):
                yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def check_placeholders(post):
    hits = [h for s in strings(post) for h in PLACEHOLDER.findall(s)]
    if hits:
        sys.exit(f"{post['id']}: unfilled placeholders {sorted(set(hits))} - fill them before rendering")


def render_carousel(chrome, post, folder, tmp):
    slides = post["slides"]
    if not 2 <= len(slides) <= 10:
        sys.exit("a carousel needs 2-10 slides")
    files = []
    for i, s in enumerate(slides, 1):
        png = Path(tmp) / f"slide-{i:02d}.png"
        screenshot(chrome, slide_html(s, i, len(slides)), 1080, 1350, png, tmp)
        jpg = folder / f"slide-{i:02d}.jpg"
        to_jpg(png, jpg)
        files.append(jpg.name)
    return {"media": files}


def render_reel(chrome, post, folder, tmp):
    scenes = post["scenes"]
    pngs, durs = [], []
    for i, s in enumerate(scenes, 1):
        png = Path(tmp) / f"scene-{i:02d}.png"
        screenshot(chrome, scene_html(s), 1080, 1920, png, tmp)
        pngs.append(png)
        durs.append(float(s.get("seconds", SCENE_SECONDS.get(s.get("layout", "point"), 3.0))))

    inputs, chains = [], []
    for i, (png, d) in enumerate(zip(pngs, durs)):
        inputs += ["-loop", "1", "-t", f"{d + FADE:.2f}", "-i", str(png)]
        # slow push-in so still frames feel alive
        chains.append(
            f"[{i}:v]scale=w='trunc(1080*(1+0.035*t/{d + FADE:.2f})/2)*2':h=-2:eval=frame,"
            f"crop=1080:1920,fps=30,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[s{i}]")
    last, offset = "s0", 0.0
    for i in range(1, len(pngs)):
        offset += durs[i - 1]
        out = f"x{i}"
        chains.append(f"[{last}][s{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[{out}]")
        last = out
    total = sum(durs) + FADE
    chains.append(f"[{last}]trim=duration={total:.2f}[v]")
    out_mp4 = folder / "reel.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
           "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-filter_complex", ";".join(chains), "-map", "[v]", "-map", f"{len(pngs)}:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    subprocess.run(cmd, check=True)
    to_jpg(pngs[0], folder / "cover.jpg")
    return {"media": ["reel.mp4"], "cover": "cover.jpg", "seconds": round(total, 1)}


def main(dirs):
    chrome = find_chrome()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")
    for d in dirs:
        folder = (ROOT / d) if not Path(d).is_absolute() else Path(d)
        post = json.loads((folder / "post.json").read_text(encoding="utf-8"))
        check_placeholders(post)
        with tempfile.TemporaryDirectory() as tmp:
            result = render_carousel(chrome, post, folder, tmp) if post["format"] == "carousel" \
                else render_reel(chrome, post, folder, tmp)
        post["rendered"] = result
        (folder / "post.json").write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{post['id']}: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
