"use strict";

/**
 * Local tests for api/scores.js. No network.
 *   node tests/test_scores_api.js
 */

const assert = require("assert");
const handler = require("../api/scores.js");

const SCORE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard";

function mockRes() {
  return {
    statusCode: 0,
    headers: {},
    body: "",
    writeHead(status, headers) {
      this.statusCode = status;
      this.headers = headers || {};
    },
    end(body) {
      this.body = body || "";
    },
    json() {
      return JSON.parse(this.body);
    },
  };
}

function competitor(id, where, abbr, name, score) {
  return {
    id: id,
    homeAway: where,
    score: score,
    team: { id: id, abbreviation: abbr, displayName: name },
  };
}

function event(opts) {
  return {
    id: opts.id,
    date: opts.kickoff,
    name: opts.name || "should not leak",
    competitions: [
      {
        id: opts.id,
        date: opts.kickoff,
        status: {
          displayClock: opts.clock,
          period: opts.period,
          type: {
            state: opts.state,
            shortDetail: opts.detail,
            detail: opts.longDetail,
            description: "ignore me",
          },
        },
        competitors: [
          competitor("2", "home", "GB", "Green Bay Packers", opts.homeScore),
          competitor("1", "away", "ATL", "Atlanta Falcons", opts.awayScore),
        ],
        situation: opts.situation,
        notes: [{ headline: "do not leak" }],
      },
    ],
  };
}

async function invoke(url) {
  const res = mockRes();
  await handler({ method: "GET", url: url || "/api/scores" }, res);
  return res;
}

function mockFetch(payload, status) {
  let seen = "";
  global.fetch = async (url) => {
    seen = String(url);
    if (payload instanceof Error) throw payload;
    return {
      ok: status == null ? true : status >= 200 && status < 300,
      status: status == null ? 200 : status,
      json: async () => payload,
    };
  };
  return () => seen;
}

async function testPre() {
  const seen = mockFetch({
    events: [event({
      id: 401,
      kickoff: "2026-09-27T17:00:00Z",
      state: "pre",
      detail: "Sun 1:00 PM EDT",
      clock: "0:00",
      period: 0,
      homeScore: "0",
      awayScore: "0",
    })],
    leagues: [{ name: "NFL" }],
  });
  const res = await invoke();
  assert.strictEqual(seen(), SCORE_URL);
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.headers["Cache-Control"], "public, s-maxage=600, stale-while-revalidate=3600");
  const game = res.json().games[0];
  assert.strictEqual(game.id, "401");
  assert.strictEqual(game.kickoff, "2026-09-27T17:00:00.000Z");
  assert.strictEqual(game.status, "pre");
  assert.strictEqual(game.period, 0);
  assert.strictEqual(game.display_clock, "0:00");
  assert.strictEqual(game.detail, "Sun 1:00 PM EDT");
  assert.deepStrictEqual(game.home, { name: "Green Bay Packers", abbr: "GB", score: 0 });
  assert.deepStrictEqual(game.away, { name: "Atlanta Falcons", abbr: "ATL", score: 0 });
  assert.strictEqual(game.possession, null);
  assert.strictEqual(game.red_zone, null);
  assert.ok(!res.body.includes("should not leak"));
  assert.ok(!res.body.includes("do not leak"));
}

async function testInProgress() {
  const seen = mockFetch({
    events: [
      event({
        id: "402",
        kickoff: "2026-09-27T17:00:00Z",
        state: "in",
        detail: "Q3 4:12",
        clock: "4:12",
        period: 3,
        homeScore: "21",
        awayScore: 17,
        situation: { possession: "2", isRedZone: true, down: 1 },
      }),
      { id: "broken", competitions: [{ competitors: [{ homeAway: "home" }] }] },
      { competitions: null, status: { type: { state: "in" } } },
    ],
  });
  const res = await invoke("/api/scores?dates=20260927");
  assert.strictEqual(seen(), SCORE_URL + "?dates=20260927");
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.headers["Cache-Control"], "public, s-maxage=30, stale-while-revalidate=30");
  const body = res.json();
  assert.strictEqual(body.games.length, 1);
  const game = body.games[0];
  assert.strictEqual(game.status, "in");
  assert.strictEqual(game.period, 3);
  assert.strictEqual(game.display_clock, "4:12");
  assert.strictEqual(game.detail, "Q3 4:12");
  assert.strictEqual(game.home.score, 21);
  assert.strictEqual(game.away.score, 17);
  assert.strictEqual(game.possession, "GB");
  assert.strictEqual(game.red_zone, true);
  assert.ok(body.fetched_at && !Number.isNaN(Date.parse(body.fetched_at)));
}

async function testFinal() {
  mockFetch({
    events: [event({
      id: "403",
      kickoff: "2026-09-25T00:20:00Z",
      state: "post",
      detail: "Final/OT",
      longDetail: "Final/OT",
      clock: "0:00",
      period: 5,
      homeScore: 20,
      awayScore: 23,
      situation: {},
    })],
  });
  const res = await invoke();
  const game = res.json().games[0];
  assert.strictEqual(res.headers["Cache-Control"], "public, s-maxage=600, stale-while-revalidate=3600");
  assert.strictEqual(game.status, "post");
  assert.strictEqual(game.detail, "Final/OT");
  assert.strictEqual(game.period, 5);
  assert.strictEqual(game.home.score, 20);
  assert.strictEqual(game.away.score, 23);
  assert.strictEqual(game.possession, null);
  assert.strictEqual(game.red_zone, null);
}

async function testQueryObject() {
  const seen = mockFetch({ events: [] });
  const res = mockRes();
  await handler({ method: "GET", url: "/api/scores", query: { dates: "20260928" } }, res);
  assert.strictEqual(seen(), SCORE_URL + "?dates=20260928");
  assert.strictEqual(res.statusCode, 200);
  assert.deepStrictEqual(res.json().games, []);
}

async function testBadDates() {
  let called = 0;
  global.fetch = async () => {
    called += 1;
    throw new Error("dates should not be forwarded");
  };
  for (const dates of ["2026", "202609271", "abcd1234", "2026-09-27", "../etc"]) {
    const res = await invoke("/api/scores?dates=" + encodeURIComponent(dates));
    assert.strictEqual(res.statusCode, 400, dates);
    assert.strictEqual(res.headers["Cache-Control"], "public, max-age=0, s-maxage=60");
    assert.deepStrictEqual(res.json(), { error: "Live scores unavailable right now" });
  }
  assert.strictEqual(called, 0);
}

async function testUpstreamError() {
  mockFetch({ message: "nope" }, 500);
  const res = await invoke();
  assert.strictEqual(res.statusCode, 502);
  assert.strictEqual(res.headers["Cache-Control"], "public, max-age=0, s-maxage=60");
  assert.deepStrictEqual(res.json(), { error: "Live scores unavailable right now" });

  global.fetch = async () => {
    throw new Error("network down");
  };
  const thrown = await invoke();
  assert.strictEqual(thrown.statusCode, 502);
  assert.deepStrictEqual(thrown.json(), { error: "Live scores unavailable right now" });

  mockFetch(["not", "an", "object"]);
  const bad = await invoke();
  assert.strictEqual(bad.statusCode, 502);

  mockFetch({ events: "nope" });
  const gaps = await invoke();
  assert.strictEqual(gaps.statusCode, 200);
  assert.deepStrictEqual(gaps.json().games, []);
  assert.strictEqual(gaps.headers["Cache-Control"], "public, s-maxage=600, stale-while-revalidate=3600");
}

async function main() {
  await testPre();
  await testInProgress();
  await testFinal();
  await testQueryObject();
  await testBadDates();
  await testUpstreamError();
  console.log("OK api/scores.js: pre, in progress, final, error");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
