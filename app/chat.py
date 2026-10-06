"""Question answering over a scope (article, issue, theme, library) with observation citations."""
import re
from collections import defaultdict
from datetime import timedelta

from . import analysis
from .analysis import all_obs, brief, d, today
from .analyzers import llm
from .text import cosine, embed, from_blob

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "nine": 9, "twelve": 12, "a": 1}


def time_window(q):
    """Returns (start_date, end_date, label) parsed from phrases like 'last 3 months', 'six months ago'."""
    ref = today()
    m = re.search(r"(last|past)\s+(\w+)?\s*(week|month|quarter|year)s?", q, re.I)
    if m:
        n = NUM.get((m.group(2) or "a").lower()) or (int(m.group(2)) if (m.group(2) or "").isdigit() else 1)
        days = {"week": 7, "month": 31, "quarter": 92, "year": 365}[m.group(3).lower()] * n
        return ref - timedelta(days=days), ref, f"the last {n} {m.group(3)}(s)"
    m = re.search(r"(\w+)\s+(week|month)s?\s+ago", q, re.I)
    if m:
        n = NUM.get(m.group(1).lower()) or (int(m.group(1)) if m.group(1).isdigit() else 1)
        days = (7 if m.group(2).lower() == "week" else 30) * n
        return ref - timedelta(days=days + 60), ref - timedelta(days=max(days - 60, 0)), f"around {n} {m.group(2)}(s) ago"
    return None, None, None


def scope_obs(conn, scope, sid):
    if scope == "article":
        return all_obs(conn, "o.article_id=?", (sid,)), conn.execute("SELECT title FROM articles WHERE id=?", (sid,)).fetchone()[0]
    if scope == "issue":
        return all_obs(conn, "a.issue_id=?", (sid,)), "issue " + conn.execute("SELECT title FROM issues WHERE id=?", (sid,)).fetchone()[0]
    if scope == "theme":
        return analysis.theme_obs(conn, sid), "theme " + conn.execute("SELECT name FROM themes WHERE id=?", (sid,)).fetchone()[0]
    return all_obs(conn), "the whole library"


INTENTS = [
    ("against", r"\b(against|counter|weak|critic|flaw|objection|rebut)", {"counterargument": .35, "uncertainty": .2, "assumption": .2}),
    ("predictions", r"\bpredict|forecast|came true|supported them", {"prediction": .5}),
    ("compare", r"\b(compare|differ|disagree|versus|vs\.?|contrast)\b", {"argument": .15, "assumption": .2, "claim": .1}),
    ("change", r"\b(chang|evolv|shift|over time|trajector|understanding)", {}),
    ("assumptions", r"\bassum", {"assumption": .5}),
]


def ask(conn, scope, sid, question):
    obs, desc = scope_obs(conn, scope, sid)
    start, end, wlabel = time_window(question)
    intent, boosts = "general", {}
    for name, rx, b in INTENTS:
        if re.search(rx, question, re.I):
            intent, boosts = name, b
            break
    pubs = [p for p in {o["publication"] for o in obs if o["publication"]}
            if re.search(re.escape(p.replace("The ", "")), question, re.I)]
    qv = embed(question)
    vecs = {r[0]: from_blob(r[1]) for r in conn.execute("SELECT id, embedding FROM observations")}
    scored = []
    for o in obs:
        s = cosine(qv, vecs[o["id"]]) + boosts.get(o["type"], 0)
        if pubs and o["publication"] in pubs:
            s += 0.15
        if start and d(o["date"]) and start <= d(o["date"]) <= end:
            s += 0.2
        scored.append((s, o))
    scored.sort(key=lambda x: -x[0])
    top = [o for _, o in scored[:30]]
    if intent == "change":
        top = sorted(top, key=lambda o: o["date"] or "")
    if llm.provider():
        blocks = "\n".join(f"[O{o['id']}] ({o['date']}, {o['publication']}, \"{o['article_title']}\", {o['type']}, "
                           f"{o['epistemic']}, stage={o['modality'] or '-'}) {o['statement']}" for o in top)
        if wlabel:
            desc += f"; the user asks about {wlabel} (today is {today()})"
        try:
            r = llm.answer(question, desc, blocks)
            ids = sorted({int(x) for x in re.findall(r"\[O(\d+)\]", r["answer"])} | set(r.get("citations", [])))
            byid = {o["id"]: o for o in obs}
            return {"mode": "llm", "answer": r["answer"], "citations": [brief(byid[i]) for i in ids if i in byid]}
        except Exception as e:  # fall back to offline answer
            note = f"LLM call failed ({type(e).__name__}); offline answer shown.\n\n"
        else:
            note = ""
    else:
        note = ""
    return local_answer(conn, question, intent, top, obs, desc, wlabel, start, end, pubs, note)


def C(o):
    return f"[O{o['id']}]"


def local_answer(conn, q, intent, top, obs, desc, wlabel, start, end, pubs, note=""):
    lines = [note + f"_Offline answer assembled from stored observations in {desc} (no LLM configured)._"]
    used = []

    def add(o, prefix="- "):
        used.append(o)
        tag = {"source_fact": "reported", "author_interpretation": "author's view", "ai_inference": "AI inference"}[o["epistemic"]]
        lines.append(f"{prefix}{o['statement']} {C(o)} \u2014 _{o['publication'] or ''}, {o['date'] or 'undated'}, {tag}_")

    if intent == "against":
        ca = [o for o in top if o["type"] in ("counterargument", "uncertainty", "assumption")][:6]
        contra = [l for l in analysis.links(conn, [o["id"] for o in obs]) if l["relation"] == "contradicts"]
        lines.append("**Strongest challenges in the text and elsewhere in your library:**")
        for o in ca:
            add(o)
        byid = {o["id"]: o for o in all_obs(conn)}
        for l in contra[:3]:
            other = byid.get(l["dst_id"]) if l["src_id"] in {o["id"] for o in obs} else byid.get(l["src_id"])
            if other:
                add(other, "- Contradicting source: ")
    elif intent == "predictions":
        preds = [o for o in obs if o["type"] == "prediction" and (not start or (d(o["date"]) and start <= d(o["date"]) <= end))]
        pats = {p["id"]: p for p in analysis.patterns(conn)["predictions"]}
        lines.append(f"**Predictions{(' from ' + wlabel) if wlabel else ''} and what later articles said:**")
        for o in preds[:8]:
            add(o)
            st = o["prediction_status"] or "open"
            ev = pats.get(o["id"], {}).get("evidence", [])
            lines.append(f"  - status: **{st}**")
            for e in ev[:2]:
                add(e["obs"], f"  - later ({e['relation']}): ")
        if not preds:
            lines.append("No predictions found in that period.")
    elif intent == "compare" and len(pubs) >= 2:
        for p in pubs:
            lines.append(f"**{p}:**")
            for o in [o for o in top if o["publication"] == p][:5]:
                add(o)
    elif intent == "change":
        lines.append(f"**How things moved{(' in ' + wlabel) if wlabel else ''}:**")
        sigs = analysis.signals_for(obs)
        shown = 0
        for s in sigs:
            tr = s["trajectory"]
            inside = [o for o in tr if not start or (d(o["date"]) and start <= d(o["date"]) <= end)]
            before = [o for o in tr if start and d(o["date"]) and d(o["date"]) < start]
            if not inside:
                continue
            shown += 1
            lines.append(f"**{s['key']}**: now {s['stage']} ({s['reason']})")
            if before:
                add(before[-1], "  - Before: ")
            for o in inside[-2:]:
                add(o, "  - Then: " if before else "  - ")
            if shown >= 5:
                break
        if not shown:
            lines.append("Nothing in this scope was published in that period.")
    else:
        groups = defaultdict(list)
        for o in top[:12]:
            groups[o["type"]].append(o)
        for t, g in groups.items():
            lines.append(f"**{t.capitalize()}**")
            for o in g:
                add(o)
    seen, cites = set(), []
    for o in used:
        if o["id"] not in seen:
            seen.add(o["id"])
            cites.append(brief(o))
    return {"mode": "local", "answer": "\n".join(lines), "citations": cites}
