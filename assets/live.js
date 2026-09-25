/* Live Board: /api/odds + the current card's Our Spread (live-spreads.json). */
(function (root) {
  "use strict";

  var BOOK_ORDER = ["draftkings", "fanduel", "betmgm", "caesars"];
  var BOOK_SHORT = {
    draftkings: "DK",
    fanduel: "FD",
    betmgm: "MGM",
    caesars: "CZR",
    williamhill_us: "CZR",
  };
  var DASH = "\u2014";
  var MINUS = "\u2212";

  function norm(s) {
    return String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function isNum(n) {
    return typeof n === "number" && isFinite(n);
  }

  function median(values) {
    var xs = [];
    for (var i = 0; i < values.length; i++) {
      if (isNum(values[i])) xs.push(values[i]);
    }
    if (!xs.length) return null;
    xs.sort(function (a, b) { return a - b; });
    var mid = Math.floor(xs.length / 2);
    if (xs.length % 2) return xs[mid];
    return (xs[mid - 1] + xs[mid]) / 2;
  }

  function sub(a, b) {
    return Math.round((a - b) * 100) / 100;
  }

  function namesMatch(a, b) {
    return norm(a) === norm(b);
  }

  function findCard(games, home, away) {
    var list = games || [];
    for (var i = 0; i < list.length; i++) {
      var g = list[i];
      var same = namesMatch(g.home_team, home) && namesMatch(g.away_team, away);
      var flip = namesMatch(g.home_team, away) && namesMatch(g.away_team, home);
      if (same || flip) return g;
    }
    return null;
  }

  /* Card quote is that team's spread (negative = that team favored).
     Home-team perspective matches the market column: negative = home favored. */
  function toHomePoint(row, home, away) {
    if (!row || !isNum(row.our_point)) return null;
    if (namesMatch(row.our_team, home)) return row.our_point;
    if (namesMatch(row.our_team, away)) return -row.our_point;
    return null;
  }

  function gap(market, ourHome) {
    if (!isNum(market) || !isNum(ourHome)) return null;
    return sub(market, ourHome);
  }

  function fmtSigned(n) {
    if (!isNum(n)) return DASH;
    var rounded = Math.round(n * 100) / 100;
    var cents = Math.round(Math.abs(rounded) * 100);
    var digits = cents % 10 === 0 ? 1 : 2;
    var abs = Math.abs(rounded).toFixed(digits);
    if (rounded < 0) return MINUS + abs;
    if (rounded > 0) return "+" + abs;
    return Number(0).toFixed(digits);
  }

  function fmtPlain(n) {
    if (!isNum(n)) return DASH;
    var rounded = Math.round(n * 100) / 100;
    var cents = Math.round(Math.abs(rounded) * 100);
    var digits = cents % 10 === 0 ? 1 : 2;
    return rounded.toFixed(digits);
  }

  function fmtPrice(n) {
    if (!isNum(n)) return "";
    var v = Math.round(n);
    if (v > 0) return "+" + v;
    if (v < 0) return MINUS + Math.abs(v);
    return "0";
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function minusText(s) {
    return String(s).replace(/(^|\s)-(?=\d)/g, "$1" + MINUS);
  }

  function abbr(name, card) {
    var teams = (card && card.teams) || {};
    if (teams[name]) return teams[name];
    var want = norm(name);
    var keys = Object.keys(teams);
    for (var i = 0; i < keys.length; i++) {
      if (norm(keys[i]) === want) return teams[keys[i]];
    }
    return name;
  }

  function bookEntries(books) {
    var keys = Object.keys(books || {});
    keys.sort(function (a, b) {
      var ia = BOOK_ORDER.indexOf(a);
      var ib = BOOK_ORDER.indexOf(b);
      if (ia < 0) ia = 99;
      if (ib < 0) ib = 99;
      if (ia !== ib) return ia - ib;
      return a < b ? -1 : a > b ? 1 : 0;
    });
    var out = [];
    for (var i = 0; i < keys.length; i++) {
      out.push({
        key: keys[i],
        short: BOOK_SHORT[keys[i]] || keys[i],
        book: books[keys[i]] || {},
      });
    }
    return out;
  }

  function bookSpreadLine(entries) {
    var parts = [];
    for (var i = 0; i < entries.length; i++) {
      var sp = entries[i].book && entries[i].book.spread;
      if (!sp || !isNum(sp.point)) continue;
      var price = fmtPrice(sp.price);
      parts.push(price
        ? entries[i].short + " " + fmtSigned(sp.point) + " (" + price + ")"
        : entries[i].short + " " + fmtSigned(sp.point));
    }
    return parts.join(" \u00b7 ");
  }

  function bookTotalLine(entries) {
    var parts = [];
    for (var i = 0; i < entries.length; i++) {
      var total = entries[i].book && entries[i].book.total;
      if (!total || !isNum(total.point)) continue;
      parts.push(entries[i].short + " " + fmtPlain(total.point));
    }
    return parts.join(" \u00b7 ");
  }

  function fmtKick(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Los_Angeles",
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    }).format(d);
  }

  function fmtPt(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return null;
    return new Intl.DateTimeFormat("en-US", {
      timeZone: "America/Los_Angeles",
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(d);
  }

  function newestStamp(odds) {
    var best = null;
    var games = (odds && odds.games) || [];
    for (var i = 0; i < games.length; i++) {
      var books = games[i].books || {};
      var keys = Object.keys(books);
      for (var k = 0; k < keys.length; k++) {
        var lu = books[keys[k]] && books[keys[k]].last_update;
        var t = lu ? Date.parse(lu) : NaN;
        if (!isNaN(t) && (best == null || t > best)) best = t;
      }
    }
    if (best != null) return new Date(best).toISOString();
    return odds && odds.fetched_at || null;
  }

  function updatedLine(odds) {
    var when = fmtPt(newestStamp(odds));
    if (!when) return "Refreshes about every 2 hours";
    return "Lines updated " + when + " PT \u00b7 refreshes about every 2 hours";
  }

  function cell(label, cls, inner) {
    return '<td data-l="' + esc(label) + '"' + (cls ? ' class="' + cls + '"' : "") + ">" + inner + "</td>";
  }

  function small(text) {
    if (!text) return "";
    return '<span class="book-lines">' + esc(text) + "</span>";
  }

  function renderTable(odds, card) {
    var games = ((odds && odds.games) || []).slice().sort(function (a, b) {
      var ta = Date.parse(a.commence_time);
      var tb = Date.parse(b.commence_time);
      if (isNaN(ta)) ta = 0;
      if (isNaN(tb)) tb = 0;
      return ta - tb;
    });
    if (!games.length) return "";
    var rows = "";
    for (var i = 0; i < games.length; i++) {
      var game = games[i];
      var home = game.home_team || "";
      var away = game.away_team || "";
      var homeAbbr = abbr(home, card);
      var awayAbbr = abbr(away, card);
      var entries = bookEntries(game.books);
      var spreadPts = [];
      var totalPts = [];
      for (var b = 0; b < entries.length; b++) {
        var book = entries[b].book || {};
        if (book.spread && isNum(book.spread.point)) spreadPts.push(book.spread.point);
        if (book.total && isNum(book.total.point)) totalPts.push(book.total.point);
      }
      var market = median(spreadPts);
      var total = median(totalPts);
      var row = findCard(card && card.games, home, away);
      var ourHome = toHomePoint(row, home, away);
      var gapN = gap(market, ourHome);
      var kick = fmtKick(game.commence_time);
      var marketInner = market == null
        ? DASH
        : "<b>" + esc(homeAbbr) + " " + fmtSigned(market) + "</b>" + small(bookSpreadLine(entries));
      var totalInner = total == null
        ? DASH
        : "<b>" + fmtPlain(total) + "</b>" + small(bookTotalLine(entries));
      var ourInner = ourHome == null ? DASH : "<b>" + esc(homeAbbr) + " " + fmtSigned(ourHome) + "</b>";
      if (row && row.our_label && ourHome != null && !namesMatch(row.our_team, home)) {
        ourInner += small("card " + minusText(row.our_label));
      }
      var gapInner = gapN == null ? DASH : fmtSigned(gapN);
      rows += "<tr>" +
        cell("Matchup", "game", "<b>" + esc(awayAbbr) + " @ " + esc(homeAbbr) + "</b>" +
          (kick ? '<span class="sub">' + esc(kick) + "</span>" : "")) +
        cell("Market spread", "market-cell", marketInner) +
        cell("Total", "total-cell", totalInner) +
        cell("Our Spread", "", ourInner) +
        cell("Gap", "gap", gapInner) +
        "</tr>";
    }
    return '<table class="live-table"><thead><tr>' +
      '<th scope="col">Matchup</th><th scope="col">Market spread</th><th scope="col">Total</th><th scope="col">Our Spread</th><th scope="col">Gap</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table>";
  }

  function showDown(board, updated) {
    if (board) board.innerHTML = '<div class="empty"><b>Live odds unavailable right now</b></div>';
    if (updated) updated.hidden = true;
  }

  async function boot() {
    var board = document.getElementById("live-board");
    var updated = document.getElementById("live-updated");
    if (!board) return;
    try {
      var oddsRes = await fetch("/api/odds", { headers: { accept: "application/json" } });
      var odds = null;
      try { odds = await oddsRes.json(); } catch (e) { odds = null; }
      if (!oddsRes.ok || !odds || odds.error || !Array.isArray(odds.games) || !odds.games.length) {
        showDown(board, updated);
        return;
      }
      var card = { games: [], teams: {} };
      try {
        var cardRes = await fetch("/live-spreads.json", { headers: { accept: "application/json" } });
        if (cardRes.ok) {
          var parsed = await cardRes.json();
          if (parsed && Array.isArray(parsed.games)) card = parsed;
        }
      } catch (e) { /* show the board; Our Spread stays blank */ }
      var html = renderTable(odds, card);
      if (!html) {
        showDown(board, updated);
        return;
      }
      board.innerHTML = html;
      if (updated) {
        updated.hidden = false;
        updated.textContent = updatedLine(odds);
      }
    } catch (e) {
      showDown(board, updated);
    }
  }

  var api = {
    norm: norm,
    median: median,
    sub: sub,
    findCard: findCard,
    toHomePoint: toHomePoint,
    gap: gap,
    fmtSigned: fmtSigned,
    fmtPlain: fmtPlain,
    renderTable: renderTable,
    updatedLine: updatedLine,
    newestStamp: newestStamp,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
    else boot();
  } else if (root) {
    root.vectorLive = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
