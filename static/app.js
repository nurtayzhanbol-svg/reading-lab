"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const app = $("#app");
let CONFIG = {llm: false};

async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch {} throw new Error(m); }
  return r.json();
}
const post = (p, body) => api(p, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});

const EPI = {source_fact: "Reported", author_interpretation: "Author's view", ai_inference: "AI inference"};
const TYPE_ORDER = ["claim","argument","evidence","fact","event","prediction","assumption","uncertainty","implication","counterargument","insight","question","dimension"];
const TYPE_LABEL = {claim:"Key claims",argument:"Arguments",evidence:"Evidence & data",fact:"Facts",event:"Events",prediction:"Predictions",assumption:"Assumptions",uncertainty:"Uncertainties",implication:"Implications",counterargument:"Counterarguments",insight:"Worth remembering",question:"Questions raised",dimension:"Other observations"};
const epi = e => `<span class="badge e-${e}" title="${esc({source_fact:"Fact or data reported by the source",author_interpretation:"The author's interpretation or argument",ai_inference:"An inference made by the AI, not stated in the text"}[e])}">${EPI[e] || e}</span>`;
const stage = (s, why) => `<span class="badge st-${s}" title="${esc(why || "")}">${esc(s)}</span>`;
const pstat = s => s ? `<span class="badge ps-${s}">${esc(s)}</span>` : "";
const mod = m => m ? `<span class="chip" title="How far the development has gone, as described">${esc(m)}</span>` : "";
const fmtDate = d => d ? new Date(d + "T00:00:00").toLocaleDateString(undefined, {year: "numeric", month: "short", day: "numeric"}) : "undated";
const monthLabel = m => m && m !== "unknown" ? new Date(m + "-01T00:00:00").toLocaleDateString(undefined, {year: "numeric", month: "long"}) : "Undated";
const src = o => `${esc(o.publication || "")}${o.publication ? " · " : ""}${fmtDate(o.date)}`;

// inline observation reference: click opens provenance drawer
const more = (items, n = 5) => items.length <= n ? items.join("") : items.slice(0, n).join("") + `<details class="more"><summary>Show ${items.length - n} more</summary>${items.slice(n).join("")}</details>`;
const oref = (o, extra = "") => `<div class="o-inline" data-oid="${o.id}">${esc(o.statement)} ${extra}<span class="src">${epi(o.epistemic)} ${src(o)} — <em>${esc(o.article_title || "")}</em></span></div>`;

function md(text) {
  // minimal markdown: bold, italics, bullet lists (with indentation), citations [O12]
  const lines = esc(text).split("\n");
  let html = "", depth = 0;
  for (const raw of lines) {
    const m = raw.match(/^(\s*)- (.*)$/);
    if (m) {
      const d = Math.floor(m[1].length / 2) + 1;
      while (depth < d) { html += "<ul>"; depth++; }
      while (depth > d) { html += "</ul>"; depth--; }
      html += `<li>${inline(m[2])}</li>`;
    } else {
      while (depth > 0) { html += "</ul>"; depth--; }
      if (raw.trim()) html += `<p>${inline(raw)}</p>`;
    }
  }
  while (depth > 0) { html += "</ul>"; depth--; }
  return html;
  function inline(s) {
    return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[\s(])_(.+?)_(?=[\s.,;)]|$)/g, "$1<em>$2</em>")
      .replace(/\[O(\d+)\]/g, '<span class="cite" data-oid="$1">O$1</span>');
  }
}

// ---------- provenance drawer ----------
async function openObs(id) {
  const dr = $("#drawer"), body = $("#drawer-body");
  dr.hidden = false; body.innerHTML = '<div class="loading">Loading…</div>';
  const o = await api(`/api/observations/${id}`);
  let passage = "";
  if (o.passage) {
    const p = o.passage.text, s = (o.quote_start ?? -1) - o.passage.char_start, e = (o.quote_end ?? -1) - o.passage.char_start;
    passage = s >= 0 && e > s ? esc(p.slice(0, s)) + "<mark>" + esc(p.slice(s, e)) + "</mark>" + esc(p.slice(e)) : esc(p);
  }
  const links = o.links.map(l => `<div class="conn"><span class="rel rel-${l.relation}">${l.direction === "later" ? "later article " : "earlier article "}${l.relation}</span>${l.note ? ` <span class="muted small">— ${esc(l.note)}</span>` : ""}${oref(l.other)}</div>`).join("");
  body.innerHTML = `
    <div class="meta">${esc(TYPE_LABEL[o.type] || o.type)} · confidence ${o.confidence != null ? Math.round(o.confidence * 100) + "%" : "–"}</div>
    <h2 style="margin-top:.3rem">${esc(o.statement)}</h2>
    <div class="b">${epi(o.epistemic)} ${mod(o.modality)} ${pstat(o.prediction_status)} ${o.signal_key ? `<span class="chip" title="Tracked signal">signal: ${esc(o.signal_key)}</span>` : ""}</div>
    <h3>Source passage</h3>
    <div class="passage">${passage || '<span class="empty">No passage recorded.</span>'}</div>
    <p class="meta"><a href="#/article/${o.article_id}?o=${o.id}" data-close>${esc(o.article_title)}</a> — ${src(o)}</p>
    ${o.themes.length ? `<h3>Themes</h3>${o.themes.map(t => `<a class="chip" href="#/theme/${t.id}" data-close>${esc(t.name)}</a>`).join("")}` : ""}
    ${o.entities.length ? `<h3>Entities</h3>${o.entities.map(e => `<span class="chip">${esc(e.name)}</span>`).join("")}` : ""}
    <h3>Connections across the library</h3>${links || '<p class="empty">None yet.</p>'}
    <p class="meta" style="margin-top:1.5rem">Produced by <code>${esc(o.run?.analyzer)}</code> (${esc(o.run?.model)}, ${esc(o.run?.prompt_version)}) on ${esc((o.run?.created_at || "").slice(0, 10))}</p>`;
}
function closeDrawer() { $("#drawer").hidden = true; }
document.addEventListener("click", e => {
  const close = e.target.closest("[data-close]");
  if (close) { closeDrawer(); if (close.tagName !== "A") return; }
  const ref = e.target.closest(".cite, .o-inline, .traj .pt");
  if (ref) { e.preventDefault(); openObs(ref.dataset.oid); }
});
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });

// ---------- ask box (shared) ----------
function askBox(scope, id, suggestions) {
  return `<div class="ask" data-scope="${scope}" data-id="${id ?? ""}">
    <form><input name="q" placeholder="Ask about ${scope === "library" ? "your whole library" : "this " + scope}…" autocomplete="off"><button class="btn primary">Ask</button></form>
    <div class="sugg">${suggestions.map(s => `<button type="button">${esc(s)}</button>`).join("")}</div>
    <div class="answers"></div>
    ${CONFIG.llm ? "" : '<p class="meta">No LLM configured: answers are assembled from stored observations. Set OPENAI_API_KEY or ANTHROPIC_API_KEY for generated answers.</p>'}
  </div>`;
}
document.addEventListener("submit", async e => {
  const box = e.target.closest(".ask");
  if (!box) return;
  e.preventDefault();
  const q = e.target.q.value.trim();
  if (q) runAsk(box, q);
});
document.addEventListener("click", e => {
  const b = e.target.closest(".ask .sugg button");
  if (b) { const box = b.closest(".ask"); box.querySelector("input").value = b.textContent; runAsk(box, b.textContent); }
});
async function runAsk(box, q) {
  const out = box.querySelector(".answers");
  const div = document.createElement("div");
  div.className = "answer"; div.innerHTML = `<div class="q">${esc(q)}</div><div class="loading">Thinking…</div>`;
  out.prepend(div);
  try {
    const r = await post("/api/ask", {scope: box.dataset.scope, id: box.dataset.id ? +box.dataset.id : null, question: q});
    div.innerHTML = `<div class="q">${esc(q)}</div>${md(r.answer)}<p class="meta">${r.citations.length} cited observations · ${r.mode === "llm" ? "LLM answer" : "offline answer"}</p>`;
  } catch (err) { div.innerHTML = `<div class="q">${esc(q)}</div><p class="notice">${esc(err.message)}</p>`; }
}

// ---------- views ----------
async function viewLibrary() {
  const arts = await api("/api/articles");
  const byMonth = {};
  for (const a of arts) (byMonth[(a.date || "unknown").slice(0, 7)] ??= []).push(a);
  const issues = {};
  for (const a of arts) if (a.issue_id) (issues[a.issue_id] ??= {title: a.issue, n: 0}).n++;
  app.innerHTML = `<div class="narrow">
    <div class="toolbar" style="justify-content:space-between"><h1 style="margin:0">Library</h1><a class="btn primary" href="#/add">+ Add article</a></div>
    <input id="lib-q" placeholder="Filter by title, thesis or publication…">
    ${Object.keys(issues).length ? `<p class="meta" style="margin-top:.8rem">Issues: ${Object.entries(issues).map(([id, i]) => `<a href="#/issue/${id}">${esc(i.title)}</a> (${i.n})`).join(" · ")}</p>` : ""}
    <div id="lib-list"></div></div>`;
  const render = q => {
    const ql = (q || "").toLowerCase();
    $("#lib-list").innerHTML = Object.keys(byMonth).sort().reverse().map(m => {
      const items = byMonth[m].filter(a => !ql || (a.title + (a.thesis || "") + (a.publication || "")).toLowerCase().includes(ql));
      if (!items.length) return "";
      return `<div class="month">${monthLabel(m)}</div>` + items.map(articleItem).join("");
    }).join("") || '<p class="empty">No articles yet. Add one to get started.</p>';
  };
  $("#lib-q").addEventListener("input", e => render(e.target.value));
  render("");
}
const articleItem = a => `<a class="list-item" href="#/article/${a.id}">
  <div class="meta">${esc(a.publication || "Unknown publication")} · ${fmtDate(a.date)}${a.issue ? " · " + esc(a.issue) : ""}${a.is_sample ? ' · <span title="Synthetic sample article">sample</span>' : ""}</div>
  <div class="t">${esc(a.title)}</div>
  ${a.thesis ? `<div class="thesis">${esc(a.thesis)}</div>` : ""}
  <div>${a.themes.map(t => `<span class="chip">${esc(t.name)}</span>`).join("")}<span class="meta"> ${a.n_obs} observations</span></div></a>`;

async function viewIssue(id) {
  const r = await api(`/api/issues/${id}`);
  app.innerHTML = `<div class="narrow"><p class="meta"><a href="#/library">Library</a> / Issue</p><h1>${esc(r.issue.title)}</h1>
    <p class="meta">${esc(r.issue.publication || "")} · ${fmtDate(r.issue.date)} · ${r.articles.length} articles</p>
    ${r.articles.map(articleItem).join("")}
    <h2>Ask this issue</h2>${askBox("issue", id, ["What connects the articles in this issue?", "What assumptions do these articles share?", "Which predictions does this issue make?"])}</div>`;
}

async function viewAdd() {
  const arts = await api("/api/articles");
  const pubs = [...new Set(arts.map(a => a.publication).filter(Boolean))];
  app.innerHTML = `<div class="narrow"><h1>Add an article</h1>
    <p class="muted">Paste text or upload a PDF. The original is stored unchanged; analysis can be re-run later with a different model.</p>
    <form id="add-form">
      <div class="tabs"><button type="button" class="on" data-mode="text">Paste text</button><button type="button" data-mode="pdf">Upload PDF</button></div>
      <div data-pane="text"><textarea name="text" placeholder="Paste the article text here. Paragraphs separated by blank lines."></textarea></div>
      <div data-pane="pdf" hidden><input type="file" name="file" accept="application/pdf,.pdf,text/plain"></div>
      <div class="grid2">
        <div><label>Title (optional; inferred from the first line otherwise)</label><input name="title"></div>
        <div><label>Publication</label><input name="publication" list="pubs"><datalist id="pubs">${pubs.map(p => `<option value="${esc(p)}">`).join("")}</datalist></div>
        <div><label>Publication date</label><input type="date" name="date" value="${new Date().toISOString().slice(0, 10)}"></div>
        <div><label>Author</label><input name="author"></div>
        <div><label>Issue (optional, groups articles)</label><input name="issue" placeholder="e.g. The Meridian, 3 October 2026"></div>
        <div><label>Analyzer</label><select name="analyzer"><option value="auto">${CONFIG.llm ? "LLM (" + esc(CONFIG.provider + " " + CONFIG.model) + ")" : "Offline heuristic (no LLM configured)"}</option><option value="local">Offline heuristic</option></select></div>
      </div>
      <p><button class="btn primary" id="add-btn">Ingest and analyse</button> <span id="add-status" class="muted small"></span></p>
    </form></div>`;
  let mode = "text";
  $$("#add-form .tabs button").forEach(b => b.onclick = () => {
    mode = b.dataset.mode;
    $$("#add-form .tabs button").forEach(x => x.classList.toggle("on", x === b));
    $$("#add-form [data-pane]").forEach(p => p.hidden = p.dataset.pane !== mode);
  });
  $("#add-form").onsubmit = async e => {
    e.preventDefault();
    const f = e.target, fd = new FormData();
    if (mode === "text") fd.append("text", f.text.value); else if (f.file.files[0]) fd.append("file", f.file.files[0]);
    for (const k of ["title", "publication", "date", "author", "issue", "analyzer"]) if (f[k].value) fd.append(k, f[k].value);
    $("#add-btn").disabled = true; $("#add-status").textContent = "Extracting, analysing and linking…";
    try {
      const r = await api("/api/articles", {method: "POST", body: fd});
      location.hash = `#/article/${r.id}`;
      if (r.analysis_error) alert("Article stored, but analysis failed: " + r.analysis_error);
    } catch (err) { $("#add-status").textContent = err.message; $("#add-btn").disabled = false; }
  };
}

function highlightText(passages, observations) {
  // wrap each observation's quote range in <mark>; overlapping ranges: first one wins
  return passages.map(p => {
    const ranges = observations.filter(o => o.passage_id === p.id && o.quote_start != null)
      .map(o => ({s: o.quote_start - p.char_start, e: o.quote_end - p.char_start, o}))
      .filter(r => r.s >= 0 && r.e <= p.text.length + 1).sort((a, b) => a.s - b.s);
    let out = "", pos = 0;
    for (const r of ranges) {
      if (r.s < pos) continue;
      out += esc(p.text.slice(pos, r.s)) + `<mark class="m-${r.o.epistemic}" data-mark="${r.o.id}" title="${esc(r.o.statement)}">${esc(p.text.slice(r.s, r.e))}</mark>`;
      pos = r.e;
    }
    return `<p data-pid="${p.id}">${out + esc(p.text.slice(pos))}</p>`;
  }).join("");
}

async function viewArticle(id, params) {
  const r = await api(`/api/articles/${id}`);
  const a = r.article;
  const obsHtml = filter => {
    const groups = {};
    for (const o of r.observations) if (!filter || o.epistemic === filter) (groups[o.type] ??= []).push(o);
    return TYPE_ORDER.filter(t => groups[t]).map(t => `<h3>${TYPE_LABEL[t]}</h3>` + groups[t].map(o => `
      <div class="obs" data-obs="${o.id}"><div class="s">${esc(o.statement)}</div>
      <div class="b">${epi(o.epistemic)} ${mod(o.modality)} ${pstat(o.prediction_status)} ${o.dimension ? `<span class="chip" title="Analytical dimension">${esc(o.dimension)}</span>` : ""}
      ${o.themes.map(t => `<a class="chip" href="#/theme/${t.id}">${esc(t.name)}</a>`).join("")}
      <a href="#" class="small" data-detail="${o.id}">provenance ›</a></div></div>`).join("")).join("") || '<p class="empty">No observations.</p>';
  };
  const byRel = {};
  for (const c of r.connections) (byRel[c.direction + ":" + c.relation] ??= []).push(c);
  const mineStmt = Object.fromEntries(r.observations.map(o => [o.id, o.statement]));
  const relTitle = {"earlier:evolves": "Developments this article builds on", "later:evolves": "How later articles moved this on", "earlier:supports": "Earlier articles this supports", "later:supports": "Later articles that support this", "earlier:contradicts": "Disagrees with earlier articles", "later:contradicts": "Later articles that contradict this", "earlier:repeats": "Recurs from earlier articles", "later:repeats": "Recurs in later articles"};
  const connHtml = Object.keys(relTitle).filter(k => byRel[k]).map(k => `<h3>${relTitle[k]}</h3>` + byRel[k].map(c => `
    <div class="conn"><div class="mine">This article: “${esc(mineStmt[c.mine])}”</div>
    <span class="rel rel-${c.relation}">${c.relation}</span>${c.note ? ` <span class="muted small">— ${esc(c.note)}</span>` : ""}${c.origin === "auto" ? ' <span class="muted small" title="Found automatically by similarity and shared signal">(auto)</span>' : ""}
    ${oref(c.other)}</div>`).join("")).join("") || '<p class="empty">No connections to other articles yet.</p>';
  const run = r.run;
  app.innerHTML = `<div class="reader">
    <article>
      <p class="meta"><a href="#/library">Library</a>${a.issue_id ? ` / <a href="#/issue/${a.issue_id}">${esc(a.issue)}</a>` : ""}</p>
      <div class="meta">${esc(a.publication || "Unknown publication")} · ${fmtDate(a.date)}${a.author ? " · " + esc(a.author) : ""}${a.is_sample ? " · synthetic sample" : ""}</div>
      <h1>${esc(a.title)}</h1>
      <div class="legend"><span><mark class="m-source_fact">reported</mark></span><span><mark class="m-author_interpretation">author's view</mark></span><span><mark class="m-ai_inference">AI inference source</mark></span><span>Tap an underlined passage to see what was extracted from it.</span></div>
      <div class="article-body">${highlightText(r.passages, r.observations)}</div>
    </article>
    <aside class="side" id="side">
      <div class="side-close"><strong>Analysis</strong><button class="icon" id="side-x" aria-label="Close analysis">&times;</button></div>
      <div class="tabs" id="side-tabs"><button class="on" data-tab="analysis">Analysis</button><button data-tab="connections">Connections (${r.connections.length})</button><button data-tab="ask">Ask</button></div>
      <div data-tabpane="analysis">
        ${r.thesis ? `<div class="thesis-box">${esc(r.thesis)}</div>` : ""}
        ${r.dimensions.length ? `<div class="meta">Dimensions inferred for this article:</div><div style="margin:.2rem 0 .6rem">${r.dimensions.map(d => `<span class="chip" title="${esc(d.why)}">${esc(d.name)}</span>`).join("")}</div>` : ""}
        <div class="filters" id="epi-f"><button class="on" data-f="">All ${r.observations.length}</button>${Object.keys(EPI).map(k => `<button data-f="${k}">${EPI[k]} ${r.observations.filter(o => o.epistemic === k).length}</button>`).join("")}</div>
        <div id="obs-list">${obsHtml("")}</div>
        <p class="meta" style="margin-top:1.2rem">Analysis: <code>${esc(run?.analyzer)}</code> · ${esc(run?.model)} · ${esc(run?.prompt_version)} · ${esc((run?.created_at || "").slice(0, 10))}${r.runs.length > 1 ? ` · ${r.runs.length} runs kept` : ""}</p>
        <p><button class="btn small" id="reanalyze" data-a="local">Re-run offline analyzer</button> ${CONFIG.llm ? `<button class="btn small" id="reanalyze2" data-a="auto">Re-run with LLM</button>` : ""}</p>
      </div>
      <div data-tabpane="connections" hidden>${connHtml}</div>
      <div data-tabpane="ask" hidden>${askBox("article", id, ["What is the strongest argument against this article?", "What assumptions does this article make?", "How does this compare with what I read about this topic last month?"])}</div>
    </aside></div>
    <button class="btn primary fab" id="fab">Analysis · ${r.observations.length}</button>`;
  const side = $("#side");
  $("#fab").onclick = () => side.classList.add("open");
  $("#side-x").onclick = () => side.classList.remove("open");
  const showTab = t => { $$("#side-tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === t)); $$("[data-tabpane]").forEach(p => p.hidden = p.dataset.tabpane !== t); };
  $$("#side-tabs button").forEach(b => b.onclick = () => showTab(b.dataset.tab));
  $$("#epi-f button").forEach(b => b.onclick = () => { $$("#epi-f button").forEach(x => x.classList.toggle("on", x === b)); $("#obs-list").innerHTML = obsHtml(b.dataset.f); });
  const flash = el => { el.classList.add("hl"); setTimeout(() => el.classList.remove("hl"), 2200); };
  const focusObs = (oid, openSheet) => {
    showTab("analysis");
    if (openSheet) side.classList.add("open");
    const card = $(`.obs[data-obs="${oid}"]`, side);
    if (card) { card.scrollIntoView({block: "center", behavior: "smooth"}); flash(card); }
  };
  const focusMark = oid => {
    const m = $(`mark[data-mark="${oid}"]`);
    const o = r.observations.find(x => x.id == oid);
    const el = m || (o && $(`p[data-pid="${o.passage_id}"]`));
    if (el) { el.scrollIntoView({block: "center", behavior: "smooth"}); flash(el); }
  };
  app.onclick = e => {
    const det = e.target.closest("[data-detail]");
    if (det) { e.preventDefault(); openObs(det.dataset.detail); return; }
    const card = e.target.closest(".obs");
    if (card && !e.target.closest("a")) {
      if (matchMedia("(max-width:900px)").matches) side.classList.remove("open");
      focusMark(card.dataset.obs); return;
    }
    const m = e.target.closest("mark[data-mark]");
    if (m) focusObs(m.dataset.mark, true);
  };
  for (const btn of $$("#reanalyze, #reanalyze2")) btn.onclick = async () => {
    btn.disabled = true; btn.textContent = "Analysing…";
    try { await api(`/api/articles/${id}/reanalyze?analyzer=${btn.dataset.a}`, {method: "POST"}); route(); } catch (err) { alert(err.message); btn.disabled = false; }
  };
  if (params.get("o")) setTimeout(() => { focusMark(params.get("o")); focusObs(params.get("o"), false); }, 50);
}

function spark(months) {
  const keys = Object.keys(months).sort();
  if (!keys.length) return "";
  const [y0, m0] = keys[0].split("-").map(Number), [y1, m1] = keys[keys.length - 1].split("-").map(Number);
  const all = [];
  for (let y = y0, m = m0; y < y1 || (y === y1 && m <= m1); m++, m > 12 && (m = 1, y++)) all.push(`${y}-${String(m).padStart(2, "0")}`);
  const max = Math.max(...Object.values(months));
  return `<div class="spark" title="Observations per month, ${keys[0]} to ${keys[keys.length - 1]}">${all.map(k => `<span style="height:${Math.max(4, 100 * (months[k] || 0) / max)}%" title="${k}: ${months[k] || 0}"></span>`).join("")}</div>`;
}

async function viewThemes() {
  const ts = await api("/api/themes");
  const active = ts.filter(t => t.status === "active"), sugg = ts.filter(t => t.status === "suggested");
  app.innerHTML = `<div class="toolbar" style="justify-content:space-between"><h1 style="margin:0">Themes</h1><button class="btn" id="new-theme">+ New theme</button></div>
    <p class="muted">Themes are evolving analytical objects: each is a synthesis of the observations attached to it, tracked over time.</p>
    <form id="theme-form" class="card" hidden><div class="grid2"><div><label>Name</label><input name="name" required></div><div><label>Keywords (comma-separated, help auto-assignment)</label><input name="keywords"></div></div>
      <label>Description</label><input name="description"><p><button class="btn primary">Create and assign observations</button></p></form>
    <div class="theme-grid">${active.map(t => `<a class="card theme-card" href="#/theme/${t.id}">
      <div class="n">${esc(t.name)}</div><div>${stage(t.stage, t.stage_reason)} <span class="meta">${esc(t.stage_reason)}</span></div>
      <p class="small muted" style="margin:.4rem 0 0">${esc(t.description || "")}</p>
      ${spark(t.months)}<div class="meta">${t.n_articles} articles · ${t.n_obs} observations · last ${fmtDate(t.last)}</div></a>`).join("")}</div>
    ${sugg.length ? `<h2>Suggested by AI</h2>${sugg.map(t => `<div class="card"><strong>${esc(t.name)}</strong> <span class="badge e-ai_inference">AI suggestion</span>
      <p class="small muted">${esc(t.description || "")}</p><p class="meta">${t.n_obs} observations already point to it.</p>
      <button class="btn small primary" data-accept="${t.id}">Accept as theme</button> <button class="btn small" data-reject="${t.id}">Dismiss</button></div>`).join("")}` : ""}`;
  $("#new-theme").onclick = () => $("#theme-form").hidden = !$("#theme-form").hidden;
  $("#theme-form").onsubmit = async e => {
    e.preventDefault(); const f = e.target;
    const r = await post("/api/themes", {name: f.name.value, description: f.description.value, keywords: f.keywords.value.split(",").map(s => s.trim()).filter(Boolean)});
    location.hash = `#/theme/${r.id}`;
  };
  const patch = (id, status) => api(`/api/themes/${id}`, {method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify({status})}).then(viewThemes);
  $$("[data-accept]").forEach(b => b.onclick = () => patch(b.dataset.accept, "active"));
  $$("[data-reject]").forEach(b => b.onclick = () => patch(b.dataset.reject, "rejected"));
}

const traj = s => `<div class="traj">${s.trajectory.map((o, i) => `${i ? '<span class="arrow">→</span>' : ""}<span class="pt" data-oid="${o.id}" title="${esc(o.statement)}"><span class="dot ${o.modality || ""}"></span>${esc((o.date || "").slice(0, 7))}${o.modality ? " " + esc(o.modality) : ""}</span>`).join("")}</div>`;
const sigRow = s => `<div class="sig"><strong>${esc(s.key)}</strong> ${stage(s.stage, s.reason)} <span class="meta">${esc(s.reason)} · ${s.articles} articles · ${s.publications.map(esc).join(", ")}</span>${traj(s)}</div>`;

async function viewTheme(id) {
  const r = await api(`/api/themes/${id}`);
  const t = r.theme;
  const sec = (key, title, html) => html ? `<section id="s-${key}"><h2>${title}</h2>${html}</section>` : "";
  const list = (arr, f = o => oref(o), n = 5) => arr.length ? more(arr.map(o => `<div class="conn">${f(o)}</div>`), n) : "";
  const ai = r.ai_synthesis;
  const sections = [
    ["overview", "Overview", `${ai ? `<div class="card">${["current_state", "how_it_changed", "competing_interpretations", "what_to_watch"].map(k => `<h3>${k.replace(/_/g, " ")}</h3>${md(ai[k] || "")}`).join("")}<p class="meta">Generated by ${esc(ai.method)} on ${esc(ai.created_at.slice(0, 10))}</p></div>` : ""}
      <div class="card">${r.narrative.map(p => `<p>${esc(p.text)} ${p.cites.map(c => `<span class="cite" data-oid="${c}">O${c}</span>`).join(" ")}</p>`).join("")}
      <p class="meta">Computed from the stored observations and links${CONFIG.llm ? "" : " (no LLM configured)"}.</p>
      ${CONFIG.llm ? `<button class="btn small" id="synth">${ai ? "Regenerate" : "Generate"} AI synthesis</button>` : ""}</div>`],
    ["current", "Current state", list(r.current_state, c => `<div class="meta">${esc(c.signal)} ${stage(c.stage)}</div>${oref(c.obs)}`)],
    ["changed", "How the theme changed over time", (r.developments.length ? `<h3>Developments</h3>` + more(r.developments.map(l => `<div class="pair"><div>${oref(l.src)}</div><div class="vs rel rel-evolves">→ ${esc(l.note || "evolves")}</div><div>${oref(l.dst)}</div></div>`), 4) : "") +
      `<h3>Timeline</h3><div class="timeline">${r.timeline.map(m => `<div class="tl"><div class="m">${monthLabel(m.month)} <span class="meta">· ${m.articles} article(s), ${m.count} observations${Object.keys(m.modalities).length ? " · " + Object.entries(m.modalities).map(([k, v]) => `${k} ${v}`).join(", ") : ""}</span></div>${more(m.highlights.map(o => oref(o)), 2)}</div>`).join("")}</div>`],
    ["signals", "Signals", r.signals.length ? `<div class="legend">${["discussed", "proposed", "committed", "implemented", "constrained", "doubted", "reversed"].map(m => `<span><span class="dot ${m}" style="display:inline-block;width:9px;height:9px;border-radius:50%"></span> ${m}</span>`).join("")}</div>` + more(r.signals.map(sigRow), 5) : ""],
    ["competing", "Competing interpretations", r.competing_interpretations.map(c => `<h3>${esc(c.signal)}</h3>` + c.views.map(v => `<div class="conn"><strong class="small">${esc(v.publication)}</strong>${oref(v.obs)}</div>`).join("")).join("") +
      (r.contradictions.length ? `<h3>Direct contradictions</h3>` + r.contradictions.map(l => `<div class="pair"><div>${oref(l.src)}</div><div class="vs rel rel-contradicts">vs ${l.note ? "<br>" + esc(l.note) : ""}</div><div>${oref(l.dst)}</div></div>`).join("") : "")],
    ["predictions", "Predictions", list(r.predictions, o => oref(o, pstat(o.prediction_status)))],
    ["questions", "Unresolved questions", list(r.unresolved_questions)],
    ["evidence", "Important evidence", list(r.evidence)],
    ["articles", "Articles", r.articles.map(a => `<div class="conn"><a href="#/article/${a.id}">${esc(a.title)}</a> <span class="meta">${esc(a.publication)} · ${fmtDate(a.date)} · ${a.n} observations</span></div>`).join("") +
      (r.related_themes.length ? `<h3>Often appears with</h3>${r.related_themes.map(x => `<a class="chip" href="#/theme/${x.id}">${esc(x.name)} (${x.shared_articles})</a>`).join("")}` : "")],
    ["ask", "Ask this theme", askBox("theme", id, [`What changed in my understanding of ${t.name} during the last 3 months?`, "Which predictions were supported or contradicted?", "Where do publications disagree?"])],
  ].filter(s => s[2]);
  app.innerHTML = `<div class="narrow" style="max-width:860px">
    <p class="meta"><a href="#/themes">Themes</a>${t.status !== "active" ? " · " + esc(t.status) : ""}</p>
    <h1>${esc(t.name)}</h1>
    <div>${stage(r.stage, r.stage_reason)} <span class="meta">${esc(r.stage_reason)} · ${r.articles.length} articles · ${r.n_observations} observations · ${fmtDate(r.first)} – ${fmtDate(r.last)}</span></div>
    ${t.description ? `<p class="muted">${esc(t.description)}</p>` : ""}
    <div class="anchors">${sections.map(s => `<a href="#" data-jump="s-${s[0]}">${s[1]}</a>`).join("")}</div>
    ${sections.map(s => sec(...s)).join("")}</div>`;
  $$("[data-jump]").forEach(a => a.onclick = e => { e.preventDefault(); document.getElementById(a.dataset.jump).scrollIntoView({behavior: "smooth"}); });
  const sb = $("#synth");
  if (sb) sb.onclick = async () => { sb.disabled = true; sb.textContent = "Generating…"; try { await post(`/api/themes/${id}/synthesize`, {}); viewTheme(id); } catch (err) { alert(err.message); sb.disabled = false; } };
}

async function viewPatterns(params) {
  const days = +(params.get("days") || 90);
  const [p, s] = await Promise.all([api(`/api/patterns?days=${days}`), api("/api/stats")]);
  const none = '<p class="empty">Nothing yet.</p>';
  const pair = (a, b, mid) => `<div class="pair"><div>${oref(a)}</div><div class="vs">${mid}</div><div>${oref(b)}</div></div>`;
  const ch = p.changed;
  const preds = {supported: [], contradicted: [], disputed: [], open: []};
  for (const x of p.predictions) (preds[x.prediction_status || "open"] ??= []).push(x);
  const maxM = Math.max(1, ...s.months.map(m => m[1]));
  const months = [...new Set(Object.values(s.theme_month).flatMap(o => Object.keys(o)))].filter(m => m && m !== "null").sort();
  const pubs = [...new Set(s.publication_theme.map(r => r.pub))], themes = [...new Set(s.publication_theme.map(r => r.theme))];
  const pt = Object.fromEntries(s.publication_theme.map(r => [r.pub + "|" + r.theme, r.c]));
  app.innerHTML = `<div class="narrow" style="max-width:900px">
    <div class="toolbar" style="justify-content:space-between"><h1 style="margin:0">Patterns</h1>
      <div class="filters">${[30, 90, 180, 365].map(d => `<button class="${d === days ? "on" : ""}" data-days="${d}">last ${d < 365 ? d + " days" : "year"}</button>`).join("")}</div></div>
    <p class="muted">Cross-article patterns computed from ${s.observations} observations in ${s.articles} articles. These are <span class="badge e-ai_inference">AI inference</span> built on top of what sources reported and what authors argued; every item links back to its passages.</p>
    ${askBox("library", null, ["What has changed in my reading during the last month?", "Show predictions I encountered six months ago and whether subsequent articles supported them.", "What assumptions do The Meridian and The Northern Ledger make differently?", "Which assumptions recur across unrelated topics?"])}

    <h2>What changed in the last ${days} days</h2>
    <p class="meta">${ch.articles} articles read in this window.</p>
    ${ch.stage_shifts.length ? `<h3>Signals moving</h3>${more(ch.stage_shifts.map(x => `<div class="conn"><strong>${esc(x.key)}</strong> ${stage(x.stage, x.reason)} <span class="meta">${esc(x.reason)}</span>${oref(x.obs)}</div>`), 5)}` : ""}
    ${ch.new_signals.length ? `<h3>New signals</h3>${ch.new_signals.map(x => `<div class="conn"><strong>${esc(x.key)}</strong> <span class="meta">first seen ${fmtDate(x.first)}</span>${oref(x.obs)}</div>`).join("")}` : ""}
    ${ch.predictions_tested.length ? `<h3>Predictions tested by recent articles</h3>${ch.predictions_tested.map(x => `<div class="conn">${oref(x, pstat(x.prediction_status))}</div>`).join("")}` : ""}
    ${ch.new_predictions.length ? `<h3>New predictions to watch</h3>${ch.new_predictions.map(x => `<div class="conn">${oref(x)}</div>`).join("")}` : ""}

    <h2>Easy to miss when reading articles one by one</h2>
    ${p.cross_theme_links.length ? `<h3>The same development across different themes</h3>${p.cross_theme_links.map(x => pair(x.a, x.b, `<span class="rel">${esc(x.relation)}</span><br>${x.themes.map(esc).join(" · ")}`)).join("")}` : none}
    ${p.bridging_entities.length ? `<h3>Entities connecting several themes</h3><table><tr><th>Entity</th><th>Articles</th><th>Themes</th></tr>${p.bridging_entities.map(e => `<tr><td>${esc(e.name)}</td><td>${e.articles}</td><td>${e.themes.map(esc).join(", ")}</td></tr>`).join("")}</table>` : ""}

    <h2>Assumptions that recur across articles</h2>
    ${p.recurring_assumptions.map(r => `<div class="card"><strong>${esc(r.signal || "shared assumption")}</strong> <span class="meta">${r.obs.length} articles · ${r.themes.map(esc).join(", ")}</span>${r.obs.map(o => `<div class="conn">${oref(o)}</div>`).join("")}</div>`).join("") || none}

    <h2>Where sources disagree</h2>
    ${p.disagreements.map(x => pair(x.a, x.b, `<span class="rel rel-contradicts">vs</span>${x.note ? "<br>" + esc(x.note) : ""}${x.cross_publication ? "<br>across publications" : ""}`)).join("") || none}

    <h2>Predictions: supported, contradicted, open</h2>
    <p>${Object.entries(preds).filter(([, v]) => v.length).map(([k, v]) => `${pstat(k)} ${v.length}`).join(" &nbsp; ")}</p>
    ${["contradicted", "disputed", "supported", "open"].filter(k => preds[k].length).map(k => `<h3>${k}</h3>` + preds[k].map(x => `<div class="conn">${oref(x)}${x.evidence.map(e => `<div style="margin:.3rem 0 0 1rem"><span class="rel rel-${e.relation}">later: ${e.relation}</span>${oref(e.obs)}</div>`).join("")}</div>`).join("")).join("")}

    <h2>Signals</h2>
    <div class="two"><div><h3>Strengthened recently</h3>${p.strengthened.map(sigRow).join("") || none}</div><div><h3>Weakening or fading</h3>${p.weakened.map(sigRow).join("") || none}</div></div>

    <h2>Themes</h2>
    <div class="two"><div><h3>Frequency (articles, this vs previous ${days} days)</h3><table>${p.theme_trend.map(t => `<tr><td><a href="#/theme/${t.theme_id}">${esc(t.name)}</a></td><td>${t.current} vs ${t.previous}</td><td>${t.delta > 0 ? "▲" : t.delta < 0 ? "▼" : "–"}</td></tr>`).join("")}</table></div>
    <div><h3>Themes that occur together</h3><table>${p.cooccurrence.map(c => `<tr><td>${esc(c.a)} + ${esc(c.b)}</td><td>${c.articles} articles</td></tr>`).join("")}</table></div></div>

    <h3>Entities becoming more central</h3>
    <table><tr><th>Entity</th><th>This window</th><th>Previous</th><th>All</th><th>Themes</th></tr>${p.entities.slice(0, 8).map(e => `<tr><td>${esc(e.name)} <span class="meta">${esc(e.kind || "")}</span></td><td>${e.current}</td><td>${e.previous}</td><td>${e.articles}</td><td class="small">${e.themes.map(esc).join(", ")}</td></tr>`).join("")}</table>

    <h2>Corpus statistics</h2>
    <h3>Articles read per month</h3>
    <div class="bars">${s.months.map(([m, c]) => `<div title="${m}: ${c}"><span>${c}</span><i style="height:${80 * c / maxM}%"></i><span>${m.slice(2)}</span></div>`).join("")}</div>
    <h3>Themes over time (articles per month)</h3>
    <div style="overflow-x:auto"><table class="heat"><tr><th></th>${months.map(m => `<th>${m.slice(2)}</th>`).join("")}</tr>${Object.entries(s.theme_month).map(([t, row]) => `<tr><td>${esc(t)}</td>${months.map(m => `<td class="v" style="background:${row[m] ? `rgba(47,93,138,${0.15 + 0.25 * row[m]})` : "transparent"}">${row[m] || ""}</td>`).join("")}</tr>`).join("")}</table></div>
    <div class="two"><div><h3>Publications by theme</h3><div style="overflow-x:auto"><table><tr><th></th>${themes.map(t => `<th>${esc(t)}</th>`).join("")}</tr>${pubs.map(pb => `<tr><td>${esc(pb)}</td>${themes.map(t => `<td>${pt[pb + "|" + t] || ""}</td>`).join("")}</tr>`).join("")}</table></div></div>
    <div><h3>Recurring analytical dimensions</h3><table>${s.recurring_dimensions.map(d => `<tr><td>${esc(d.dimension)}</td><td>${d.a} articles</td></tr>`).join("")}</table>
    <h3>What the library is made of</h3><p>${Object.entries(s.epistemic).map(([k, v]) => `${epi(k)} ${v}`).join(" &nbsp; ")}</p></div></div>
  </div>`;
  $$("[data-days]").forEach(b => b.onclick = () => location.hash = `#/patterns?days=${b.dataset.days}`);
}

// ---------- router ----------
async function route() {
  closeDrawer();
  const [path, qs] = (location.hash.slice(1) || "/library").split("?");
  const params = new URLSearchParams(qs || "");
  const parts = path.split("/").filter(Boolean);
  $$("[data-nav]").forEach(a => a.classList.toggle("active", path.startsWith("/" + a.dataset.nav) || (a.dataset.nav === "library" && /^\/(article|issue)/.test(path)) || (a.dataset.nav === "themes" && path.startsWith("/theme"))));
  app.onclick = null;
  app.innerHTML = '<div class="loading">Loading…</div>';
  try {
    if (parts[0] === "article") await viewArticle(+parts[1], params);
    else if (parts[0] === "issue") await viewIssue(+parts[1]);
    else if (parts[0] === "themes") await viewThemes();
    else if (parts[0] === "theme") await viewTheme(+parts[1]);
    else if (parts[0] === "patterns") await viewPatterns(params);
    else if (parts[0] === "add") await viewAdd();
    else await viewLibrary();
    if (parts[0] !== "article" || !params.get("o")) window.scrollTo(0, 0);
  } catch (err) { app.innerHTML = `<p class="notice">${esc(err.message)}</p>`; }
}
window.addEventListener("hashchange", route);
api("/api/config").then(c => { CONFIG = c; }).finally(route);
