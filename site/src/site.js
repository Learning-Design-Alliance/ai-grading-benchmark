// AI Grading Benchmark site. Reads the datasets embedded by site/build.py (out/public/*.json) and draws every
// view. No library: tables and SVG charts are built here so the page works offline and from any static host.
"use strict";
const D = JSON.parse(document.getElementById("data").textContent);
const $ = s => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") e.className = v; else if (k === "html") e.innerHTML = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  kids.flat().forEach(c => c !== null && c !== undefined && e.append(c.nodeType ? c : String(c)));
  return e;
};
const SVG = "http://www.w3.org/2000/svg";
const sv = (tag, attrs = {}, ...kids) => {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) e.setAttribute(k, v);
  kids.flat().forEach(c => c && e.append(c.nodeType ? c : document.createTextNode(String(c))));
  return e;
};

// ------------------------------------------------------------------ formats
const nul = v => v === null || v === undefined || (typeof v === "number" && isNaN(v));
const fx = d => v => nul(v) ? "—" : Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const f0 = fx(0), f1 = fx(1), f2 = fx(2), f3 = fx(3);
const pct = v => nul(v) ? "—" : f0(v * 100) + "%";
const pct1 = v => nul(v) ? "—" : f1(v) + "%";
const signed = d => v => nul(v) ? "—" : (v > 0 ? "+" : v < 0 ? "−" : "") + fx(d)(Math.abs(v));
const sig = (v, n = 2) => nul(v) ? "—" : Number(Number(v).toPrecision(n)).toLocaleString("en-US");
const iv = (lo, hi, f = f2) => nul(lo) ? "" : `[${f(lo)}, ${f(hi)}]`;
const money = v => nul(v) ? "—" : "$" + (v < 0.1 ? fx(3)(v) : f2(v));
const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const KIND_COLOR = { "frontier": "var(--s1)", "small hosted": "var(--s2)", "open weights": "var(--s3)", "baseline": "var(--base)" };
const KINDS = ["frontier", "small hosted", "open weights"];
const TASKS = ["Short answers", "Code", "Essays"];
const MODELS = D.models || [], OVERALL = D.overall || [], LB = D.leaderboard || [];
const byName = {}; OVERALL.forEach(r => byName[r.model] = r);
const kindOf = name => (byName[name] || {}).kind || ((LB.find(r => r.model === name) || {}).kind) || null;
const modelLink = name => { const o = byName[name]; return o ? el("a", { href: "#model-" + slug(o.key) }, name) : name; };

// ------------------------------------------------------------------ tooltip
const tip = $("#tip");
function showTip(ev, html) { tip.innerHTML = html; tip.hidden = false; moveTip(ev); }
function moveTip(ev) {
  const r = tip.getBoundingClientRect(); let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px";
}
const hideTip = () => { tip.hidden = true; };

// ------------------------------------------------------------------ tables
// cols: {k, h, f(v,row) -> string|Node, c: class, sort: value fn or false, title}
function table(id, rows, cols, opts = {}) {
  const box = document.getElementById(id); if (!box) return;
  let sortK = opts.sort || null, dir = opts.dir || -1;
  const draw = () => {
    box.innerHTML = "";
    const t = el("table"), thead = el("thead"), tr = el("tr");
    cols.forEach(c => {
      const th = el("th", { class: typeof c.c === "string" ? c.c.split(" ").map(x => x === "name" ? "l" : x).filter(x => ["l", "t"].includes(x)).join(" ") || null : null, title: c.title, scope: "col" });
      if (c.sort !== false && opts.sortable !== false) {
        th.append(el("button", { type: "button", onclick: () => { if (sortK === c.k) dir = -dir; else { sortK = c.k; dir = typeof c.c === "string" && /\b(l|t|name)\b/.test(c.c) ? 1 : -1; } draw(); } }, c.h));
        th.setAttribute("aria-sort", sortK === c.k ? (dir > 0 ? "ascending" : "descending") : "none");
      } else th.textContent = c.h;
      tr.append(th);
    });
    thead.append(tr); t.append(thead);
    let rs = rows.slice();
    if (sortK) {
      const col = cols.find(c => c.k === sortK) || {};
      const val = col.sort ? col.sort : r => r[sortK];
      rs.sort((a, b) => {
        if (opts.pinBottom && opts.pinBottom(a) !== opts.pinBottom(b)) return opts.pinBottom(a) ? 1 : -1;
        const x = val(a), y = val(b);
        if (nul(x) && nul(y)) return 0; if (nul(x)) return 1; if (nul(y)) return -1;
        return typeof x === "string" ? dir * x.localeCompare(y) : dir * (x - y);
      });
    }
    const tb = el("tbody");
    rs.forEach(r => {
      const row = el("tr", { class: opts.rowClass ? opts.rowClass(r) : null });
      cols.forEach(c => {
        const v = c.f ? c.f(r[c.k], r) : r[c.k];
        const cls = typeof c.c === "function" ? c.c(r[c.k], r) : c.c;
        row.append(el("td", { class: cls || "n" }, nul(v) ? "—" : v));
      });
      tb.append(row);
    });
    t.append(tb); box.append(t);
  };
  draw();
}

// ------------------------------------------------------------------ interval chart
// rows: {label, est, lo, hi, kind, base, href, tip}; one axis, intervals as 2px lines, a dot (or a diamond for a
// baseline) at the estimate. refs: [{v, text}]. Colour follows the model's group, never its rank.
function intervalChart(id, rows, o = {}) {
  const box = document.getElementById(id); if (!box) return; box.innerHTML = "";
  rows = rows.filter(r => !nul(r.est));
  if (!rows.length) { box.append(el("p", { class: "sub" }, "No results yet.")); return; }
  const present = new Set(rows.map(r => r.base ? "baseline" : r.kind).filter(Boolean)); const kinds = KINDS.concat(["baseline"]).filter(k => present.has(k));
  if (o.legend !== false && kinds.length > 1) box.append(legend(kinds));
  const W = 780, rowH = 24, top = 26, labW = o.labW || 270, right = 64;
  const H = top + rows.length * rowH + 10;
  const vals = rows.flatMap(r => [r.est, r.lo, r.hi]).filter(v => !nul(v)).concat((o.refs || []).map(r => r.v));
  let [mn, mx] = o.domain || [Math.min(...vals), Math.max(...vals)];
  if (!o.domain) { const pad = (mx - mn) * 0.06 || 1; mn -= pad; mx += pad; if (o.zero) { mn = Math.min(mn, 0); mx = Math.max(mx, 0); } }
  const x = v => labW + (Math.max(mn, Math.min(mx, v)) - mn) / (mx - mn) * (W - labW - right);
  const s = sv("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": o.aria || "Chart" });
  const ticks = niceTicks(mn, mx, 5);
  const g = sv("g", { class: "grid" });
  ticks.forEach(t => { g.append(sv("line", { x1: x(t), x2: x(t), y1: top - 6, y2: H - 6 })); g.append(sv("text", { class: "tick", x: x(t), y: 12, "text-anchor": "middle" }, (o.tickFmt || sigTick)(t))); });
  s.append(g);
  (o.refs || []).forEach(rf => {
    s.append(sv("line", { class: "ref", x1: x(rf.v), x2: x(rf.v), y1: top - 6, y2: H - 6 }));
    if (rf.text) s.append(sv("text", { class: "reftext", x: x(rf.v) + 4, y: H - 10 }, rf.text));
  });
  rows.forEach((r, i) => {
    const y = top + i * rowH + rowH / 2;
    const col = KIND_COLOR[r.base ? "baseline" : r.kind] || "var(--s1)";
    const gr = sv("g", { class: "row" });
    const lab = sv("text", { class: "lab" + (r.base ? " base" : ""), x: labW - 10, y: y + 4, "text-anchor": "end" }, trunc(r.label, o.labMax || 40));
    gr.append(lab);
    if (!nul(r.lo) && !nul(r.hi)) gr.append(sv("line", { class: "ci", x1: x(r.lo), x2: x(r.hi), y1: y, y2: y, stroke: col }));
    if (r.base) gr.append(sv("path", { d: `M${x(r.est)},${y - 6} l6,6 l-6,6 l-6,-6 z`, fill: "var(--surface)", stroke: col, "stroke-width": 2 }));
    else gr.append(sv("circle", { cx: x(r.est), cy: y, r: 5, fill: col, stroke: "var(--surface)", "stroke-width": 2 }));
    gr.append(sv("text", { class: "tick", x: W - right + 8, y: y + 4 }, (o.valFmt || f2)(r.est)));
    const hit = sv("rect", { class: "hit", x: 0, y: y - rowH / 2, width: W, height: rowH });
    hit.addEventListener("mousemove", ev => showTip(ev, r.tip || `<b>${esc(r.label)}</b><br>${(o.valFmt || f2)(r.est)} ${nul(r.lo) ? "" : iv(r.lo, r.hi, o.valFmt || f2)}`));
    hit.addEventListener("mouseleave", hideTip);
    if (r.href) hit.addEventListener("click", () => { location.hash = r.href; });
    if (r.href) hit.style.cursor = "pointer";
    gr.append(hit); s.append(gr);
  });
  if (o.axis) s.append(sv("text", { class: "tick", x: labW, y: H - 0 }, ""));
  box.append(s);
  if (o.axis) box.append(el("p", { class: "sub", style: "margin:4px 0 6px" }, o.axis));
}
function legend(kinds) {
  const names = { "frontier": "Frontier", "small hosted": "Small hosted", "open weights": "Open weights", "baseline": "Non-AI baseline" };
  return el("div", { class: "legend" }, kinds.map(k => {
    const s = sv("svg", { viewBox: "0 0 14 14" });
    s.append(k === "baseline" ? sv("path", { d: "M7,1 l6,6 l-6,6 l-6,-6 z", fill: "var(--surface)", stroke: KIND_COLOR[k], "stroke-width": 2 }) : sv("circle", { cx: 7, cy: 7, r: 5, fill: KIND_COLOR[k] }));
    return el("span", {}, s, names[k] || k);
  }));
}
function niceTicks(a, b, n) {
  const step0 = (b - a) / n, mag = Math.pow(10, Math.floor(Math.log10(step0))), r = step0 / mag;
  const step = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * mag;
  const out = []; for (let t = Math.ceil(a / step) * step; t <= b + 1e-9; t += step) out.push(+t.toFixed(10)); return out;
}
const sigTick = v => Math.abs(v) >= 100 ? f0(v) : String(+v.toFixed(3));
const trunc = (s, n) => String(s).length > n ? String(s).slice(0, n - 1) + "…" : String(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ------------------------------------------------------------------ segmented controls
function seg(id, options, current, onPick) {
  const box = document.getElementById(id); if (!box) return; box.innerHTML = "";
  options.forEach(o => {
    const [val, text] = Array.isArray(o) ? o : [o, o];
    box.append(el("button", { type: "button", "aria-pressed": String(val === current), onclick: () => {
      box.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", "false"));
      box.querySelector(`[data-v="${CSS.escape(val)}"]`).setAttribute("aria-pressed", "true"); onPick(val);
    }, "data-v": val }, text));
  });
}

// ================================================================== OVERVIEW
function drawOverview() {
  const complete = OVERALL.filter(r => r.complete), clean = complete.filter(r => !r.flags);
  const gamed = complete.filter(r => /gamed/.test(r.flags || "")).length;
  const blank = complete.filter(r => /blank/.test(r.flags || "")).length;
  const push = (D.pushback || []).filter(r => /YIELDS/.test(r.verdict || "")).length;
  const speechSilent = (D.speech || []).filter(r => (r.silence_pct || 0) > 50).length;
  const watch = (D.video || []).filter(r => /WATCHES/.test(r.verdict || "")).length;
  const ess = (D.baselines || []).find(b => b.task === "Essays" && b.baseline === "tfidf-ridge");
  const cards = [
    [`${clean.length} of ${complete.length}`, `models pass every disqualifying check. ${gamed} can be talked into marks by a note in the answer, and ${blank} credit blank or junk answers.`, "#leaderboard", "See the leaderboard"],
    [`${push} of ${(D.pushback || []).length}`, "models raise a mark when the student only says they deserve more, with nothing about the work changed.", "#robustness", "Gaming and pushback"],
    [`${speechSilent} of ${(D.speech || []).length}`, `audio graders give marks to a silent recording, and only ${watch} of ${(D.video || []).length} video runs watch the recording rather than timing it.`, "#media", "Speech, handwriting, video"],
    [ess ? f2(ess.qwk) : "—", "essay agreement of a classic word-feature scorer trained on marked essays: level with the best language models, and it cannot be gamed. It needs thousands of marked essays and gives no feedback.", "#tasks", "Compare with baselines"],
  ];
  const box = $("#findings"); box.innerHTML = "";
  cards.forEach(([big, text, href, cta]) => box.append(el("div", { class: "finding" }, el("div", { class: "big" }, big), el("p", {}, text), el("a", { href }, cta + " →"))));
  const top = complete.filter(r => !r.flags).sort((a, b) => a.rank - b.rank).slice(0, 8);
  table("t-top", top, [
    { k: "rank", h: "Rank", c: "n", f: (v, r) => `${v}` },
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) },
    { k: "vendor", h: "Vendor", c: "l dim" },
    { k: "overall", h: "Overall", f: f1 },
    { k: "rank_lo", h: "Rank interval", c: "dim n", f: (v, r) => v ? `${v}–${r.rank_hi}` : "—" },
    { k: "task_lo", h: "Range across tasks", c: "dim n", f: (v, r) => nul(v) ? "—" : `${f1(v)}–${f1(r.task_hi)}` },
  ], { sortable: false });
}

// ================================================================== LEADERBOARD
const WROWS = D.weights || [];
const STRANDS = WROWS.map(w => w.strand);
const SHORT = { agreement: "Agreement", decision: "Pass/fail", relevant: "Wrong content", irrelevant: "Ignores gaming", fairness: "Label fairness",
  consistency: "Consistent", feedback: "Feedback", working: "Reads working", pushback: "Holds under pushback" };
const DEFAULT_W = Object.fromEntries(WROWS.map(w => [w.strand, w.weight]));
const PRESETS = {
  "Default": DEFAULT_W,
  "Agreement only": Object.fromEntries(STRANDS.map(k => [k, k === "agreement" || k === "decision" ? (k === "agreement" ? 30 : 10) : 0])),
  "Robustness first": { agreement: 10, decision: 5, relevant: 20, irrelevant: 25, fairness: 15, consistency: 5, feedback: 5, working: 5, pushback: 20 },
  "Equal": Object.fromEntries(STRANDS.map(k => [k, 10])),
};
let W = { ...DEFAULT_W };
const shown = new Set(KINDS);
const scoreWith = (r, w) => { let tot = 0, sum = 0; STRANDS.forEach(k => { if (!nul(r[k]) && w[k]) { tot += w[k]; sum += w[k] * r[k]; } }); return tot ? sum / tot : null; };
function ranked(w) {
  const rows = OVERALL.map(r => ({ ...r, mine: scoreWith(r, w) }));
  const done = rows.filter(r => r.complete).sort((a, b) => (!!a.flags - !!b.flags) || (b.mine - a.mine));
  done.forEach((r, i) => r.myRank = i + 1);
  return done.concat(rows.filter(r => !r.complete));
}
function drawLeaderboard() {
  seg("presets", Object.keys(PRESETS), presetName(), p => { W = { ...PRESETS[p] }; drawSliders(); drawOverallTable(); });
  drawSliders(); drawKindFilter(); drawOverallTable();
  table("t-weights", WROWS, [{ k: "strand", h: "Strand", c: "l", f: v => SHORT[v] || v }, { k: "weight", h: "Default weight" }, { k: "means", h: "What it measures", c: "t" }], { sortable: false });
  $("#w-reset").onclick = () => { W = { ...DEFAULT_W }; drawLeaderboard(); };
}
function presetName() { return Object.keys(PRESETS).find(p => STRANDS.every(k => (PRESETS[p][k] || 0) === (W[k] || 0))) || null; }
function drawSliders() {
  const box = $("#sliders"); box.innerHTML = "";
  const total = STRANDS.reduce((a, k) => a + (W[k] || 0), 0) || 1;
  WROWS.forEach(r => {
    const id = "w-" + r.strand;
    const share = el("span", { class: "w" }, `${Math.round((W[r.strand] || 0) / total * 100)}%`);
    const inp = el("input", { type: "range", id, min: 0, max: 40, step: 1, value: W[r.strand] || 0, "aria-describedby": id + "-d" });
    inp.addEventListener("input", () => { W[r.strand] = +inp.value; drawSliders(); drawOverallTable(); document.getElementById(id).focus(); seg("presets", Object.keys(PRESETS), presetName(), p => { W = { ...PRESETS[p] }; drawSliders(); drawOverallTable(); }); });
    box.append(el("label", { class: "slider", for: id }, el("span", {}, SHORT[r.strand] || r.strand), share, inp, el("small", { id: id + "-d" }, r.means)));
  });
}
function drawKindFilter() {
  const box = $("#kind-filter"); box.innerHTML = "";
  KINDS.forEach(k => {
    const b = el("button", { type: "button", class: "chip", "aria-pressed": String(shown.has(k)) }, el("i", { style: `background:${KIND_COLOR[k]}` }), k[0].toUpperCase() + k.slice(1));
    b.onclick = () => { shown.has(k) ? shown.delete(k) : shown.add(k); b.setAttribute("aria-pressed", String(shown.has(k))); drawOverallTable(); };
    box.append(b);
  });
}
function drawOverallTable() {
  const isDef = STRANDS.every(k => (W[k] || 0) === DEFAULT_W[k]);
  const rows = ranked(W).filter(r => shown.has(r.kind));
  const moved = rows.filter(r => r.complete && r.myRank !== r.rank).length;
  $("#w-status").innerHTML = isDef ? "Showing the <b>default weights</b>." :
    `Ranked by <b>your weights</b>${presetName() ? " (" + presetName() + ")" : ""}. ${moved} model${moved === 1 ? "" : "s"} moved; the Default column is unchanged.`;
  const strandCols = STRANDS.map(k => ({ k, h: SHORT[k] || k, title: (WROWS.find(w => w.strand === k) || {}).means, f: f0, c: v => !nul(v) && v < 60 ? "bad" : "n" }));
  table("t-overall", rows, [
    { k: "myRank", h: isDef ? "Rank" : "Your rank", f: (v, r) => r.complete ? String(v) : "—" },
    { k: "move", h: "", sort: false, f: (v, r) => { if (!r.complete || isDef) return ""; const d = r.rank - r.myRank; return d === 0 ? el("span", { class: "move dim" }, "·") : el("span", { class: "move " + (d > 0 ? "up" : "down") }, (d > 0 ? "▲" : "▼") + Math.abs(d)); } },
    { k: "model", h: "Model", c: "name", f: (v, r) => el("span", {}, modelLink(v), r.retention_note ? " †" : "", r.flags ? el("span", { class: "flags" }, r.flags.split("; ").map(x => el("span", { class: "flag" }, x))) : "") },
    { k: "mine", h: isDef ? "Overall" : "Your score", f: f1 },
    { k: "overall", h: "Default", f: (v, r) => isDef ? "" : `${f1(v)} (#${r.rank || "—"})`, c: "dim n" },
    ...strandCols,
    { k: "rank_lo", h: "Rank interval", c: "dim n", f: (v, r) => v ? `${v}–${r.rank_hi}` : (r.complete ? "—" : "not run on every task") },
    { k: "task_lo", h: "Range across tasks", c: "dim n", f: (v, r) => nul(v) ? "—" : `${f1(v)}–${f1(r.task_hi)}` },
  ], { sort: "myRank", dir: 1, pinBottom: r => !r.complete });
}

// ================================================================== TASKS (with baselines)
let TASK = "Short answers";
const BASE = D.baselines || [];
const BNAME = { "length": "length alone", "tfidf-ridge": "word features (tf-idf)", "reference-similarity": "similarity to reference", "encoder-ridge": "small sentence encoder", "deberta-ft": "fine-tuned DeBERTa" };
function ceilingFor(task) {
  if (task === "Essays") return 0.745;
  const r = LB.filter(x => x.task === task && !nul(x.share) && x.share > 0).map(x => x.qwk / x.share);
  r.sort((a, b) => a - b); return r.length ? r[Math.floor(r.length / 2)] : null;
}
function drawTasks() {
  seg("task-tabs", TASKS, TASK, t => { TASK = t; drawTaskViews(); });
  drawTaskViews();
}
function drawTaskViews() {
  const rows = LB.filter(r => r.task === TASK), bases = BASE.filter(b => b.task === TASK), ceil = ceilingFor(TASK);
  $("#agree-title").textContent = `Agreement with the experts: ${TASK.toLowerCase()}`;
  $("#agree-sub").textContent = `Quadratic weighted kappa with the expert markers' mark, 95% interval. The dashed line is how well the experts agree with each other${TASK === "Essays" ? " (the published rater agreement, κ 0.745)" : ""}: a model near it disagrees with them about as often as they disagree with each other. Diamonds are non-AI baselines.`;
  const pts = rows.map(r => ({ label: r.model, est: r.qwk, lo: r.qwk_lo, hi: r.qwk_hi, kind: r.kind, href: "model-" + slug((byName[r.model] || {}).key || r.model),
    tip: `<b>${esc(r.model)}</b><br>QWK ${f3(r.qwk)} ${iv(r.qwk_lo, r.qwk_hi, f2)}<br>${TASK === "Essays" ? "Share of published rater agreement " + pct(r.published_share) : "Share of the human ceiling " + pct(r.share)}` }))
    .concat(bases.map(b => ({ label: "Baseline · " + (BNAME[b.baseline] || b.baseline), est: b.qwk, lo: b.qwk_lo, hi: b.qwk_hi, base: true,
      tip: `<b>${esc(BNAME[b.baseline] || b.baseline)}</b> (non-AI)<br>QWK ${f3(b.qwk)} ${iv(b.qwk_lo, b.qwk_hi, f2)}<br>Trained on ${f0(b.n_train)} marked answers · credits blank answers ${pct1(b.blank_pct)}` })))
    .sort((a, b) => b.est - a.est);
  intervalChart("c-agree", pts, { domain: [Math.min(0, ...pts.map(p => p.lo ?? p.est)), 1], refs: ceil ? [{ v: ceil, text: "experts with each other" }] : [], valFmt: f2, aria: "Agreement with experts by model and baseline" });
  const gpts = rows.filter(r => !nul(r.gaming_pct)).map(r => ({ label: r.model, est: r.gaming_pct, lo: r.gaming_lo, hi: r.gaming_hi, kind: r.kind, href: "model-" + slug((byName[r.model] || {}).key || r.model) }))
    .concat(bases.filter(b => !nul(b.gaming_pct)).map(b => ({ label: "Baseline · " + (BNAME[b.baseline] || b.baseline), est: b.gaming_pct, base: true })))
    .sort((a, b) => b.est - a.est);
  intervalChart("c-gaming", gpts, { refs: [{ v: 0 }, { v: 5, text: "5% flag" }], zero: true, valFmt: v => f1(v) + "%", tickFmt: v => f0(v) + "%", aria: "Gain from gaming, % of scale" });
  scatterCost(rows, ceil);
  const essays = TASK === "Essays";
  const brow = bases.map(b => ({ model: "Baseline · " + (BNAME[b.baseline] || b.baseline), _base: true, kind: "baseline", share: essays ? null : b.share, published_share: essays ? b.share_published : null,
    qwk: b.qwk, qwk_lo: b.qwk_lo, qwk_hi: b.qwk_hi, blank_pct: b.blank_pct, gaming_pct: b.gaming_pct, label_pct: 0, retest: 1, refused: 0, cost_per_1k: null, decision_share: null, blicket_pct: null, surface_pct: null }));
  const R = (v, t) => !nul(v) && v > t;
  table("t-board", rows.concat(brow), [
    { k: "model", h: "Model", c: "name", f: (v, r) => r._base ? v : modelLink(v) },
    { k: essays ? "published_share" : "share", h: essays ? "Share of rater κ" : "Share of ceiling", f: pct },
    { k: "qwk", h: "QWK", f: f3 },
    { k: "decision_share", h: "Pass/fail", f: pct, title: "pass/fail agreement at the scale midpoint, as a share of the markers' own" },
    { k: "blank_pct", h: "Blank credited", f: pct1, c: v => R(v, 0) ? "bad" : "n" },
    { k: "blicket_pct", h: "Nonsense key word", f: signed(1), title: "change when a key word is replaced with a nonsense word, % of scale" },
    { k: "gaming_pct", h: "Gaming gain", f: signed(1), c: v => R(v, 5) ? "bad" : "n", title: "largest gain from a polite request or a forged note, % of scale" },
    { k: "surface_pct", h: "Re-wrapped", f: signed(1) },
    { k: "label_pct", h: "Strong vs weak label", f: signed(1), c: v => R(Math.abs(v ?? 0), 5) ? "bad" : "n" },
    { k: "retest", h: "Same twice", f: f2 },
    { k: "refused", h: "Refused", f: f0 },
    { k: "cost_per_1k", h: "$ / 1,000", f: money },
  ], { sort: "qwk", rowClass: r => r._base ? "baseline" : null });
}
function scatterCost(rows, ceil) {
  const box = $("#c-cost"); box.innerHTML = "";
  const pts = rows.filter(r => !nul(r.cost_per_1k) && r.cost_per_1k > 0 && !nul(r.qwk));
  if (!pts.length) { box.append(el("p", { class: "sub" }, "No cost data for this task.")); return; }
  box.append(legend(KINDS.filter(k => pts.some(p => p.kind === k))));
  const W = 760, H = 330, L = 48, R = 20, T = 14, B = 40;
  const lx = pts.map(p => Math.log10(p.cost_per_1k)), x0 = Math.floor(Math.min(...lx)), x1 = Math.ceil(Math.max(...lx));
  const y0 = Math.min(0, ...pts.map(p => p.qwk)), y1 = 1;
  const x = v => L + (Math.log10(v) - x0) / (x1 - x0) * (W - L - R), y = v => T + (y1 - v) / (y1 - y0) * (H - T - B);
  const s = sv("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Agreement against cost per 1,000 gradings" });
  const g = sv("g", { class: "grid" });
  for (let e = x0; e <= x1; e++) { g.append(sv("line", { x1: x(10 ** e), x2: x(10 ** e), y1: T, y2: H - B })); g.append(sv("text", { class: "tick", x: x(10 ** e), y: H - B + 16, "text-anchor": "middle" }, "$" + (10 ** e >= 1 ? f0(10 ** e) : String(10 ** e)))); }
  niceTicks(y0, y1, 5).forEach(t => { g.append(sv("line", { x1: L, x2: W - R, y1: y(t), y2: y(t) })); g.append(sv("text", { class: "tick", x: L - 8, y: y(t) + 4, "text-anchor": "end" }, String(+t.toFixed(2)))); });
  s.append(g);
  s.append(sv("text", { class: "tick", x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle" }, "$ per 1,000 gradings (log scale)"));
  s.append(sv("text", { class: "tick", x: 10, y: T + 4 }, "QWK"));
  if (ceil) { s.append(sv("line", { class: "ref", x1: L, x2: W - R, y1: y(ceil), y2: y(ceil) })); s.append(sv("text", { class: "reftext", x: L + 6, y: y(ceil) - 6 }, "experts with each other")); }
  pts.forEach(p => {
    const c = sv("circle", { cx: x(p.cost_per_1k), cy: y(p.qwk), r: 6, fill: KIND_COLOR[p.kind], stroke: "var(--surface)", "stroke-width": 2 });
    c.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(p.model)}</b><br>QWK ${f3(p.qwk)}<br>${money(p.cost_per_1k)} per 1,000`));
    c.addEventListener("mouseleave", hideTip); s.append(c);
  });
  box.append(s);
}

// ================================================================== MODELS
function drawModels() {
  const rows = MODELS.map(m => ({ ...m, ov: byName[m.model] || {} }));
  table("t-models", rows, [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) },
    { k: "vendor", h: "Vendor", c: "l dim" },
    { k: "kind", h: "Group", c: "l", sort: r => r.ov.kind, f: (v, r) => r.ov.kind || "candidate" },
    { k: "weights", h: "Open weights?", c: "l", f: v => /open/i.test(v || "") ? "yes" : "no" },
    { k: "params", h: "Size", c: "l dim", f: v => trunc(v || "—", 24) },
    { k: "cutoff", h: "Training cutoff", c: "l", f: v => trunc(v || "—", 18) },
    { k: "overall", h: "Overall", sort: r => r.ov.overall, f: (v, r) => f1(r.ov.overall) },
    { k: "flags", h: "Flags", c: "l", sort: r => r.ov.flags || "", f: (v, r) => r.ov.flags ? el("span", {}, r.ov.flags.split("; ").map(x => el("span", { class: "flag" }, x))) : (r.ov.complete ? el("span", { class: "pill ok" }, "none") : "") },
  ], { sort: "overall" });
}
function drawModel(token) {
  const o = OVERALL.find(r => "model-" + slug(r.key) === token);
  const box = $("#model-page"); box.innerHTML = "";
  if (!o) { box.append(el("p", {}, "No such model. ", el("a", { href: "#models" }, "All models"))); return; }
  const m = MODELS.find(r => r.key === o.key) || {};
  const head = el("div", { class: "head" },
    el("div", { class: "eyebrow" }, el("a", { href: "#models" }, "Models"), " · ", o.vendor, " · ", o.kind),
    el("h2", {}, o.model),
    el("div", { class: "modelhead" },
      el("span", { class: "lede" }, o.complete ? `Overall ${f1(o.overall)}, rank ${o.rank} (interval ${o.rank_lo}–${o.rank_hi}) under the default weights.` : "Not yet run on every task."),
      ...(o.flags ? o.flags.split("; ").map(x => el("span", { class: "flag" }, x)) : [el("span", { class: "pill ok" }, "no disqualifying flag")])));
  const strands = el("div", { class: "strands" }, WROWS.map(w => {
    const v = o[w.strand];
    return el("div", { class: "strand", title: w.means }, el("span", {}, SHORT[w.strand]), el("span", { class: "bar" }, el("i", { class: !nul(v) && v < 60 ? "low" : null, style: `width:${nul(v) ? 0 : Math.max(0, Math.min(100, v))}%` })), el("span", { class: "v" }, f0(v)));
  }));
  const tasks = LB.filter(r => r.model === o.model);
  const tbl = el("div", { class: "tbl", id: "t-mtask" });
  const push = (D.pushback || []).find(r => r.model === o.model), maths = (D.maths || []).find(r => r.model === o.model), fb = (D.feedback_board || []).find(r => r.model === o.model);
  const other = el("div", { class: "facts" },
    fact("Pushback", push ? `${signed(1)(push.effect_pct)}% of the scale ${iv(push.effect_lo, push.effect_hi, f1)} · ${push.verdict.toLowerCase()}` : "not run"),
    fact("Maths working", maths ? `working effect ${f2(maths.working)} of 4 ${iv(maths.working_lo, maths.working_hi, f2)}` : "not run"),
    fact("Feedback halo", fb ? `${signed(2)(fb.halo)} ${iv(fb.halo_lo, fb.halo_hi, f2)}` : "not run"),
    fact("States the answer", fb ? pct1(fb.gives_away_pct) + " of feedback below full marks" : "not run"));
  const docs = el("dl", { class: "facts" },
    fact("Weights", m.weights), fact("Licence", m.licence), fact("Size", m.params), fact("Cutoff", m.cutoff),
    fact("Training data", m.training_data), fact("Tokens", m.training_tokens), fact("Sources", m.training_sources),
    fact("Users' data", m.user_data), fact("Benchmarks removed", m.decontamination), fact("Other models' outputs", m.distilled_from),
    fact("Education data", m.education_data), fact("Card on sycophancy", m.sycophancy_claim), fact("Card on injection", m.injection_claim),
    fact("Bias", m.bias_claim), fact("Energy disclosed", m.energy), fact("Zero retention", m.zdr), fact("FMTI (vendor)", m.fmti),
    fact("Card", m.card ? el("a", { href: m.card, rel: "noopener" }, (m.card_date ? m.card_date + " · " : "") + "vendor card") : null));
  box.append(el("div", { class: "view" }, head,
    el("div", { class: "block" }, el("h3", {}, "Strand scores"), el("p", { class: "sub" }, "0 to 100; under 60 is marked."), strands),
    el("div", { class: "block" }, el("h3", {}, "By task"), tbl),
    el("div", { class: "block" }, el("h3", {}, "Whole-model tests"), other),
    el("div", { class: "block" }, el("h3", {}, "What the vendor documents"), el("p", { class: "sub" }, "From the vendor's card, licence and retention pages, read on 2026-10-25. \"Not stated\" is silence, not a no."), docs)));
  table("t-mtask", tasks, [
    { k: "task", h: "Task", c: "l" }, { k: "qwk", h: "QWK", f: (v, r) => `${f3(v)} ${iv(r.qwk_lo, r.qwk_hi, f2)}` },
    { k: "share", h: "Share of ceiling", f: (v, r) => r.task === "Essays" ? pct(r.published_share) + " (rater κ)" : pct(v) },
    { k: "gaming_pct", h: "Gaming gain", f: signed(1), c: v => !nul(v) && v > 5 ? "bad" : "n" },
    { k: "blank_pct", h: "Blank credited", f: pct1, c: v => !nul(v) && v > 0 ? "bad" : "n" },
    { k: "label_pct", h: "Label effect", f: signed(1) }, { k: "retest", h: "Same twice", f: f2 }, { k: "cost_per_1k", h: "$ / 1,000", f: money },
  ], { sortable: false });
  scrollTo(0, 0);
}
function fact(k, v) { return el("div", {}, el("dt", {}, k), el("dd", {}, nul(v) || v === "" ? "—" : v)); }

// ================================================================== ROBUSTNESS
let FLAGTASK = "Short answers";
function drawRobustness() {
  const pb = (D.pushback || []).map(r => ({ label: r.model, est: r.effect_pct, lo: r.effect_lo, hi: r.effect_hi, kind: kindOf(r.model), href: "model-" + slug((byName[r.model] || {}).key || ""),
    tip: `<b>${esc(r.model)}</b><br>${signed(1)(r.effect_pct)}% ${iv(r.effect_lo, r.effect_hi, f1)}<br>${esc(r.verdict)}` })).sort((a, b) => b.est - a.est);
  intervalChart("c-pushback", pb, { refs: [{ v: 0 }], zero: true, valFmt: v => signed(1)(v) + "%", tickFmt: v => f0(v) + "%", aria: "Pushback effect" });
  const ps = (D.pushback_split || []).filter(r => !nul(r.effect_fair_pct)).map(r => ({ label: r.model, est: r.effect_fair_pct, lo: r.effect_fair_lo, hi: r.effect_fair_hi, kind: kindOf(r.model) })).sort((a, b) => b.est - a.est);
  intervalChart("c-pushsplit", ps, { refs: [{ v: 0 }], zero: true, valFmt: v => signed(1)(v) + "%", tickFmt: v => f0(v) + "%", aria: "Pushback on fairly marked answers" });
  seg("flag-tabs", TASKS, FLAGTASK, t => { FLAGTASK = t; drawFlags(); }); drawFlags();
  const pp = {}; (D.per_prompt || []).forEach(r => { if (nul(r.qwk)) return; const k = r.model + "|" + r.task; (pp[k] = pp[k] || { model: r.model, task: r.task, lo: 1, hi: -1, n: 0 }); pp[k].lo = Math.min(pp[k].lo, r.qwk); pp[k].hi = Math.max(pp[k].hi, r.qwk); pp[k].n++; });
  table("t-perprompt", Object.values(pp), [{ k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "task", h: "Task", c: "l" }, { k: "n", h: "Prompts" }, { k: "lo", h: "Lowest QWK", f: f2 }, { k: "hi", h: "Highest QWK", f: f2 }, { k: "spread", h: "Spread", sort: r => r.hi - r.lo, f: (v, r) => f2(r.hi - r.lo) }], { sort: "spread" });
}
function drawFlags() {
  const P = v => v === "PASS" ? el("span", { class: "pill ok" }, "pass") : v === "FAIL" ? el("span", { class: "pill bad" }, "fail") : el("span", { class: "pill" }, "unclear");
  table("t-flags", (D.agreement_flags || []).filter(r => r.task === FLAGTASK), [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) },
    { k: "qwk", h: "QWK", f: f3 }, { k: "qwk_flag", h: "At least 0.70", f: P, c: "l" },
    { k: "degradation", h: "Raters' minus model's", f: signed(3) }, { k: "degradation_flag", h: "At most 0.10", f: P, c: "l" },
    { k: "smd", h: "Mean difference (SD)", f: (v, r) => `${signed(2)(v)} ${iv(r.smd_lo, r.smd_hi, f2)}` }, { k: "smd_flag", h: "Within ±0.15", f: P, c: "l" },
  ], { sort: "qwk" });
}

// ================================================================== MATHS, FEEDBACK, FAIRNESS
function drawMaths() {
  const rows = D.maths || [];
  intervalChart("c-maths", rows.map(r => ({ label: r.model, est: r.working, lo: r.working_lo, hi: r.working_hi, kind: kindOf(r.model), base: /no model/.test(r.model) })).sort((a, b) => b.est - a.est),
    { domain: [0, 4], refs: [{ v: 2, text: "full strand score" }], valFmt: f2, aria: "Working effect, of 4" });
  table("t-maths", rows, [
    { k: "model", h: "Grader", c: "name", f: v => /no model/.test(v) ? v : modelLink(v) },
    { k: "working", h: "Working effect (of 4)", f: (v, r) => `${f2(v)} ${iv(r.working_lo, r.working_hi, f2)}` },
    { k: "correct", h: "Right working, right answer", f: f2 }, { k: "slip", h: "Right working, wrong answer", f: f2 },
    { k: "lucky", h: "Wrong working, right answer", f: f2 }, { k: "wrong", h: "Wrong working, wrong answer", f: f2 },
    { k: "lucky_full_pct", h: "Wrong working given full marks", f: pct1 }, { k: "first_step_pct", h: "First wrong step found", f: pct1 },
  ], { sort: "working", rowClass: r => /no model/.test(r.model) ? "baseline" : null });
}
function drawFeedback() {
  const fb = D.feedback_board || [];
  intervalChart("c-halo", fb.map(r => ({ label: r.model, est: r.halo, lo: r.halo_lo, hi: r.halo_hi, kind: kindOf(r.model) })).sort((a, b) => b.est - a.est), { refs: [{ v: 0 }], zero: true, valFmt: signed(2), aria: "Feedback halo" });
  intervalChart("c-gives", fb.map(r => ({ label: r.model, est: r.gives_away_pct, lo: r.gives_away_lo, hi: r.gives_away_hi, kind: kindOf(r.model) })).sort((a, b) => b.est - a.est), { domain: [0, 100], valFmt: v => f0(v) + "%", tickFmt: v => f0(v) + "%", aria: "Feedback states the answer" });
  table("t-fbchecks", D.feedback_checks || [], [{ k: "label", h: "Measure", c: "l" }, { k: "by", h: "From", c: "t dim" }, { k: "auc", h: "AUC vs annotators", f: (v, r) => `${f2(v)} ${iv(r.lo, r.hi, f2)}` }, { k: "length_auc", h: "Length alone", f: f2 }, { k: "verdict", h: "Verdict", c: "l", f: v => el("span", { class: "pill " + (/NOT/.test(v) ? "bad" : "ok") }, v.toLowerCase()) }], { sortable: false });
}
function drawFairness() {
  const rows = (D.fairness || []).map(r => ({ label: `${r.test.replace(/^(ELLIPSE|ASAP 2.0): /, "")} · ${r.grader}`, est: r.gap, lo: r.lo, hi: r.hi, kind: r.grader === "second human rater" ? "baseline" : kindOf(r.grader), base: /human/i.test(r.grader),
    tip: `<b>${esc(r.test)}</b><br>${esc(r.grader)}: ${signed(3)(r.gap)} ${iv(r.lo, r.hi, f2)}<br>${esc(r.verdict)}` }));
  intervalChart("c-fair", rows, { refs: [{ v: -0.1, text: "−0.10" }, { v: 0.1, text: "+0.10" }, { v: 0 }], zero: true, labW: 300, valFmt: signed(2), aria: "Gap between groups" });
  table("t-drift", D.drift || [], [{ k: "from", h: "From", c: "l" }, { k: "to", h: "To", c: "l" }, { k: "shift", h: "Mean shift (marks of 5)", f: (v, r) => `${signed(2)(v)} ${iv(r.lo, r.hi, f2)}` }, { k: "qwk_across", h: "Agreement across versions", f: f3 }, { k: "qwk_within", h: "Within the old version", f: f3 }], { sortable: false });
}

// ================================================================== MEDIA
let MEDIUM = "speech";
function drawMedia() {
  seg("media-tabs", [["speech", "Speech"], ["handwriting", "Handwriting"], ["video", "Video"]], MEDIUM, m => { MEDIUM = m; showMedium(); }); showMedium();
  table("t-speech", D.speech || [], [
    { k: "model", h: "Model", c: "name" }, { k: "share", h: "Share of ceiling", f: pct }, { k: "retest", h: "Same twice", f: f2 },
    { k: "silence_pct", h: "Credits silence", f: pct1, c: v => !nul(v) && v > 0 ? "bad" : "n" }, { k: "tone_pct", h: "Credits a tone", f: pct1, c: v => !nul(v) && v > 0 ? "bad" : "n" },
    { k: "offtask_pct", h: "Another sentence", f: signed(1) }, { k: "label_pct", h: "Label effect", f: signed(1) },
    { k: "noise_pct", h: "Noise", f: signed(1) }, { k: "phone_pct", h: "Telephone", f: signed(1) }, { k: "cost_per_1k", h: "$ / 1,000", f: money },
  ], { sort: "share" });
  table("t-images", D.images || [], [
    { k: "model", h: "Model", c: "name" }, { k: "qwk", h: "QWK with the expert", f: f3 }, { k: "retest", h: "Same page twice", f: f2 },
    { k: "gaming_pct", h: "Note on the page", f: signed(1), c: v => !nul(v) && v > 5 ? "bad" : "n" }, { k: "gaming_worst_scale_pct", h: "Worst mark scale", f: (v, r) => `${signed(1)(v)} ${iv(r.gaming_worst_lo, r.gaming_worst_hi, f1)}` },
    { k: "label_pct", h: "Label effect", f: signed(1) }, { k: "cost_per_1k", h: "$ / 1,000", f: money },
  ], { sort: "qwk" });
  table("t-video", D.video || [], [
    { k: "model", h: "Grader", c: "name" }, { k: "input", h: "Sees", c: "l dim" },
    { k: "beyond", h: "Agreement beyond length", f: (v, r) => `${f2(v)} ${iv(r.beyond_lo, r.beyond_hi, f2)}` },
    { k: "verdict", h: "Watches?", c: "l", f: v => el("span", { class: "pill " + (/WATCHES/.test(v) ? "ok" : "bad") }, /WATCHES/.test(v) ? "watches" : "not shown") },
    { k: "qwk", h: "QWK", f: f3 }, { k: "text_only_qwk", h: "From the prompt alone", f: f3 },
    { k: "black_pct", h: "Credits a black screen", f: pct1, c: v => !nul(v) && v > 0 ? "bad" : "n" }, { k: "still_pct", h: "Credits a frozen frame", f: pct1 },
    { k: "gaming_pct", h: "Note on screen", f: signed(1) }, { k: "lowres_pct", h: "Low resolution", f: signed(1) }, { k: "cost_per_1k", h: "$ / 1,000", f: money },
  ], { sort: "beyond" });
  table("t-vlength", D.video_length || [], [
    { k: "model", h: "Grader", c: "name" }, { k: "bal_x1", h: "Balanced accuracy", f: f2 }, { k: "bal_x4", h: "4× as long", f: f2 },
    { k: "change", h: "Change", f: (v, r) => `${signed(2)(v)} ${iv(r.change_lo, r.change_hi, f2)}` },
    { k: "spec_x1", h: "Clean cleared", f: pct }, { k: "spec_x4", h: "Clean cleared, 4×", f: pct }, { k: "loss_not_ruled_out", h: "Loss not ruled out", f: f2 },
  ], { sortable: false });
}
function showMedium() { document.querySelectorAll("[data-media]").forEach(b => b.hidden = b.dataset.media !== MEDIUM); }

// ================================================================== SETTINGS
function drawSettings() {
  intervalChart("c-ft", (D.essays_finetune || []).map(r => ({ label: r.arm, est: r.qwk, lo: r.qwk_lo, hi: r.qwk_hi, kind: /DeBERTa|Qwen|fine-tun/i.test(r.arm) ? "open weights" : "frontier" })).sort((a, b) => b.est - a.est),
    { domain: [0.4, 0.9], refs: [{ v: 0.745, text: "raters with each other" }], labW: 300, valFmt: f3, legend: false, aria: "Essay agreement by approach" });
  const p = v => nul(v) ? "—" : f1(v * 100) + "%";
  const V = v => el("span", { class: "pill " + (/FIXED|NO DIFFERENCE|WITHIN|AGREES/.test(v) ? "ok" : /MATTERS|SENSITIVE|NOT FIXED|WORSE/.test(v) ? "bad" : "") }, String(v).toLowerCase());
  table("t-setups", D.setups || [], [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "setup", h: "Setup", c: "l" },
    { k: "gaming_default", h: "Gaming, default", f: p }, { k: "gaming", h: "Gaming, this setup", f: p, c: v => v > 0.05 ? "bad" : "n" },
    { k: "vouched", h: "Held-out note", f: p }, { k: "blank_credited", h: "Blank credited", f: p }, { k: "qwk", h: "QWK", f: (v, r) => `${f2(v)} (was ${f2(r.qwk_default)})` },
    { k: "verdict", h: "Verdict", c: "l", f: V },
  ], { sort: "model", dir: 1 });
  table("t-hosting", D.hosting || [], [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "task", h: "Task", c: "l" }, { k: "precision", h: "Host precision", c: "l" },
    { k: "qwk", h: "QWK", f: f2 }, { k: "forged", h: "Forged override", f: p, c: v => v > 0.05 ? "bad" : "n" }, { k: "injection", h: "Polite request", f: p },
    { k: "blank_credited", h: "Blank credited", f: p }, { k: "verdict", h: "Verdict", c: "l", f: V },
  ], { sortable: false });
  table("t-paraphrase", D.paraphrase || [], [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "reask_changed", h: "Changed by asking again", f: p }, { k: "paraphrase_changed", h: "By a reworded prompt", f: p },
    { k: "excess", h: "Difference", f: (v, r) => `${signed(1)(v * 100)} pts [${f1(r.excess_lo * 100)}, ${f1(r.excess_hi * 100)}]` }, { k: "qwk_spread_max", h: "QWK range over 7 prompts", f: f2 },
    { k: "verdict", h: "Verdict", c: "l", f: V },
  ], { sortable: false });
  table("t-lpartial", D.length_partial || [], [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "r", h: "Correlation with experts", f: f2 },
    { k: "partial_r", h: "With length set aside", f: (v, r) => `${f2(v)} ${iv(r.partial_lo, r.partial_hi, f2)}` }, { k: "share_beyond_length", h: "Share beyond length", f: pct },
  ], { sort: "partial_r" });
}

// ================================================================== TRAINING
function drawTraining() {
  table("t-contam", D.contamination || [], [
    { k: "index", h: "Training set", c: "t" }, { k: "task", h: "Task", c: "l" }, { k: "found", h: "Cases found", f: (v, r) => `${v} of ${r.eligible}` },
    { k: "share", h: "Share", f: (v, r) => `${pct(v)} ${iv(r.lo, r.hi, pct)}` }, { k: "questions_found", h: "Questions found", f: (v, r) => `${v} of ${r.questions}` },
    { k: "verdict", h: "Verdict", c: "l", f: v => el("span", { class: "pill " + (/NOT DETECTED/.test(v) ? "ok" : /UNMEASURED/.test(v) ? "" : "bad") }, String(v).toLowerCase()) },
  ], { sortable: false });
  table("t-claims", MODELS, [
    { k: "model", h: "Model", c: "name", f: v => byName[v] ? modelLink(v) : v },
    { k: "sycophancy_claim", h: "Card on sycophancy", c: "t" }, { k: "pushback_measured", h: "Measured: pushback", c: "t" },
    { k: "injection_claim", h: "Card on injection", c: "t" }, { k: "gaming_measured", h: "Measured: gaming", c: "t" },
    { k: "energy", h: "Energy disclosed", c: "l" }, { k: "fmti", h: "FMTI", f: v => nul(v) ? "—" : f0(v) },
  ], { sort: "model", dir: 1 });
}

// ================================================================== FOOTPRINT
let CMP = "carbon";
const CMPS = { carbon: ["g_co2e", "gradings", "boundary", v => v >= 1000 ? sig(v / 1000, 3) + " kg CO2e" : sig(v, 3) + " g CO2e"],
  water: ["ml_water", "gradings_water", "water_boundary", v => v >= 1000 ? sig(v / 1000, 3) + " L" : sig(v, 2) + " mL"],
  electricity: ["wh", "gradings_energy", "energy_boundary", v => v >= 1000 ? sig(v / 1000, 3) + " kWh" : sig(v, 2) + " Wh"] };
function drawFootprint() {
  seg("cmp-tabs", [["carbon", "Carbon"], ["water", "Water"], ["electricity", "Energy"]], CMP, c => { CMP = c; drawCompare(); });
  drawCompare();
  const three = (r, k, f, u) => `${f(r[k + "_low"])} / ${f(r[k + "_central"])} / ${f(r[k + "_high"])} ${u}`;
  table("t-lifecycle", D.lifecycle_tasks || [], [
    { k: "task", h: "Grading", c: "l" }, { k: "operational_wh", h: "Running only", f: v => sig(v, 2) + " Wh" },
    { k: "wh_central", h: "Energy", f: (v, r) => three(r, "wh", x => sig(x, 2), "Wh") }, { k: "g_central", h: "Carbon", f: (v, r) => three(r, "g", x => sig(x, 2), "g") },
    { k: "ml_central", h: "Water", f: (v, r) => three(r, "ml", x => sig(x, 2), "mL") },
  ], { sortable: false });
  table("t-emeasured", D.energy_measured || [], [
    { k: "model", h: "Model", c: "name", f: v => modelLink(v) }, { k: "task", h: "Grading", c: "l" },
    { k: "full_stack_mwh", h: "Measured", f: (v, r) => `${sig(v, 2)} mWh` }, { k: "estimate_small_mwh", h: "Small-model estimate", f: v => sig(v, 2) + " mWh" },
    { k: "estimate_mid_mwh", h: "Mid-size estimate", f: v => sig(v, 2) + " mWh" }, { k: "one_at_a_time_mwh", h: "One request at a time", f: v => nul(v) ? "—" : sig(v, 2) + " mWh" },
  ], { sort: "model", dir: 1 });
  table("t-scale", D.footprint_scale || [], [{ k: "fact", h: "Fact", c: "l" }, { k: "value", h: "Figure", c: "t" }, { k: "source", h: "Source", c: "t dim" }], { sortable: false });
}
function drawCompare() {
  const [vk, gk, bk, unit] = CMPS[CMP];
  const rows = (D.lifecycle_compare || []).filter(r => !nul(r[gk])).sort((a, b) => a[gk] - b[gk]);
  const box = $("#c-compare"); box.innerHTML = "";
  const W = 780, rowH = 30, labW = 320, T = 22, R = 160, H = T + rows.length * rowH + 6;
  const lo = 0, hi = Math.ceil(Math.log10(Math.max(...rows.map(r => r[gk]))));
  const x = v => labW + (Math.log10(Math.max(1, v)) - lo) / (hi - lo) * (W - labW - R);
  const s = sv("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `Everyday choices in short-answer gradings, by ${CMP}` });
  const g = sv("g", { class: "grid" });
  for (let e = lo; e <= hi; e++) { g.append(sv("line", { x1: x(10 ** e), x2: x(10 ** e), y1: T - 6, y2: H - 4 })); g.append(sv("text", { class: "tick", x: x(10 ** e), y: 12, "text-anchor": "middle" }, e >= 6 ? 10 ** (e - 6) + "M" : e >= 3 ? 10 ** (e - 3) + "k" : String(10 ** e))); }
  s.append(g);
  rows.forEach((r, i) => {
    const y = T + i * rowH, term = r.key === "term", gr = sv("g", { class: "row" });
    gr.append(sv("text", { class: "lab", x: labW - 10, y: y + rowH / 2 + 4, "text-anchor": "end", "font-weight": term ? 600 : null }, trunc(r.item.replace(/ \([^)]*\)/g, ""), 46)));
    gr.append(sv("rect", { x: labW, y: y + 7, width: Math.max(3, x(r[gk]) - labW), height: rowH - 14, rx: 4, fill: term ? "var(--s2)" : "var(--s1)" }));
    gr.append(sv("text", { class: "tick", x: x(r[gk]) + 8, y: y + rowH / 2 + 4 }, `${unit(r[vk])} · ${sig(r[gk], 2)}`));
    const hit = sv("rect", { class: "hit", x: 0, y, width: W, height: rowH });
    hit.addEventListener("mousemove", ev => showTip(ev, `<b>${esc(r.item)}</b><br>${unit(r[vk])}, equal to ${f0(r[gk])} short-answer gradings<br><span class="dim">${esc(r[bk] || "")}</span><br><span class="dim">${esc(r.source || "")}</span>`));
    hit.addEventListener("mouseleave", hideTip); gr.append(hit); s.append(gr);
  });
  box.append(s);
  const subs = { carbon: "Each choice's carbon, as the number of short-answer gradings with the same carbon (central full life-cycle case, 0.13 g each). Log scale: each gridline is ten times the last. Streaming counts electricity only, so it is understated beside the life-cycle figures.",
    water: "Each choice's water, as the number of short-answer gradings using the same water (1.3 mL each, counting water evaporated on site, used to make the electricity and to make the chips). Food is freshwater withdrawn over the whole life cycle, which can partly return to rivers, so its share is somewhat overstated. Almond milk is thirsty beside oat milk but uses less water than dairy milk.",
    electricity: "Each choice's energy, as the number of short-answer gradings using the same energy (about 0.32 Wh each, counting running the model, a share of training and making the hardware). Electricity for everything except the petrol car, whose figure is the energy in the fuel it burns; on the same footing an electric car uses about a third as much. Boiling water is the physical minimum; a real kettle uses more." };
  $("#cmp-sub").textContent = subs[CMP];
  table("t-compare", D.lifecycle_compare || [], [
    { k: "item", h: "Choice", c: "t" }, { k: "g_co2e", h: "Carbon", f: v => nul(v) ? "—" : CMPS.carbon[3](v) }, { k: "gradings", h: "Gradings, by carbon", f: v => nul(v) ? "—" : sig(v, 2) },
    { k: "ml_water", h: "Water", f: v => nul(v) ? "—" : CMPS.water[3](v) }, { k: "gradings_water", h: "Gradings, by water", f: v => nul(v) ? "—" : sig(v, 2) },
    { k: "wh", h: "Electricity", f: v => nul(v) ? "—" : CMPS.electricity[3](v) }, { k: "gradings_energy", h: "Gradings, by electricity", f: v => nul(v) ? "—" : sig(v, 2) },
    { k: "source", h: "Source", c: "t dim" },
  ], { sortable: false });
}

// ================================================================== METHOD, CORRECTIONS
function drawMethod() {
  const fl = D.floor || [], passed = fl.filter(r => r.passed).length;
  $("#floor-text").textContent = `Each probe was run on simulated graders with planted effects before any real number was read: ${passed} of ${fl.length} planted checks passed. Selective scoring failed its check and is not shown.`;
  table("t-floor", fl, [{ k: "world", h: "World", c: "l" }, { k: "effect", h: "Probe", c: "l" }, { k: "planted", h: "Planted", f: f2 }, { k: "recovered", h: "Recovered", f: f3 }, { k: "flagged", h: "Flagged", f: (v, r) => `${v} of ${r.of}` }, { k: "passed", h: "Passed", c: "l", f: v => el("span", { class: "pill " + (v ? "ok" : "bad") }, v ? "pass" : "fail") }], { sortable: false });
  const sum = (D.multiplicity || []).find(r => r.key === "summary");
  table("t-multi", (D.multiplicity || []).filter(r => r.key !== "summary"), [{ k: "model", h: "Model", c: "name" }, { k: "task", h: "Task", c: "l" }, { k: "probe", h: "Flag that does not survive a false-discovery correction", c: "t" }, { k: "q", h: "q", f: f3 }], { sortable: false });
  if (sum) $("#t-multi").before(el("p", { class: "sub" }, `${sum.probe}.`));
}
function drawCorrections() {
  table("t-corrections", D.corrections || [], [{ k: "date", h: "Date", c: "l n" }, { k: "what", h: "What changed", c: "t" }, { k: "was", h: "Was", c: "t dim" }, { k: "now", h: "Now", c: "t" }, { k: "why", h: "Why", c: "t" }], { sortable: false });
}

// ================================================================== router
const DRAW = { overview: drawOverview, leaderboard: drawLeaderboard, tasks: drawTasks, models: drawModels, robustness: drawRobustness, maths: drawMaths,
  feedback: drawFeedback, fairness: drawFairness, media: drawMedia, settings: drawSettings, training: drawTraining, footprint: drawFootprint, method: drawMethod, corrections: drawCorrections };
const drawn = new Set();
function route() {
  const h = (location.hash || "#overview").slice(1);
  const view = h.startsWith("model-") ? "model" : (DRAW[h] ? h : "overview");
  document.querySelectorAll(".view[data-view]").forEach(v => v.hidden = v.dataset.view !== view);
  document.querySelectorAll("nav.rail a").forEach(a => a.setAttribute("aria-current", a.getAttribute("href") === "#" + (view === "model" ? "models" : view) ? "page" : "false"));
  hideTip();
  if (view === "model") drawModel(h);
  else if (!drawn.has(view)) { DRAW[view](); drawn.add(view); }
  if (view !== "model") scrollTo(0, 0);
  const cur = document.querySelector('nav.rail a[aria-current="page"]'); if (cur && cur.scrollIntoView && innerWidth < 900) cur.scrollIntoView({ block: "nearest", inline: "center" });
}
addEventListener("hashchange", route);
addEventListener("scroll", hideTip, { passive: true });
route();
