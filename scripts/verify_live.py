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
AI_URL = "https://www.vectorpicks.com/ai-picks.html"
HOME_MARKERS = (
    "Week 9",
    "Monday, Nov 9, 2026 PT",
    "JAX 33, BAL 10",
    "4-NrBHuRlUE",
    "q2OazIWZ5vE",
    "11-11 with 3 pending",
    "9-16 with 5 pending",
    "shorts.html#week-9-results",
    "BUF@MIN is Pending",
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
)
AI_MARKERS = (
    'id="vector-top5"',
    "Vector Top 5",
    "Westgate SuperContest",
    "ARI +12.5",
    ">2-3<",
    "Final: CIN 34, ATL 17",
    "Final: CLE 22, NO 23 (OT)",
    "Monday night, pending",
    "Week 10 early look — provisional, lines will move, final card Thursday",
    "DAL +4.5",
    "NYJ +8.5",
    "MIN +3",
    "NO +1.5",
    "HOU \u22124.5",
    "Byes: CHI, DEN, PHI, TB",
    "49-36-2",
    "48-37-2",
    "33-33-2",
    "20-10-0",
    "BUF @ MIN not final",
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
    bust = url + ("&" if "?" in url else "?") + "cb=20261109w9results"
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
    print(f"Live {name} contains the Week 9 markers.")
    return True


def main():
    ok = True
    for name, url, markers in (
        ("homepage", HOME_URL, HOME_MARKERS),
        ("shorts", SHORTS_URL, SHORTS_MARKERS),
        ("card", CARD_URL, CARD_MARKERS),
        ("ai-picks", AI_URL, AI_MARKERS),
    ):
        status, body = fetch(url)
        ok = check(name, status, body, markers) and ok
    if not ok:
        print("A green local build is not a publish. Merge to main, wait for Vercel, then run this again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
