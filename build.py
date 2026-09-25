#!/usr/bin/env python3
"""VectorPicks.com static site generator (stdlib only).

Usage:
  python3 build.py              # regenerate public/ from data/
  python3 build.py --validate   # build, then validate feed.xml (+ a test feed with a sample episode)

Inputs (data/):
  site_config.json   base_url, titles, podcast metadata (one place to change the domain)
  weeks/*.json       one file per week (e.g. 2026-w04.json); newest = "latest card"
  ats-tracker.csv    graded picks (synced from tracker_sync_from if that path exists)
  episodes.json      podcast episodes -> episodes.html + feed.xml
  shorts.json        YouTube Shorts list (+ local latest Short)
  methodology.html   methodology body
Static files in assets/ are copied to public/assets/.
The Live Board (live.html) reads /api/odds in the browser and joins it to
public/live-spreads.json, written here from the latest week's card.
"""
import csv, glob, html, json, os, re, shutil, sys
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
NAV = [("index.html", "Home"), ("card.html", "Weekly Card"), ("live.html", "Live Board"),
       ("record.html", "Record"), ("methodology.html", "Methodology"),
       ("episodes.html", "Podcast"), ("shorts.html", "Shorts")]

def page(fname, title, body, desc=None, active=None):
    active = active or fname
    nav = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{t}</a>' for h, t in NAV)
    full_title = f"{title} | {CFG['site_name']}" if title else f"{CFG['site_name']} | {CFG['title']}"
    desc = desc or CFG["description"]
    canon = f"{BASE}/" if fname == "index.html" else f"{BASE}/{fname}"
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(BASE)}/assets/og-image.png">
<meta property="og:url" content="{e(canon)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#081834">
<link rel="icon" href="assets/favicon.png" type="image/png">
<link rel="alternate" type="application/rss+xml" title="{e(CFG['title'])} podcast" href="feed.xml">
<link rel="stylesheet" href="assets/style.css">
</head>
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
  <p class="small">&copy; {date.today().year} {e(CFG['site_name'])} &middot; {e(CFG['title'])} &middot; <a href="{e(CFG.get('youtube_url',''))}" rel="noopener">YouTube {e(CFG.get('youtube_handle',''))}</a> &middot; <a href="mailto:{e(CFG['email'])}">{e(CFG['email'])}</a> &middot; <a href="feed.xml">Podcast RSS</a></p>
</footer>
<script src="assets/site.js" defer></script>
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
    body = f"""
<section class="hero hero-sm"><p class="kicker">Week {w['week']} &middot; {w['season']}</p><h1>Weekly <span class="g">Card</span></h1>
<p class="muted">As of {e(w['as_of'])}.</p></section>
<section class="summary-grid">
<div class="panel"><h2>{tier_badge('Best Bet')} Best Bets</h2><ul class="picks big">{li(s['best_bets'])}</ul></div>
<div class="panel"><h2>{tier_badge('Lean')} Leans</h2><ul class="picks">{li(s['leans'])}</ul></div>
<div class="panel"><h2>{tier_badge('Pass')} Passes</h2><ul class="picks">{li(s['passes'])}</ul></div>
</section>
<section class="panel"><h2>Full card: Market vs Our Spread</h2>
<p class="note"><b>Westgate</b> = contest line of record (graded here). <b>Market</b> = {e(w['market_source'])}. <b>Gap</b> = points between the Westgate line and Our Spread, toward the card side. {e(w['hfa_note'])}</p>
<div class="table-wrap"><table class="card-table"><thead><tr><th>Game</th><th>Westgate</th><th>Market</th><th>Our Spread</th><th>Gap</th><th>Tier</th><th>Card side</th><th>Result</th><th>Why</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section class="panel" id="powers"><h2>Power ratings: healthy &rarr; injury-adjusted</h2>
<p class="note">Points vs a league-average team. Injury &Delta; = our player-value layer (Out/Doubtful full value, Questionable/DNP ~half). Rank is display only.</p>
<div class="table-wrap"><table class="power-table"><thead><tr><th>#</th><th>Team</th><th>Healthy</th><th>Injury &Delta;</th><th>Adjusted</th><th>Drivers</th></tr></thead><tbody>{pw}</tbody></table></div></section>
<section class="panel"><h2>Missing / not used this week</h2><ul class="missing">{li(w.get('missing', []))}</ul>
<p class="note">Lines: {e(w['line_source'])}</p></section>
"""
    page(fname, f"Week {w['week']} {w['season']} Card", body,
         desc=f"Week {w['week']} {w['season']} NFL card: Westgate line vs Our Spread, gap and tier for every game.", active="card.html")

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
        head = "<th>Wk</th><th>Date</th><th>Game</th><th>Pick (line)</th><th>Our Spread</th><th>Gap</th><th>Tier</th><th>Result</th>" + ("<th>Score</th><th>Units</th>" if show_score else "")
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
<section class="hero hero-sm ep-hero"><img src="assets/podcast-cover-600.png" alt="{e(CFG['title'])} podcast cover" width="200" height="200">
<div><p class="kicker">Podcast</p><h1>{e(CFG['title'])}</h1><p class="muted">Vector talks power ratings, our spreads and the weekly card. Four shows a week.</p>
<p><a class="btn" href="feed.xml">RSS feed</a></p></div></section>
<section class="panel"><h2>Shows</h2><ul class="shows">{shows}</ul></section>
<section class="panel"><h2>Episodes</h2>{lst}</section>
"""
    page("episodes.html", "Podcast", body, desc=f"{CFG['title']} podcast episodes: Tuesday Rankings, Thursday Picks, Sunday Update, Sunday Recap.")

def yt_id(url):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{6,})", url or "")
    return m.group(1) if m else None

def build_shorts(sh):
    cards = ""
    for s in sh["shorts"]:
        vid = yt_id(s.get("youtube_url"))
        if vid:
            cards += f'<div class="short"><div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{e(vid)}" title="{e(s.get("title",""))}" loading="lazy" allowfullscreen></iframe></div><p>{e(s.get("title",""))}</p></div>'
    for i in range(max(0, sh.get("placeholder_slots", 3) - len(sh["shorts"]))):
        cards += '<div class="short"><div class="yt placeholder"><span>YouTube Short<br>coming soon</span></div></div>'
    lt = sh.get("latest_local")
    latest = ""
    if lt:
        latest = f"""<section class="panel latest-short"><h2>Latest Short &middot; Week {lt['week']} {lt['season']}</h2>
<div class="short-feature"><video controls preload="none" poster="{e(lt['thumbnail'])}" src="{e(lt['video'])}" playsinline></video>
<div><h3>{e(lt['title'])}</h3><p class="muted">Vertical 9:16 recap. {'<a href="'+e(lt['youtube_url'])+'">Watch on YouTube</a>' if lt.get('youtube_url') else 'Follow <a href="'+e(CFG.get('youtube_url',''))+'">'+e(CFG.get('youtube_handle',''))+'</a> on YouTube for every Short.'}</p></div></div></section>"""
    body = f"""<section class="hero hero-sm"><p class="kicker">60 seconds, every week</p><h1><span class="g">Shorts</span></h1></section>
{latest}<section class="panel"><h2>On YouTube</h2><div class="shorts-grid">{cards}</div></section>"""
    page("shorts.html", "Shorts", body, desc="VectorPicks weekly NFL Shorts.")

def build_home(weeks, rows, tidx, eps, sh):
    w = weeks[-1]
    s = w["summary"]
    bb = "".join(f'<li>{e(minus(x))}</li>' for x in s["best_bets"])
    wk_rows = [r for r in rows if r["Season"] == w["season"] and int(r["Week"]) == w["week"]]
    wt = tally(wk_rows)
    cashed = [r for r in wk_rows if r["_res"] == "W"]
    cash_html = "".join(f'<div class="cashed">{e(minus(r["Pick"]+" "+r["Line"]))} CASHED <span>{e(r["Final Score"])}</span></div>' for r in cashed)
    ep = episode_card(eps[0]) if eps else '<div class="empty">First episode coming soon. <a href="episodes.html">Podcast page &rarr;</a></div>'
    lt = sh.get("latest_local") or {}
    body = f"""
<section class="hero"><p class="kicker">with VECTOR &middot; your AI analyst</p>
<h1>Week {w['week']}<br><span class="g">AI NFL Picks</span></h1>
<p class="muted">Our own power ratings. Our own spreads. Graded at the posted line, losses included.</p></section>
<div class="home-grid">
<section class="panel week-card"><div class="wc-head"><h2>Week {w['week']} &middot; {w['season']}</h2><div class="wk-rec"><small>WEEK {w['week']} RECORD</small><b>{wt['rec'][:-2] if wt['P']==0 else wt['rec']}</b></div></div>
<p class="kicker">{len(s['best_bets'])} Best Bets</p><ul class="picks big">{bb}</ul>{cash_html}
<p class="note">Leans: {e(minus(', '.join(s['leans'])))}.</p>
<div class="btn-row"><a class="btn" href="card.html">Full card &rarr;</a><a class="btn ghost" href="live.html">Live Board &rarr;</a></div></section>
{record_box(rows)}
<section class="panel"><h2>Latest episode</h2>{ep}</section>
<section class="panel"><h2>Latest Short</h2><a href="shorts.html" class="thumb-link"><img src="{e(lt.get('thumbnail',''))}" alt="{e(lt.get('title',''))}" loading="lazy" width="576" height="1024"></a><p class="muted">{e(lt.get('title',''))}</p></section>
<section class="panel how"><h2>How it works</h2><ol><li><b>Power ratings</b> in points vs average.</li><li><b>Injury layer</b> with a points value per player.</li><li><b>Our Spread</b>, built independent of Vegas.</li><li><b>Gap + checklist</b> decides Best Bet, Lean or Pass.</li></ol><a class="btn ghost" href="methodology.html">Methodology &rarr;</a></section>
</div>"""
    page("index.html", None, body)

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
<p class="muted">Upcoming NFL games. The market spread is the median of DraftKings, FanDuel, BetMGM and Caesars, from the home team's side. Negative means the home team is favored.</p></section>
<section class="panel">
<p id="live-updated" class="note" hidden></p>
<div id="live-board" class="table-wrap" aria-live="polite"><p class="muted">Loading lines…</p></div>
<p class="note">Our Spread is the Week {int(week['week'])} {int(week['season'])} card, restated on the same home-team side as the market number. <b>Gap</b> = Market &minus; Our Spread. A dash means that game has no Our Spread on the card.</p>
<div class="rg"><span class="age">21+</span> <span>Entertainment and opinion only. Not betting advice. Gambling problem? Call <a href="tel:18004262537"><b>1-800-GAMBLER</b></a>.</span></div>
</section>
<script src="assets/live.js" defer></script>
"""
    page("live.html", "Live Board", body,
         desc="Live NFL spreads from DraftKings, FanDuel, BetMGM and Caesars, next to this week's Our Spread. Entertainment and opinion only. Not betting advice. 21+.")

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
    # Independent spot check while this file is still the Week 3 2026 card.
    if week["season"] == 2026 and int(week["week"]) == 3:
        want = {
            ("Atlanta Falcons", "Green Bay Packers"): ("Green Bay Packers", -2.4),
            ("Las Vegas Raiders", "New Orleans Saints"): ("Las Vegas Raiders", -0.8),
            ("Houston Texans", "Indianapolis Colts"): ("Indianapolis Colts", -4.2),
            ("Minnesota Vikings", "Tampa Bay Buccaneers"): ("Minnesota Vikings", -5.4),
            ("Baltimore Ravens", "Dallas Cowboys"): ("Baltimore Ravens", -3.5),
        }
        for (away, home), (our_team, our_point) in want.items():
            g = next(x for x in data["games"] if x["away_team"] == away and x["home_team"] == home)
            if g["our_team"] != our_team or g["our_point"] != our_point:
                raise SystemExit(f"Our Spread mismatch for {away} @ {home}: {g['our_team']} {g['our_point']}")
    live_html = open(os.path.join(OUT, "live.html")).read()
    for needle in ("Live Board", "assets/live.js", "1-800-GAMBLER", "Entertainment and opinion only",
                   'href="live.html" aria-current="page"'):
        if needle not in live_html:
            raise SystemExit(f"live.html missing {needle}")
    for fname in ("index.html", "card.html", "record.html"):
        doc = open(os.path.join(OUT, fname)).read()
        if 'href="live.html"' not in doc:
            raise SystemExit(f"{fname} missing Live Board link")
    if "live-spreads.json" not in os.listdir(OUT):
        raise SystemExit("live-spreads.json was not written")
    print(f"OK live board: Week {data['week']} {data['season']}, {len(data['games'])} Our Spreads, nav + home link")

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

# ---------------------------------------------------------------- misc
def build_misc():
    pages = ["", "card.html", "live.html", "record.html", "methodology.html", "episodes.html", "shorts.html"] + \
            [f"{w['slug']}.html" for w in WEEKS]
    urls = "".join(f"<url><loc>{BASE}/{p}</loc></url>" for p in pages)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    page("404.html", "Not found", '<section class="hero hero-sm"><h1>404</h1><p class="muted">That page is not on the card. <a href="index.html">Back home</a>.</p></section>')

def main():
    global WEEKS
    # public/ is fully generated; keep episodes/ (mp3s you drop in) between builds
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        p = os.path.join(OUT, name)
        if name == "episodes":
            continue
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    os.makedirs(os.path.join(OUT, "episodes"), exist_ok=True)
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
        test_out = os.path.join(ROOT, "tests", "feed.test.xml")
        build_feed(load_episodes(os.path.join(ROOT, "tests", "sample_episodes.json")), test_out)
        validate_feed(test_out, expect_items=1)

if __name__ == "__main__":
    main()
