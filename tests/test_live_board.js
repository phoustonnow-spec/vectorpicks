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
  // Our Spread and Gap are the last two cells and must be a dash, not a made-up number.
  assert.ok(cells[3].includes("\u2014"), cells[3]);
  assert.ok(cells[4].includes("\u2014"), cells[4]);
  assert.ok(!mystery.includes("+0.8") && !mystery.includes("\u22122.4"));
  assert.ok(mystery.includes("Some Other Team \u22121.0"));

  const blank = row(html, "HOU @ IND");
  assert.ok(blank.includes("\u2014"));
  // No market number, so Gap stays blank even though Our Spread exists.
  assert.ok(!blank.includes("IND \u22124.2") || blank.includes("\u2014"));
  const blankCells = blank.split("</td>");
  assert.ok(blankCells[1].includes("\u2014"), "missing books must not invent a market");
  assert.ok(blankCells[3].includes("IND \u22124.2"), blankCells[3]);
  assert.ok(blankCells[4].includes("\u2014"), "gap without a market is a dash");

  const line = live.updatedLine(odds);
  assert.ok(line.startsWith("Lines updated "), line);
  assert.ok(line.includes(" PT \u00b7 refreshes about every 4 hours"), line);
  assert.ok(!line.includes("2 hours"), line);
  // Newest book last_update is 18:10Z, which is 11:10 AM Pacific on Sep 25, 2026.
  assert.ok(line.includes("11:10"), line);
}

function main() {
  testMath();
  testRender();
  console.log("OK live board: median, home-perspective gap, empty Our Spread");
}

main();
