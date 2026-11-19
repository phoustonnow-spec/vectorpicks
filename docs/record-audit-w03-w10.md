# Record audit, Weeks 3–10

Graded Nov 17, 2026 from the published Westgate cards in `data/weeks/` and `data/ats-tracker.csv`, against `data/verified-finals-2026-11-07.json` plus the later Week 9 and Week 10 snapshots, including `data/verified-finals-2026-11-17.json`. Each side is the published pick at that row's Westgate line. A pass is not a pick. A push stays a push. Week 10 is complete: 14 of 14, including Monday night LAC 23, BAL 20. The Nov 14 audit stopped at TNF (WAS +2.5 win, 13 pending). Those 13 are graded here. The Thursday Nov 12 card is the card of record. Saturday tier changes are not folded in.

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
| 10 | 1-1-0 | 3-4-0 | 3-2-0 | — | 7-7-0 | 0 |
| Total | 12-10-0 | 16-24-0 | 7-7-1 | 1-1-0 | 36-42-1 | 0 |

Units are wins minus losses. Best Bets +2, Leans −8, Card tier 0, full card −6. Week 10 Best Bets are DAL +4.5 (loss, SF 46, DAL 40) and LAC +4.5 (win, LAC 23, BAL 20).

The one push is Week 5 CIN −7 (CIN 31, MIA 24). The full card is Best Bets plus Leans plus Card plus the Week 5 Hold (BAL +3.5, win) and Provisional (WAS −3.5, loss).

## Week 10 addendum

The Nov 14 table had Week 10 at 1-0-0 through TNF only, and the tracked total at Best Bets 11-9-0, Leans 14-20-0, Card 4-5-1, full card 30-35-1, with 13 pending. The other 13 finals are the ESPN scores in `data/verified-finals-2026-11-17.json`. Adding them to the Thursday rows is Best Bets 1-1, Leans 3-4, Card 3-2, full card 7-7. The tracked box moves by that amount and nothing else.

Week 10's Saturday update moved MIN +3.5 from Lean to Best Bet and HOU −4.5 from Lean to Card before those kickoffs. MIN won 30-10. HOU lost 24-27. Applying that would make Best Bets 2-1, Leans 2-3, and Card 3-3. The full card is 7-7 either way. The graded rows stay the Thursday card, the same rule as Week 8.

## Why 19-23, 9-7-1, and 39-39-1 are not this record

This section is the Nov 14 discrepancy, before the other 13 Week 10 games were graded. It is unchanged. Completing Week 10 does not add the 13 Week 4 passes.

Best Bets matched at 11-9-0. The other tally's full card was 9 wins and 4 losses higher (39-39-1 versus 30-35-1).

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
- Week 8's Saturday short moved PIT −3.5 from Lean to Best Bet and SEA −3 from Lean to Pass before those kickoffs. Applying that would make Best Bets 12-9-0 on the Nov 14 through-TNF tally. Both tallies were 11-9, so neither one applied it. The graded rows stay the Thursday card.
- Week 10 Saturday moves are graded in the addendum above. They are not folded into the rows. TNF stays the Thursday Lean, WAS +2.5, win.

## Week 11

Week 11 is not in this audit. The Thursday Nov 19 card adds 13 pending rows at the Westgate SuperContest Week 11 lines. Those rows do not change the Weeks 3-10 totals above.
