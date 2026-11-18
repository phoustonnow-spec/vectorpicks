#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the Week 11 rankings,
the graded Week 10 card, the tracked-weeks record, and the Week 11
provisional DraftKings AI board.
Exit 1 when production is still the Week 11 AI-picks pending notice or is missing a marker.

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
LIVE_MARKERS = (
    "Live Board",
    "Week 11",
    "Week 11 has no card in the repo",
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "Week 11 card pending",
    "No Week 11 picks, edges, or line comparisons",
    "Entertainment and opinion only",
)
HOME_MARKERS = (
    "Week 11",
    "Wednesday, Nov 18, 2026 PT",
    "Week 11 power rankings are posted. The Week 11 card is not.",
    'id="week-11-status"',
    "Week 11 card pending: the Westgate SuperContest Week 11 sheet was not posted as of Tue Nov 17, 2026 8:56 AM PT.",
    "No Week 11 picks, edges, or line comparisons are published here.",
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "Graded rows stay the Thursday card.",
    "DAL +4.5 vs SF",
    "LAC +4.5 at BAL",
    "SF 46, DAL 40",
    "LAC 23, BAL 20",
    "WAS 24, NYG 21",
    'id="rankings"',
    "Vector power rankings entering Week 11",
    "Injury adjustments are provisional this week",
    "<b>JAX</b></td><td>5.2</td>",
    "<b>ARI</b></td><td>−10.5</td>",
    "12-10-0",
    "16-24-0",
    "7-7-1",
    "36-42-1",
    "+2u",
    "-8u",
    "-6u",
    "Tracked weeks",
    "0 pending",
    "8cZ7qpdWyvU",
    'data-yt="8cZ7qpdWyvU"',
    "fvn8h67Mze0",
    "1cY3MSjjkzE",
    "Entertainment and opinion only. Not betting advice.",
)
SHORTS_MARKERS = (
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
    "Official Westgate standings after Week 9",
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
    "Week 11 card pending",
    "No Week 11 picks, edges, or line comparisons",
    "Week 10 final 7-7 (Best Bets 1-1, Leans 3-4, Card 3-2).",
    "WAS +2.5",
    "WAS +0.3",
    "DAL +4.5",
    "LAC +4.5",
    "SF 46, DAL 40",
    "LAC 23, BAL 20",
    "Lines: Westgate SuperContest Week 10",
    "Kickoff Thu Nov 12, 5:15 PM PT",
    "1cY3MSjjkzE",
    "fvn8h67Mze0",
    "8cZ7qpdWyvU",
    "Week 10 Saturday update (Nov 14, 2026)",
    "WAS 24, NYG 21",
    "WIN",
    "LOSS",
    "Week 9 final 3-10",
    "Official Westgate standings after Week 9",
    "NYG −2.5",
    "Best Bet",
    "Lean",
    "Stated tracker, Weeks 3-10 through TNF",
    "Entertainment only, not betting advice",
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
    "36-42-1",
    "+2u",
    "-8u",
    "-6u",
    "Those 13 grade 9-4",
    "The full card also counts Hold and Provisional",
    "WAS +2.5",
    "WAS 24, NYG 21",
    "LAC 23, BAL 20",
    "None yet.",
    "Official Westgate standings after Week 9",
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
    "13 games pending",
    "1 of 14 graded",
    "11-9-0",
)


def fetch(url):
    bust = url + ("&" if "?" in url else "?") + "cb=20261118w11"
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
        for edge in STALE + ("NYJ +8.5", "Week 10 early look"):
            if edge in body:
                present.append(edge)
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
    order_bad = name == "shorts" and (
        body.find("8cZ7qpdWyvU") > body.find("fvn8h67Mze0")
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
            print("Week 10 leaders Short is not before the Saturday, Thursday, and Week 9 Shorts")
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
