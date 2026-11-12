#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the Week 10 Westgate card.
Exit 1 when production is still the pre-card placeholder or is missing a marker.

  python3 scripts/verify_live.py
"""
import sys
import urllib.request
from datetime import datetime, timezone

HOME_URL = "https://www.vectorpicks.com/"
SHORTS_URL = "https://www.vectorpicks.com/shorts.html"
CARD_URL = "https://www.vectorpicks.com/card.html"
RECORD_URL = "https://www.vectorpicks.com/record.html"
AI_URL = "https://www.vectorpicks.com/ai-picks.html"
W9_CARD_URL = "https://www.vectorpicks.com/card-2026-w09.html"
HOME_MARKERS = (
    "Week 10",
    "Thursday, Nov 12, 2026 PT",
    "WAS +2.5",
    "Kickoff Thu Nov 12, 5:15 PM PT",
    "DAL +4.5 vs SF",
    "LAC +4.5 at BAL",
    "Lines: Westgate SuperContest Week 10",
    "injury layer is still being reconciled",
    "14 games pending",
    "Week 9 final 3-10",
    "Best Bets 0-2",
    "Leans 3-8",
    "MIN +3.5 is a loss, BUF 23, MIN 6",
    "Official Westgate standings after Week 9",
    "LAMBDA LAMBDA LAMBDA-1 32-12-1",
    "THREAD CLOD FOOL-1 30-15-0",
    "1cY3MSjjkzE",
    'data-yt="1cY3MSjjkzE"',
    'id="tnf"',
    'id="rankings"',
    "Vector power rankings entering Week 10",
    "Injury adjustments are provisional this week",
    "11-9-0",
    "13-20-0",
    "29-35-1",
    "Byes: CHI, DEN, PHI, TB",
)
SHORTS_MARKERS = (
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
    "WAS +2.5",
    "DAL +4.5",
    "LAC +4.5",
    "Lines: Westgate SuperContest Week 10",
    "Kickoff Thu Nov 12, 5:15 PM PT",
    "injury layer is still being reconciled",
    "1cY3MSjjkzE",
    "Week 10 NFL AI Picks",
    "PENDING",
    "Week 9 final 3-10",
    "Official Westgate standings after Week 9",
    "NYG −2.5",
    "Best Bet",
    "Lean",
)
RECORD_MARKERS = (
    "Week 9 final 3-10",
    "Best Bets 0-2",
    "Leans 3-8",
    "MIN +3.5 is a loss, BUF 23, MIN 6",
    "Tracked weeks",
    "not a full-season total",
    "11-9-0",
    "13-20-0",
    "29-35-1",
    "14 pending",
    "WAS +2.5",
    "PENDING",
    "Official Westgate standings after Week 9",
    "Gaps, not a complete season",
)
AI_MARKERS = (
    "Week 10",
    "PROVISIONAL",
    "DraftKings line",
    "Not a Westgate card.",
    "PROVISIONAL BOARD",
    "Byes: CHI, DEN, PHI, TB",
    "Munich",
    "Leans (provisional)",
    "Provisional top 5 (not Best Bets)",
    "JAX −10.5",
    "BUF −8.5",
    "NYG −2.5",
    "KC −3.5",
    "LV +6.5",
    "CLE +4.5",
    "ARI +9.5",
    "NYJ +8.5",
    "GB −3",
    "SF −4.5",
    "PIT +3.5",
    "IND −3.5",
    "HOU −4.5",
    "DAL +4.5",
    "MIN +3",
    "LAC +4.5",
    "WAS +2.5",
)
W10_URL = "https://www.vectorpicks.com/ai-picks-2026-w10.html"
W9_URL = "https://www.vectorpicks.com/ai-picks-2026-w09.html"
AI_MARKERS = AI_MARKERS + ("ai-picks-2026-w09.html", "ai-picks-2026-w10.html")
W10_MARKERS = (
    "Week 10",
    "PROVISIONAL",
    "DraftKings line",
    "Not a Westgate card.",
    "Provisional top 5 (not Best Bets)",
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
)


def fetch(url):
    bust = url + ("&" if "?" in url else "?") + "cb=20261112w10thursday"
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
    if name in ("homepage", "card", "record"):
        for edge in STALE + ("NYJ +8.5", "Week 10 early look"):
            if edge in body:
                present.append(edge)
    if name == "ai-picks" and "Week 10 early look" in body:
        present.append("Week 10 early look")
    if name == "week9-card" and ("WAS +2.5" in body or "1cY3MSjjkzE" in body or "Westgate SuperContest Week 10" in body):
        present.append("week 10 card leaked into the week 9 archive")
    order_bad = name == "shorts" and (
        body.find("1cY3MSjjkzE") > body.find("4-NrBHuRlUE") or body.find("4-NrBHuRlUE") > body.find("q2OazIWZ5vE")
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
            print("Week 10 Short is not before the Week 9 Shorts")
        return False
    print(f"Live {name} contains the expected markers.")
    return True


def main():
    ok = True
    for name, url, markers in (
        ("homepage", HOME_URL, HOME_MARKERS),
        ("shorts", SHORTS_URL, SHORTS_MARKERS),
        ("card", CARD_URL, CARD_MARKERS),
        ("record", RECORD_URL, RECORD_MARKERS),
        ("ai-picks", AI_URL, AI_MARKERS),
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
