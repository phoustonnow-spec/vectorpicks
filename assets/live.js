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
    if (!when) return "Refreshes about every 4 hours";
    return "Lines updated " + when + " PT \u00b7 refreshes about every 4 hours";
  }

  var PUBLISHED = { "Best Bet": 1, Lean: 1, Card: 1 };
  var SCORE_POLL_LIVE = 60000;
  var SCORE_POLL_IDLE = 600000;

  function coverMargin(line, pickScore, oppScore) {
    return Math.round((pickScore + line - oppScore) * 100) / 100;
  }

  /* Graded at the published Westgate side. Positive margin is covering. */
  function atsStatus(line, pickScore, oppScore, state) {
    if (state !== "in" && state !== "post") return null;
    if (!isNum(line) || !isNum(pickScore) || !isNum(oppScore)) return null;
    var margin = coverMargin(line, pickScore, oppScore);
    if (margin === 0) return "Push";
    if (state === "post") return margin > 0 ? "Won" : "Lost";
    return margin > 0 ? "Covering" : "Not covering";
  }

  function hasPick(row) {
    if (!row || !row.pick_label || !isNum(row.pick_line)) return false;
    if (row.tier && !PUBLISHED[row.tier]) return false;
    return true;
  }

  function pairKey(home, away) {
    var a = norm(home);
    var b = norm(away);
    if (!a || !b) return "";
    return a < b ? a + "|" + b : b + "|" + a;
  }

  function scorePairKey(score) {
    if (!score) return "";
    var home = score.home || {};
    var away = score.away || {};
    return pairKey(home.name || home.abbr, away.name || away.abbr);
  }

  function sameSides(score, home, away, card) {
    if (!score || !score.home || !score.away) return false;
    if (namesMatch(score.home.name, home) && namesMatch(score.away.name, away)) return true;
    if (namesMatch(score.home.name, away) && namesMatch(score.away.name, home)) return true;
    var sh = score.home.abbr;
    var sa = score.away.abbr;
    var ha = abbr(home, card);
    var aa = abbr(away, card);
    if (!sh || !sa || ha === home || aa === away) return false;
    return (sh === ha && sa === aa) || (sh === aa && sa === ha);
  }

  function findScore(scores, home, away, card) {
    var list = (scores && scores.games) || [];
    for (var i = 0; i < list.length; i++) {
      if (sameSides(list[i], home, away, card)) return list[i];
    }
    return null;
  }

  function pickSideScores(row, score) {
    if (!hasPick(row) || !score || !score.home || !score.away) return null;
    var home = score.home;
    var away = score.away;
    var pickHome = namesMatch(row.pick_team, home.name) || (row.pick_abbr && home.abbr === row.pick_abbr);
    var pickAway = namesMatch(row.pick_team, away.name) || (row.pick_abbr && away.abbr === row.pick_abbr);
    if (pickHome && !pickAway) return { pick: home.score, opp: away.score };
    if (pickAway && !pickHome) return { pick: away.score, opp: home.score };
    return null;
  }

  function atsFor(row, score) {
    var sides = pickSideScores(row, score);
    if (!sides) return null;
    return atsStatus(row.pick_line, sides.pick, sides.opp, score.status);
  }

  function nextScoresDelay(games) {
    var list = games || [];
    for (var i = 0; i < list.length; i++) {
      if (list[i] && list[i].status === "in") return SCORE_POLL_LIVE;
    }
    return SCORE_POLL_IDLE;
  }

  function kickoffOf(game) {
    var raw = game.commence_time || (game.score && game.score.kickoff);
    var t = Date.parse(raw);
    return isNaN(t) ? 0 : t;
  }

  function sortBucket(game) {
    var status = game.score && game.score.status;
    if (status === "in") return 0;
    if (status === "post") return 2;
    return 1;
  }

  function mergeBoard(odds, card, scores) {
    var used = {};
    var rows = ((odds && odds.games) || []).map(function (game) {
      var score = findScore(scores, game.home_team, game.away_team, card);
      if (score) used[scorePairKey(score)] = 1;
      return {
        home_team: game.home_team,
        away_team: game.away_team,
        commence_time: game.commence_time,
        books: game.books || {},
        score: score,
      };
    });
    var extras = (scores && scores.games) || [];
    for (var i = 0; i < extras.length; i++) {
      var score = extras[i];
      var key = scorePairKey(score);
      if (!key || used[key]) continue;
      used[key] = 1;
      var home = (score.home && (score.home.name || score.home.abbr)) || "";
      var away = (score.away && (score.away.name || score.away.abbr)) || "";
      rows.push({
        home_team: home,
        away_team: away,
        commence_time: score.kickoff,
        books: {},
        score: score,
      });
    }
    rows.sort(function (a, b) {
      var bucket = sortBucket(a) - sortBucket(b);
      if (bucket) return bucket;
      return kickoffOf(a) - kickoffOf(b);
    });
    return rows;
  }

  function atsClass(label) {
    if (label === "Won" || label === "Covering") return "good";
    if (label === "Lost" || label === "Not covering") return "bad";
    return "push";
  }

  function scoreInner(score, ats) {
    if (!score || score.status === "pre" || !score.status) {
      var upcoming = score && score.detail ? esc(score.detail) : DASH;
      return upcoming;
    }
    var away = score.away || {};
    var home = score.home || {};
    var awayScore = isNum(away.score) ? String(away.score) : DASH;
    var homeScore = isNum(home.score) ? String(home.score) : DASH;
    var line = esc(away.abbr || away.name || "Away") + " " + awayScore +
      " · " + esc(home.abbr || home.name || "Home") + " " + homeScore;
    var detail = score.detail ? '<span class="sub">' + esc(score.detail) + "</span>" : "";
    var extra = "";
    if (score.status === "in" && score.possession) {
      var ball = esc(score.possession) + " ball";
      if (score.red_zone) ball += " · Red zone";
      extra = '<span class="book-lines">' + ball + "</span>";
    }
    var badge = ats ? '<span class="ats ats-' + atsClass(ats) + '">' + esc(ats) + "</span>" : "";
    return "<b>" + line + "</b>" + detail + extra + badge;
  }

  function cell(label, cls, inner) {
    return '<td data-l="' + esc(label) + '"' + (cls ? ' class="' + cls + '"' : "") + ">" + inner + "</td>";
  }

  function small(text) {
    if (!text) return "";
    return '<span class="book-lines">' + esc(text) + "</span>";
  }

  function renderTable(odds, card, scores) {
    var games = mergeBoard(odds, card, scores);
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
      var pickHtml = hasPick(row)
        ? '<span class="pick-badge">Our pick: ' + esc(minusText(row.pick_label)) + "</span>"
        : "";
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
          (kick ? '<span class="sub">' + esc(kick) + "</span>" : "") + pickHtml) +
        cell("Score", "score-cell", scoreInner(game.score, atsFor(row, game.score))) +
        cell("Market spread", "market-cell", marketInner) +
        cell("Total", "total-cell", totalInner) +
        cell("Our Spread", "", ourInner) +
        cell("Gap", "gap", gapInner) +
        "</tr>";
    }
    return '<table class="live-table"><thead><tr>' +
      '<th scope="col">Matchup</th><th scope="col">Score</th><th scope="col">Market spread</th><th scope="col">Total</th><th scope="col">Our Spread</th><th scope="col">Gap</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table>";
  }

  function renderStrip(scores, card) {
    var games = ((scores && scores.games) || []).filter(function (game) {
      if (!game || (game.status !== "in" && game.status !== "post")) return false;
      var home = game.home && (game.home.name || game.home.abbr);
      var away = game.away && (game.away.name || game.away.abbr);
      return hasPick(findCard(card && card.games, home, away));
    }).sort(function (a, b) {
      return sortBucket({ score: a }) - sortBucket({ score: b }) ||
        kickoffOf({ score: a, commence_time: a.kickoff }) - kickoffOf({ score: b, commence_time: b.kickoff });
    });
    if (!games.length) return "";
    var anyLive = games.some(function (game) { return game.status === "in"; });
    var chips = "";
    for (var i = 0; i < games.length; i++) {
      var game = games[i];
      var home = game.home || {};
      var away = game.away || {};
      var row = findCard(card && card.games, home.name || home.abbr, away.name || away.abbr);
      var ats = atsFor(row, game);
      var atsHtml = ats ? '<span class="ats ats-' + atsClass(ats) + '">' + esc(ats) + "</span>" : "";
      chips += '<a class="score-chip" href="live.html"><b>' +
        esc(away.abbr || away.name || "") + " " + (isNum(away.score) ? away.score : DASH) +
        " · " + esc(home.abbr || home.name || "") + " " + (isNum(home.score) ? home.score : DASH) +
        "</b><span class=\"sub\">" + esc(game.detail || "") + "</span>" +
        '<span class="pick-badge">Our pick: ' + esc(minusText(row.pick_label)) + "</span>" +
        atsHtml + "</a>";
    }
    return '<section class="panel live-strip" aria-label="' + (anyLive ? "Live now" : "Final scores") + '">' +
      "<h2>" + (anyLive ? "Live now" : "Final scores") + "</h2>" +
      '<div class="score-row">' + chips + "</div>" +
      '<p class="note">Scores via ESPN; unofficial, may lag. <a href="live.html">Live Board</a></p></section>';
  }

  function showDown(board, updated) {
    if (board) board.innerHTML = '<div class="empty"><b>Live odds unavailable right now</b></div>';
    if (updated) updated.hidden = true;
  }

  function readJson(res) {
    return res.json().catch(function () { return null; });
  }

  async function loadCard() {
    try {
      var cardRes = await fetch("/live-spreads.json", { headers: { accept: "application/json" } });
      if (!cardRes.ok) return { games: [], teams: {} };
      var parsed = await readJson(cardRes);
      if (parsed && Array.isArray(parsed.games)) return parsed;
    } catch (e) { /* Our Spread and picks stay blank */ }
    return { games: [], teams: {} };
  }

  async function loadScores() {
    try {
      var res = await fetch("/api/scores", { headers: { accept: "application/json" }, cache: "no-store" });
      var data = await readJson(res);
      if (!res.ok || !data || data.error || !Array.isArray(data.games)) return null;
      return data;
    } catch (e) {
      return null;
    }
  }

  async function boot() {
    var board = document.getElementById("live-board");
    var strip = document.getElementById("live-strip");
    var updated = document.getElementById("live-updated");
    if (!board && !strip) return;
    var card = await loadCard();
    var odds = null;
    if (board) {
      try {
        var oddsRes = await fetch("/api/odds", { headers: { accept: "application/json" } });
        var parsed = await readJson(oddsRes);
        if (oddsRes.ok && parsed && !parsed.error && Array.isArray(parsed.games)) odds = parsed;
      } catch (e) { odds = null; }
    }
    var timer = null;

    function paint(scores) {
      if (board) {
        var html = renderTable(odds, card, scores);
        if (!html) showDown(board, updated);
        else {
          board.innerHTML = html;
          if (updated) {
            if (odds && odds.games && odds.games.length) {
              updated.hidden = false;
              updated.textContent = updatedLine(odds);
            } else updated.hidden = true;
          }
        }
      }
      if (strip) strip.innerHTML = renderStrip(scores, card);
    }

    async function refreshScores() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      var scores = await loadScores();
      paint(scores);
      if (typeof document !== "undefined" && document.hidden) return;
      var delay = scores ? nextScoresDelay(scores.games) : SCORE_POLL_LIVE;
      timer = setTimeout(refreshScores, delay);
    }

    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
          if (timer) {
            clearTimeout(timer);
            timer = null;
          }
          return;
        }
        refreshScores();
      });
    }
    await refreshScores();
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
    renderStrip: renderStrip,
    updatedLine: updatedLine,
    newestStamp: newestStamp,
    atsStatus: atsStatus,
    coverMargin: coverMargin,
    hasPick: hasPick,
    mergeBoard: mergeBoard,
    nextScoresDelay: nextScoresDelay,
    sortBucket: sortBucket,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
    else boot();
  } else if (root) {
    root.vectorLive = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
