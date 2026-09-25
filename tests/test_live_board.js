"use strict";

/**
 * Client render checks for the Live Board. No network.
 *   node tests/test_live_board.js
 */

const assert = require("assert");
const live = require("../assets/live.js");

const card = {
  season: 2026,
  week: 3,
  teams: {
    "Atlanta Falcons": "ATL",
    "Green Bay Packers": "GB",
    "Las Vegas Raiders": "LV",
    "New Orleans Saints": "NO",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
  },
  games: [
    {
      away_team: "Atlanta Falcons",
      home_team: "Green Bay Packers",
      our_team: "Green Bay Packers",
      our_point: -2.4,
      our_label: "GB -2.4",
    },
    {
      away_team: "Las Vegas Raiders",
      home_team: "New Orleans Saints",
      our_team: "Las Vegas Raiders",
      our_point: -0.8,
      our_label: "LV -0.8",
    },
    {
      away_team: "Houston Texans",
      home_team: "Indianapolis Colts",
      our_team: "Indianapolis Colts",
      our_point: -4.2,
      our_label: "IND -4.2",
    },
  ],
};

function testMath() {
  assert.strictEqual(live.median([-5.5, -4.5, -4.5, -5]), -4.75);
  assert.strictEqual(live.median([-5.5, -4.5, -4]), -4.5);
  assert.strictEqual(live.median([]), null);
  const gb = live.findCard(card.games, "Green Bay Packers", "Atlanta Falcons");
  assert.strictEqual(live.toHomePoint(gb, "Green Bay Packers", "Atlanta Falcons"), -2.4);
  // Home/away flipped vs the card still uses the API home side.
  assert.strictEqual(live.toHomePoint(gb, "Atlanta Falcons", "Green Bay Packers"), 2.4);
  const no = live.findCard(card.games, "New Orleans Saints", "Las Vegas Raiders");
  assert.strictEqual(live.toHomePoint(no, "New Orleans Saints", "Las Vegas Raiders"), 0.8);
  const ind = card.games[2];
  // Westgate-style check: market home +2.5 minus our home -4.2 = +6.7 (card gap magnitude).
  assert.strictEqual(live.gap(2.5, live.toHomePoint(ind, "Indianapolis Colts", "Houston Texans")), 6.7);
  assert.strictEqual(live.gap(-4.5, -2.4), -2.1);
  assert.strictEqual(live.gap(null, -2.4), null);
  assert.strictEqual(live.toHomePoint(null, "Green Bay Packers", "Atlanta Falcons"), null);
  assert.strictEqual(live.fmtSigned(-4.75), "\u22124.75");
  assert.strictEqual(live.fmtSigned(-2.4), "\u22122.4");
  assert.strictEqual(live.fmtSigned(0.8), "+0.8");
}

function row(html, matchup) {
  const parts = html.split("<tr>").slice(1);
  const found = parts.find((p) => p.includes(matchup));
  assert.ok(found, "missing row " + matchup);
  return found;
}

function testRender() {
  const odds = {
    fetched_at: "2026-09-25T16:00:00Z",
    games: [
      {
        id: "gb",
        commence_time: "2026-09-27T20:25:00Z",
        home_team: "Green Bay Packers",
        away_team: "Atlanta Falcons",
        books: {
          fanduel: { last_update: "2026-09-25T18:05:00Z", spread: { point: -4.5, price: -108 }, total: { point: 45.5, over_price: -110, under_price: -110 } },
          draftkings: { last_update: "2026-09-25T18:00:00Z", spread: { point: -5.5, price: -110 }, total: { point: 44.5, over_price: -105, under_price: -115 } },
          caesars: { spread: { point: -5, price: -115 }, total: { point: 44 } },
          betmgm: { spread: { point: -4.5, price: -110 }, total: { point: 44.5 } },
        },
      },
      {
        id: "no",
        commence_time: "2026-09-28T00:20:00Z",
        home_team: "New Orleans Saints",
        away_team: "Las Vegas Raiders",
        books: {
          draftkings: { last_update: "2026-09-25T18:10:00Z", spread: { point: -3, price: -110 }, total: { point: 41.5 } },
        },
      },
      {
        id: "mystery",
        commence_time: "2026-09-27T17:00:00Z",
        home_team: "Some Other Team",
        away_team: "Mystery Club",
        books: {
          draftkings: { spread: { point: -1, price: -110 }, total: { point: 40 } },
        },
      },
      {
        id: "blank",
        commence_time: "2026-09-27T18:00:00Z",
        home_team: "Indianapolis Colts",
        away_team: "Houston Texans",
        books: { draftkings: { spread: null, total: null } },
      },
    ],
  };
  const html = live.renderTable(odds, card);
  const mysteryAt = html.indexOf("Mystery Club @ Some Other Team");
  const indAt = html.indexOf("HOU @ IND");
  const gbAt = html.indexOf("ATL @ GB");
  const noAt = html.indexOf("LV @ NO");
  assert.ok(mysteryAt >= 0 && indAt > mysteryAt && gbAt > indAt && noAt > gbAt, "games are not sorted by kickoff");

  const gbRow = row(html, "ATL @ GB");
  assert.ok(gbRow.includes("GB \u22124.75"), gbRow);
  assert.ok(gbRow.includes("GB \u22122.4"), gbRow);
  assert.ok(gbRow.includes("\u22122.35"), "gap should be market - our (" + gbRow + ")");
  assert.ok(gbRow.includes("DK \u22125.5"), "book lines missing");
  assert.ok(gbRow.includes("FD \u22124.5"), gbRow);
  assert.ok(gbRow.indexOf("DK") < gbRow.indexOf("FD"), "books should follow DK, FD, MGM, CZR");
  assert.ok(!gbRow.includes("card GB"), "same-side card label should not be repeated");

  const noRow = row(html, "LV @ NO");
  assert.ok(noRow.includes("NO +0.8"), noRow);
  assert.ok(noRow.includes("card LV \u22120.8"), noRow);
  assert.ok(noRow.includes("\u22123.8"), noRow);

  const mystery = row(html, "Mystery Club @ Some Other Team");
  const cells = mystery.split("</td>");
  // Score, Our Spread, and Gap stay a dash. No invented pick or line.
  assert.ok(cells[1].includes("\u2014"), cells[1]);
  assert.ok(cells[4].includes("\u2014"), cells[4]);
  assert.ok(cells[5].includes("\u2014"), cells[5]);
  assert.ok(!mystery.includes("+0.8") && !mystery.includes("\u22122.4"));
  assert.ok(mystery.includes("Some Other Team \u22121.0"));

  const blank = row(html, "HOU @ IND");
  assert.ok(blank.includes("\u2014"));
  // No market number, so Gap stays blank even though Our Spread exists.
  assert.ok(!blank.includes("IND \u22124.2") || blank.includes("\u2014"));
  const blankCells = blank.split("</td>");
  assert.ok(blankCells[2].includes("\u2014"), "missing books must not invent a market");
  assert.ok(blankCells[4].includes("IND \u22124.2"), blankCells[4]);
  assert.ok(blankCells[5].includes("\u2014"), "gap without a market is a dash");

  const line = live.updatedLine(odds);
  assert.ok(line.startsWith("Lines updated "), line);
  assert.ok(line.includes(" PT \u00b7 refreshes about every 4 hours"), line);
  assert.ok(!line.includes("2 hours"), line);
  // Newest book last_update is 18:10Z, which is 11:10 AM Pacific on Sep 25, 2026.
  assert.ok(line.includes("11:10"), line);
}

function testAts() {
  // Favorite: MIN -1.5. 24-21 covers by 1.5; 21-20 does not; 24-22.5 is not an NFL score.
  assert.strictEqual(live.atsStatus(-1.5, 24, 21, "in"), "Covering");
  assert.strictEqual(live.atsStatus(-1.5, 24, 21, "post"), "Won");
  assert.strictEqual(live.atsStatus(-1.5, 21, 20, "in"), "Not covering");
  assert.strictEqual(live.atsStatus(-1.5, 21, 20, "post"), "Lost");
  // Dog: ATL +5.5. 17-20 covers; 14-20 does not.
  assert.strictEqual(live.atsStatus(5.5, 17, 20, "in"), "Covering");
  assert.strictEqual(live.atsStatus(5.5, 17, 20, "post"), "Won");
  assert.strictEqual(live.atsStatus(5.5, 14, 20, "in"), "Not covering");
  assert.strictEqual(live.atsStatus(5.5, 14, 20, "post"), "Lost");
  // Push, either side, live or final. Pre-game never gets a status.
  assert.strictEqual(live.atsStatus(-3, 24, 21, "in"), "Push");
  assert.strictEqual(live.atsStatus(-3, 24, 21, "post"), "Push");
  assert.strictEqual(live.atsStatus(3, 17, 20, "post"), "Push");
  assert.strictEqual(live.atsStatus(3, 17, 20, "pre"), null);
  assert.strictEqual(live.atsStatus(5.5, null, 20, "in"), null);
  assert.strictEqual(live.coverMargin(5.5, 14, 20), -0.5);
  assert.strictEqual(live.coverMargin(-7.5, 31, 24), -0.5);

  const picked = {
    games: [
      {
        away_team: "Atlanta Falcons",
        home_team: "Green Bay Packers",
        our_team: "Green Bay Packers",
        our_point: -2.4,
        our_label: "GB -2.4",
        pick_team: "Atlanta Falcons",
        pick_abbr: "ATL",
        pick_line: 5.5,
        pick_label: "ATL +5.5",
        tier: "Lean",
      },
      {
        away_team: "Seattle Seahawks",
        home_team: "Washington Commanders",
        our_team: "Seattle Seahawks",
        our_point: -10.8,
        our_label: "SEA -10.8",
        pick_team: null,
        pick_abbr: null,
        pick_line: null,
        pick_label: null,
        tier: "Pass",
      },
    ],
    teams: card.teams,
  };
  const scores = {
    games: [
      {
        status: "post",
        detail: "Final",
        kickoff: "2026-09-28T00:20:00Z",
        home: { name: "Green Bay Packers", abbr: "GB", score: 14 },
        away: { name: "Atlanta Falcons", abbr: "ATL", score: 17 },
      },
      {
        status: "in",
        detail: "Q3 4:12",
        kickoff: "2026-09-27T17:00:00Z",
        possession: "NE",
        red_zone: true,
        home: { name: "Jacksonville Jaguars", abbr: "JAX", score: 10 },
        away: { name: "New England Patriots", abbr: "NE", score: 14 },
      },
      {
        status: "pre",
        detail: "Sun 1:00 PM",
        kickoff: "2026-09-27T20:25:00Z",
        home: { name: "Washington Commanders", abbr: "WAS", score: 0 },
        away: { name: "Seattle Seahawks", abbr: "SEA", score: 0 },
      },
    ],
  };
  const odds = {
    games: [
      {
        commence_time: "2026-09-27T20:25:00Z",
        home_team: "Washington Commanders",
        away_team: "Seattle Seahawks",
        books: { draftkings: { spread: { point: -7, price: -110 }, total: { point: 43 } } },
      },
    ],
  };
  const merged = live.mergeBoard(odds, picked, scores);
  assert.strictEqual(merged.length, 3);
  assert.strictEqual(merged[0].away_team, "New England Patriots");
  assert.strictEqual(merged[1].away_team, "Seattle Seahawks");
  assert.strictEqual(merged[2].away_team, "Atlanta Falcons");
  const html = live.renderTable(odds, picked, scores);
  assert.ok(html.includes("Our pick: ATL +5.5"), html);
  assert.ok(html.includes("Won"), html);
  assert.ok(html.includes("ATL 17"), html);
  assert.ok(!html.includes("Our pick: SEA"), html);
  assert.ok(html.indexOf("NE 14") < html.indexOf("Seattle Seahawks @ Washington Commanders"), "live games sort before upcoming");
  assert.ok(html.indexOf("Seattle Seahawks @ Washington Commanders") < html.indexOf("ATL @ GB"), "finals sort after upcoming");
  const strip = live.renderStrip(scores, {
    games: picked.games.concat([{
      away_team: "New England Patriots",
      home_team: "Jacksonville Jaguars",
      pick_team: "New England Patriots",
      pick_abbr: "NE",
      pick_line: 3,
      pick_label: "NE +3",
      tier: "Lean",
    }]),
    teams: {},
  });
  assert.ok(strip.includes("Live now"), strip);
  assert.ok(strip.includes("Our pick: NE +3"), strip);
  assert.ok(strip.includes("Covering"), strip);
  assert.ok(strip.includes("Our pick: ATL +5.5"), strip);
  assert.ok(!strip.includes("SEA"), strip);
  assert.ok(strip.includes("Scores via ESPN; unofficial, may lag."), strip);
  assert.strictEqual(live.nextScoresDelay(scores.games), 60000);
  assert.strictEqual(live.nextScoresDelay([{ status: "post" }, { status: "pre" }]), 600000);
  assert.strictEqual(live.renderStrip({ games: [scores.games[2]] }, picked), "");
}

function main() {
  testMath();
  testRender();
  testAts();
  console.log("OK live board: median, home-perspective gap, empty Our Spread");
}

main();
