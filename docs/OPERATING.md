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

Report it in the pull request. For Nov 15, 2026 the public Short is https://www.youtube.com/shorts/8cZ7qpdWyvU (Week 10 Westgate SuperContest Top 5 Leaders | Panthers & Steelers 3 of 5). It lists the supplied top 5 Week 10 picks at the Westgate fixed lines, using standings through Week 9. It is not a line change and it is not folded into the graded rows. The Saturday Short https://www.youtube.com/shorts/fvn8h67Mze0 and the Thursday Short https://www.youtube.com/shorts/1cY3MSjjkzE stay listed. Leaders agree on CAR +2.5 (3), PIT +3.5 (3), CLE +4.5 (2), and DAL +4.5 (2). The Saturday card agrees on CAR +2.5, PIT +3.5, and DAL +4.5, and fades CLE +4.5 (Vector has HOU -4.5). Contest-leader rows are not Vector picks. Entertainment only, not betting advice. Open gaps:

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
