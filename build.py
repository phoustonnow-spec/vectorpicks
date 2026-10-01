#!/usr/bin/env python3
"""VectorPicks.com static site generator (stdlib only).

Usage:
  python3 build.py              # regenerate public/ from data/
  python3 build.py --validate   # build, then validate feed.xml (+ a test feed with a sample episode)

Inputs (data/):
  site_config.json   base_url, titles, podcast metadata, ga_measurement_id (one place to change the domain)
  ai-picks/*.json    AI chatbot picks per week -> ai-picks.html (+ archive per week)
  weeks/*.json       one file per week (e.g. 2026-w04.json); newest = "latest card"
  ats-tracker.csv    graded picks (synced from tracker_sync_from if that path exists)
  episodes.json      podcast episodes -> episodes.html + feed.xml
  shorts.json        YouTube Shorts list (+ local latest Short)
  methodology.html   methodology body
Static files in assets/ are copied to public/assets/.
The Live Board (live.html) reads /api/odds in the browser and joins it to
public/live-spreads.json, written here from the latest week's card.
"""
import csv, glob, hashlib, html, json, os, re, shutil, subprocess, sys
from datetime import datetime, date
from email.utils import format_datetime
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "public")
SHOW_TYPES = ["Tuesday Rankings", "Thursday Picks", "Sunday Update", "Sunday Recap"]
TIER_CLASS = {"Best Bet": "bestbet", "Lean": "lean", "Card": "card", "Pass": "pass"}
e = lambda s: html.escape(str(s), quote=True)

def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)

CFG = load("site_config.json")
BASE = CFG["base_url"].rstrip("/")
ASSET_Q = {}

def sha10(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:10]

def asset(rel):
    rel = rel.lstrip("/")
    q = ASSET_Q.get(rel)
    return f"{rel}?v={q}" if q else rel

def index_assets():
    ASSET_Q.clear()
    base = os.path.join(OUT, "assets")
    for dirpath, _, names in os.walk(base):
        for name in names:
            full = os.path.join(dirpath, name)
            rel = "assets/" + os.path.relpath(full, base).replace(os.sep, "/")
            ASSET_Q[rel] = sha10(full)

def minus(s):  # typographic minus for display
    return re.sub(r"(?<![\w])-(?=\d)", "\u2212", str(s))

# ---------------------------------------------------------------- data
def load_weeks():
    weeks = []
    for p in sorted(glob.glob(os.path.join(DATA, "weeks", "*.json"))):
        w = json.load(open(p))
        w["slug"] = f"card-{w['season']}-w{int(w['week']):02d}"
        weeks.append(w)
    weeks.sort(key=lambda w: (w["season"], w["week"]))
    return weeks

def load_tracker():
    src = CFG.get("tracker_sync_from")
    dst = os.path.join(ROOT, CFG["tracker_csv"])
    if src and os.path.exists(src):
        shutil.copyfile(src, dst)
    rows = list(csv.DictReader(open(dst, newline="")))
    start = CFG["record_start"]
    out = []
    for r in rows:
        season = int(r.get("Season") or start["season"])
        wk = int(r["Week"])
        if (season, wk) < (start["season"], start["week"]):
            continue
        r["Season"] = season
        r["_res"] = (r.get("ATS Result") or "").strip()
        out.append(r)
    return out

def tally(rows, tier=None):
    t = {"W": 0, "L": 0, "P": 0, "pending": 0}
    for r in rows:
        if tier and r["Tier"] != tier:
            continue
        res = r["_res"]
        if res in ("W", "L", "P"):
            t[res] += 1
        elif res == "pending":
            t["pending"] += 1
    t["units"] = t["W"] - t["L"]
    t["rec"] = f"{t['W']}-{t['L']}-{t['P']}"
    g = t["W"] + t["L"]
    t["pct"] = f"{100*t['W']/g:.1f}%" if g else "\u2014"
    return t

def tracker_index(rows):
    return {(r["Season"], int(r["Week"]), r["Game"]): r for r in rows}

# ---------------------------------------------------------------- layout
NAV = [("index.html", "Home"), ("card.html", "Weekly Card"), ("ai-picks.html", "AI Picks"), ("live.html", "Live Board"),
       ("record.html", "Record"), ("methodology.html", "Methodology"),
       ("episodes.html", "Podcast"), ("shorts.html", "Shorts")]

def gtag_snippet():
    """Standard GA4 gtag snippet, or "" when ga_measurement_id is empty."""
    gid = str(CFG.get("ga_measurement_id") or "").strip()
    if not gid:
        return ""
    if not re.fullmatch(r"G-[A-Z0-9]+", gid):
        raise SystemExit("ga_measurement_id must be a GA4 id like G-XXXXXXXX, or empty")
    return (
        "<!-- Google tag (gtag.js) -->\n"
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{gid}');\n"
        "</script>\n"
    )

def nav_html(active):
    parts = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        parts.append(f'<a href="{e(href)}"{cur}>{e(label)}</a>')
    yt = CFG.get("youtube_url") or "https://www.youtube.com/@VectorPicks"
    parts.append(f'<a class="nav-yt" href="{e(yt)}" target="_blank" rel="noopener">YouTube</a>')
    return "".join(parts)

def youtube_subscribe():
    base = (CFG.get("youtube_url") or "https://www.youtube.com/@VectorPicks").split("?")[0].rstrip("/")
    return base + "?sub_confirmation=1"

def home_json_ld():
    logo = f"{BASE}/{asset('assets/icon-512.png')}"
    yt = CFG.get("youtube_url") or "https://www.youtube.com/@VectorPicks"
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": BASE + "/#organization",
                "name": "Vector Picks",
                "url": BASE + "/",
                "logo": logo,
                "sameAs": [yt],
            },
            {
                "@type": "WebSite",
                "@id": BASE + "/#website",
                "name": "Vector Picks",
                "url": BASE + "/",
                "publisher": {"@id": BASE + "/#organization"},
            },
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(payload, separators=(",", ":")) + "</script>\n"

def font_preload():
    rel = "assets/fonts/Anton-Regular.woff2"
    if rel not in ASSET_Q:
        return ""
    return f'<link rel="preload" href="{e(asset(rel))}" as="font" type="font/woff2" crossorigin>\n'

def og_image_meta():
    rel = "assets/og-image.png"
    url = f"{BASE}/{asset(rel)}"
    width, height = 1200, 630
    try:
        from PIL import Image
        path = os.path.join(OUT, rel)
        if os.path.exists(path):
            with Image.open(path) as im:
                width, height = im.size
    except Exception:
        pass
    return (
        f'<meta property="og:image" content="{e(url)}">\n'
        f'<meta property="og:image:width" content="{width}">\n'
        f'<meta property="og:image:height" content="{height}">\n'
        f'<meta property="og:image:alt" content="Vector Picks">\n'
        f'<meta name="twitter:image" content="{e(url)}">\n'
    )

def page(fname, title, body, desc=None, active=None, extra_head=""):
    active = active or fname
    nav = nav_html(active)
    full_title = f"{title} | {CFG['site_name']}" if title else f"{CFG['site_name']} | {CFG['title']}"
    desc = desc or CFG["description"]
    canon = f"{BASE}/" if fname == "index.html" else f"{BASE}/{fname}"
    touch = "assets/apple-touch-icon.png"
    doc = f"""<!doctype html>
<html lang="en">
<head>
{gtag_snippet()}<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canon)}">
{og_image_meta()}<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#081834">
{font_preload()}<link rel="icon" href="{e(asset('assets/favicon.png'))}" type="image/png">
<link rel="apple-touch-icon" href="{e(asset(touch))}">
<link rel="manifest" href="site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{e(CFG['title'])} podcast" href="feed.xml">
<link rel="stylesheet" href="{e(asset('assets/style.css'))}">
{extra_head}</head>
<body>
<div class="topbar"></div>
<header class="site-header">
  <a class="brand" href="index.html">
    <span class="brand-name">VECTOR<b>PICKS</b><small>.com</small></span>
    <span class="brand-tag">AI NFL WEEKLY SELECTIONS</span>
  </a>
  <button class="nav-toggle" aria-expanded="false" aria-controls="nav" aria-label="Menu">&#9776;</button>
  <nav id="nav" class="site-nav">{nav}</nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <div class="rg"><span class="age">21+</span> <span>Entertainment and opinion only. Not betting advice. Gambling problem? Call <a href="tel:18004262537"><b>1-800-GAMBLER</b></a>.</span></div>
  <p>Lines of record: official Westgate SuperContest weekly card. Every pick graded at the posted line, flat 1 unit, losses included. <a href="methodology.html#integrity">Integrity rules</a>.</p>
  <p class="small">&copy; {date.today().year} {e(CFG['site_name'])} &middot; {e(CFG['title'])} &middot; <a href="{e(CFG.get('youtube_url',''))}" target="_blank" rel="noopener">YouTube {e(CFG.get('youtube_handle',''))}</a> &middot; <a href="mailto:{e(CFG['email'])}">{e(CFG['email'])}</a> &middot; <a href="feed.xml">Podcast RSS</a></p>
</footer>
<script src="{e(asset('assets/site.js'))}" defer></script>
</body>
</html>
"""
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(doc)

def tier_badge(t):
    return f'<span class="tier tier-{TIER_CLASS.get(t, "card")}">{e(t)}</span>'

def result_badge(r):
    res = (r or {}).get("_res", "")
    cls = {"W": "win", "L": "loss", "P": "push"}.get(res, "pend")
    label = {"W": "WIN", "L": "LOSS", "P": "PUSH", "n/a": "NO SIDE", "pending": "PENDING", "": "\u2014"}.get(res, res)
    return f'<span class="res res-{cls}">{e(label)}</span>'

def record_box(rows, heading="Season record"):
    cells = ""
    for label, tier in (("Best Bets", "Best Bet"), ("Leans", "Lean"), ("Full card", None)):
        t = tally(rows, tier)
        u = f"{t['units']:+d}u" if t["units"] else "0u"
        cells += f'<div class="rec-cell"><div class="rec-label">{label}</div><div class="rec-num">{t["rec"]}</div><div class="rec-sub">{u} &middot; {t["pending"]} pending</div></div>'
    s = CFG["record_start"]
    return f'<section class="panel record-box"><h2 class="kicker">{e(heading)}</h2><div class="rec-grid">{cells}</div><p class="note">W-L-P at the Westgate line, flat 1 unit, since Week {s["week"]} {s["season"]}. <a href="record.html">Every pick &rarr;</a></p></section>'

# ---------------------------------------------------------------- pages
def build_card(w, tidx, fname):
    rows = ""
    for g in w["games"]:
        tr = tidx.get((w["season"], w["week"], g["game"]))
        score = e(tr["Final Score"]) if tr and tr.get("Final Score") else ""
        rows += f"""<tr class="t-{TIER_CLASS.get(g['tier'],'card')}">
<td class="game"><b>{e(g['label'])}</b><span class="sub">{e(g['day'])} {e(g['date'][5:].replace('-','/'))}</span></td>
<td data-l="Westgate">{e(minus(g['westgate']))}</td>
<td data-l="Market" class="muted">{e(minus(g.get('market') or ''))}</td>
<td data-l="Our Spread"><b>{e(minus(g['our']))}</b></td>
<td data-l="Gap" class="gap">{g['gap']:.1f}</td>
<td data-l="Tier">{tier_badge(g['tier'])}</td>
<td data-l="Card side" class="pick">{e(minus(g['pick']))}</td>
<td data-l="Result">{result_badge(tr)}{f'<span class="sub">{score}</span>' if score else ''}</td>
<td class="note-cell" data-l="Why">{e(minus(g['note']))}</td>
</tr>"""
    pw = ""
    for i, (team, h, d, a, why) in enumerate(sorted(w.get("powers", []), key=lambda x: -x[3]), 1):
        dcls = "neg" if d < 0 else ("pos" if d > 0 else "")
        pw += f'<tr><td class="rank">{i}</td><td><b>{e(team)}</b></td><td>{minus(f"{h:+.1f}")}</td><td class="{dcls}">{minus(f"{d:+.1f}") if d else "0"}</td><td><b>{minus(f"{a:+.1f}")}</b></td><td class="muted">{e(minus(why))}</td></tr>'
    s = w["summary"]
    li = lambda xs: "".join(f"<li>{e(minus(x))}</li>" for x in xs)
    update = f'<p class="note">{e(w["update_note"])}</p>' if w.get("update_note") else ""
    body = f"""
<section class="hero hero-sm"><p class="kicker">Week {w['week']} &middot; {w['season']}</p><h1>Weekly <span class="g">Card</span></h1>
<p class="muted">As of {e(w['as_of'])}.</p>{update}</section>
<section class="summary-grid">
<div class="panel"><h2>{tier_badge('Best Bet')} Best Bets</h2><ul class="picks big">{li(s['best_bets'])}</ul></div>
<div class="panel"><h2>{tier_badge('Lean')} Leans</h2><ul class="picks">{li(s['leans'])}</ul></div>
<div class="panel"><h2>{tier_badge('Pass')} Passes</h2><ul class="picks">{li(s['passes'])}</ul></div>
</section>
<section class="panel"><h2>Full card: Market vs Our Spread</h2>
<p class="note"><b>Westgate</b> = contest line of record (graded here). <b>Market</b> = {e(w['market_source'])}. <b>Gap</b> = points between the Westgate line and Our Spread, toward the card side. {e(w['hfa_note'])}</p>
<div class="table-wrap"><table class="card-table"><thead><tr><th scope="col">Game</th><th scope="col">Westgate</th><th scope="col">Market</th><th scope="col">Our Spread</th><th scope="col">Gap</th><th scope="col">Tier</th><th scope="col">Card side</th><th scope="col">Result</th><th scope="col">Why</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section class="panel" id="powers"><h2>{e(w.get("powers_title", "Power ratings: healthy &rarr; injury-adjusted"))}</h2>
<p class="note">{e(w.get("powers_note", "Points vs a league-average team. Injury Δ = our player-value layer (Out/Doubtful full value, Questionable/DNP ~half). Rank is display only."))}</p>
<div class="table-wrap"><table class="power-table"><thead><tr><th scope="col">#</th><th scope="col">Team</th><th scope="col">{e(w.get("powers_healthy_label", "Healthy"))}</th><th scope="col">Injury &Delta;</th><th scope="col">Adjusted</th><th scope="col">Drivers</th></tr></thead><tbody>{pw}</tbody></table></div></section>
<section class="panel"><h2>Missing / not used this week</h2><ul class="missing">{li(w.get('missing', []))}</ul>
<p class="note">Lines: {e(w['line_source'])}</p></section>
"""
    archived = fname != "card.html"
    title = f"Week {w['week']} {w['season']} Card" + (" archive" if archived else "")
    if archived:
        desc = f"Archived Week {w['week']} {w['season']} NFL card: Westgate line versus Our Spread, with the gap and tier for every game."
    else:
        desc = f"Week {w['week']} {w['season']} NFL card: Westgate line versus Our Spread, with the gap and tier for every game."
    page(fname, title, body, desc=desc, active="card.html")

def build_week_index(weeks):
    items = "".join(f'<li><a href="{w["slug"]}.html">Week {w["week"]} &middot; {w["season"]}</a></li>' for w in reversed(weeks))
    return f'<section class="panel"><h2>All weekly cards</h2><ul class="weeklist">{items}</ul></section>'

def build_record(rows, tidx):
    graded = [r for r in rows if r["_res"] in ("W", "L", "P")]
    pending = [r for r in rows if r["_res"] == "pending"]
    def tbl(rs, show_score=True):
        if not rs:
            return '<p class="muted">None yet.</p>'
        b = ""
        for r in rs:
            pick = r["Pick"] if r["Pick"].startswith("No side") else f'{r["Pick"]} {r["Line"]}'
            b += f"""<tr><td data-l="Wk">{e(r['Week'])}</td><td data-l="Date">{e(r['Date'][5:].replace('-','/'))}</td><td class="game" data-l="Game"><b>{e(r['Game'])}</b></td>
<td data-l="Pick" class="pick">{e(minus(pick))}</td><td data-l="Our Spread">{e(minus(r['Our Spread']))}</td><td data-l="Gap">{e(r['Gap'])}</td><td data-l="Tier">{tier_badge(r['Tier'])}</td>
<td data-l="Result">{result_badge(r)}</td>{f'<td data-l="Score">{e(r["Final Score"])}</td><td data-l="Units">{e(r["Units"] and ("%+d" % int(r["Units"])) or "")}</td>' if show_score else ''}</tr>"""
        head = '<th scope="col">Wk</th><th scope="col">Date</th><th scope="col">Game</th><th scope="col">Pick (line)</th><th scope="col">Our Spread</th><th scope="col">Gap</th><th scope="col">Tier</th><th scope="col">Result</th>' + ('<th scope="col">Score</th><th scope="col">Units</th>' if show_score else "")
        return f'<div class="table-wrap"><table class="rec-table"><thead><tr>{head}</tr></thead><tbody>{b}</tbody></table></div>'
    body = f"""
<section class="hero hero-sm"><p class="kicker">Transparent &middot; graded at the posted line</p><h1>The <span class="g">Record</span></h1>
<p class="muted">Every pick since Week {CFG['record_start']['week']} {CFG['record_start']['season']}. Wins and losses stay up. Flat 1 unit: win +1, loss &minus;1, push 0 (contest-style, no juice).</p></section>
{record_box(rows)}
<section class="panel"><h2>Graded picks</h2>{tbl(graded)}</section>
<section class="panel"><h2>Pending</h2>{tbl(pending, show_score=False)}
<p class="note">Games where Our Spread equals the Westgate line have no side and are not graded. Pass-tier games carry a card side (contest format) and count only toward the full-card record.</p></section>
"""
    page("record.html", "Record", body, desc="Every VectorPicks pick graded at the Westgate line: Best Bets, Leans and full card W-L-P.")

def fmt_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%b %-d, %Y")

def load_episodes(path=None):
    data = json.load(open(path)) if path else load("episodes.json")
    eps = data.get("episodes", [])
    for ep in eps:
        if ep["show_type"] not in SHOW_TYPES:
            raise SystemExit(f"episodes.json: bad show_type {ep['show_type']!r}; use one of {SHOW_TYPES}")
        local = os.path.join(OUT, ep["mp3"])
        if not ep.get("bytes") and os.path.exists(local):
            ep["bytes"] = os.path.getsize(local)
    return sorted(eps, key=lambda x: x["date"], reverse=True)

def episode_card(ep):
    return f"""<article class="ep"><div class="ep-meta"><span class="show">{e(ep['show_type'])}</span> <span class="muted">{fmt_date(ep['date'])} &middot; {e(ep['duration'])}</span></div>
<h3>{e(ep['title'])}</h3><p>{e(ep['description'])}</p><audio controls preload="none" src="{e(ep['mp3'])}"></audio></article>"""

def build_episodes(eps):
    lst = "".join(episode_card(x) for x in eps) or '<div class="empty"><b>No episodes published yet.</b><br>New shows drop weekly: Tuesday Rankings, Thursday Picks, Sunday Update and Sunday Recap.</div>'
    shows = "".join(f"<li><b>{s}</b></li>" for s in SHOW_TYPES)
    body = f"""
<section class="hero hero-sm ep-hero"><img src="{e(asset('assets/podcast-cover-600.webp'))}" alt="{e(CFG['title'])} podcast cover" width="600" height="600" decoding="async">
<div><p class="kicker">Podcast</p><h1>{e(CFG['title'])}</h1><p class="muted">Vector talks power ratings, our spreads and the weekly card. Four shows a week.</p>
<p><a class="btn" href="feed.xml">RSS feed</a></p></div></section>
<section class="panel"><h2>Shows</h2><ul class="shows">{shows}</ul></section>
<section class="panel"><h2>Episodes</h2>{lst}</section>
"""
    page("episodes.html", "Podcast", body, desc=f"{CFG['title']} podcast episodes: Tuesday Rankings, Thursday Picks, Sunday Update, Sunday Recap.")

def yt_id(url):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{6,})", url or "")
    return m.group(1) if m else None

def newest_short(sh):
    """Most recent YouTube Short from the same list the Shorts page embeds."""
    rows = [s for s in (sh.get("shorts") or []) if yt_id(s.get("youtube_url"))]
    rows.sort(key=lambda s: (s.get("date") or "", int(s.get("week") or 0)), reverse=True)
    if rows:
        return rows[0]
    lt = sh.get("latest_local") or {}
    if yt_id(lt.get("youtube_url")):
        return lt
    return None

def yt_facade(item):
    vid = yt_id(item.get("youtube_url") if item else "")
    if not vid:
        return ""
    title = item.get("title") or "YouTube Short"
    thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return (
        f'<button type="button" class="yt-facade" data-yt="{e(vid)}" data-title="{e(title)}" '
        f'aria-label="Play {e(title)}">'
        f'<img src="{e(thumb)}" alt="" width="480" height="360" loading="lazy" decoding="async">'
        f'<span class="yt-play" aria-hidden="true"></span></button>'
    )

def build_shorts(sh):
    cards = ""
    for s in sh["shorts"]:
        vid = yt_id(s.get("youtube_url"))
        if vid:
            cards += f'<div class="short"><div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{e(vid)}" title="{e(s.get("title",""))}" width="315" height="560" loading="lazy" allowfullscreen></iframe></div><p>{e(s.get("title",""))}</p></div>'
    for i in range(max(0, sh.get("placeholder_slots", 3) - len(sh["shorts"]))):
        cards += '<div class="short"><div class="yt placeholder"><span>YouTube Short<br>coming soon</span></div></div>'
    lt = sh.get("latest_local")
    latest = ""
    if lt:
        poster = asset(lt["thumbnail"]) if lt.get("thumbnail") else ""
        video = asset(lt["video"]) if lt.get("video") else ""
        latest = f"""<section class="panel latest-short"><h2>Latest Short &middot; Week {lt['week']} {lt['season']}</h2>
<div class="short-feature"><video controls preload="none" poster="{e(poster)}" src="{e(video)}" playsinline width="576" height="1024"></video>
<div><h3>{e(lt['title'])}</h3><p class="muted">Vertical 9:16 recap. {'<a href="'+e(lt['youtube_url'])+'" target="_blank" rel="noopener">Watch on YouTube</a>' if lt.get('youtube_url') else 'Follow <a href="'+e(CFG.get('youtube_url',''))+'" target="_blank" rel="noopener">'+e(CFG.get('youtube_handle',''))+'</a> on YouTube for every Short.'}</p></div></div></section>"""
    body = f"""<section class="hero hero-sm"><p class="kicker">60 seconds, every week</p><h1><span class="g">Shorts</span></h1></section>
{latest}<section class="panel"><h2>On YouTube</h2><div class="shorts-grid">{cards}</div></section>"""
    page("shorts.html", "Shorts", body, desc="Weekly NFL Shorts from Vector Picks: the card and power ratings in about a minute, on YouTube.")

def build_home(weeks, rows, tidx, eps, sh):
    w = weeks[-1]
    s = w["summary"]
    bb = "".join(f'<li>{e(minus(x))}</li>' for x in s["best_bets"])
    wk_rows = [r for r in rows if r["Season"] == w["season"] and int(r["Week"]) == w["week"]]
    wt = tally(wk_rows)
    cashed = [r for r in wk_rows if r["_res"] == "W"]
    cash_html = "".join(f'<div class="cashed">{e(minus(r["Pick"]+" "+r["Line"]))} CASHED <span>{e(r["Final Score"])}</span></div>' for r in cashed)
    ep = episode_card(eps[0]) if eps else '<div class="empty">First episode coming soon. <a href="episodes.html">Podcast page &rarr;</a></div>'
    short = newest_short(sh)
    facade = yt_facade(short) if short else ""
    short_title = (short or {}).get("title") or "Latest Short"
    short_block = (
        f'<section class="panel home-short"><h2>Latest Short</h2>{facade}'
        f'<p class="muted">{e(short_title)}</p>'
        f'<p><a href="shorts.html">All Shorts &rarr;</a></p></section>'
        if facade else
        '<section class="panel"><h2>Latest Short</h2><p class="muted">A new Short is on the way.</p><p><a href="shorts.html">Shorts &rarr;</a></p></section>'
    )
    body = f"""
<section class="hero"><p class="kicker">with VECTOR &middot; your AI analyst</p>
<h1>Week {w['week']}<br><span class="g">AI NFL Picks</span></h1>
<p class="muted">Our own power ratings. Our own spreads. Graded at the posted line, losses included.</p>
<p class="btn-row"><a class="btn" href="{e(youtube_subscribe())}" target="_blank" rel="noopener">Watch &amp; Subscribe on YouTube</a></p></section>
<div class="home-grid">
<section class="panel week-card"><div class="wc-head"><h2>Week {w['week']} &middot; {w['season']}</h2><div class="wk-rec"><small>WEEK {w['week']} RECORD</small><b>{wt['rec'][:-2] if wt['P']==0 else wt['rec']}</b></div></div>
<p class="kicker">{len(s['best_bets'])} Best Bet{'' if len(s['best_bets']) == 1 else 's'}</p><ul class="picks big">{bb}</ul>{cash_html}
<p class="note">Leans: {e(minus(', '.join(s['leans'])))}.</p>
{f'<p class="note">{e(w["update_note"])}</p>' if w.get("update_note") else ""}
<div class="btn-row"><a class="btn" href="card.html">Full card &rarr;</a><a class="btn ghost" href="live.html">Live Board &rarr;</a></div></section>
{record_box(rows)}
<section class="panel"><h2>Latest episode</h2>{ep}</section>
{short_block}
<section class="panel how"><h2>How it works</h2><ol><li><b>Power ratings</b> in points vs average.</li><li><b>Injury layer</b> with a points value per player.</li><li><b>Our Spread</b>, built independent of Vegas.</li><li><b>Gap + checklist</b> decides Best Bet, Lean or Pass.</li></ol><a class="btn ghost" href="methodology.html">Methodology &rarr;</a></section>
</div>
<div id="live-strip"></div>
<script src="{e(asset('assets/live.js'))}" defer></script>"""
    page("index.html", None, body,
         desc=f"Week {w['week']} {w['season']} AI NFL picks from Vector: power ratings, our own spreads, and a graded record. Watch on YouTube. Entertainment only. 21+.",
         extra_head=home_json_ld())

# NFL abbreviations used on the card -> Odds API full names. Display only;
# a game with no parseable Our Spread is omitted so the page shows a dash.
ABBR = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

def split_matchup(label):
    base = re.sub(r"\s*\([^)]*\)\s*$", "", label or "").strip()
    parts = re.split(r"\s*@\s*", base)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0].strip(), parts[1].strip()

def parse_our(text):
    m = re.match(r"^([A-Z]{2,3})\s+([+-]?\d+(?:\.\d+)?)$", (text or "").strip())
    if not m:
        return None
    return m.group(1), round(float(m.group(2)), 2)

PUBLISHED_TIERS = {"Best Bet", "Lean", "Card"}

def published_pick(game, away_abbr, home_abbr):
    """Westgate side we actually publish. Pass and 'No side' stay blank."""
    tier = (game.get("tier") or "").strip()
    empty = {"pick_team": None, "pick_abbr": None, "pick_line": None, "pick_label": None, "tier": tier or None}
    if tier not in PUBLISHED_TIERS:
        return empty
    parsed = parse_our(game.get("pick") or "")
    if not parsed or parsed[0] not in (away_abbr, home_abbr) or parsed[0] not in ABBR:
        return empty
    return {
        "pick_team": ABBR[parsed[0]],
        "pick_abbr": parsed[0],
        "pick_line": parsed[1],
        "pick_label": game["pick"].strip(),
        "tier": tier,
    }

def live_spreads_payload(week):
    """Current-week card numbers for the Live Board, matched by full team name.

    our_point is the card quote from our_team's side (negative = that team favored),
    the same sign the weekly card prints. The page restates it from the home side
    before Gap = Market − Our Spread.
    """
    games = []
    for g in week.get("games") or []:
        mu = split_matchup(g.get("label") or "")
        parsed = parse_our(g.get("our") or "")
        if not mu or not parsed:
            continue
        away_abbr, home_abbr = mu
        our_abbr, our_point = parsed
        if away_abbr not in ABBR or home_abbr not in ABBR or our_abbr not in ABBR:
            continue
        if our_abbr not in (away_abbr, home_abbr):
            continue
        games.append({
            "away_team": ABBR[away_abbr],
            "home_team": ABBR[home_abbr],
            "away_abbr": away_abbr,
            "home_abbr": home_abbr,
            "our_team": ABBR[our_abbr],
            "our_point": our_point,
            "our_label": g["our"].strip(),
            **published_pick(g, away_abbr, home_abbr),
        })
    return {
        "season": week["season"],
        "week": week["week"],
        "as_of": week.get("as_of"),
        "teams": {name: abbr for abbr, name in sorted(ABBR.items(), key=lambda kv: kv[1])},
        "games": games,
    }

def write_live_spreads(week):
    path = os.path.join(OUT, "live-spreads.json")
    with open(path, "w") as f:
        json.dump(live_spreads_payload(week), f, indent=2)
        f.write("\n")

def build_live(week):
    body = f"""
<section class="hero hero-sm"><p class="kicker">Market vs Our Spread</p><h1>Live <span class="g">Board</span></h1>
<p class="muted">NFL games with the market spread next to Our Spread, and the score when ESPN has one. The market spread is the median of DraftKings, FanDuel, BetMGM and Caesars, from the home team's side. Negative means the home team is favored.</p></section>
<section class="panel">
<p id="live-updated" class="note" hidden></p>
<div id="live-board" class="table-wrap" aria-live="polite"><p class="muted">Loading lines…</p></div>
<p class="note">Our Spread is the Week {int(week['week'])} {int(week['season'])} card, restated on the same home-team side as the market number. <b>Gap</b> = Market &minus; Our Spread. A dash means that game has no Our Spread on the card. A pick badge is the published Best Bet, Lean, or Card side at the Westgate line.</p>
<p class="note">Scores via ESPN; unofficial, may lag.</p>
<div class="rg"><span class="age">21+</span> <span>Entertainment and opinion only. Not betting advice. Gambling problem? Call <a href="tel:18004262537"><b>1-800-GAMBLER</b></a>.</span></div>
</section>
<script src="{e(asset('assets/live.js'))}" defer></script>
"""
    page("live.html", "Live Board", body,
         desc="Live NFL scores and spreads next to this week's Our Spread, with covering status for published picks. Entertainment and opinion only. Not betting advice. 21+.")

def validate_live(week):
    path = os.path.join(OUT, "live-spreads.json")
    data = json.load(open(path))
    expect = live_spreads_payload(week)
    if data != expect:
        raise SystemExit("live-spreads.json does not match the current weekly card")
    if len(data["games"]) != len(week.get("games") or []):
        raise SystemExit(f"live-spreads.json has {len(data['games'])} games; card has {len(week.get('games') or [])}")
    for g in data["games"]:
        parsed = parse_our(g["our_label"])
        if not parsed or ABBR[parsed[0]] != g["our_team"] or parsed[1] != g["our_point"]:
            raise SystemExit(f"live-spreads.json quote mismatch: {g}")
        if g["our_team"] not in (g["home_team"], g["away_team"]):
            raise SystemExit(f"Our Spread team is not in the matchup: {g}")
    # Independent spot check while this file is still the Week 3 2026 card (Sat 9/26 v3 update).
    if week["season"] == 2026 and int(week["week"]) == 3:
        want = {
            ("Atlanta Falcons", "Green Bay Packers"): ("Green Bay Packers", -2.4),
            ("Philadelphia Eagles", "Chicago Bears"): ("Philadelphia Eagles", -2.0),
            ("Cincinnati Bengals", "Pittsburgh Steelers"): ("Cincinnati Bengals", -1.0),
            ("Los Angeles Rams", "Denver Broncos"): ("Los Angeles Rams", -0.7),
            ("Arizona Cardinals", "San Francisco 49ers"): ("San Francisco 49ers", -9.9),
        }
        for (away, home), (our_team, our_point) in want.items():
            g = next(x for x in data["games"] if x["away_team"] == away and x["home_team"] == home)
            if g["our_team"] != our_team or g["our_point"] != our_point:
                raise SystemExit(f"Our Spread mismatch for {away} @ {home}: {g['our_team']} {g['our_point']}")
    live_html = open(os.path.join(OUT, "live.html")).read()
    for needle in ("Live Board", "assets/live.js", "1-800-GAMBLER", "Entertainment and opinion only",
                   'href="live.html" aria-current="page"', "Scores via ESPN; unofficial, may lag."):
        if needle not in live_html:
            raise SystemExit(f"live.html missing {needle}")
    if week["season"] == 2026 and int(week["week"]) == 3:
        by_matchup = {(g["away_abbr"], g["home_abbr"]): g for g in data["games"]}
        expect_pub = {
            ("PHI", "CHI"): ("CHI +4.5", "Best Bet"), ("CIN", "PIT"): ("PIT +3.5", "Best Bet"),
            ("LAR", "DEN"): ("DEN +2.5", "Best Bet"), ("KC", "MIA"): ("MIA +11.5", "Lean"),
            ("ARI", "SF"): ("SF -8.5", "Lean"), ("ATL", "GB"): ("ATL +5.5", "Lean"),
        }
        for mu, (label, tier) in expect_pub.items():
            g = by_matchup[mu]
            if g["pick_label"] != label or g["tier"] != tier:
                raise SystemExit(f"published pick mismatch for {mu}: {g}")
        for mu in (("HOU", "IND"), ("NE", "JAX"), ("LV", "NO"), ("TEN", "NYG"), ("SEA", "WAS"),
                   ("CAR", "CLE"), ("LAC", "BUF"), ("BAL", "DAL"), ("NYJ", "DET"), ("MIN", "TB")):
            g = by_matchup[mu]
            if g["pick_label"] is not None:
                raise SystemExit(f"removed game should not publish a pick: {g}")
    home = open(os.path.join(OUT, "index.html")).read()
    if 'id="live-strip"' not in home or "assets/live.js" not in home:
        raise SystemExit("home page is missing the live scores strip")
    note = "Updated model (v3): starts from the betting market"
    card_html = open(os.path.join(OUT, "card.html")).read()
    if note not in card_html.replace("&#x27;", "'") or note not in home.replace("&#x27;", "'"):
        raise SystemExit("Sat 9/26 v3 model note missing from the card or home page")
    for gone in ("DET -6.5 vs NYJ", "TB +1.5 vs MIN", "DET \u22126.5 vs NYJ"):
        if gone in home or gone in card_html:
            raise SystemExit(f"removed Lean still listed on the card/home page: {gone}")
    if "IND +2.5 vs HOU" in home or "IND +2.5 vs HOU" in card_html:
        raise SystemExit("IND +2.5 still listed on the card/home page")
    for fname in ("index.html", "card.html", "record.html"):
        doc = open(os.path.join(OUT, fname)).read()
        if 'href="live.html"' not in doc:
            raise SystemExit(f"{fname} missing Live Board link")
    if "live-spreads.json" not in os.listdir(OUT):
        raise SystemExit("live-spreads.json was not written")
    print(f"OK live board: Week {data['week']} {data['season']}, {len(data['games'])} Our Spreads, nav + home link")

def validate_analytics():
    gid = str(CFG.get("ga_measurement_id") or "").strip()
    pages = []
    for dirpath, _, names in os.walk(OUT):
        for name in names:
            if name.endswith(".html"):
                pages.append(os.path.join(dirpath, name))
    basenames = {os.path.basename(p) for p in pages}
    for name in ("index.html", "live.html", "404.html"):
        if name not in basenames:
            raise SystemExit(f"analytics check missing {name}")
    for path in pages:
        text = open(path).read()
        has_tag = "googletagmanager.com/gtag/js" in text or "gtag('config'" in text
        if gid and not has_tag:
            raise SystemExit(f"{os.path.basename(path)} is missing the gtag snippet")
        if not gid and has_tag:
            raise SystemExit(f"{os.path.basename(path)} includes gtag but ga_measurement_id is empty")
    saved = CFG.get("ga_measurement_id", "")
    try:
        CFG["ga_measurement_id"] = "G-TEST1234"
        snippet = gtag_snippet()
        if "https://www.googletagmanager.com/gtag/js?id=G-TEST1234" not in snippet:
            raise SystemExit("gtag snippet missing async script")
        if "gtag('config', 'G-TEST1234')" not in snippet:
            raise SystemExit("gtag snippet missing gtag('config')")
        CFG["ga_measurement_id"] = "   "
        if gtag_snippet() != "":
            raise SystemExit("blank ga_measurement_id should inject nothing")
        CFG["ga_measurement_id"] = "<script>"
        try:
            gtag_snippet()
        except SystemExit as err:
            if "GA4" not in str(err):
                raise
        else:
            raise SystemExit("invalid ga_measurement_id should fail the build")
    finally:
        CFG["ga_measurement_id"] = saved
    print(f"OK analytics: ga_measurement_id {gid or 'empty'}, {len(pages)} pages, snippet injects only when set")

def validate_seo():
    pages = []
    for dirpath, _, names in os.walk(OUT):
        for name in names:
            if name.endswith(".html"):
                pages.append(os.path.join(dirpath, name))
    titles, descs = {}, {}
    for path in pages:
        text = open(path).read()
        name = os.path.basename(path)
        if re.search(r"https://(?!www\.)vectorpicks\.com", text):
            raise SystemExit(f"{name} still points at the apex domain")
        title = re.search(r"<title>(.*?)</title>", text)
        desc = re.search(r'<meta name="description" content="(.*?)"', text)
        if not title or not desc:
            raise SystemExit(f"{name} missing title or description")
        if title.group(1) in titles:
            raise SystemExit(f"duplicate title {title.group(1)!r} on {name} and {titles[title.group(1)]}")
        if desc.group(1) in descs:
            raise SystemExit(f"duplicate description on {name} and {descs[desc.group(1)]}")
        titles[title.group(1)] = name
        descs[desc.group(1)] = name
        for needle in ('property="og:image"', 'og:image:width', 'og:image:height', 'twitter:card" content="summary_large_image"',
                       'rel="canonical"', 'name="viewport"', 'name="theme-color"', 'rel="manifest"', 'apple-touch-icon',
                       'rel="icon"'):
            if needle not in text:
                raise SystemExit(f"{name} missing {needle}")
        if 'class="nav-yt"' not in text or 'target="_blank" rel="noopener">YouTube' not in text:
            raise SystemExit(f"{name} missing the YouTube nav link")
        if "<th" in text and 'scope="col"' not in text:
            raise SystemExit(f"{name} has a table header without scope")
    home = open(os.path.join(OUT, "index.html")).read()
    for needle in ("sub_confirmation=1", "yt-facade", "i.ytimg.com/vi/", "application/ld+json", '"sameAs"',
                   "https://www.youtube.com/@VectorPicks", "Watch &amp; Subscribe on YouTube"):
        if needle not in home:
            raise SystemExit(f"home missing {needle}")
    live_js = open(os.path.join(ROOT, "assets", "live.js")).read()
    if 'scope="col"' not in live_js:
        raise SystemExit("live board headers are missing scope")
    for path in ("sitemap.xml", "robots.txt", "feed.xml"):
        text = open(os.path.join(OUT, path)).read()
        if "https://www.vectorpicks.com" not in text or re.search(r"https://(?!www\.)vectorpicks\.com", text):
            raise SystemExit(f"{path} is not on https://www.vectorpicks.com")
    if not os.path.exists(os.path.join(OUT, "site.webmanifest")):
        raise SystemExit("site.webmanifest was not written")
    print(f"OK seo: www canonical, {len(pages)} unique titles, YouTube nav, JSON-LD, manifest")

def build_methodology():
    body = f'<section class="hero hero-sm"><p class="kicker">How Vector picks</p><h1><span class="g">Methodology</span></h1></section><article class="panel prose">{open(os.path.join(DATA,"methodology.html")).read()}</article>'
    page("methodology.html", "Methodology", body, desc="How VectorPicks builds power ratings, injury adjustments, Our Spread, and Best Bet / Lean / Pass tiers.")

# ---------------------------------------------------------------- feed
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"

def build_feed(eps, out_path):
    def x(s): return html.escape(str(s), quote=False)
    now = format_datetime(datetime.now().astimezone())
    items = ""
    for ep in eps:
        dt = datetime.strptime(ep["date"], "%Y-%m-%d").replace(hour=6).astimezone()
        url = f"{BASE}/{ep['mp3'].lstrip('/')}"
        guid = ep.get("guid") or url
        items += f"""
    <item>
      <title>{x(ep['title'])}</title>
      <description>{x(ep['description'])}</description>
      <itunes:summary>{x(ep['description'])}</itunes:summary>
      <pubDate>{format_datetime(dt)}</pubDate>
      <enclosure url="{x(url)}" length="{int(ep.get('bytes') or 0)}" type="audio/mpeg"/>
      <guid isPermaLink="false">{x(guid)}</guid>
      <itunes:duration>{x(ep['duration'])}</itunes:duration>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>{'true' if CFG.get('explicit') else 'false'}</itunes:explicit>
      <itunes:keywords>{x(ep['show_type'])}</itunes:keywords>
    </item>"""
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="{ITUNES}" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{x(CFG['title'])}</title>
    <link>{x(BASE)}/</link>
    <atom:link href="{x(BASE)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{x(CFG['description'])}</description>
    <language>{x(CFG['language'])}</language>
    <copyright>&#169; {date.today().year} {x(CFG['site_name'])}</copyright>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{x(CFG['author'])}</itunes:author>
    <itunes:summary>{x(CFG['description'])}</itunes:summary>
    <itunes:owner>
      <itunes:name>{x(CFG['owner_name'])}</itunes:name>
      <itunes:email>{x(CFG['email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{x(BASE)}/{x(CFG['artwork'])}"/>
    <image><url>{x(BASE)}/{x(CFG['artwork'])}</url><title>{x(CFG['title'])}</title><link>{x(BASE)}/</link></image>
    <itunes:category text="{x(CFG['itunes_category'])}"><itunes:category text="{x(CFG['itunes_subcategory'])}"/></itunes:category>
    <itunes:explicit>{'true' if CFG.get('explicit') else 'false'}</itunes:explicit>
    <itunes:type>episodic</itunes:type>{items}
  </channel>
</rss>
"""
    with open(out_path, "w") as f:
        f.write(feed)

def validate_feed(path, expect_items=None):
    tree = ET.parse(path)  # raises on malformed XML
    ch = tree.getroot().find("channel")
    ns = {"itunes": ITUNES}
    req_channel = ["title", "link", "description", "language", "itunes:author", "itunes:image", "itunes:category",
                   "itunes:explicit", "itunes:owner/itunes:email", "itunes:owner/itunes:name"]
    missing = [t for t in req_channel if ch.find(t, ns) is None]
    items = ch.findall("item")
    for it in items:
        for t in ["title", "enclosure", "guid", "pubDate", "itunes:duration", "itunes:explicit"]:
            if it.find(t, ns) is None:
                missing.append(f"item/{t}")
        enc = it.find("enclosure")
        if enc is not None and not all(enc.get(a) for a in ("url", "length", "type")):
            missing.append("item/enclosure@attrs")
    img = ch.find("itunes:image", ns).get("href")
    if missing:
        raise SystemExit(f"{path}: missing {missing}")
    if expect_items is not None and len(items) != expect_items:
        raise SystemExit(f"{path}: expected {expect_items} items, got {len(items)}")
    print(f"OK {os.path.relpath(path, ROOT)}: well-formed, {len(items)} item(s), required iTunes tags present, artwork {img}")

# ---------------------------------------------------------------- assets
FONT_UNICODES = "U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2018,U+2019,U+201C,U+201D,U+2022,U+2026,U+20AC,U+2122,U+2192,U+2212"

def subset_fonts():
    fonts = os.path.join(ROOT, "assets", "fonts")
    jobs = [
        ("Anton-Regular.ttf", "Anton-Regular.woff2", ["--layout-features=kern"]),
        ("Montserrat-VariableFont_wght.ttf", "Montserrat-Variable.woff2", ["--layout-features=kern,liga,calt", "--desubroutinize"]),
    ]
    try:
        subprocess.check_call([sys.executable, "-c", "import fontTools, brotli"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("fonttools/brotli not available; deployed CSS will keep the full TTF")
        return False
    for src, dest, extra in jobs:
        sp = os.path.join(fonts, src)
        dp = os.path.join(fonts, dest)
        if not os.path.exists(sp):
            continue
        before = os.path.getsize(sp)
        subprocess.check_call([
            sys.executable, "-m", "fontTools.subset", sp,
            f"--output-file={dp}", "--flavor=woff2", f"--unicodes={FONT_UNICODES}", *extra,
        ])
        print(f"font {src}: {before} -> {dest} {os.path.getsize(dp)} bytes (saved {before - os.path.getsize(dp)})")
    return True

def convert_webp():
    from PIL import Image
    jobs = [
        ("podcast-cover-600.png", "podcast-cover-600.webp"),
        ("shorts/wk3-2026-thumbnail.png", "shorts/wk3-2026-thumbnail.webp"),
    ]
    for src, dest in jobs:
        sp = os.path.join(ROOT, "assets", src)
        dp = os.path.join(ROOT, "assets", dest)
        if os.path.exists(sp):
            before = os.path.getsize(sp)
            Image.open(sp).convert("RGB").save(dp, "WEBP", quality=78, method=6)
            after = os.path.getsize(dp)
            os.remove(sp)
            print(f"webp {src}: {before} -> {dest} {after} bytes (saved {before - after})")
        elif not os.path.exists(dp):
            raise SystemExit(f"missing image {src} (and no {dest})")

def recompress_pngs():
    from PIL import Image
    for rel in ("favicon.png", "og-image.png", "podcast-cover-3000.png"):
        path = os.path.join(ROOT, "assets", rel)
        if not os.path.exists(path):
            continue
        before = os.path.getsize(path)
        tmp = path + ".opt"
        Image.open(path).save(tmp, "PNG", optimize=True)
        after = os.path.getsize(tmp)
        if after + 32 < before:
            os.replace(tmp, path)
            print(f"png {rel}: {before} -> {after} bytes (saved {before - after})")
        else:
            os.remove(tmp)

def minify_css(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}:;,])\s*", r"\1", text)
    return text.strip() + "\n"

def version_css_urls(css):
    def repl(m):
        raw = m.group(1).strip().strip("'\"")
        if raw.startswith(("data:", "http:", "https:")):
            return m.group(0)
        path = os.path.normpath(os.path.join(OUT, "assets", raw.split("?", 1)[0]))
        if os.path.isfile(path):
            rel = raw.split("?", 1)[0]
            return f'url("{rel}?v={sha10(path)}")'
        return m.group(0)
    return re.sub(r"url\(([^)]+)\)", repl, css)

def write_public_css():
    src = os.path.join(ROOT, "assets", "style.css")
    css = version_css_urls(minify_css(open(src).read()))
    woff = os.path.join(OUT, "assets", "fonts", "Anton-Regular.woff2")
    if not os.path.exists(woff):
        css = css.replace("fonts/Anton-Regular.woff2", "fonts/Anton-Regular.ttf")
        css = css.replace("fonts/Montserrat-Variable.woff2", "fonts/Montserrat-VariableFont_wght.ttf")
        css = version_css_urls(css)
    with open(os.path.join(OUT, "assets", "style.css"), "w") as f:
        f.write(css)

def generate_icons():
    from PIL import Image
    src = os.path.join(ROOT, "brand", "youtube-profile.png")
    if not os.path.exists(src):
        src = os.path.join(ROOT, "assets", "favicon.png")
    im = Image.open(src).convert("RGBA")
    out = os.path.join(OUT, "assets")
    for size, name in ((180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
        im.resize((size, size), Image.Resampling.LANCZOS).save(os.path.join(out, name), "PNG", optimize=True)

def drop_unreferenced_fonts():
    fonts = os.path.join(OUT, "assets", "fonts")
    if not os.path.isdir(fonts):
        return
    if os.path.exists(os.path.join(fonts, "Anton-Regular.woff2")) and os.path.exists(os.path.join(fonts, "Montserrat-Variable.woff2")):
        for name in os.listdir(fonts):
            if name.endswith(".ttf"):
                os.remove(os.path.join(fonts, name))

def flag_large_assets():
    for root in (os.path.join(ROOT, "assets"), OUT):
        for dirpath, _, names in os.walk(root):
            for name in names:
                full = os.path.join(dirpath, name)
                n = os.path.getsize(full)
                if n > 300 * 1024:
                    print(f"LARGE {n} bytes  {os.path.relpath(full, ROOT)}")

def write_manifest():
    icons = []
    for name, size in (("icon-192.png", "192x192"), ("icon-512.png", "512x512")):
        rel = f"assets/{name}"
        icons.append({"src": "/" + asset(rel), "sizes": size, "type": "image/png", "purpose": "any"})
    manifest = {
        "name": "Vector Picks",
        "short_name": "Vector Picks",
        "description": CFG["description"],
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#081834",
        "theme_color": "#081834",
        "icons": icons,
    }
    with open(os.path.join(OUT, "site.webmanifest"), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

# ---------------------------------------------------------------- AI picks
def load_ai_weeks():
    """data/ai-picks/YYYY-wNN.json, one file per week (same shape as 2026-w03.json)."""
    weeks = []
    for p in sorted(glob.glob(os.path.join(DATA, "ai-picks", "*.json"))):
        w = json.load(open(p))
        w["_path"] = p
        w["slug"] = f"ai-picks-{w['season']}-w{int(w['week']):02d}"
        regrade_ai_week(w)
        weeks.append(w)
    weeks.sort(key=lambda w: (w["season"], w["week"]))
    return weeks

def fmt_units(u):
    return (f"{u:g}U")

BANNED_PUBLIC = re.compile(r"dr\.?\s*bob|walterfootball|walter football|\bwalt\b", re.I)
PICK_RE = re.compile(r"^([A-Z]{2,3})\s+([+-])(\d+(?:\.\d+)?)$")
FINAL_RE = re.compile(r"^([A-Z]{2,3})\s+(\d+),\s*([A-Z]{2,3})\s+(\d+)$")
ATS_BADGE = {"W": ("win", "WIN"), "L": ("loss", "LOSS"), "P": ("push", "PUSH")}

def parse_ats_pick(pick):
    """Team and the points added to that team's score. None when it is not a side."""
    if not isinstance(pick, str):
        return None
    m = PICK_RE.match(pick.strip())
    if not m:
        return None
    points = float(m.group(3))
    return m.group(1), (points if m.group(2) == "+" else -points)

def final_score(g):
    """(away, home) only when the game is final. In-progress scores are ignored."""
    sc = g.get("score")
    if isinstance(sc, dict):
        if sc.get("status") != "final":
            return None
        try:
            return int(sc["away"]), int(sc["home"])
        except (KeyError, TypeError, ValueError):
            return None
    final = g.get("final")
    if not isinstance(final, str):
        return None
    m = FINAL_RE.match(final.strip())
    if not m:
        return None
    away, home = g["game"].split("@")
    if m.group(1) != away or m.group(3) != home:
        return None
    return int(m.group(2)), int(m.group(4))

def grade_ats(pick, g):
    """W/L/P at the listed line, or None when the game is not final."""
    parsed = parse_ats_pick(pick)
    scored = final_score(g)
    if not parsed or not scored:
        return None
    team, spread = parsed
    away, home = g["game"].split("@")
    away_s, home_s = scored
    if team == away:
        margin = away_s + spread - home_s
    elif team == home:
        margin = home_s + spread - away_s
    else:
        raise SystemExit(f"{g['game']}: pick {pick!r} is not one of the two teams")
    if margin > 0:
        return "W"
    if margin < 0:
        return "L"
    return "P"

def json_num(n):
    n = float(n)
    return int(n) if n == int(n) else n

def tally_marks(marks):
    w = l = p = pending = 0
    for mark in marks:
        if mark == "W":
            w += 1
        elif mark == "L":
            l += 1
        elif mark == "P":
            p += 1
        else:
            pending += 1
    return [w, l, p], pending

def as_pick(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("pick") or "").strip()
    return ""

def vector_bet_rows(raw, games, sides=None):
    """Ordered (game id, pick, units or None).

    Dict form is game-id keyed (Best Bets and Leans). List form is
    {game, pick, units}, the contest card used from Week 4.
    """
    known = {g["game"] for g in games}
    by_pick = {}
    if isinstance(sides, dict):
        for gid, value in sides.items():
            pick = as_pick(value)
            if gid in known and pick:
                by_pick.setdefault(pick, gid)
    rows = []
    if isinstance(raw, dict):
        for gid, value in raw.items():
            pick = as_pick(value)
            if gid in known and pick:
                units = value.get("units") if isinstance(value, dict) else None
                rows.append((gid, pick, units))
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                pick, gid, units = item.strip(), None, None
            elif isinstance(item, dict):
                pick = as_pick(item)
                gid = item.get("game") or None
                units = item.get("units")
            else:
                continue
            if not gid:
                gid = by_pick.get(pick)
            if gid in known and pick and parse_ats_pick(pick):
                rows.append((gid, pick, units))
    return rows

def vector_full_sides(vec, games):
    sides = vec.get("sides") if vec else None
    game_ids = [g["game"] for g in games]
    return isinstance(sides, dict) and bool(game_ids) and all(gid in sides for gid in game_ids)

def vector_published(vec, games):
    """Best bets, leans, grid sides, and stated best-bet units.

    A full `sides` map is the grid when every game is listed. Otherwise the
    grid is Best Bets and Leans only, with a dash on the rest.
    """
    if not vec:
        return {}, {}, {}, {}
    game_ids = [g["game"] for g in games]
    sides = vec.get("sides") if isinstance(vec.get("sides"), dict) else {}
    best_rows = vector_bet_rows(vec.get("best_bets"), games, sides)
    lean_rows = vector_bet_rows(vec.get("leans"), games, sides)
    best = {gid: pick for gid, pick, _ in best_rows}
    leans = {gid: pick for gid, pick, _ in lean_rows}
    units = {gid: u for gid, _, u in best_rows}
    if vector_full_sides(vec, games):
        full = {}
        for gid in game_ids:
            pick = as_pick(sides.get(gid))
            if pick and not parse_ats_pick(pick):
                raise SystemExit(f"{gid}: vector side {pick!r} is not a spread")
            if parse_ats_pick(pick):
                full[gid] = pick
        return best, leans, full, units
    shown = dict(best)
    shown.update(leans)
    return best, leans, shown, units

def vector_pick_game(vec, best, leans, pick):
    sides = vec.get("sides") if isinstance(vec.get("sides"), dict) else {}
    for gid, pk in list(sides.items()) + list(best.items()) + list(leans.items()):
        if pk == pick:
            return gid
    return None

def regrade_ai_week(w):
    """Grade every listed side from stored final scores and write the results back.

    Updating a game's score and rebuilding recomputes highlights and the scoreboard.
    Games without status "final" stay ungraded.
    """
    games = {g["game"]: g for g in w["games"]}
    for g in w["games"]:
        scored = final_score(g)
        if not scored:
            continue
        away, home = g["game"].split("@")
        g["final"] = f"{away} {scored[0]}, {home} {scored[1]}"
    best, leans, shown, bet_units = vector_published(w.get("vector") or {}, w["games"])
    picks = {}
    def add(gid, pick):
        if gid in games and isinstance(pick, str) and pick.strip():
            picks.setdefault(gid, set()).add(pick.strip())
    for a in w.get("ais") or []:
        for gid, pick in (a.get("sides") or {}).items():
            add(gid, pick)
        for b in a.get("best_bets") or []:
            add(next((gid for gid, pk in (a.get("sides") or {}).items() if pk == b.get("pick")), None), b.get("pick"))
        for pick in a.get("pick5") or []:
            add(next((gid for gid, pk in (a.get("sides") or {}).items() if pk == pick), None), pick)
    for gid, pick in {**best, **leans, **shown}.items():
        add(gid, pick)
    results = {}
    for g in w["games"]:
        gid = g["game"]
        bucket = {}
        for pick in sorted(picks.get(gid) or []):
            mark = grade_ats(pick, g)
            if mark:
                bucket[pick] = mark
        if bucket:
            results[gid] = bucket
    w["results"] = results
    def mark_of(gid, pick):
        return (results.get(gid) or {}).get(pick)
    def side_gid(a, pick):
        for gid, pk in (a.get("sides") or {}).items():
            if pk == pick:
                return gid
        return None
    grades = {}
    for a in w.get("ais") or []:
        side_marks = [mark_of(gid, pick) for gid, pick in (a.get("sides") or {}).items()]
        sides, sides_pending = tally_marks(side_marks)
        units = 0.0
        bb_marks = []
        for b in a.get("best_bets") or []:
            mark = mark_of(side_gid(a, b.get("pick")), b.get("pick"))
            bb_marks.append(mark)
            if mark == "W":
                units += float(b.get("units") or 0)
            elif mark == "L":
                units -= float(b.get("units") or 0)
        _, bb_pending = tally_marks(bb_marks)
        p5_marks = [mark_of(side_gid(a, pick), pick) for pick in (a.get("pick5") or [])]
        pick5, pick5_pending = tally_marks(p5_marks)
        grades[a["id"]] = {
            "sides": sides,
            "sides_pending": sides_pending,
            "best_bet_units": json_num(units),
            "best_bets_pending": bb_pending,
            "pick5": pick5,
            "pick5_pending": pick5_pending,
        }
    if w.get("vector"):
        # Stated unit size when the card has one; otherwise flat 1U. Leans count as sides, not best-bet units.
        vec = w["vector"]
        side_marks = [mark_of(gid, pick) for gid, pick in shown.items()]
        sides, sides_pending = tally_marks(side_marks)
        units = 0.0
        bb_marks = []
        for gid, pick in best.items():
            mark = mark_of(gid, pick)
            bb_marks.append(mark)
            stake = bet_units.get(gid)
            stake = 1.0 if stake is None else float(stake)
            if mark == "W":
                units += stake
            elif mark == "L":
                units -= stake
        _, bb_pending = tally_marks(bb_marks)
        p5_list = vec.get("pick5") if isinstance(vec.get("pick5"), list) else []
        entry = {
            "sides": sides,
            "sides_pending": sides_pending,
            "best_bet_units": json_num(units),
            "best_bets_pending": bb_pending,
            "pick5": None,
        }
        if p5_list:
            p5_marks = [mark_of(vector_pick_game(vec, best, leans, pick), pick) for pick in p5_list]
            pick5, pick5_pending = tally_marks(p5_marks)
            entry["pick5"] = pick5
            entry["pick5_pending"] = pick5_pending
        grades["vector"] = entry
    w["grades"] = grades
    ungraded = [g["game"] for g in w["games"] if g["game"] in picks and not final_score(g)]
    w["ungraded_games"] = ungraded
    w["graded"] = not ungraded and bool(picks)
    save_ai_week(w)

def save_ai_week(w):
    path = w.get("_path")
    if not path:
        return
    data = {k: v for k, v in w.items() if k != "slug" and not str(k).startswith("_")}
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if os.path.exists(path) and open(path).read() == text:
        return
    with open(path, "w") as f:
        f.write(text)

def ats_badge(res):
    if res not in ATS_BADGE:
        return ""
    cls, label = ATS_BADGE[res]
    return f' <span class="res res-{cls}">{label}</span>'

def ai_cell(pick, units=None, tag=None, res=None):
    if not pick:
        return '<span class="muted">&mdash;</span>'
    extra = ""
    if units is not None:
        extra += f' <span class="ai-u">{e(fmt_units(units))}</span>'
    if tag:
        extra += f' <span class="sub">{e(tag)}</span>'
    extra += ats_badge(res)
    return f"<b>{e(minus(pick))}</b>{extra}"

def pick_li(pick, res=None, units=None, sub=None):
    cls = ' class="covered"' if res == "W" else ""
    extra = ""
    if units is not None:
        extra += f' <span class="ai-u">{e(fmt_units(units))}</span>'
    if sub:
        extra += f' <span class="sub">{e(sub)}</span>'
    extra += ats_badge(res)
    return f"<li{cls}>{e(minus(pick))}{extra}</li>"

def ai_scoreboard(ai_weeks):
    """Season totals from stored grades. Partial weeks still show the games that are final."""
    last = ai_weeks[-1]
    entrants = [(a["id"], a["name"]) for a in last["ais"]]
    vec = last.get("vector")
    tot = {}
    for w in ai_weeks:
        for eid, g in (w.get("grades") or {}).items():
            t = tot.setdefault(eid, {"s": [0, 0, 0], "s_pend": 0, "u": 0.0, "u_pend": 0, "p5": [0, 0, 0], "p5_pend": 0, "has_p5": False})
            for i, n in enumerate(g.get("sides") or [0, 0, 0]):
                t["s"][i] += n
            t["s_pend"] += g.get("sides_pending") or 0
            t["u"] += g.get("best_bet_units") or 0
            t["u_pend"] += g.get("best_bets_pending") or 0
            if g.get("pick5") is not None:
                t["has_p5"] = True
                for i, n in enumerate(g["pick5"]):
                    t["p5"][i] += n
                t["p5_pend"] += g.get("pick5_pending") or 0
    pend_txt = "Grades after Monday night"
    def pend_sub(n):
        return f'<span class="sub">{int(n)} not final</span>' if n else ""
    def row(eid, name, has_p5=True, cls=""):
        t = tot.get(eid)
        if not t:
            cells = f'<td data-l="Sides W-L-P" class="muted">{pend_txt}</td><td data-l="Best-bet units" class="muted">{pend_txt}</td><td data-l="Pick 5" class="muted">{pend_txt if has_p5 else "n/a"}</td>'
        else:
            p5 = (f'<b>{"-".join(map(str, t["p5"]))}</b>{pend_sub(t["p5_pend"])}') if (has_p5 and t["has_p5"]) else "n/a"
            cells = (f'<td data-l="Sides W-L-P"><b>{"-".join(map(str, t["s"]))}</b>{pend_sub(t["s_pend"])}</td>'
                     f'<td data-l="Best-bet units"><b>{minus(f"{t["u"]:+g}U")}</b>{pend_sub(t["u_pend"])}</td>'
                     f'<td data-l="Pick 5">{p5}</td>')
        attr = f' class="{cls}"' if cls else ""
        return f'<tr{attr}><td class="game" data-l="Entrant"><b>{e(name)}</b></td>{cells}</tr>'
    head = '<thead><tr><th scope="col">Entrant</th><th scope="col">Sides W-L-P</th><th scope="col">Best-bet units</th><th scope="col">Pick 5</th></tr></thead>'
    ai_rows = "".join(row(i, n) for i, n in entrants)
    ai_tbl = f'<h3>The AIs</h3><div class="table-wrap"><table class="rec-table ai-score">{head}<tbody>{ai_rows}</tbody></table></div>'
    ref_rows = ""
    if vec:
        ref_rows += row("vector", vec["name"] + " (ours)", cls="vec-row")
    ref_tbl = f'<h3>Super Agent Vector (ours, not an AI chatbot entry)</h3><div class="table-wrap"><table class="rec-table ai-score">{head}<tbody>{ref_rows}</tbody></table></div>' if ref_rows else ""
    if ref_tbl:
        full = any(vector_full_sides(w.get("vector") or {}, w.get("games") or []) for w in ai_weeks)
        has_p5 = any(isinstance((w.get("vector") or {}).get("pick5"), list) and (w.get("vector") or {}).get("pick5") for w in ai_weeks)
        if full or has_p5:
            ref_tbl += '<p class="note">Vector sides are every game on a week that publishes a full side map, and Best Bets plus Leans on earlier weeks. Best-bet units use the stated size, or flat 1U when none is stated. Pick 5 counts when Vector published one.</p>'
        else:
            ref_tbl += '<p class="note">Vector sides are the published Best Bets and Leans. Best-bet units are flat 1U. Pick 5 does not apply.</p>'
    notes = []
    for w in ai_weeks:
        if w.get("graded"):
            continue
        left = w.get("ungraded_games") or []
        labels = []
        by_id = {g["game"]: g.get("label") or g["game"] for g in w.get("games") or []}
        for gid in left:
            labels.append(by_id.get(gid, gid))
        if w.get("grades") and labels:
            if len(labels) == len(w.get("games") or []):
                notes.append(f"Week {w['week']} {w['season']}: no finals yet, so those picks are left out of the records above.")
            else:
                notes.append(f"Week {w['week']} {w['season']}: {e(', '.join(labels))} not final, so those picks are left out of the records above.")
        elif not w.get("grades"):
            notes.append(f"Week {w['week']} {w['season']}: <b>{pend_txt}</b> (pending).")
    pend_note = f'<p class="note">{" ".join(notes)}</p>' if notes else ""
    return ai_tbl + ref_tbl + pend_note

def build_ai_picks(w, ai_weeks, fname):
    ais = w["ais"]
    vec = w.get("vector") or {}
    res = w.get("results") or {}
    games = {g["game"]: g for g in w["games"]}
    best, leans, shown, bet_units = vector_published(vec, w["games"])
    full_card = vector_full_sides(vec, w["games"])
    p5_list = vec.get("pick5") if isinstance(vec.get("pick5"), list) else []
    def cell(name, pick, gid, extra_cls=""):
        mark = (res.get(gid) or {}).get(pick) if pick else None
        cls = " ".join(x for x in (extra_cls, "covered" if mark == "W" else "") if x)
        attr = f' class="{cls}"' if cls else ""
        return f'<td data-l="{e(name)}"{attr}>{ai_cell(pick, res=mark)}</td>'
    rows = ""
    for g in w["games"]:
        gid = g["game"]
        final = f'<span class="sub">Final: {e(g["final"])}</span>' if g.get("final") else ""
        cells = "".join(cell(a["name"], (a.get("sides") or {}).get(gid), gid) for a in ais)
        if vec:
            cells += cell("Vector", shown.get(gid), gid, "vec-col")
        rows += f'<tr><td class="game"><b>{e(g["label"])}</b><span class="sub">{e(g["day"])} {e(g["date"][5:].replace("-", "/"))}{(" &middot; " + e(g["kickoff_pt"])) if g.get("kickoff_pt") else ""}</span>{final}</td><td data-l="Westgate" class="muted">{e(minus(g["westgate"]))}</td>{cells}</tr>'
    head = '<th scope="col">Game</th><th scope="col">Westgate</th>' + "".join(f'<th scope="col">{e(a["name"])}</th>' for a in ais)
    if vec:
        head += '<th scope="col">Vector<span class="sub">ours</span></th>'
    def side_gid(a, pick):
        for gid, pk in (a.get("sides") or {}).items():
            if pk == pick:
                return gid
        return None
    cards = ""
    for a in ais:
        bb = "".join(pick_li(b["pick"], res=(res.get(side_gid(a, b["pick"])) or {}).get(b["pick"]), units=b["units"]) for b in a["best_bets"])
        p5 = "".join(pick_li(p, res=(res.get(side_gid(a, p)) or {}).get(p)) for p in a["pick5"])
        stamp = e(a["timing"]) if a.get("timing") else f'Received {e(a.get("received", ""))}'
        cards += f'<div class="panel"><h2>{e(a["name"])}</h2><p class="sub">{stamp}</p><h3>Best bets</h3><ul class="picks big">{bb}</ul><h3>Pick 5</h3><ol class="picks">{p5}</ol><p class="note">Tiebreaker: {e(a.get("tiebreaker", ""))}</p></div>'
    if vec:
        bb = "".join(pick_li(pk, res=(res.get(gid) or {}).get(pk), units=bet_units.get(gid), sub=(games.get(gid) or {}).get("label")) for gid, pk in best.items())
        ln = "".join(pick_li(pk, res=(res.get(gid) or {}).get(pk), sub=(games.get(gid) or {}).get("label")) for gid, pk in leans.items())
        leans_html = f'<h3>Leans</h3><ul class="picks">{ln}</ul>' if leans else ""
        if p5_list:
            p5 = "".join(pick_li(p, res=(res.get(vector_pick_game(vec, best, leans, p)) or {}).get(p)) for p in p5_list)
            p5_html = f'<h3>Pick 5</h3><ol class="picks">{p5}</ol><p class="note">Tiebreaker: {e(vec.get("tiebreaker", ""))}</p>'
            foot = '<p class="note">Our model, not a chatbot entry.</p>'
        else:
            p5_html = ""
            foot = '<p class="note">Our model, not a chatbot entry. No pick 5.</p>'
        cards += f'<div class="panel vec-card"><h2>Vector</h2><p class="sub">{e(vec.get("name") or "Super Agent Vector")} &middot; ours</p><h3>Best bets</h3><ul class="picks big">{bb}</ul>{leans_html}{p5_html}{foot}</div>'
    cons = "".join(f"<li>{e(minus(c))}</li>" for c in w.get("consensus", []))
    def vec_li(d, with_units=False):
        out = ""
        for gid, pk in d.items():
            if gid not in games:
                continue
            mark = (res.get(gid) or {}).get(pk)
            out += pick_li(pk, res=mark, units=bet_units.get(gid) if with_units else None, sub=games[gid]["label"])
        return out
    n_ais = {3: "three", 4: "four", 5: "five"}.get(len(ais), str(len(ais)))
    card_same_week = any(c.get("season") == w["season"] and int(c.get("week")) == int(w["week"]) for c in (globals().get("WEEKS") or []))
    card_link = ' Full numbers on the <a href="card.html">Weekly Card</a>.' if card_same_week else ""
    vec_blurb = f"Vector's own Week {w['week']} card from our model, kept separate from the {n_ais} chatbots.{card_link}"
    vec_html = ""
    if vec and leans and not p5_list:
        vec_html = f"""<section class="panel vec-block" id="vector"><p class="kicker">Not an AI chatbot entry &middot; our own model</p><h2><span class="g">{e(vec.get('name') or 'Super Agent Vector')}</span></h2>
<p class="note">{vec_blurb}</p>
<div class="summary-grid vec-grid"><div><h3>{tier_badge('Best Bet')} Best Bets</h3><ul class="picks big">{vec_li(best)}</ul></div>
<div><h3>{tier_badge('Lean')} Leans</h3><ul class="picks">{vec_li(leans)}</ul></div></div></section>"""
    elif vec:
        blocks = f'<div><h3>{tier_badge("Best Bet")} Best Bets</h3><ul class="picks big">{vec_li(best, with_units=True)}</ul></div>'
        if leans:
            blocks += f'<div><h3>{tier_badge("Lean")} Leans</h3><ul class="picks">{vec_li(leans)}</ul></div>'
        if p5_list:
            items = ""
            for p in p5_list:
                gid = vector_pick_game(vec, best, leans, p)
                mark = (res.get(gid) or {}).get(p) if gid else None
                items += pick_li(p, res=mark, sub=(games.get(gid) or {}).get("label") if gid else None)
            blocks += f'<div><h3>Pick 5</h3><ol class="picks">{items}</ol><p class="note">Tiebreaker: {e(vec.get("tiebreaker", ""))}</p></div>'
        vec_html = f"""<section class="panel vec-block" id="vector"><p class="kicker">Not an AI chatbot entry &middot; our own model</p><h2><span class="g">{e(vec.get('name') or 'Super Agent Vector')}</span></h2>
<p class="note">{vec_blurb}</p>
<div class="summary-grid vec-grid">{blocks}</div></section>"""
    names = " vs ".join(e(a["name"]) for a in ais)
    who = e(vec.get("name") or "Super Agent Vector")
    if full_card:
        grid_note = f"Each side is graded at the line that entrant listed. Vector is {who}, ours, with a side on every game. Yellow means the side covered. Pushes are not highlighted. Final scores are from ESPN, and games that are not final are not graded."
    else:
        grid_note = f"Each side is graded at the line that entrant listed. Vector is {who}, ours: Best Bets and Leans only, and a dash where we had no side. Yellow means the side covered. Pushes are not highlighted. Final scores are from ESPN, and games that are not final are not graded."
    cons_block = f'<section class="panel callout"><h2>Consensus</h2><ul class="picks">{cons}</ul></section>\n' if w.get("consensus") else ""
    body = f"""
<section class="hero hero-sm"><p class="kicker">Week {w['week']} &middot; {w['season']} &middot; AI vs AI</p><h1>AI <span class="g">Picks</span></h1>
<p class="muted">{e(w['intro'])}</p><p class="note">{e(w.get('prompt_note', ''))}</p></section>
{cons_block}<section class="panel"><h2>Game by game: {names}, plus Vector</h2>
<p class="note">{grid_note}</p>
<div class="table-wrap"><table class="rec-table ai-grid"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Lines: {e(w['line_source'])}</p></section>
<section class="summary-grid ai-cards">{cards}</section>
{vec_html}
<section class="panel" id="scoreboard"><h2>Season <span class="g">Scoreboard</span></h2>{ai_scoreboard([x for x in ai_weeks if (x['season'], x['week']) <= (w['season'], w['week'])])}
<p class="note">Entertainment and opinion only. Nothing here is betting advice.</p></section>
"""
    if fname == "ai-picks.html" and len(ai_weeks) > 1:
        items = "".join(f'<li><a href="{x["slug"]}.html">Week {x["week"]} &middot; {x["season"]}</a></li>' for x in reversed(ai_weeks))
        body += f'<section class="panel"><h2>All AI pick weeks</h2><ul class="weeklist">{items}</ul></section>\n'
    if BANNED_PUBLIC.search(body) or any(BANNED_PUBLIC.search(a.get("name") or "") or BANNED_PUBLIC.search(a.get("id") or "") for a in ais):
        raise SystemExit(f"{fname}: refused to publish Dr. Bob or WalterFootball / Walt picks")
    archived = fname != "ai-picks.html"
    title = f"AI Picks Week {w['week']} {w['season']}" + (" archive" if archived else "")
    desc = (f"{'Archived ' if archived else ''}Week {w['week']} {w['season']} NFL picks against the spread from {", ".join(a["name"] for a in ais[:-1])} and {ais[-1]["name"]}, "
            f"side by side, plus Super Agent Vector's own card. Entertainment only.")
    page(fname, title, body, desc=desc, active="ai-picks.html")

# ---------------------------------------------------------------- misc
def build_misc():
    pages = ["", "card.html", "live.html", "record.html", "methodology.html", "episodes.html", "shorts.html"] + \
            [f"{w['slug']}.html" for w in WEEKS] + \
            (["ai-picks.html"] + [f"{w['slug']}.html" for w in AI_WEEKS] if AI_WEEKS else [])
    urls = "".join(f"<url><loc>{BASE}/{p}</loc></url>" for p in pages)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    page("404.html", "Page not found", '<section class="hero hero-sm"><h1>404</h1><p class="muted">That page is not on the card. <a href="index.html">Back home</a>.</p></section>',
         desc="That page is not on the Vector Picks card. Go back to the weekly NFL picks.")
    write_manifest()

def main():
    global WEEKS, AI_WEEKS
    subset_fonts()
    convert_webp()
    recompress_pngs()
    # public/ is fully generated; keep episodes/ (mp3s you drop in) between builds
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        p = os.path.join(OUT, name)
        if name == "episodes":
            continue
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    os.makedirs(os.path.join(OUT, "episodes"), exist_ok=True)
    drop_unreferenced_fonts()
    write_public_css()
    generate_icons()
    index_assets()
    flag_large_assets()
    WEEKS = load_weeks()
    rows = load_tracker()
    tidx = tracker_index(rows)
    eps = load_episodes()
    sh = load("shorts.json")
    for w in WEEKS:
        build_card(w, tidx, w["slug"] + ".html")
    build_card(WEEKS[-1], tidx, "card.html")
    # append archive list to card.html
    with open(os.path.join(OUT, "card.html")) as f:
        doc = f.read()
    doc = doc.replace("</main>", build_week_index(WEEKS) + "\n</main>")
    open(os.path.join(OUT, "card.html"), "w").write(doc)
    build_record(rows, tidx)
    AI_WEEKS = load_ai_weeks()
    for aw in AI_WEEKS:
        build_ai_picks(aw, AI_WEEKS, aw["slug"] + ".html")
    if AI_WEEKS:
        build_ai_picks(AI_WEEKS[-1], AI_WEEKS, "ai-picks.html")
    build_episodes(eps)
    build_shorts(sh)
    build_home(WEEKS, rows, tidx, eps, sh)
    write_live_spreads(WEEKS[-1])
    build_live(WEEKS[-1])
    build_methodology()
    build_feed(eps, os.path.join(OUT, "feed.xml"))
    build_misc()
    print(f"Built {len(os.listdir(OUT))} entries in public/ (latest card: Week {WEEKS[-1]['week']} {WEEKS[-1]['season']}; "
          f"{len(rows)} tracker rows; {len(eps)} episodes)")
    if "--validate" in sys.argv:
        validate_feed(os.path.join(OUT, "feed.xml"), expect_items=len(eps))
        validate_live(WEEKS[-1])
        validate_analytics()
        validate_seo()
        test_out = os.path.join(ROOT, "tests", "feed.test.xml")
        build_feed(load_episodes(os.path.join(ROOT, "tests", "sample_episodes.json")), test_out)
        validate_feed(test_out, expect_items=1)

if __name__ == "__main__":
    main()
