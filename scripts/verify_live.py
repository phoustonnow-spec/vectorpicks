#!/usr/bin/env python3
"""Check the live site after a merge. A local build is not a publish.

Exit 0 only when https://www.vectorpicks.com serves the expected Week 9 markers.
Exit 1 when the live site is still an older week or is missing a marker.

  python3 scripts/verify_live.py
"""
import sys
import urllib.request

URL = "https://www.vectorpicks.com/"
MARKERS = (
    "Week 9",
    "Saturday, Nov 7, 2026 PT",
    "JAX 33, BAL 10",
    "q2OazIWZ5vE",
)
FORBIDDEN = ("cXnzFQPN7mE",)


def main():
    request = urllib.request.Request(URL, headers={"cache-control": "no-cache"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", "replace")
        print(f"status {response.status} last-modified {response.headers.get('last-modified')}")
    missing = [m for m in MARKERS if m not in body]
    present = [m for m in FORBIDDEN if m in body]
    if missing or present:
        print("Live site does not match this build.")
        if missing:
            print("missing: " + ", ".join(missing))
        if present:
            print("forbidden: " + ", ".join(present))
        print("A green local build is not a publish. Merge to main, wait for Vercel, then run this again.")
        return 1
    print("Live homepage contains the Week 9 markers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
