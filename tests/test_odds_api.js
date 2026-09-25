"use strict";

/**
 * Local tests for api/odds.js. No network and no real ODDS_API_KEY.
 *   node tests/test_odds_api.js
 */

const assert = require("assert");
const handler = require("../api/odds.js");

const SECRET = "super-secret-odds-key";
const REQUIRED_PREFIX =
  "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds" +
  "?regions=us&markets=spreads,totals&oddsFormat=american" +
  "&bookmakers=draftkings,fanduel,betmgm,caesars&apiKey=";

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

function sampleGame() {
  return {
    id: "game-1",
    sport_key: "americanfootball_nfl",
    sport_title: "NFL",
    commence_time: "2026-09-27T17:00:00Z",
    home_team: "Green Bay Packers",
    away_team: "Atlanta Falcons",
    apiKey: SECRET,
    bookmakers: [
      {
        key: "draftkings",
        title: "DraftKings",
        last_update: "2026-09-25T18:00:00Z",
        markets: [
          {
            key: "spreads",
            outcomes: [
              { name: "Atlanta Falcons", price: -110, point: 5.5 },
              { name: "Green Bay Packers", price: -110, point: -5.5 },
            ],
          },
          {
            key: "totals",
            outcomes: [
              { name: "Over", price: -105, point: 44.5 },
              { name: "Under", price: -115, point: 44.5 },
            ],
          },
          {
            key: "h2h",
            outcomes: [
              { name: "Green Bay Packers", price: -240 },
              { name: "Atlanta Falcons", price: 200 },
            ],
          },
        ],
      },
      {
        key: "fanduel",
        title: "FanDuel",
        last_update: "2026-09-25T18:05:00Z",
        markets: [
          {
            key: "spreads",
            outcomes: [
              { name: "Green Bay Packers", price: -108, point: -4.5 },
              { name: "Atlanta Falcons", price: -112, point: 4.5 },
            ],
          },
        ],
      },
    ],
  };
}

async function invoke() {
  const res = mockRes();
  await handler({ method: "GET" }, res);
  return res;
}

async function testSuccess() {
  let called = 0;
  let seenUrl = "";
  process.env.ODDS_API_KEY = SECRET;
  global.fetch = async (url) => {
    called += 1;
    seenUrl = String(url);
    return {
      ok: true,
      status: 200,
      headers: { get: (name) => (name === "x-requests-remaining" ? "432" : null) },
      json: async () => [sampleGame()],
    };
  };
  const res = await invoke();
  assert.strictEqual(called, 1);
  assert.strictEqual(seenUrl, REQUIRED_PREFIX + SECRET);
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.headers["Cache-Control"], "public, s-maxage=14400, stale-while-revalidate=86400");
  assert.ok(!seenUrl.includes("h2h"), seenUrl);
  assert.strictEqual(res.headers["x-requests-remaining"], "432");
  assert.ok(String(res.headers["Content-Type"]).includes("application/json"));
  const body = res.json();
  assert.strictEqual(body.requests_remaining, "432");
  assert.ok(body.fetched_at && !Number.isNaN(Date.parse(body.fetched_at)));
  assert.strictEqual(body.games.length, 1);
  const game = body.games[0];
  assert.deepStrictEqual(Object.keys(game).sort(), ["away_team", "books", "commence_time", "home_team", "id"]);
  assert.strictEqual(game.id, "game-1");
  assert.strictEqual(game.home_team, "Green Bay Packers");
  assert.strictEqual(game.away_team, "Atlanta Falcons");
  assert.strictEqual(game.books.draftkings.spread.point, -5.5);
  assert.strictEqual(game.books.draftkings.spread.price, -110);
  assert.strictEqual(game.books.draftkings.total.point, 44.5);
  assert.strictEqual(game.books.draftkings.total.over_price, -105);
  assert.strictEqual(game.books.draftkings.total.under_price, -115);
  assert.strictEqual(game.books.draftkings.moneylines, undefined);
  assert.ok(!Object.prototype.hasOwnProperty.call(game.books.draftkings, "moneylines"));
  assert.strictEqual(game.books.draftkings.last_update, "2026-09-25T18:00:00Z");
  assert.strictEqual(game.books.fanduel.spread.point, -4.5);
  assert.strictEqual(game.books.fanduel.total, null);
  assert.strictEqual(game.books.fanduel.moneylines, undefined);
  const raw = res.body;
  assert.ok(!raw.includes(SECRET), "response leaked the API key");
  assert.ok(!raw.includes("sport_key"), "response was not trimmed");
  assert.ok(!raw.includes("moneylines") && !raw.includes("-240"), "h2h moneylines were not dropped");
  assert.ok(!raw.includes("Atlanta Falcons\", \"price\": -110, \"point\": 5.5") && game.books.draftkings.spread.point < 0);
}

async function testMissingKey() {
  delete process.env.ODDS_API_KEY;
  let called = 0;
  global.fetch = async () => {
    called += 1;
    throw new Error("fetch should not run without a key");
  };
  const res = await invoke();
  assert.strictEqual(called, 0);
  assert.strictEqual(res.statusCode, 500);
  assert.strictEqual(res.headers["Cache-Control"], "public, max-age=0, s-maxage=60");
  assert.ok(!res.headers["Cache-Control"].includes("14400"));
  assert.deepStrictEqual(res.json(), { error: "Live odds unavailable right now" });
  assert.ok(!res.body.includes("ODDS_API_KEY"));
}

async function testUpstreamHttpError() {
  process.env.ODDS_API_KEY = SECRET;
  global.fetch = async () => ({
    ok: false,
    status: 401,
    headers: { get: (name) => (name === "x-requests-remaining" ? "7" : null) },
    json: async () => ({ message: "invalid key " + SECRET }),
  });
  const res = await invoke();
  assert.strictEqual(res.statusCode, 502);
  assert.strictEqual(res.headers["Cache-Control"], "public, max-age=0, s-maxage=60");
  assert.strictEqual(res.headers["x-requests-remaining"], "7");
  assert.deepStrictEqual(res.json(), { error: "Live odds unavailable right now" });
  assert.ok(!res.body.includes(SECRET));
}

async function testUpstreamThrow() {
  process.env.ODDS_API_KEY = SECRET;
  global.fetch = async () => {
    throw new Error("network down " + SECRET);
  };
  const res = await invoke();
  assert.strictEqual(res.statusCode, 502);
  assert.strictEqual(res.headers["Cache-Control"], "public, max-age=0, s-maxage=60");
  assert.deepStrictEqual(res.json(), { error: "Live odds unavailable right now" });
  assert.ok(!res.body.includes(SECRET));
}

async function testUpstreamNotArray() {
  process.env.ODDS_API_KEY = SECRET;
  global.fetch = async () => ({
    ok: true,
    status: 200,
    headers: { get: () => null },
    json: async () => ({ message: "nope", apiKey: SECRET }),
  });
  const res = await invoke();
  assert.strictEqual(res.statusCode, 502);
  assert.ok(!res.body.includes(SECRET));
}

async function main() {
  const prev = process.env.ODDS_API_KEY;
  try {
    await testSuccess();
    await testMissingKey();
    await testUpstreamHttpError();
    await testUpstreamThrow();
    await testUpstreamNotArray();
  } finally {
    if (prev === undefined) delete process.env.ODDS_API_KEY;
    else process.env.ODDS_API_KEY = prev;
  }
  console.log("OK api/odds.js: success, missing key, upstream error");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
