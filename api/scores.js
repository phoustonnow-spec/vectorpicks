"use strict";

/**
 * GET /api/scores
 *
 * Server-side proxy for ESPN's public NFL scoreboard.
 * No API key. Optional ?dates=YYYYMMDD (exactly eight digits) is forwarded.
 * Anything else in dates is rejected and not sent upstream.
 *
 * Success (200):
 *   {
 *     fetched_at,
 *     games: [{
 *       id, kickoff, status,          // status: pre | in | post | null
 *       period, display_clock, detail,
 *       home: { name, abbr, score },
 *       away: { name, abbr, score },
 *       possession,                   // team abbreviation, or null
 *       red_zone                      // true/false, or null when ESPN omits it
 *     }]
 *   }
 *   Cache-Control: public, s-maxage=30, stale-while-revalidate=30
 *     when any game is in progress, otherwise
 *     public, s-maxage=600, stale-while-revalidate=3600
 *
 * Upstream failure (502) or a bad dates query (400):
 *   { error: "Live scores unavailable right now" }
 *   Cache-Control: public, max-age=0, s-maxage=60
 */

const SCORE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard";
const CACHE_LIVE = "public, s-maxage=30, stale-while-revalidate=30";
const CACHE_IDLE = "public, s-maxage=600, stale-while-revalidate=3600";
const CACHE_ERR = "public, max-age=0, s-maxage=60";
const ERROR_BODY = { error: "Live scores unavailable right now" };

function send(res, status, payload, cache) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": cache,
  });
  res.end(JSON.stringify(payload));
}

function datesQuery(req) {
  let raw = req && req.query ? req.query.dates : undefined;
  if ((raw == null || raw === "") && req && req.url) {
    const match = String(req.url).match(/[?&]dates=([^&]*)/);
    if (match) {
      try {
        raw = decodeURIComponent(match[1]);
      } catch (err) {
        raw = match[1];
      }
    }
  }
  if (Array.isArray(raw)) raw = raw[0];
  if (raw == null || raw === "") return { ok: true, dates: null };
  const dates = String(raw);
  if (!/^\d{8}$/.test(dates)) return { ok: false, dates: null };
  return { ok: true, dates: dates };
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function textOrNull(value) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function intOrNull(value) {
  if (typeof value === "number" && Number.isFinite(value)) return Math.trunc(value);
  if (typeof value === "string" && /^-?\d+$/.test(value.trim())) return parseInt(value, 10);
  return null;
}

function isoOrNull(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return null;
  return new Date(parsed).toISOString();
}

function statusOf(status) {
  const type = asObject(status && status.type) || {};
  const state = type.state;
  return state === "pre" || state === "in" || state === "post" ? state : null;
}

function sideOf(competitor) {
  const team = asObject(competitor && competitor.team) || {};
  return {
    name: textOrNull(team.displayName) || textOrNull(team.name) || textOrNull(competitor && competitor.displayName),
    abbr: textOrNull(team.abbreviation) || textOrNull(competitor && competitor.abbreviation),
    score: intOrNull(competitor && competitor.score),
    ids: [competitor && competitor.id, team.id].filter(function (id) {
      return id != null && String(id) !== "";
    }).map(String),
  };
}

function trimEvent(event) {
  const root = asObject(event);
  if (!root) return null;
  const competition = asObject(asArray(root.competitions)[0]) || {};
  const competitors = asArray(competition.competitors);
  let home = null;
  let away = null;
  for (let i = 0; i < competitors.length; i++) {
    const side = sideOf(competitors[i]);
    const where = competitors[i] && competitors[i].homeAway;
    if (where === "home" && !home) home = side;
    else if (where === "away" && !away) away = side;
  }
  if (!home || !away || (!home.name && !home.abbr) || (!away.name && !away.abbr)) return null;
  const status = asObject(competition.status) || asObject(root.status) || {};
  const type = asObject(status.type) || {};
  const situation = asObject(competition.situation);
  let possession = null;
  let redZone = null;
  if (situation) {
    if (situation.possession != null && String(situation.possession) !== "") {
      const want = String(situation.possession);
      const sides = [home, away];
      for (let i = 0; i < sides.length; i++) {
        if (sides[i].ids.indexOf(want) !== -1) {
          possession = sides[i].abbr;
          break;
        }
      }
    }
    if (typeof situation.isRedZone === "boolean") redZone = situation.isRedZone;
  }
  const id = textOrNull(root.id != null ? String(root.id) : null) || textOrNull(competition.id != null ? String(competition.id) : null);
  return {
    id: id,
    kickoff: isoOrNull(competition.date) || isoOrNull(root.date),
    status: statusOf(status),
    period: intOrNull(status.period),
    display_clock: textOrNull(status.displayClock),
    detail: textOrNull(type.shortDetail) || textOrNull(type.detail),
    home: { name: home.name, abbr: home.abbr, score: home.score },
    away: { name: away.name, abbr: away.abbr, score: away.score },
    possession: possession,
    red_zone: redZone,
  };
}

function trimBoard(data) {
  const events = data && Array.isArray(data.events) ? data.events : [];
  const games = [];
  for (let i = 0; i < events.length; i++) {
    let game = null;
    try {
      game = trimEvent(events[i]);
    } catch (err) {
      game = null;
    }
    if (game) games.push(game);
  }
  return games;
}

function cacheFor(games) {
  for (let i = 0; i < games.length; i++) {
    if (games[i] && games[i].status === "in") return CACHE_LIVE;
  }
  return CACHE_IDLE;
}

async function handler(req, res) {
  const method = req && req.method;
  if (method && method !== "GET" && method !== "HEAD") {
    send(res, 405, ERROR_BODY, CACHE_ERR);
    return;
  }

  const dates = datesQuery(req);
  if (!dates.ok) {
    send(res, 400, ERROR_BODY, CACHE_ERR);
    return;
  }

  const url = dates.dates ? SCORE_URL + "?dates=" + dates.dates : SCORE_URL;
  let upstream;
  try {
    upstream = await fetch(url, { headers: { accept: "application/json" } });
  } catch (err) {
    send(res, 502, ERROR_BODY, CACHE_ERR);
    return;
  }
  if (!upstream || !upstream.ok) {
    send(res, 502, ERROR_BODY, CACHE_ERR);
    return;
  }

  let data;
  try {
    data = await upstream.json();
  } catch (err) {
    send(res, 502, ERROR_BODY, CACHE_ERR);
    return;
  }
  if (!asObject(data)) {
    send(res, 502, ERROR_BODY, CACHE_ERR);
    return;
  }

  const games = trimBoard(data);
  send(res, 200, {
    fetched_at: new Date().toISOString(),
    games: games,
  }, cacheFor(games));
}

module.exports = handler;
