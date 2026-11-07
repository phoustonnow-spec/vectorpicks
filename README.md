# VectorPicks.com — AI NFL Weekly Selections

Static site + podcast feed for **AI NFL Weekly Selections** with Vector, your AI analyst.
Entertainment and opinion only. 21+. Gambling problem? Call 1-800-GAMBLER.

## Layout

```
build.py            generator (Python 3 stdlib only) -> public/
make_art.py         brand art (podcast cover 3000x3000, favicon, og-image); needs Pillow, run only when art changes
vercel.json         Vercel config: serve public/ as-is, feed.xml + mp3 content-type headers
data/
  site_config.json  base_url (domain lives here only), titles, podcast owner/email/artwork
  weeks/2026-wNN.json  one file per week -> card-YYYY-wNN.html; the Pacific calendar week is card.html
  ats-tracker.csv   graded picks -> record.html + home record box
  episodes.json     podcast episodes -> episodes.html + feed.xml
  shorts.json       YouTube Shorts links (placeholder slots while empty)
  methodology.html  methodology page body
assets/             css, js, fonts (Anton + Montserrat, SIL OFL), images, Week 3 Short
public/             GENERATED build output (committed; this is what Vercel serves)
tests/              sample_episodes.json (feed test fixture), screenshots.py (local visual check)
```

## Rebuild

```bash
python3 build.py --validate      # regenerate public/ and validate feed.xml (+ a 1-item test feed)
python3 -m http.server 8765 -d public   # preview at http://localhost:8765
```

`public/` is wiped and regenerated on every build, except `public/episodes/` (drop mp3s there).
The committed `data/ats-tracker.csv` is the tracker. A local box file is not copied unless `VECTORPICKS_SYNC_TRACKER=1`.

The current week is the 2026 NFL week for today's Pacific date, not whichever week file happens to be newest. See `docs/OPERATING.md` for the source, build, pull request, merge, and live-check steps. A green build is not a publish.

## Weekly routine

1. **New week card:** add `data/weeks/2026-wNN.json`. From Week 10 on, every game needs a Vector side. Use only numbers from that week's named board. No invented lines, splits, injuries, or scores. A Saturday change is a separate dated note, not a rewrite of the original card.
2. **Results:** grade a row only when `data/verified-finals-2026-11-07.json` (or its successor snapshot) has that final. Update `ATS Result`, `Final Score`, and `Units` at the row's own line. A finished game left `pending` fails the build.
3. **Episode:** put the mp3 in `public/episodes/`, add an entry to `data/episodes.json`:
   `{"title","date":"YYYY-MM-DD","show_type":"Tuesday Rankings|Thursday Picks|Sunday Update|Sunday Recap","mp3":"episodes/file.mp3","duration":"HH:MM:SS","description"}`. `bytes` is filled in automatically.
4. **Short:** add a public `{"title","date","week","youtube_url"}` to `data/shorts.json`. Never add `cXnzFQPN7mE`.
5. `python3 build.py --validate`, then `python3 tests/test_recovery.py` and the `node tests/test_*.js` files. Open a pull request. After merge, run `python3 scripts/verify_live.py`.

## Deploy (GitHub + Vercel)

- Import the GitHub repo in Vercel. `vercel.json` sets framework "Other", no install, output directory `public`. No build runs on Vercel; the committed `public/` is served.
- Add the custom domain in Vercel (Project > Settings > Domains) and point DNS as Vercel instructs.
- `base_url` in `data/site_config.json` is `https://www.vectorpicks.com`. Change it there if the domain differs, rebuild, commit. Canonical tags, Open Graph URLs, `sitemap.xml`, `robots.txt`, and `feed.xml` all use that value.
- Before submitting `https://www.vectorpicks.com/feed.xml` to Apple Podcasts / Spotify: set a real `email`, publish at least one episode.
