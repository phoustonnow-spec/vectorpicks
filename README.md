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
  weeks/2026-w03.json  one file per week -> card-YYYY-wNN.html; newest also = card.html
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
If `/workspace/shorts/ats-tracker.csv` exists (box workflow), the build copies it into `data/` first.

## Weekly routine

1. **New week card:** add `data/weeks/2026-wNN.json` (same shape as `2026-w03.json`). Use only numbers from the week's board files. No invented lines, splits, injuries or scores.
2. **Results:** update the tracker CSV (`ATS Result` W/L/P, `Final Score`, `Units`); add rows for new weeks. Optional `Season` column (defaults to 2026).
3. **Episode:** put the mp3 in `public/episodes/`, add an entry to `data/episodes.json`:
   `{"title","date":"YYYY-MM-DD","show_type":"Tuesday Rankings|Thursday Picks|Sunday Update|Sunday Recap","mp3":"episodes/file.mp3","duration":"HH:MM:SS","description"}`. `bytes` is filled in automatically.
4. **Short:** add `{"title","date","week","youtube_url"}` to `data/shorts.json`.
5. `python3 build.py --validate`, commit, push. Vercel redeploys automatically.

## Deploy (GitHub + Vercel)

- Import the GitHub repo in Vercel. `vercel.json` sets framework "Other", no install, output directory `public`. No build runs on Vercel; the committed `public/` is served.
- Add the custom domain in Vercel (Project > Settings > Domains) and point DNS as Vercel instructs.
- `base_url` in `data/site_config.json` is `https://vectorpicks.com`. Change it there if the domain differs, rebuild, commit.
- Before submitting `https://vectorpicks.com/feed.xml` to Apple Podcasts / Spotify: set a real `email`, publish at least one episode.
