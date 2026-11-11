#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the expected Week 9 markers.
Exit 1 when the live site is still an older week or is missing a marker.

  python3 scripts/verify_live.py
"""
import sys
import urllib.request

HOME_URL = "https://www.vectorpicks.com/"
SHORTS_URL = "https://www.vectorpicks.com/shorts.html"
CARD_URL = "https://www.vectorpicks.com/card.html"
RECORD_URL = "https://www.vectorpicks.com/record.html"
AI_URL = "https://www.vectorpicks.com/ai-picks.html"
HOME_MARKERS = (
    "Week 10",
    "Wednesday, Nov 11, 2026 PT",
    "Week 9 final 3-10",
    "MIN +3.5 is a loss, BUF 23, MIN 6",
    "WEEK 9 RECORD",
    ">3-10<",
    'id="rankings"',
    'id="week-10-status"',
    "Vector power rankings entering Week 10",
    "Injury adjustments are provisional this week",
    "the Week 10 Vector card publishes after the official contest lines are out",
    "<b>JAX</b></td><td>5.9</td>",
    '<b>HOU</b></td><td>4.3</td><td>8</td><td class="pos">+6</td>',
    "11-9-0",
    "13-20-0",
    "29-35-1",
    "JAX 33, BAL 10",
    "4-NrBHuRlUE",
    "q2OazIWZ5vE",
    "No Week 10 picks, edges, or line comparisons",
)
SHORTS_MARKERS = (
    "4-NrBHuRlUE",
    "q2OazIWZ5vE",
    "81Pq1yT8hQQ",
    "Week 8 Westgate SuperContest Top 5 Leaders",
    "Week 4 Westgate SuperContest Top 5 Leaders",
    "LAMBDA LAMBDA LAMBDA-1 29-10-1",
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
    "Week 9: <b>0-4 with 1 pending</b>",
)
CARD_MARKERS = (
    "4-NrBHuRlUE",
    "q2OazIWZ5vE",
    "Thu card line",
    "BAL +10",
    "JAX 33, BAL 10",
    "DAL 27, IND 23",
    "CLE 22, NO 23 (OT)",
    "Week 9 final 3-10",
    "MIN +3.5",
    "BUF 23, MIN 6",
    "LOSS",
    "No side",
    'id="week-10-status"',
    "the Week 10 Vector card publishes after the official contest lines are out",
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
    "JAX \u221210.5",
    "BUF \u22128.5",
    "NYG \u22122.5",
    "KC \u22123.5",
    "LV +6.5",
    "CLE +4.5",
    "ARI +9.5",
    "NYJ +8.5",
    "GB \u22123",
    "SF \u22124.5",
    "PIT +3.5",
    "IND \u22123.5",
    "HOU \u22124.5",
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
    "JAX \u221210.5",
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


def fetch(url):
    bust = url + ("&" if "?" in url else "?") + "cb=20261110w10tuesday"
    request = urllib.request.Request(bust, headers={
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": "vectorpicks-verify-live",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", "replace")
        print(f"{url} status {response.status} last-modified {response.headers.get('last-modified')} bytes {len(body)}")
        return response.status, body


def check(name, status, body, markers):
    missing = [m for m in markers if m not in body]
    present = [m for m in FORBIDDEN if m.lower() in body.lower()]
    if name in ("homepage", "card", "record"):
        for edge in ("DAL +4.5", "NYJ +8.5", "Week 10 early look"):
            if edge in body:
                present.append(edge)
    if name == "ai-picks" and "Week 10 early look" in body:
        present.append("Week 10 early look")
    order_bad = name == "shorts" and body.find("4-NrBHuRlUE") > body.find("q2OazIWZ5vE")
    if status != 200 or missing or present or order_bad:
        print(f"Live {name} does not match this build.")
        if status != 200:
            print(f"status {status}")
        if missing:
            print("missing: " + ", ".join(missing))
        if present:
            print("forbidden: " + ", ".join(present))
        if order_bad:
            print("Week 9 leaders short is not before the Saturday short")
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
    ):
        status, body = fetch(url)
        ok = check(name, status, body, markers) and ok
    if not ok:
        print("A green local build is not a publish. Merge to main, wait for Vercel, then run this again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
