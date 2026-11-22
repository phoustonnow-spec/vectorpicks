#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the Week 11 Sunday
leaders Short on top of the Saturday update, the Thursday Westgate card, the
TNF loss, the tracked-weeks record, and the Week 11 provisional DraftKings AI board.
Exit 1 when production is still the Week 11 card-pending notice or is missing a marker.

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
    "Our Spread is the Week 11 2026 card (Westgate)",
    "Entertainment and opinion only",
    "assets/live.js",
)
HOME_MARKERS = (
    "Week 11",
    "Sunday, Nov 22, 2026 PT",
    "Thursday Nov 19, 2026 card",
    'id="tnf"',
    "IND +12.5",
    "HOU \u221212.5",
    "Our Spread IND +11.0",
    "Gap 1.5",
    "Thu Nov 19, 5:15 PM PT",
    "WAS +6.5 vs CIN (Mon)",
    "NO +11.5 at CHI",
    "TB +7 at DET (QB status pending)",
    "Model side only, not a recommendation: MIA +16.5 at BUF, PHI +4.5 vs PIT.",
    "1 of 13 graded. 12 games pending.",
    "Week 11 Saturday update (Nov 21, 2026)",
    "HOU 26, IND 3",
    "IND 3, HOU 26",
    "BAL +2.5",
    "TB +7 at DET",
    "Friday model build plus Saturday injury-status adjustments",
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "LAC 23, BAL 20 (LAC +4.5 won)",
    "Graded rows stay the Thursday card.",
    "DAL +4.5 vs SF",
    "SF 46, DAL 40",
    "WAS 24, NYG 21",
    "Official Westgate Week 10 standings",
    "LAMBDA LAMBDA LAMBDA-1 36-13-1",
    "AMICI2-1 33-16-1",
    "THREAD CLOD FOOL-1 33-17-0",
    "BIG LIB-1 32-17-1",
    "The crowd top 5 went 3-2 in the SuperContest and 2-3 in Gold.",
    "Westgate SuperContest Week 11 contest card (posted Wed Nov 18, 2026)",
    "Tiers are confidence labels, not proven probabilities.",
    "not a fresh full rerun",
    "Thursday picks, Saturday update.",
    'id="rankings"',
    "Vector power rankings entering Week 11",
    "Injury adjustments are provisional this week",
    "<b>JAX</b></td><td>5.2</td>",
    "<b>ARI</b></td><td>\u221210.5</td>",
    "12-10-0",
    "16-24-0",
    "7-8-1",
    "36-43-1",
    "+2u",
    "-8u",
    "-7u",
    "1 pending",
    "2 pending",
    "9 pending",
    "12 pending",
    "Tracked weeks",
    "aXnadwU-Z7U",
    'data-yt="aXnadwU-Z7U"',
    "Week 11 Westgate SuperContest Top 5 Leaders",
    "MATTLEGEND27-1 34-16",
    "RIGGED NFL-1 33-16-1",
    "RJ551155-3 33-17",
    "TB +7 (4 of 5)",
    "Contest-leader rows are not Vector picks",
    "Entertainment only, not betting advice",
    "Qd7DWqq_jy8",
    "Week 11 Saturday Update: IND +12.5 Lost TNF, TB +7 Now a Best Bet | Vector Picks",
    "LqjTjbZOWb4",
    "Week 11 NFL AI Picks: IND +12.5 TNF, WAS +6.5 Best Bet | Week 10 Recap",
    "Entertainment and opinion only. Not betting advice.",
)
SHORTS_MARKERS = (
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
    "Thursday Nov 19, 2026 card",
    "Thu Nov 19, 2026 ~8:45 AM PT",
    "IND +12.5",
    "HOU \u221212.5",
    "Our Spread IND +11.0",
    "WAS +6.5",
    "NO +11.5",
    "TB +7",
    "MIA +16.5",
    "PHI +4.5",
    "Model side only, not a recommendation",
    "PENDING",
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "LAC 23, BAL 20 (LAC +4.5 won)",
    "Lines: Westgate SuperContest Week 11 contest card (posted Wed Nov 18, 2026)",
    "Thu Nov 19, 5:15 PM PT",
    "Official Westgate Week 10 standings",
    "LAMBDA LAMBDA LAMBDA-1 36-13-1",
    "Tiers are confidence labels, not proven probabilities.",
    "not a fresh full rerun",
    "Thursday picks, Saturday update.",
    "Entertainment only, not betting advice.",
    "Byes: ATL, CLE, GB, LAR, NE, SEA",
    "https://www.youtube.com/shorts/LqjTjbZOWb4",
    "Week 11 NFL AI Picks: IND +12.5 TNF, WAS +6.5 Best Bet | Week 10 Recap",
    "https://www.youtube.com/shorts/aXnadwU-Z7U",
    "Week 11 Westgate SuperContest Top 5 Leaders",
    "MATTLEGEND27-1 34-16",
    "Contest-leader rows are not Vector picks",
    "TB +7 (4 of 5)",
    "https://www.youtube.com/shorts/Qd7DWqq_jy8",
    "Week 11 Saturday Update: IND +12.5 Lost TNF, TB +7 Now a Best Bet | Vector Picks",
    "Week 11 Saturday update (Nov 21, 2026)",
    "HOU 26, IND 3",
    "BAL +2.5",
    "IND 3, HOU 26",
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
    "12 pending",
    "Official Westgate Week 10 standings",
    "LAMBDA LAMBDA LAMBDA-1 36-13-1",
    "Gaps, not a complete season",
    "Saturday tier changes are not folded in.",
)
AI_MARKERS = (
    "Week 11",
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
    "Mexico City",
    "game.html",
    "ai-picks-2026-w11.html",
    "ai-picks-2026-w10.html",
    "ai-picks-2026-w09.html",
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
    bust = url + ("&" if "?" in url else "?") + "cb=20261122w11leaders"
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
        bb = body.split('<ul class="picks big">', 1)[1].split("</ul>", 1)[0]
        if "WAS +6.5 vs CIN (Mon)" not in bb or "MIA" in bb or "PHI" in bb:
            present.append("home Best Bets are not WAS +6.5 alone")
        if "13 games pending. Not graded." in body or "7-7-1" in body or "36-42-1" in body:
            present.append("home still shows the pre-TNF Week 11 record")
        sat = body.split('id="week-11-saturday"', 1)[-1].split("</section>", 1)[0]
        sat_bets = sat.split("<h3>Best Bets</h3>", 1)[-1].split("</ul>", 1)[0]
        if "TB +7 at DET" not in sat_bets or "WAS +6.5 vs CIN (Mon)" not in sat_bets or "MIA" in sat_bets or "PHI" in sat_bets:
            present.append("Saturday Best Bets are not TB +7 and WAS +6.5")
        rest = body.split("Rest of card:", 1)[1].split("</p>", 1)[0]
        if "MIA +16.5" in rest or "PHI +4.5" in rest:
            present.append("model-only sides are in the rest of the card")
    card_table = body.split("Full card: Market vs Our Spread", 1)[-1] if name == "card" else ""
    if name == "card" and (
        "https://www.youtube.com/shorts/Qd7DWqq_jy8" not in body
        or "https://www.youtube.com/shorts/LqjTjbZOWb4" not in body
        or "https://www.youtube.com/shorts/aXnadwU-Z7U" not in body
        or "MATTLEGEND27-1 34-16" not in body
        or "Contest-leader rows are not Vector picks" not in body
        or card_table.count("PENDING") != 12
        or "IND 3, HOU 26" not in card_table
    ):
        present.append("Week 11 card Short is missing or the card is not 12 pending rows plus the TNF loss")
    if name == "homepage" and ('data-yt="aXnadwU-Z7U"' not in body or 'data-yt="Qd7DWqq_jy8"' in body):
        present.append("home latest Short is not the Week 11 leaders Short")
    if name == "live" and ("Week 11 has no card in the repo" in body or "Week 11 card pending" in body):
        present.append("live board is still the Week 11 gap page")
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
    if name in ("ai-picks", "ai-picks-w11"):
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
        body.find("aXnadwU-Z7U") > body.find("Qd7DWqq_jy8")
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
