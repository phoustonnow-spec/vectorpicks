#!/usr/bin/env python3
"""Guards for the Week 9 recovery. No network.

  python3 tests/test_recovery.py
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build


def test_calendar():
    assert build.nfl_week(date(2026, 11, 7)) == 9
    assert build.nfl_week(date(2026, 11, 5)) == 9
    assert build.nfl_week(date(2026, 11, 9)) == 9
    assert build.nfl_week(date(2026, 11, 10)) == 10
    assert build.nfl_week(date(2026, 11, 11)) == 10
    assert build.nfl_week(date(2026, 11, 12)) == 10
    assert build.nfl_week(date(2026, 11, 4)) == 9  # gap day belongs to the next week
    assert build.nfl_week(date(2026, 11, 2)) == 8
    assert build.nfl_week(date(2026, 10, 8)) == 5
    assert build.nfl_week(date(2026, 9, 9)) == 1
    assert build.game_date_ok("2026-11-05", 9, 2026)
    assert not build.game_date_ok("2026-10-08", 9, 2026)
    assert not build.game_date_ok("2026-11-04", 9, 2026)


def test_tnf_grade():
    game = {"game": "JAX@BAL", "score": {"away": 33, "home": 10, "status": "final"}}
    assert build.grade_ats("BAL +10", game) == "L"
    assert build.grade_ats("JAX -10", game) == "W"
    assert build.grade_ats("BAL +10", {"game": "JAX@BAL"}) is None


def test_names_and_private_video():
    assert build.BANNED_PUBLIC.search("Walter Nolen is out") is None
    assert build.public_name_violation("Walter Nolen is out") is None
    assert build.public_name_violation("WalterFootball")
    assert build.public_name_violation("See Walter for the card")
    assert build.public_name_violation("SportsLine")
    assert build.BANNED_PUBLIC.search("walter football")
    assert build.BANNED_PUBLIC.search("Kevin Cole")
    try:
        build.assert_public_video("cXnzFQPN7mE", "test")
    except SystemExit as err:
        assert "cXnzFQPN7mE" in str(err)
    else:
        raise AssertionError("private video was allowed")


def test_built_pages():
    root = build.OUT
    home = open(os.path.join(root, "index.html"), encoding="utf-8").read()
    ai = open(os.path.join(root, "ai-picks.html"), encoding="utf-8").read()
    card = open(os.path.join(root, "card.html"), encoding="utf-8").read()
    archive_card = open(os.path.join(root, "card-2026-w09.html"), encoding="utf-8").read()
    assert "Week 10" in home and build.stamp_pt(build.today_pt()) in home
    assert "Week 9 final 3-10" in home and "MIN +3.5 is a loss, BUF 23, MIN 6" in home
    assert "WAS +2.5" in home and "DAL +4.5" in home and "LAC +4.5" in home
    assert "Lines: Westgate SuperContest Week 10" in home
    assert "1cY3MSjjkzE" in home and 'data-yt="1cY3MSjjkzE"' in home
    assert 'id="rankings"' in home and "5.9" in home and "Injury adjustments are provisional this week" in home
    assert "NYJ +8.5" not in home and "Week 10 early look" not in home
    assert "No Week 10 picks" not in home
    shorts = open(os.path.join(root, "shorts.html"), encoding="utf-8").read()
    assert "1cY3MSjjkzE" in shorts and shorts.find("1cY3MSjjkzE") < shorts.find("4-NrBHuRlUE")
    assert "4-NrBHuRlUE" in shorts and shorts.find("4-NrBHuRlUE") < shorts.find("q2OazIWZ5vE")
    assert "Week 9 Saturday Update" in shorts
    assert "81Pq1yT8hQQ" in shorts and "Week 4 Westgate SuperContest Top 5 Leaders" in shorts
    assert "LAMBDA LAMBDA LAMBDA-1 29-10-1" in shorts and "RIGGED NFL-1 29-10-1" in shorts
    assert "LAMBDA LAMBDA LAMBDA-1 32-12-1" in shorts
    assert "Entertainment and opinion only. Not betting advice." in shorts
    assert 'id="week-9-results"' in shorts
    assert "Unofficial." in shorts and "Not Westgate official standings" in shorts
    assert "11-11 with 3 pending" in shorts and "9-16 with 5 pending" in shorts
    assert "tie for fifth" in shorts and "JD3-1" in shorts and "THREAD CLOD FOOL-1" in shorts
    assert "BUF@MIN (Monday night) is Pending" in shorts
    assert shorts.count('res-win">WIN') == 20
    assert shorts.count('res-loss">LOSS') == 27
    assert shorts.count('res-pend">Pending') == 8
    assert "Official Westgate standings after Week 9" in home
    lowered = shorts.lower()
    for bad in ("kevin cole", "unexpected points", "walterfootball", "walter football", "dr bob", "dr. bob"):
        assert bad not in lowered
    assert "splash" not in lowered and "bman" not in lowered.split("webmanifest")[-1]
    archive = open(os.path.join(root, "ai-picks-2026-w09.html"), encoding="utf-8").read()
    assert "4-NrBHuRlUE" in archive_card and "q2OazIWZ5vE" in archive_card and "Thu card line" in archive_card
    assert "BUF 23, MIN 6" in archive_card and "MIN +3.5" in archive_card and "No side" in archive_card
    assert "WAS +2.5" not in archive_card and "1cY3MSjjkzE" not in archive_card
    assert "WAS +2.5" in card and "DAL +4.5" in card and "LAC +4.5" in card
    assert "Week 10 early look" not in card and "Thu card line" not in card
    assert "1cY3MSjjkzE" in card
    assert "cXnzFQPN7mE" not in home + ai + card + shorts + archive
    assert "No sides were invented" not in ai and "Week 10 early look" not in ai
    assert "PROVISIONAL" in ai and "DraftKings line" in ai and "Not a Westgate card." in ai
    assert "Provisional top 5 (not Best Bets)" in ai and "DAL +4.5" in ai
    assert "ai-picks-2026-w10.html" in ai and "Week 9" in archive
    assert "DraftKings line" in archive and "Westgate line" not in archive.split("ai-grid", 1)[-1][:500]
    assert 'id="vector-top5"' in archive and "Vector Top 5" in archive and "Westgate SuperContest" in archive
    assert "ARI +12.5" in archive and ">2-3<" in archive
    assert "Week 10 early look" in archive and "DAL +4.5" in archive and "Byes: CHI, DEN, PHI, TB" in archive
    assert "SEA@LV" not in archive and "SEA @ LV" not in archive
    assert "all 15 games are pending" not in archive.lower() and "no top 5" not in archive.lower()
    assert "Monday night, pending" not in archive and "BUF @ MIN not final" not in archive
    assert "Final: BUF 23, MIN 6" in archive
    assert "Final: CIN 34, ATL 17" in archive and "Final: CLE 22, NO 23 (OT)" in archive
    assert "49-37-2" in archive and "48-38-2" in archive and "33-34-2" in archive
    assert "Thu card line" in archive_card
    assert "This is not a publish" not in home
    text = open(os.path.join(build.ROOT, "build.py"), encoding="utf-8").read()
    assert "This is not a publish." in text
    assert "Published successfully" not in text


def test_week9_leader_grades():
    import json
    sh = json.load(open(os.path.join(build.DATA, "shorts.json"), encoding="utf-8"))
    graded = build.grade_leader_block(sh["leader_results"])
    cards = {}
    for contest in graded["contests"]:
        for ent in contest["entries"]:
            cards[(contest["id"], ent["name"])] = [row["result"] for row in ent["results"]]
            assert len(ent["picks"]) == 5
    assert cards[("supercontest", "LAMBDA LAMBDA LAMBDA-1")] == ["W", "W", "W", "L", "L"]
    assert cards[("supercontest", "RIGGED NFL-1")] == ["L", "L", "W", "W", "pending"]
    assert cards[("supercontest", "MATTLEGEND27-1")] == ["L", "W", "W", "W", "L"]
    assert cards[("supercontest", "JJ & JF-1")] == ["L", "L", "L", "W", "pending"]
    assert cards[("supercontest", "RJ551155-3")] == ["L", "W", "W", "L", "pending"]
    assert cards[("gold", "JJ & JF-1")] == cards[("supercontest", "JJ & JF-1")]
    assert cards[("gold", "THREAD CLOD FOOL-1")] == ["W", "L", "W", "L", "pending"]
    assert cards[("gold", "JERRYDABEST-1")] == ["L", "L", "W", "W", "pending"]
    assert cards[("gold", "JUST WIN BABY-1")] == ["L", "W", "L", "L", "W"]
    assert cards[("gold", "RJ551155-1")] == cards[("supercontest", "RJ551155-3")]
    assert cards[("gold", "JD3-1")] == ["L", "L", "L", "L", "pending"]
    by_id = {c["id"]: c for c in graded["contests"]}
    assert (by_id["supercontest"]["wins"], by_id["supercontest"]["losses"], by_id["supercontest"]["pending"]) == (11, 11, 3)
    assert (by_id["gold"]["wins"], by_id["gold"]["losses"], by_id["gold"]["pending"]) == (9, 16, 5)
    assert len(by_id["supercontest"]["entries"]) == 5
    assert len(by_id["gold"]["entries"]) == 6
    pending = [row for c in graded["contests"] for ent in c["entries"] for row in ent["results"] if row["result"] == "pending"]
    assert pending and all(row["game"] == "BUF@MIN" for row in pending)
    assert len(pending) == 8


def test_full_card_rule_rejects_a_pass():
    weeks = [{
        "season": 2026,
        "week": 10,
        "line_column": "Posted line",
        "line_source": "example",
        "pass_policy": "full",
        "games": [{
            "game": "NYJ@KC",
            "date": "2026-11-15",
            "tier": "Pass",
            "pick": "No side",
        }],
    }]
    try:
        build.validate_sources(weeks, [], {"shorts": [], "never_embed": ["cXnzFQPN7mE"]})
    except SystemExit as err:
        assert "side on every game" in str(err)
    else:
        raise AssertionError("a Week 10 pass was accepted")


def main():
    test_calendar()
    test_tnf_grade()
    test_names_and_private_video()
    test_built_pages()
    test_week9_leader_grades()
    test_full_card_rule_rejects_a_pass()
    print("OK recovery guards")


if __name__ == "__main__":
    main()
