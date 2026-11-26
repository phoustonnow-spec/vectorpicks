#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the Week 12 card
(GB @ LAR graded WIN, 15 pending, KC +2.5 highlighted, no Best Bets), the Week 12 AI board,
the graded Week 11 Thursday card (6-7, including Monday night), and the
tracked-weeks record with that one Lean win counted.
Exit 1 when production is still the rankings-only page or is missing a marker.

  python3 scripts/verify_live.py
"""
import sys
import urllib.request
from datetime import datetime, timezone

HOME_URL = "https://www.vectorpicks.com/"
SHORTS_URL = "https://www.vectorpicks.com/shorts.html"
CARD_URL = "https://www.vectorpicks.com/card.html"
RECORD_URL = "https://www.vectorpicks.com/record.html"
LIVE_URL = "https://www.vectorpicks.com/live.html"
AI_URL = "https://www.vectorpicks.com/ai-picks.html"
W9_CARD_URL = "https://www.vectorpicks.com/card-2026-w09.html"
W10_CARD_URL = "https://www.vectorpicks.com/card-2026-w10.html"
LIVE_MARKERS = (
    "Live Board",
    "assets/live.js",
    "Our Spread is the Week 12",
    "Entertainment and opinion only",
)
HOME_MARKERS = (
    "Week 12",
    "Thursday, Nov 26, 2026 PT",
    'id="highlight"',
    "Thanksgiving night",
    "KC @ BUF",
    "KC +2.5",
    "Thursday Nov 26, 5:20 PM PT",
    "Westgate KC +2.5 (BUF \u22122.5)",
    "Our Spread BUF \u22122.2",
    "Gap 0.3",
    "Card, near coin flip.",
    "GB @ LAR: LAR \u22122.5 WIN",
    "GB 13, LAR 26",
    "CHI \u22122.5 at DET (10:00 AM PT, Card, coin flip)",
    "No Best Bets",
    "No Best Bets this week so far. Updates Saturday.",
    "Leans: LAR \u22122.5, ATL +7, IND +7.",
    "Model side only, not a recommendation: PHI +8.5 at DAL, MIA +3.5 vs NYJ.",
    "1 of 16 graded. 15 games pending.",
    "Week 12 so far 1-0 (Leans 1-0; Best Bets 0-0; Card 0-0).",
    "not a fresh fully reconciled rerun",
    "Tiers are confidence labels, not proven probabilities.",
    "Wednesday picks, Saturday update.",
    "Week 11 final 6-7 (Best Bets 1-0, Leans 1-1, Card 4-6).",
    "CIN 20, WAS 22",
    "IND 3, HOU 26",
    "Graded rows stay the Thursday card.",
    'id="week-11-recap"',
    "Official Westgate standings thru Week 11",
    "LAMBDA LAMBDA LAMBDA-1 39-15-1",
    "Wk11 3-2",
    "Official Westgate Week 10 standings",
    "THREAD CLOD FOOL-1 33-17-0",
    "BIG LIB-1 32-17-1",
    "The crowd top 5 went 3-2 in the SuperContest and 2-3 in Gold.",
    'id="rankings"',
    "Vector power rankings entering Week 12",
    "Injury adjustments are built player by player for all 32 teams but remain provisional until midweek practice reports",
    "<b>BUF</b></td><td>5.2</td>",
    "<b>ARI</b></td><td>\u22129.8</td>",
    "13-10-0",
    "18-25-0",
    "11-13-1",
    "43-49-1",
    "+3u",
    "-7u",
    "-2u",
    "-6u",
    "0 pending",
    "2 pending",
    "13 pending",
    "15 pending",
    "Tracked weeks",
    "VMwVPQtbbeo",
    'data-yt="VMwVPQtbbeo"',
    "Week 12 NFL AI Picks: LAR -2.5 Tonight (GB @ LAR) | Week 11 Recap",
    "Entertainment only, not betting advice",
    "Entertainment and opinion only. Not betting advice.",
)
SHORTS_MARKERS = (
    "VMwVPQtbbeo",
    "Week 12 NFL AI Picks: LAR -2.5 Tonight (GB @ LAR) | Week 11 Recap",
    "aXnadwU-Z7U",
    "Week 11 Westgate SuperContest Top 5 Leaders",
    "MATTLEGEND27-1 34-16",
    "RJ551155-3 33-17",
    "TB +7 (4 of 5)",
    "Contest-leader rows are not Vector picks",
    "Entertainment only, not betting advice",
    "Qd7DWqq_jy8",
    "Week 11 Saturday Update: IND +12.5 Lost TNF, TB +7 Now a Best Bet | Vector Picks",
    "LqjTjbZOWb4",
    "Week 11 NFL AI Picks: IND +12.5 TNF, WAS +6.5 Best Bet | Week 10 Recap",
    "8cZ7qpdWyvU",
    "Week 10 Westgate SuperContest Top 5 Leaders",
    "NEOPOLITAN-1 30-14-1",
    "Leaders agree (2+ of 5)",
    "Entertainment only, not betting advice",
    "fvn8h67Mze0",
    "Week 10 Saturday Update: WAS Covered TNF, MIN Moves Up | Vector Picks",
    "1cY3MSjjkzE",
    "Week 10 NFL AI Picks: WAS +2.5 TNF, DAL",
    "4-NrBHuRlUE",
    "q2OazIWZ5vE",
    "81Pq1yT8hQQ",
    "Week 8 Westgate SuperContest Top 5 Leaders",
    "Week 4 Westgate SuperContest Top 5 Leaders",
    "LAMBDA LAMBDA LAMBDA-1 29-10-1",
    "LAMBDA LAMBDA LAMBDA-1 32-12-1",
    "Official Westgate standings thru Week 11",
    "LAMBDA LAMBDA LAMBDA-1 39-15-1",
    "Official Westgate Week 10 standings",
    "LAMBDA LAMBDA LAMBDA-1 36-13-1",
    "Sunday Nov 8, 2026 unofficial snapshot",
    "Entertainment and opinion only. Not betting advice.",
    'id="week-9-results"',
    "Unofficial.",
    "Not Westgate official standings",
    "until Westgate posts the Week 9 standings",
    "SuperContest top 5",
    "SuperContest Gold top 6",
    "tie for fifth",
    "11-11 with 3 pending",
    "9-16 with 5 pending",
    "THREAD CLOD FOOL-1",
    "JERRYDABEST-1",
    "JUST WIN BABY-1",
    "RJ551155-1",
    "JD3-1",
    "BUF@MIN (Monday night) is Pending",
)
CARD_MARKERS = (
    "Wed 2026-11-25 ~7:15 AM PT",
    "https://www.youtube.com/shorts/VMwVPQtbbeo",
    'id="highlight"',
    "Thanksgiving night",
    "Thursday Nov 26, 5:20 PM PT",
    "KC +2.5",
    "GB @ LAR",
    "LAR \u22122.5",
    "GB 13, LAR 26",
    "Our Spread LAR \u22125.6",
    "No Best Bets",
    "ATL +7",
    "IND +7",
    "PHI +8.5",
    "MIA +3.5",
    "Model side only, not a recommendation",
    "not a fresh fully reconciled rerun",
    "Tiers are confidence labels, not proven probabilities.",
    "Wednesday picks, Saturday update.",
    "Entertainment only, not betting advice.",
    "Week 11 final 6-7 (Best Bets 1-0, Leans 1-1, Card 4-6).",
    "CIN 20, WAS 22",
    "PENDING",
)
AI_MARKERS = (
    "AI Picks Week 12 2026",
    "All 16 games are pending.",
    "Westgate line",
    "No Best Bets",
    "GB @ LAR",
    "LAR \u22122.5",
    "SF \u22123",
    "game.html",
    "ai-picks-2026-w12.html",
    "ai-picks-2026-w11.html",
    "ai-picks-2026-w10.html",
    "ai-picks-2026-w09.html",
)
RECORD_MARKERS = (
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "Week 9 final 3-10",
    "Best Bets 0-2",
    "Leans 3-8",
    "MIN +3.5 is a loss, BUF 23, MIN 6",
    "Tracked weeks",
    "not a full-season total",
    "12-10-0",
    "16-24-0",
    "7-7-1",
    "7-8-1",
    "36-42-1",
    "36-43-1",
    "+2u",
    "-8u",
    "-6u",
    "-7u",
    "Those 13 grade 9-4",
    "The full card also counts Hold and Provisional",
    "WAS +2.5",
    "WAS 24, NYG 21",
    "LAC 23, BAL 20",
    "IND +12.5",
    "IND 3, HOU 26",
    "WAS +6.5",
    "CIN 20, WAS 22",
    "Week 11 final 6-7 (Best Bets 1-0, Leans 1-1, Card 4-6).",
    "13-10-0",
    "17-25-0",
    "18-25-0",
    "11-13-1",
    "42-49-1",
    "43-49-1",
    "+3u",
    "-2u",
    "-6u",
    "The other 12 Week 11 rows stay pending",
    "Official Westgate standings thru Week 11",
    "LAMBDA LAMBDA LAMBDA-1 39-15-1",
    "Gaps, not a complete season",
    "Saturday tier changes are not folded in.",
    "GB@LAR",
    "GB 13, LAR 26",
    "15 pending",
)
W11_URL = "https://www.vectorpicks.com/ai-picks-2026-w11.html"
W11_MARKERS = (
    "Week 11",
    "archive",
    "PROVISIONAL",
    "DraftKings line",
    "Not a Westgate card.",
    "1:16 PM PT",
    "All 13 games are pending.",
    "IND +12.5",
    "PIT \u22124.5",
    "NYJ +3",
    "CAR \u22122.5",
    "MIN +3",
    "Claude",
    "Gemini",
    "Grok",
    "ChatGPT",
)
W10_URL = "https://www.vectorpicks.com/ai-picks-2026-w10.html"
W9_URL = "https://www.vectorpicks.com/ai-picks-2026-w09.html"
W10_MARKERS = (
    "Week 10",
    "PROVISIONAL",
    "DraftKings line",
    "Not a Westgate card.",
    "Final: WAS 24, NYG 21",
    "Final: LAC 23, BAL 20",
    "Final: SF 46, DAL 40",
    "JAX −10.5",
    "DAL +4.5",
    "LV +6.5",
)
W9_MARKERS = (
    "Week 9",
    "DraftKings line",
    "Final: BUF 23, MIN 6",
    "Week 10 early look",
    "DAL +4.5",
)
W10_CARD_MARKERS = (
    "Week 10",
    "Week 10 final 7-7",
    "WAS +2.5",
    "WAS +0.3",
    "NYG \u22122.5",
    "DAL +4.5",
    "LAC +4.5",
    "SF 46, DAL 40",
    "LAC 23, BAL 20",
    "1cY3MSjjkzE",
    "fvn8h67Mze0",
    "8cZ7qpdWyvU",
    "Week 10 Saturday update (Nov 14, 2026)",
    "Official Westgate standings after Week 9",
    "Lines: Westgate SuperContest Week 10",
)
W9_CARD_MARKERS = (
    "Thu card line",
    "BAL +10",
    "WAS +5.5",
    "BUF 23, MIN 6",
    "JAX 33, BAL 10",
    "No side",
)
FORBIDDEN = (
    "cXnzFQPN7mE",
    "walterfootball",
    "walter football",
    "unexpected points",
    "kevin cole",
    "dr bob",
    "dr. bob",
    "oddstrader",
    "all 15 games are pending",
    "no top 5",
)
STALE = (
    "the Week 10 Vector card publishes after the official contest lines are out",
    "No Week 10 picks, edges, or line comparisons",
    "Week 10 Westgate card not posted yet",
    "Vector power rankings entering Week 10",
    "1 of 14 graded",
    "11-9-0",
)


def fetch(url):
    bust = url + ("&" if "?" in url else "?") + "cb=20261126w12thu"
    request = urllib.request.Request(bust, headers={
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": "vectorpicks-verify-live",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", "replace")
        print(
            f"{url} status {response.status} last-modified {response.headers.get('last-modified')} "
            f"bytes {len(body)} fetched {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        return response.status, body


def check(name, status, body, markers):
    missing = [m for m in markers if m not in body]
    present = [m for m in FORBIDDEN if m.lower() in body.lower()]
    if name in ("homepage", "live"):
        for edge in STALE + ("NYJ +8.5", "Week 10 early look", "Week 11 card pending", "No Week 11 picks, edges, or line comparisons"):
            if edge in body:
                present.append(edge)
    if name == "homepage":
        if '<ul class="picks big">' in body:
            present.append("home published a Best Bet list")
        leans = body.split("Leans:", 1)[-1].split("</p>", 1)[0]
        if "LAR" not in leans or "ATL +7" not in leans or "IND +7" not in leans or "PHI" in leans or "MIA" in leans:
            present.append("home Leans are not LAR, ATL, and IND")
        if "13 games pending. Not graded." in body or "1 of 13 graded. 12 games pending." in body or "7-7-1" in body or "36-42-1" in body or "12-10-0" in body:
            present.append("home still shows a pending or pre-grade Week 11 record")
        if "16 games pending. Not graded." in body or "17-25-0" in body or "42-49-1" in body or "Lean, not a Best Bet." in body or "Wednesday Nov 25, 5:00 PM PT" in body:
            present.append("home still shows Wednesday night GB @ LAR as the live pick")
        highlight = body.split('id="highlight"', 1)[-1].split("</div>", 1)[0]
        if "KC @ BUF" not in highlight or "GB @ LAR" in highlight or "PHI" in highlight:
            present.append("home highlight is not KC +2.5 at BUF")
        if "TB +7 at DET (QB status pending)" in body or "Vector numbers are provisional: injury layer still being reconciled" in body:
            present.append("home Week 11 block still reads as pending or provisional")
        if "Week 12 card pending" in body or "No Week 12 picks, edges, or line comparisons" in body:
            present.append("home still says the Week 12 card is unpublished")
    card_table = body.split("Full card: Market vs Our Spread", 1)[-1] if name == "card" else ""
    gb_row = card_table.split("GB @ LAR", 1)[-1].split("</tr>", 1)[0] if name == "card" else ""
    if name == "card" and (
        card_table.count("PENDING") != 15
        or card_table.count('res-win">WIN') != 1
        or 'res-loss">LOSS' in card_table
        or "Model side only, not a recommendation" not in card_table
        or "WIN" not in gb_row
        or "GB 13, LAR 26" not in gb_row
        or "PENDING" in gb_row
    ):
        present.append("Week 12 card is not GB @ LAR win plus 15 pending rows")
    if name == "homepage" and ('data-yt="VMwVPQtbbeo"' not in body or 'data-yt="aXnadwU-Z7U"' in body or 'data-yt="Qd7DWqq_jy8"' in body):
        present.append("home latest Short is not the Week 12 Short")
    if name == "live" and ("Week 12 has no card in the repo" in body or "Week 12 card pending" in body or "Our Spread is the Week 11" in body):
        present.append("live board is still the unpublished Week 12 notice")
    if name in ("card", "record"):
        for edge in (
            "the Week 10 Vector card publishes after the official contest lines are out",
            "No Week 10 picks, edges, or line comparisons",
            "Week 10 early look",
            "NYJ +8.5",
            "13 Week 10 rows are pending",
        ):
            if edge in body:
                present.append(edge)
    if name in ("homepage", "card"):
        for edge in ("Leans 19-23", "Card tier 9-7-1", "Full card 39-39-1"):
            if edge in body:
                present.append(edge)
    if name == "ai-picks":
        for edge in ("Week 10 early look", "Week 11 AI picks pending", "Week 12 AI picks pending", "1:16 PM PT", "DraftKings line", "No sides were invented."):
            if edge in body:
                present.append(edge)
    if name == "ai-picks-w11":
        for edge in (
            "Week 10 early look",
            "Week 11 AI picks pending",
            "No sides were invented.",
            "AI picks are not published yet",
        ):
            if edge in body:
                present.append(edge)
        claude = body.split("<h2>Claude</h2>", 1)[-1].split("<h2>", 1)[0]
        order = ["IND +12.5", "PIT \u22124.5", "NYJ +3", "CAR \u22122.5", "MIN +3"]
        pos = [claude.find(p) for p in order]
        if any(i < 0 for i in pos) or pos != sorted(pos):
            present.append("Claude top 5 is not IND +12.5, PIT -4.5, NYJ +3, CAR -2.5, MIN +3")
    if name == "week9-card" and ("WAS +2.5" in body or "1cY3MSjjkzE" in body or "fvn8h67Mze0" in body or "8cZ7qpdWyvU" in body or "Westgate SuperContest Week 10" in body):
        present.append("week 10 card leaked into the week 9 archive")
    if name == "week10-card" and ("Week 11" in body or "IND +12.5" in body or "WAS +6.5" in body or "LqjTjbZOWb4" in body or "aXnadwU-Z7U" in body):
        present.append("week 11 card leaked into the week 10 archive")
    order_bad = name == "shorts" and (
        body.find("VMwVPQtbbeo") > body.find("aXnadwU-Z7U")
        or body.find("aXnadwU-Z7U") > body.find("Qd7DWqq_jy8")
        or body.find("Qd7DWqq_jy8") > body.find("LqjTjbZOWb4")
        or body.find("LqjTjbZOWb4") > body.find("8cZ7qpdWyvU")
        or body.find("8cZ7qpdWyvU") > body.find("fvn8h67Mze0")
        or body.find("fvn8h67Mze0") > body.find("1cY3MSjjkzE")
        or body.find("1cY3MSjjkzE") > body.find("4-NrBHuRlUE")
        or body.find("4-NrBHuRlUE") > body.find("q2OazIWZ5vE")
    )
    if status != 200 or missing or present or order_bad:
        print(f"Live {name} does not match this build.")
        if status != 200:
            print(f"status {status}")
        if missing:
            print("missing: " + ", ".join(missing))
        if present:
            print("forbidden: " + ", ".join(present))
        if order_bad:
            print("Week 11 leaders Short is not before the Saturday, Thursday, and Week 10 Shorts")
        return False
    print(f"Live {name} contains the expected markers.")
    return True


def main():
    ok = True
    for name, url, markers in (
        ("homepage", HOME_URL, HOME_MARKERS),
        ("shorts", SHORTS_URL, SHORTS_MARKERS),
        ("live", LIVE_URL, LIVE_MARKERS),
        ("card", CARD_URL, CARD_MARKERS),
        ("record", RECORD_URL, RECORD_MARKERS),
        ("ai-picks", AI_URL, AI_MARKERS),
        ("ai-picks-w11", W11_URL, W11_MARKERS),
        ("ai-picks-w10", W10_URL, W10_MARKERS),
        ("ai-picks-w09", W9_URL, W9_MARKERS),
        ("week10-card", W10_CARD_URL, W10_CARD_MARKERS),
        ("week9-card", W9_CARD_URL, W9_CARD_MARKERS),
    ):
        status, body = fetch(url)
        ok = check(name, status, body, markers) and ok
    if not ok:
        print("WEBSITE NOT UPDATED")
        print("A green local build is not a publish. Merge to main, wait for Vercel, then run this again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
