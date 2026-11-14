# Record audit, Weeks 3–10 through TNF

Graded Nov 14, 2026 from the published Westgate cards in `data/weeks/` and `data/ats-tracker.csv`, against `data/verified-finals-2026-11-07.json` plus the later Week 9 and Week 10 snapshots. Each side is the published pick at that row's Westgate line. A pass is not a pick. A push stays a push. Week 10 is through TNF only (WAS 24, NYG 21; WAS +2.5 won). The other 13 Week 10 games are pending.

Every stored grade matched the score arithmetic. No published game is missing, and no game is counted twice.

| Week | Best Bets | Leans | Card | Other | Full | Pending |
|---|---|---|---|---|---|---|
| 3 | 3-0-0 | 1-2-0 | — | — | 4-2-0 | 0 |
| 4 | 2-1-0 | — | — | — | 2-1-0 | 0 |
| 5 | 3-2-0 | — | 4-3-1 | Hold 1-0-0, Provisional 0-1-0 | 8-6-1 | 0 |
| 6 | 1-1-0 | 3-1-0 | 0-2-0 | — | 4-4-0 | 0 |
| 7 | 1-2-0 | 4-3-0 | — | — | 5-5-0 | 0 |
| 8 | 1-1-0 | 2-6-0 | — | — | 3-7-0 | 0 |
| 9 | 0-2-0 | 3-8-0 | — | — | 3-10-0 | 0 |
| 10 | 0-0-0 | 1-0-0 | 0-0-0 | — | 1-0-0 | 13 |
| Total | 11-9-0 | 14-20-0 | 4-5-1 | 1-1-0 | 30-35-1 | 13 |

Units are wins minus losses. Best Bets +2, Leans −6, Card tier −1, full card −5. Week 10 pending: Best Bets 2, Leans 6, Card 5.

The one push is Week 5 CIN −7 (CIN 31, MIA 24). The full card is Best Bets plus Leans plus Card plus the Week 5 Hold (BAL +3.5, win) and Provisional (WAS −3.5, loss).

## Why 19-23, 9-7-1, and 39-39-1 are not this record

Best Bets match at 11-9-0. The other tally's full card is 9 wins and 4 losses higher (39-39-1 versus 30-35-1).

Week 4's published card is three Best Bets only (NYG +1.5 win, PHI +3 loss, CAR +3.5 win). It calls every other game a pass. The model still had a side on those 13 games. Graded at the Westgate line they are 9-4:

| Side | Result | Final |
|---|---|---|
| CLE +2.5 | W | PIT 24, CLE 27 |
| IND −3.5 | W | IND 30, WAS 13 |
| NE +6.5 | W | NE 29, BUF 26 |
| CHI −3.5 | W | NYJ 12, CHI 23 |
| HOU −2.5 | L | DAL 34, HOU 30 |
| JAX +2.5 | W | JAX 22, CIN 17 |
| TB +3.5 | W | GB 17, TB 14 |
| TEN +11.5 | W | TEN 18, BAL 24 |
| MIA +10.5 | W | MIA 10, MIN 15 |
| DEN +2.5 | L | DEN 14, SF 24 |
| KC −4.5 | L | KC 30, LV 27 |
| LAC +7.5 | W | LAC 23, SEA 30 |
| NO −2.5 | L | ATL 45, NO 24 |

30-35-1 plus 9-4 is 39-39-1. That is the whole full-card gap. Two of those sides (TB +3.5, KC −4.5) are also on the Week 4 Pick 5. Counting only the Pick 5 would add 1-1, not 9-4, so the other tally counted the whole unpublished board.

Leans and the Card tier are higher by 10 wins and 5 losses together (19-23 and 9-7-1 versus 14-20-0 and 4-5-1). That is the same 9-4, plus the Week 5 Hold win and Provisional loss. This record keeps those two out of the Lean and Card cells and inside the full card. The other tally has no separate Hold or Provisional line, and its Best Bets plus Leans plus Card equals its full card, so those two results were filed in Lean or Card. The row-by-row labels for that split are not in this repo. They are not needed to reject the total: the 13 sides were passes on the published card.

## What did not cause the gap

- No week from 3 through 10 is missing. Weeks 1 and 2 are outside this tracker on purpose.
- No game is graded twice. Each published side matches the week file and the tracker once.
- Week 8's Saturday short moved PIT −3.5 from Lean to Best Bet and SEA −3 from Lean to Pass before those kickoffs. Applying that would make Best Bets 12-9-0. Both tallies are 11-9, so neither one applied it. The graded rows stay the Thursday card.
- Week 10 Saturday moves (MIN Lean to Best Bet, HOU Lean to Card) are on games that have not been played. They do not change this record. TNF stays the Thursday Lean, WAS +2.5, win.
