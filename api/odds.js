"use strict";

/**
 * GET /api/odds
 *
 * Server-side proxy for The Odds API v4 NFL odds.
 * The key is read from ODDS_API_KEY (set it in the Vercel project env).
 * It is never written into the response, and it must not be committed.
 *
 * Success (200):
 *   {
 *     fetched_at,                 // ISO timestamp
 *     requests_remaining,         // upstream x-requests-remaining, or null
 *     games: [{
 *       id, commence_time, home_team, away_team,
 *       books: {
 *         <book key>: {
 *           last_update,
 *           spread: { point, price } | null,          // home team
 *           total: { point, over_price, under_price } | null,
 *           moneylines: { home, away } | null
 *         }
 *       }
 *     }]
 *   }
 *   Cache-Control: public, s-maxage=7200, stale-while-revalidate=86400
 *
 * Missing key (500) or upstream failure (502):
 *   { error: "Live odds unavailable right now" }
 *   Cache-Control: public, max-age=0, s-maxage=60
 */

const ODDS_URL =
  "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds" +
  "?regions=us&markets=spreads,totals,h2h&oddsFormat=american" +
  "&bookmakers=draftkings,fanduel,betmgm,caesars";

const CACHE_OK = "public, s-maxage=7200, stale-while-revalidate=86400";
const CACHE_ERR = "public, max-age=0, s-maxage=60";
const ERROR_BODY = { error: "Live odds unavailable right now" };

function send(res, status, payload, cache, extra) {
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": cache,
  };
  if (extra) {
    for (const key of Object.keys(extra)) headers[key] = extra[key];
  }
  res.writeHead(status, headers);
  res.end(JSON.stringify(payload));
}

function numOrNull(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function findOutcome(outcomes, name) {
  if (!Array.isArray(outcomes)) return null;
  for (const outcome of outcomes) {
    if (outcome && outcome.name === name) return outcome;
  }
  return null;
}

function marketByKey(markets) {
  const out = {};
  if (!Array.isArray(markets)) return out;
  for (const market of markets) {
    if (market && typeof market.key === "string") out[market.key] = market;
  }
  return out;
}

function trimBook(book, home, away) {
  const markets = marketByKey(book && book.markets);
  const spread = findOutcome(markets.spreads && markets.spreads.outcomes, home);
  const over = findOutcome(markets.totals && markets.totals.outcomes, "Over");
  const under = findOutcome(markets.totals && markets.totals.outcomes, "Under");
  const homeMl = findOutcome(markets.h2h && markets.h2h.outcomes, home);
  const awayMl = findOutcome(markets.h2h && markets.h2h.outcomes, away);
  const spreadPoint = spread ? numOrNull(spread.point) : null;
  const totalPoint = (over && numOrNull(over.point) != null)
    ? numOrNull(over.point)
    : (under ? numOrNull(under.point) : null);
  return {
    last_update: book && typeof book.last_update === "string" ? book.last_update : null,
    spread: spreadPoint == null ? null : { point: spreadPoint, price: numOrNull(spread.price) },
    total: totalPoint == null ? null : {
      point: totalPoint,
      over_price: over ? numOrNull(over.price) : null,
      under_price: under ? numOrNull(under.price) : null,
    },
    moneylines: (!homeMl && !awayMl) ? null : {
      home: homeMl ? numOrNull(homeMl.price) : null,
      away: awayMl ? numOrNull(awayMl.price) : null,
    },
  };
}

function trimGame(game) {
  const home = game && game.home_team;
  const away = game && game.away_team;
  const books = {};
  const list = game && Array.isArray(game.bookmakers) ? game.bookmakers : [];
  for (const book of list) {
    if (!book || typeof book.key !== "string" || !book.key) continue;
    books[book.key] = trimBook(book, home, away);
  }
  return {
    id: game && game.id,
    commence_time: game && game.commence_time,
    home_team: home,
    away_team: away,
    books: books,
  };
}

function remainingHeader(headers) {
  if (!headers || typeof headers.get !== "function") return null;
  const raw = headers.get("x-requests-remaining");
  if (raw == null || !/^[0-9]+$/.test(String(raw))) return null;
  return String(raw);
}

async function handler(req, res) {
  const method = req && req.method;
  if (method && method !== "GET" && method !== "HEAD") {
    send(res, 405, ERROR_BODY, CACHE_ERR, { Allow: "GET" });
    return;
  }

  const key = process.env.ODDS_API_KEY;
  if (!key) {
    send(res, 500, ERROR_BODY, CACHE_ERR);
    return;
  }

  let upstream;
  try {
    upstream = await fetch(ODDS_URL + "&apiKey=" + encodeURIComponent(key), {
      headers: { accept: "application/json" },
    });
  } catch (err) {
    send(res, 502, ERROR_BODY, CACHE_ERR);
    return;
  }

  const remaining = remainingHeader(upstream.headers);
  const extra = remaining == null ? undefined : { "x-requests-remaining": remaining };

  if (!upstream.ok) {
    send(res, 502, ERROR_BODY, CACHE_ERR, extra);
    return;
  }

  let data;
  try {
    data = await upstream.json();
  } catch (err) {
    send(res, 502, ERROR_BODY, CACHE_ERR, extra);
    return;
  }
  if (!Array.isArray(data)) {
    send(res, 502, ERROR_BODY, CACHE_ERR, extra);
    return;
  }

  send(res, 200, {
    fetched_at: new Date().toISOString(),
    requests_remaining: remaining,
    games: data.map(trimGame),
  }, CACHE_OK, extra);
}

module.exports = handler;
