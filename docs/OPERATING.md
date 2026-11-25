# Publishing VectorPicks

The live site is this GitHub repo. Vercel serves the committed `public/` directory from `main`. It does not run `build.py`. A file on another machine, including anything under `/workspace/site` or `/workspace/shorts`, is not a publish.

Checked on Nov 7, 2026: `https://www.vectorpicks.com/` matched `public/index.html` at `3f67cc5` byte for byte, and the last GitHub production deployment of that commit was Oct 23, 2026. Newer cards had never been pushed here.

## Source

1. Add or edit files in `data/`. Do not invent a line, score, injury, or model rerun.
2. Name the board. A DraftKings week stays labeled DraftKings. Do not regrade it with another book's number.
3. Keep the original card. A Saturday change goes in `saturday_update` and is not folded into the graded rows unless that note is explicitly the pre-kickoff card and is shown as its own card.
4. From Week 10 on, Vector has a side on every game. Confidence and Best Bet are separate from the side. There is no validated Best Bet probability.
5. The public method is v3: market + 0.35 × (healthy v2 − market), then injuries, home field about 2 points, 0 at a neutral site. Do not put private coefficients in this repo.
6. Grade from a saved public scoreboard snapshot. A final with no W, L, or P fails the build. A game that has not been played stays `pending`.
7. Add a row to `data/production-ledger.json` for the week. Video ids must be unique. `cXnzFQPN7mE` is private and is never an embed.
8. Do not put paid-source names, account identifiers, secrets, or private pool entries in `data/` or `public/`.

## Build

```bash
python3 build.py --validate
python3 tests/test_recovery.py
node tests/test_live_board.js
node tests/test_scores_api.js
node tests/test_odds_api.js
```

The build prints `This is not a publish.` That line is required. `VECTORPICKS_TODAY=YYYY-MM-DD` is for tests only. A normal build uses the Pacific calendar.

## Pull request

Commit the `data/` inputs and the regenerated `public/` on a branch. Open a pull request into `main`. GitHub Actions runs the same build and tests. Do not skip or disable that check.

## Merge and deploy

Merging to `main` is what Vercel deploys. The GitHub deployments API records a production deployment for that commit. This repo does not change DNS, the domain, or billing.

## Live check

After Vercel finishes:

```bash
python3 scripts/verify_live.py
```

Exit 0 means the live homepage contains the current week's markers. Exit 1 means production is still older. A green local build does not change that result. Also confirm the deployment SHA matches the merge commit.

## Backup

Keep the week's source files in the repo. A copy in Google Drive is a backup, not the site. If Drive and `main` disagree, `main` is what the site can publish, and the disagreement is reported on the pull request rather than silently copied in.

## What failed this week

Report it in the pull request. For Nov 25, 2026 the Wednesday card is 16 games, all pending. No Best Bets. Leans are LAR -2.5, ATL +7, and IND +7. PHI +8.5 and MIA +3.5 stay model side only, not a recommendation. Tonight's highlight is GB @ LAR, LAR -2.5, Lean, kickoff Wednesday Nov 25, 5:00 PM PT. Week 11 stays the Thursday card, final 6-7, Best Bets 1-0, Leans 1-1, Card 4-6, including Monday night CIN 20, WAS 22. Tracked weeks stay Best Bets 13-10-0 (+3u), Leans 17-25-0 (-8u), Card tier 11-13-1 (-2u), full card 42-49-1 (-7u). Week 12 counts only as pending: 0 Best Bets, 3 Leans, 13 Card. The Week 12 AI board is posted with earlier weeks kept. The Week 12 Short is https://www.youtube.com/shorts/VMwVPQtbbeo. Open gaps:

- Injury layer is player by player but not a fresh fully reconciled rerun. LAC and SEA quarterback statuses are pending.
- Tiers are confidence labels, not proven probabilities.
- PHI +8.5 and MIA +3.5 are model side only, not a recommendation.
- Wednesday picks, Saturday update.
- Week 11 Saturday notes stay off the graded rows.
- Week 4's 13 unpublished model sides stay off the record.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 24, 2026 the Tuesday package grades Week 11 complete and posts Week 12 power rankings. Week 11 is 13 of 13 at the Thursday Nov 19 Westgate SuperContest lines: full card 6-7, Best Bets 1-0 (WAS +6.5 win, CIN 20, WAS 22), Leans 1-1 (NO +11.5 win, TB +7 loss), Card 4-6. Monday night is CIN 20, WAS 22. MIN @ SF was in Mexico City (neutral) and is graded at SF -3. Tracked weeks are Best Bets 13-10-0 (+3u), Leans 17-25-0 (−8u), Card tier 11-13-1 (−2u), full card 42-49-1 (−7u), including the Week 5 Hold 1-0 and Provisional 0-1. The Week 12 Westgate SuperContest sheet was not posted as of Tue Nov 24, 2026 8:52 AM PT, so there is no Week 12 card and no Week 12 line. Open gaps:

- No Week 12 picks, edges, or lines. The card waits on that sheet.
- Injury adjustments on the Week 12 rankings are provisional until midweek practice reports. Not a fresh full rerun.
- Saturday Week 11 tier and side changes stay a note. Applied they would be Best Bets 1-1, Leans 1-0, Card 5-5, full card 7-6. Graded rows stay the Thursday card. BAL +2.5 would have covered (BAL 33, CAR 35). TB +7 lost.
- MIA +16.5 and PHI +4.5 stay model side only, not a recommendation. They are on the full card.
- Week 4's 13 unpublished model sides stay off the record.
- The Wednesday Week 11 AI board stays DraftKings and is not graded from this package. It is not the Westgate card.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 22, 2026 the public Short is https://www.youtube.com/shorts/aXnadwU-Z7U (Week 11 Westgate SuperContest Top 5 Leaders | Bucs +7 on 4 of 5). It lists the supplied top 5 Week 11 picks at the Westgate SuperContest Week 11 contest lines, using standings through Week 10. Fifth place was a 2-way tie at 33-17. RJ551155-3 is shown because that player's identical Gold entries are near the top of SuperContest Gold. It is not a line change and it is not folded into the graded rows. The Saturday Short https://www.youtube.com/shorts/Qd7DWqq_jy8 and the Thursday Short https://www.youtube.com/shorts/LqjTjbZOWb4 stay listed. Shared sides: TB +7 (4 of 5); MIA +16.5 and WAS +6.5 (3 of 5); SF -3, NYG +6, and CHI -11.5 (2 of 5). The Saturday card agrees on TB +7 (Best Bet), WAS +6.5 (Best Bet), and SF -3 (Card), and fades NYG +6 (Vector JAX -6) and CHI -11.5 (Vector NO +11.5, Lean). MIA +16.5 is Vector's model side only, not a recommendation. Contest-leader rows are not Vector picks. Entertainment only, not betting advice. Open gaps:

- No Week 11 results were graded from this Short. Sunday games had not been played.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- The Saturday card is not folded into the graded rows. TNF stays graded at the Thursday line.
- Vector's Week 11 numbers are still provisional. Not a fresh full rerun.
- The Wednesday AI board stays its own labeled board.
- MIA +16.5 and PHI +4.5 stay model side only, not a recommendation.

For Nov 21, 2026 the Saturday update is separate from the Thursday Nov 19 Westgate card. TNF IND +12.5 lost, final HOU 26, IND 3 (ESPN), graded Card at HOU -12.5. No Thursday side, line, Our Spread, or tier was rewritten. Saturday, at the same Westgate lines: BAL +2.5 replaces CAR -2.5 (Card, coin flip) and TB +7 moves from Lean to Best Bet. Saturday Best Bets are TB +7 at DET and WAS +6.5 vs CIN (Monday). The Lean is NO +11.5 at CHI. MIA +16.5 and PHI +4.5 stay model side only, not a recommendation. The other 12 Week 11 rows stay pending. Tracked weeks, counted from the Thursday tiers after that one loss: Best Bets 12-10-0 (+2u), Leans 16-24-0 (-8u), Card tier 7-8-1 (-1u), full card 36-43-1 (-7u). Week 11 so far is 0-1 with 12 pending. The public Saturday Short is https://www.youtube.com/shorts/Qd7DWqq_jy8. The Thursday Short https://www.youtube.com/shorts/LqjTjbZOWb4 stays listed. Open gaps:

- Vector's Week 11 numbers are provisional: Friday model build plus Saturday injury-status adjustments, player by player. This is not a fresh full rerun.
- The Saturday card is not folded into the graded rows. TNF is graded at the Thursday line.
- Tiers are confidence labels, not proven probabilities.
- MIA +16.5 and PHI +4.5 are model side only, not a recommendation.
- The Saturday Short is public and is not itself a line change.
- The Wednesday AI board stays its own labeled board. It is not this Westgate card, and it is not graded from this update.
- Saturday Week 10 tier changes stay a note. Graded rows stay the Thursday Nov 12 card.
- Week 4's 13 unpublished model sides stay off the record.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Official Westgate standings after Week 10 are a separate note. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 19, 2026 the Thursday card is the Westgate SuperContest Week 11 contest card posted Wed Nov 18. All 13 games have a side and are pending. The Best Bet is WAS +6.5. Leans are NO +11.5 and TB +7. TNF is IND +12.5 at HOU, tier Card, Our Spread IND +11.0, gap 1.5, kickoff Thu Nov 19, 5:15 PM PT. MIA +16.5 and PHI +4.5 stay on the full card as model side only, not a recommendation. Week 10 stays the Thursday Nov 12 card, final 7-7. Tracked weeks stay Best Bets 12-10-0, Leans 16-24-0, Card tier 7-7-1, full card 36-42-1, with the 13 Week 11 rows pending. The public Thursday Short is https://www.youtube.com/shorts/LqjTjbZOWb4. Open gaps:

- Vector's Week 11 numbers are provisional. The injury layer is still being reconciled. This is not a fresh full rerun.
- Tiers are confidence labels, not proven probabilities.
- MIA +16.5 and PHI +4.5 are model side only, not a recommendation.
- The Thursday Short is public and is not a line change.
- The Wednesday AI board stays its own labeled board. It is not this Westgate card, and it is not graded.
- Injury adjustments on the Week 11 rankings stay provisional.
- Saturday Week 10 tier changes stay a note. Graded rows stay the Thursday Nov 12 card.
- Week 4's 13 unpublished model sides stay off the record.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Official Westgate standings after Week 10 are a separate note. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 18, 2026 the Wednesday AI board is a provisional DraftKings card fetched at 1:16 PM PT. Claude, Gemini, Grok, and ChatGPT each have a side, a confidence, and a reason on all 13 games, three Best Bets, and a ranked top 5. Vector has a provisional lean on all 13 and a provisional top 5, and no Best Bets. All 13 games are pending. MIN vs SF is in Mexico City (neutral). Byes: ATL, CLE, GB, LAR, NE, SEA. ESPN that afternoon shows every game scheduled and none final. This board is not the Westgate card. The Week 11 Westgate SuperContest sheet is still not the card of record, so the weekly card, the record, and the live board still have no Week 11 lines. Open gaps:

- No Week 11 Westgate card. The card, the record, and the live board wait on that sheet.
- The Wednesday AI board stays labeled DraftKings. It is not graded, and it is not the Westgate card.
- Injury adjustments on the Week 11 rankings and Vector leans are provisional. Not a fresh full rerun.
- Saturday Week 10 tier changes stay a note. Graded rows stay the Thursday card.
- Week 4's 13 unpublished model sides stay off the record.
- The Week 10 AI board stays DraftKings and is graded at those lines.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 17, 2026 the Tuesday package grades Week 10 complete and posts Week 11 power rankings. Week 10 is 14 of 14 at the Thursday Nov 12 Westgate lines: full card 7-7, Best Bets 1-1 (DAL +4.5 loss, LAC +4.5 win), Leans 3-4, Card 3-2. Monday night is LAC 23, BAL 20. Tracked weeks are Best Bets 12-10-0 (+2u), Leans 16-24-0 (−8u), Card tier 7-7-1 (0u), full card 36-42-1 (−6u). The Week 11 Westgate SuperContest sheet was not posted as of Tue Nov 17, 2026 8:56 AM PT, so there is no Week 11 card and no Week 11 line. Open gaps:

- No Week 11 picks, edges, or lines. The card waits on that sheet.
- Injury adjustments on the Week 11 rankings are provisional. Not a fresh full rerun.
- Saturday Week 10 tier changes stay a note. Applied they would be Best Bets 2-1, Leans 2-3, Card 3-3. Graded rows stay the Thursday card. The full card is 7-7 either way.
- Week 4's 13 unpublished model sides stay off the record.
- The Wednesday Week 10 AI board stays DraftKings and is graded at those lines. It is not the Westgate card.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- Entertainment only, not betting advice.

For Nov 15, 2026 the public Short is https://www.youtube.com/shorts/8cZ7qpdWyvU (Week 10 Westgate SuperContest Top 5 Leaders | Panthers & Steelers 3 of 5). It lists the supplied top 5 Week 10 picks at the Westgate fixed lines, using standings through Week 9. It is not a line change and it is not folded into the graded rows. The Saturday Short https://www.youtube.com/shorts/fvn8h67Mze0 and the Thursday Short https://www.youtube.com/shorts/1cY3MSjjkzE stay listed. Leaders agree on CAR +2.5 (3), PIT +3.5 (3), CLE +4.5 (2), and DAL +4.5 (2). The Saturday card agrees on CAR +2.5, PIT +3.5, and DAL +4.5, and fades CLE +4.5 (Vector has HOU -4.5). Contest-leader rows are not Vector picks. Entertainment only, not betting advice. Open gaps:

- No Week 10 results were graded from this Short. Sunday games had not been played.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- The Saturday card is not folded into the graded rows. TNF stays graded at the Thursday line.
- Vector's Week 10 numbers are still provisional. Not a fresh full rerun.
- The Wednesday AI board stays the DraftKings card.

For Nov 14, 2026 the Saturday update is separate from the Thursday Westgate card. TNF WAS +2.5 is a win, final WAS 24, NYG 21 (ESPN). No side changed. MIN +3.5 moved from Lean to Best Bet. HOU -4.5 moved from Lean to Card. Saturday Best Bets are DAL +4.5, MIN +3.5, and LAC +4.5. The public Saturday Short is https://www.youtube.com/shorts/fvn8h67Mze0. The Thursday Short https://www.youtube.com/shorts/1cY3MSjjkzE stays listed. Open gaps:

- Vector's Week 10 numbers are still provisional: Tuesday model build plus manual injury adjustments through Saturday morning. Not a fresh full rerun.
- The Saturday card is not folded into the graded rows. TNF is graded at the Thursday line.
- The tracked-weeks record was regraded Nov 14, 2026 from final scores at the posted Westgate lines. Best Bets 11-9-0, Leans 14-20-0, Card tier 4-5-1, full card 30-35-1. A separate tally (Leans 19-23, Card 9-7-1, full card 39-39-1) counted 13 Week 4 passes that grade 9-4. That tally is not the record. See docs/record-audit-w03-w10.md.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot. Those rows are not Vector picks.
- The Wednesday AI board stays the DraftKings card. TNF is graded there at the DraftKings line, which is the same NYG -2.5. Sides were not changed.

For Nov 12, 2026 the Thursday card is the Westgate SuperContest Week 10 sheet. All 14 games have a side and are pending. Best Bets are DAL +4.5 and LAC +4.5. The TNF lean is WAS +2.5 at NYG, kickoff Thu Nov 12, 5:15 PM PT. The public Short is https://www.youtube.com/shorts/1cY3MSjjkzE. Open gaps:

- Vector's Week 10 numbers are provisional. The injury layer is still being reconciled. This is not a fresh full rerun.
- The record box is the audited tracker since Week 3. It is not a full-season total. Week 10 rows are pending and do not change the W-L. Best Bets stay 11-9. Leans and the full card stay on this page's rows only.
- The Shorts contest-leader block is still the Sunday Nov 8 snapshot, with BUF @ MIN pending there. Official Westgate standings after Week 9 are a separate note. Those rows are not Vector picks.
- No Saturday Week 9 model rerun. The Thursday Week 9 card lines are unchanged.
- No Week 9 Westgate sheet file in the repo. The Thursday Week 9 card says the source file called those numbers Westgate. The AI board is DraftKings. The Week 9 AI archive still shows the previously published provisional early look. The Wednesday Week 10 AI board stays labeled DraftKings and is not the Westgate card.

For Nov 10, 2026 the Tuesday package graded BUF @ MIN (BUF 23, MIN 6, MIN +3.5 loss) and posted Week 10 power rankings. It did not include a Week 10 contest card. That gap closed on Nov 12.

For Nov 7, 2026 the open gaps were:

- No Saturday Week 9 model rerun. The Thursday card is unchanged.
- No Week 9 Westgate sheet file in the repo. The Thursday card says the source file called those numbers Westgate. The AI board is DraftKings.
- The Week 9 injury ledger is not reconciled. No model refresh is claimed.
- Week 4 tracker rows that contradict the published pass card are not on the record.
- Contest-leader rows are not Vector picks and are not on the record.
- Shorts that quote a season total are not copied onto the record when this page's audited rows differ.
