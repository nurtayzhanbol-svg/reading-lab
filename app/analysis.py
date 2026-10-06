"""Corpus-level computation: theme temporal model, theme synthesis, patterns, statistics.
Everything here is derived from observations + links and can be recomputed at any time."""
import os
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations

from . import db
from .store import MOD_RANK

OBS_SQL = """SELECT o.id, o.article_id, o.type, o.dimension, o.statement, o.epistemic, o.confidence, o.modality,
  o.passage_id, o.quote, o.quote_start, o.quote_end, o.date, o.signal_key, o.prediction_status, o.entities,
  a.title AS article_title, p.name AS publication
  FROM observations o JOIN articles a ON a.id=o.article_id LEFT JOIN publications p ON p.id=a.publication_id"""


def today():
    t = os.environ.get("READINGLAB_TODAY")
    return date.fromisoformat(t) if t else date.today()


def d(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def brief(o):
    keys = ["id", "article_id", "type", "dimension", "statement", "epistemic", "confidence", "modality",
            "quote", "date", "signal_key", "prediction_status", "article_title", "publication", "passage_id"]
    return {k: o.get(k) for k in keys}


def all_obs(conn, where="1=1", params=()):
    return db.rows(conn.execute(f"{OBS_SQL} WHERE {where} ORDER BY o.date, o.id", params))


def links(conn, ids=None):
    q = "SELECT * FROM observation_links"
    ls = db.rows(conn.execute(q))
    if ids is not None:
        ids = set(ids)
        ls = [l for l in ls if l["src_id"] in ids or l["dst_id"] in ids]
    return ls


def update_prediction_status(conn):
    conn.execute("UPDATE observations SET prediction_status=NULL")
    conn.execute("UPDATE observations SET prediction_status='open' WHERE type='prediction'")
    for l in db.rows(conn.execute(
            "SELECT l.* FROM observation_links l JOIN observations o ON o.id=l.src_id WHERE o.type='prediction' "
            "AND l.relation IN ('supports','contradicts')")):
        if l["origin"] == "auto" and (l["score"] or 0) < 0.6:
            continue
        status = "contradicted" if l["relation"] == "contradicts" else "supported"
        cur = conn.execute("SELECT prediction_status FROM observations WHERE id=?", (l["src_id"],)).fetchone()[0]
        if cur == "contradicted" or (cur == "supported" and status == "supported"):
            continue
        if cur == "supported" and status == "contradicted":
            status = "disputed"
        conn.execute("UPDATE observations SET prediction_status=? WHERE id=?", (status, l["src_id"]))


# ---------- temporal model ----------

RECENT, PRIOR, STALE = 75, 200, 240


def _mods_on(dated, day):
    return [o["modality"] for o in dated if o["date"] == day and o["modality"]]


def stage_of(obs, ref=None):
    """Lifecycle stage for a group of dated observations: emerging, strengthening, established,
    weakening, obsolete. Returns (stage, reason). Heuristic and explained, not hard truth.
    Uses mention volume (recent vs earlier window) and how firmly the latest article frames
    the development (its modality language) compared with the first."""
    ref = ref or today()
    dated = [o for o in obs if d(o["date"])]
    if not dated:
        return "emerging", "no dated observations"
    dated.sort(key=lambda o: (o["date"], o["id"]))
    first, last = d(dated[0]["date"]), d(dated[-1]["date"])
    age = (ref - last).days
    recent = len({o["article_id"] for o in dated if (ref - d(o["date"])).days <= RECENT})
    prior = len({o["article_id"] for o in dated if RECENT < (ref - d(o["date"])).days <= PRIOR})
    arts = len({o["article_id"] for o in dated})
    first_m, last_m = _mods_on(dated, dated[0]["date"]), _mods_on(dated, dated[-1]["date"])
    avg = lambda ms: sum(MOD_RANK[m] for m in ms) / len(ms) if ms else None
    fr, lr = avg(first_m), avg(last_m)
    label = lambda ms: "/".join(dict.fromkeys(ms))
    if age > STALE:
        return "obsolete", f"not mentioned for {age} days"
    if last_m and lr is not None and lr < 0 and "reversed" in last_m:
        return "obsolete", f"latest article ({dated[-1]['date']}) reports a reversal"
    if arts > 1 and lr is not None and lr < 0.5 and any(MOD_RANK[m] < 0 for m in last_m):
        return "weakening", f"latest article ({dated[-1]['date']}) frames it as {label(last_m)}"
    if prior >= 2 and recent * 2 < prior:
        return "weakening", f"{recent} recent vs {prior} earlier articles"
    if (ref - first).days <= 90 and arts <= 2:
        return "emerging", f"first seen {(ref - first).days} days ago in {arts} article(s)"
    if fr is not None and lr is not None and arts > 1 and lr > fr + 0.5:
        return "strengthening", f"language moved from {label(first_m)} to {label(last_m)}"
    if recent > prior and recent >= 1 and arts >= 2:
        return "strengthening", f"{recent} recent vs {prior} earlier articles"
    if arts >= 3 and (last - first).days >= 120:
        return "established", f"{arts} articles over {(last - first).days} days"
    return "established", f"{arts} article(s), last seen {age} days ago"


def theme_stage(obs, ref=None):
    """Theme stage = strength-weighted vote of its signals' stages (falls back to all observations)."""
    sigs = signals_for(obs, ref)
    if not sigs:
        return stage_of(obs, ref) if obs else ("emerging", "no observations yet")
    votes = Counter()
    for s in sigs:
        votes[s["stage"]] += s["strength"]
    stage = votes.most_common(1)[0][0]
    n = sum(1 for s in sigs if s["stage"] == stage)
    return stage, f"{n} of {len(sigs)} tracked signals are {stage}"


def theme_obs(conn, theme_id):
    return all_obs(conn, "o.id IN (SELECT observation_id FROM observation_themes WHERE theme_id=?)", (theme_id,))


def signals_for(obs, ref=None):
    groups = defaultdict(list)
    for o in obs:
        if o["signal_key"]:
            groups[o["signal_key"]].append(o)
    out = []
    for key, g in groups.items():
        if len({o["article_id"] for o in g}) < 2 and len(g) < 2:
            continue
        stage, why = stage_of(g, ref)
        g.sort(key=lambda o: (o["date"] or "", o["id"]))
        out.append({"key": key, "stage": stage, "reason": why, "count": len(g),
                    "articles": len({o["article_id"] for o in g}),
                    "publications": sorted({o["publication"] for o in g if o["publication"]}),
                    "first": g[0]["date"], "last": g[-1]["date"],
                    "strength": round(sum(o["confidence"] or 0.5 for o in g), 2),
                    "trajectory": [brief(o) for o in g]})
    out.sort(key=lambda s: (-s["strength"]))
    return out


STAGE_ORDER = ["emerging", "strengthening", "established", "weakening", "obsolete"]


def compute_theme(conn, theme_id):
    t = conn.execute("SELECT * FROM themes WHERE id=?", (theme_id,)).fetchone()
    if not t:
        return None
    t = dict(t)
    obs = theme_obs(conn, theme_id)
    ids = {o["id"] for o in obs}
    byid = {o["id"]: o for o in all_obs(conn)}
    ls = links(conn, ids)
    stage, why = theme_stage(obs)
    sigs = signals_for(obs)
    arts = {}
    for o in obs:
        a = arts.setdefault(o["article_id"], {"id": o["article_id"], "title": o["article_title"],
                                              "publication": o["publication"], "date": o["date"], "n": 0})
        a["n"] += 1

    def L(l):
        return {"id": l["id"], "relation": l["relation"], "note": l["note"], "origin": l["origin"],
                "src": brief(byid[l["src_id"]]), "dst": brief(byid[l["dst_id"]])}

    inside = [l for l in ls if l["src_id"] in byid and l["dst_id"] in byid]
    evolves = sorted([L(l) for l in inside if l["relation"] == "evolves"], key=lambda x: x["dst"]["date"] or "")
    contra = [L(l) for l in inside if l["relation"] == "contradicts"]
    current = []
    for s in sigs:
        if s["stage"] in ("obsolete",):
            continue
        current.append({"signal": s["key"], "stage": s["stage"], "obs": s["trajectory"][-1]})
    interp = defaultdict(lambda: defaultdict(list))
    for o in obs:
        if o["epistemic"] == "author_interpretation" and o["type"] in ("argument", "claim", "implication") and o["signal_key"]:
            interp[o["signal_key"]][o["publication"]].append(brief(o))
    competing = [{"signal": k, "views": [{"publication": p, "obs": v[-1]} for p, v in pubs.items()]}
                 for k, pubs in interp.items() if len(pubs) > 1]
    months = defaultdict(list)
    for o in obs:
        if o["date"]:
            months[o["date"][:7]].append(o)
    timeline = []
    for m in sorted(months):
        g = months[m]
        mods = Counter(o["modality"] for o in g if o["modality"])
        top = sorted(g, key=lambda o: -(o["confidence"] or 0))[:3]
        timeline.append({"month": m, "count": len(g), "articles": len({o["article_id"] for o in g}),
                         "modalities": dict(mods), "highlights": [brief(o) for o in top]})
    co = Counter()
    for r in conn.execute("""SELECT ot2.theme_id, count(DISTINCT o.article_id) c FROM observation_themes ot1
            JOIN observations o ON o.id=ot1.observation_id
            JOIN observations o2 ON o2.article_id=o.article_id
            JOIN observation_themes ot2 ON ot2.observation_id=o2.id
            WHERE ot1.theme_id=? AND ot2.theme_id!=? GROUP BY ot2.theme_id""", (theme_id, theme_id)):
        co[r[0]] = r[1]
    related = [{"id": tid, "name": conn.execute("SELECT name FROM themes WHERE id=?", (tid,)).fetchone()[0], "shared_articles": c}
               for tid, c in co.most_common(5)]
    synth = conn.execute("SELECT * FROM theme_syntheses WHERE theme_id=? ORDER BY id DESC LIMIT 1", (theme_id,)).fetchone()
    return {
        "theme": t, "stage": stage, "stage_reason": why,
        "n_observations": len(obs), "articles": sorted(arts.values(), key=lambda a: a["date"] or ""),
        "first": obs[0]["date"] if obs else None, "last": obs[-1]["date"] if obs else None,
        "narrative": narrative(t["name"], obs, sigs, evolves, contra),
        "current_state": sorted(current, key=lambda c: STAGE_ORDER.index(c["stage"]))[:6],
        "developments": evolves[-8:],
        "strongest_signals": [s for s in sigs if s["stage"] in ("strengthening", "established", "emerging")][:5],
        "weakening_signals": [s for s in sigs if s["stage"] in ("weakening", "obsolete")][:5],
        "competing_interpretations": competing[:5],
        "contradictions": contra,
        "unresolved_questions": [brief(o) for o in obs if o["type"] in ("question", "uncertainty")][-8:],
        "evidence": [brief(o) for o in sorted(obs, key=lambda o: -(o["confidence"] or 0))
                     if o["epistemic"] == "source_fact"][:8],
        "predictions": [brief(o) for o in obs if o["type"] == "prediction"],
        "signals": sigs, "timeline": timeline, "related_themes": related,
        "ai_synthesis": {"created_at": synth["created_at"], "method": synth["method"],
                         **db.loads(synth["content_json"], {})} if synth else None,
    }


def narrative(name, obs, sigs, evolves, contra):
    """Templated, citation-bearing summary (used when no LLM is configured)."""
    if not obs:
        return []
    arts = {o["article_id"] for o in obs}
    pubs = sorted({o["publication"] for o in obs if o["publication"]})
    parts = [{"text": f"{len(obs)} observations from {len(arts)} articles ({', '.join(pubs)}) between "
                      f"{obs[0]['date']} and {obs[-1]['date']}.", "cites": []}]
    for s in sigs[:4]:
        tr = s["trajectory"]
        mods = [o["modality"] for o in tr if o["modality"]]
        path = " \u2192 ".join(dict.fromkeys(mods)) if mods else "no stage language"
        parts.append({"text": f"Signal \u201c{s['key']}\u201d is {s['stage']} ({s['reason']}); stage language: {path}. "
                              f"Latest: {tr[-1]['statement']}", "cites": [tr[0]["id"], tr[-1]["id"]]})
    if contra:
        c = contra[0]
        parts.append({"text": f"Sources disagree: \u201c{c['src']['statement']}\u201d vs \u201c{c['dst']['statement']}\u201d.",
                      "cites": [c["src"]["id"], c["dst"]["id"]]})
    return parts


# ---------- patterns ----------

def _window(obs, days, ref):
    cur = [o for o in obs if d(o["date"]) and (ref - d(o["date"])).days <= days]
    prev = [o for o in obs if d(o["date"]) and days < (ref - d(o["date"])).days <= 2 * days]
    return cur, prev


def patterns(conn, days=90):
    ref = today()
    obs = all_obs(conn)
    byid = {o["id"]: o for o in obs}
    themes = db.rows(conn.execute("SELECT * FROM themes WHERE status='active'"))
    tmap = defaultdict(set)
    for r in conn.execute("SELECT observation_id, theme_id FROM observation_themes"):
        tmap[r[0]].add(r[1])
    tname = {t["id"]: t["name"] for t in themes}
    cur, prev = _window(obs, days, ref)

    # themes appearing more / less often
    def theme_articles(group):
        c = defaultdict(set)
        for o in group:
            for t in tmap[o["id"]]:
                if t in tname:
                    c[t].add(o["article_id"])
        return {t: len(a) for t, a in c.items()}
    ca, pa = theme_articles(cur), theme_articles(prev)
    trend = sorted([{"theme_id": t, "name": tname[t], "current": ca.get(t, 0), "previous": pa.get(t, 0),
                     "delta": ca.get(t, 0) - pa.get(t, 0)} for t in tname if ca.get(t) or pa.get(t)],
                   key=lambda x: -x["delta"])

    # signal stages across the corpus
    sigs = signals_for(obs, ref)
    strengthened = [s for s in sigs if s["stage"] == "strengthening" and d(s["last"]) and (ref - d(s["last"])).days <= days]
    weakened = [s for s in sigs if s["stage"] in ("weakening", "obsolete")]

    # theme co-occurrence (articles carrying both themes)
    art_themes = defaultdict(set)
    for o in obs:
        art_themes[o["article_id"]] |= {t for t in tmap[o["id"]] if t in tname}
    pair = Counter()
    for ts in art_themes.values():
        for a, b in combinations(sorted(ts), 2):
            pair[(a, b)] += 1
    cooc = [{"a": tname[a], "b": tname[b], "a_id": a, "b_id": b, "articles": n} for (a, b), n in pair.most_common(8) if n >= 1]

    # entity centrality: mentions now vs before + how many themes they bridge
    ent_rows = db.rows(conn.execute("""SELECT e.name, e.kind, oe.observation_id FROM observation_entities oe
                                       JOIN entities e ON e.id=oe.entity_id"""))
    ent = defaultdict(lambda: {"cur": set(), "prev": set(), "all": set(), "themes": set(), "obs": []})
    for r in ent_rows:
        o = byid.get(r["observation_id"])
        if not o:
            continue
        e = ent[(r["name"], r["kind"])]
        e["all"].add(o["article_id"])
        e["themes"] |= {tname[t] for t in tmap[o["id"]] if t in tname}
        e["obs"].append(o["id"])
        dd = d(o["date"])
        if dd and (ref - dd).days <= days:
            e["cur"].add(o["article_id"])
        elif dd and (ref - dd).days <= 2 * days:
            e["prev"].add(o["article_id"])
    entities = sorted([{"name": n, "kind": k, "articles": len(v["all"]), "current": len(v["cur"]),
                        "previous": len(v["prev"]), "themes": sorted(v["themes"]), "obs": v["obs"][-3:]}
                       for (n, k), v in ent.items() if len(v["all"]) >= 2],
                      key=lambda e: (-(e["current"] - e["previous"]), -e["articles"]))

    # predictions
    ls = links(conn)
    preds = []
    for o in obs:
        if o["type"] != "prediction":
            continue
        ev = [{"relation": l["relation"], "obs": brief(byid[l["dst_id"]])} for l in ls
              if l["src_id"] == o["id"] and l["relation"] in ("supports", "contradicts") and l["dst_id"] in byid
              and not (l["origin"] == "auto" and (l["score"] or 0) < 0.6)]
        preds.append({**brief(o), "evidence": ev})

    # disagreements between publications
    disagree = []
    for l in ls:
        if l["relation"] != "contradicts" or l["src_id"] not in byid or l["dst_id"] not in byid:
            continue
        a, b = byid[l["src_id"]], byid[l["dst_id"]]
        disagree.append({"note": l["note"], "a": brief(a), "b": brief(b),
                         "cross_publication": a["publication"] != b["publication"]})
    disagree.sort(key=lambda x: not x["cross_publication"])

    # assumptions recurring across unrelated articles (different themes)
    assumptions = [o for o in obs if o["type"] == "assumption"]
    rec = []
    from .text import embed, cosine
    vec = {o["id"]: embed(o["statement"]) for o in assumptions}
    used = set()
    for a in assumptions:
        if a["id"] in used:
            continue
        group = [a] + [b for b in assumptions if b["id"] != a["id"] and b["article_id"] != a["article_id"]
                       and b["id"] not in used and (cosine(vec[a["id"]], vec[b["id"]]) > 0.3
                                                   or (a["signal_key"] and a["signal_key"] == b["signal_key"]))]
        if len({g["article_id"] for g in group}) >= 2:
            used |= {g["id"] for g in group}
            ths = set()
            for g in group:
                ths |= {tname[t] for t in tmap[g["id"]] if t in tname}
            rec.append({"signal": a["signal_key"], "themes": sorted(ths), "obs": [brief(g) for g in group]})

    # easy to miss: links that cross theme boundaries + entities bridging several themes
    cross = []
    for l in ls:
        a, b = byid.get(l["src_id"]), byid.get(l["dst_id"])
        if not a or not b or a["article_id"] == b["article_id"]:
            continue
        ta, tb = tmap[a["id"]] & set(tname), tmap[b["id"]] & set(tname)
        if ta and tb and not (ta & tb):
            cross.append({"relation": l["relation"], "a": brief(a), "b": brief(b),
                          "themes": sorted({tname[t] for t in ta | tb})})
    bridges = [e for e in entities if len(e["themes"]) >= 2][:6]

    # what changed in the window
    new_sig = [s for s in sigs if d(s["first"]) and (ref - d(s["first"])).days <= days]
    resolved = [p for p in preds if p["evidence"] and any(d(e["obs"]["date"]) and (ref - d(e["obs"]["date"])).days <= days
                                                          for e in p["evidence"])]
    changed = {
        "articles": len({o["article_id"] for o in cur}),
        "new_signals": [{"key": s["key"], "stage": s["stage"], "first": s["first"], "obs": s["trajectory"][0]} for s in new_sig][:6],
        "stage_shifts": [{"key": s["key"], "stage": s["stage"], "reason": s["reason"], "obs": s["trajectory"][-1]}
                         for s in sigs if s["stage"] in ("strengthening", "weakening") and d(s["last"])
                         and (ref - d(s["last"])).days <= days][:6],
        "predictions_tested": resolved[:6],
        "new_predictions": [brief(o) for o in cur if o["type"] == "prediction"][:6],
    }
    return {"window_days": days, "today": ref.isoformat(), "theme_trend": trend,
            "strengthened": strengthened[:6], "weakened": weakened[:6], "cooccurrence": cooc,
            "entities": entities[:12], "bridging_entities": bridges, "predictions": preds,
            "disagreements": disagree[:8], "recurring_assumptions": rec[:6],
            "cross_theme_links": cross[:6], "changed": changed}


def stats(conn):
    arts = db.rows(conn.execute("""SELECT a.id, a.date, p.name AS publication FROM articles a
                                   LEFT JOIN publications p ON p.id=a.publication_id"""))
    by_month = Counter((a["date"] or "unknown")[:7] for a in arts)
    rows = db.rows(conn.execute("""SELECT t.name, substr(o.date,1,7) m, count(DISTINCT o.article_id) c
        FROM observation_themes ot JOIN themes t ON t.id=ot.theme_id AND t.status='active'
        JOIN observations o ON o.id=ot.observation_id GROUP BY t.name, m"""))
    theme_month = defaultdict(dict)
    for r in rows:
        theme_month[r["name"]][r["m"]] = r["c"]
    pub_theme = db.rows(conn.execute("""SELECT p.name pub, t.name theme, count(DISTINCT a.id) c FROM articles a
        JOIN publications p ON p.id=a.publication_id JOIN observations o ON o.article_id=a.id
        JOIN observation_themes ot ON ot.observation_id=o.id JOIN themes t ON t.id=ot.theme_id AND t.status='active'
        GROUP BY p.name, t.name"""))
    pred = Counter(r[0] or "open" for r in conn.execute("SELECT prediction_status FROM observations WHERE type='prediction'"))
    epi = Counter(r[0] for r in conn.execute("SELECT epistemic FROM observations"))
    types = Counter(r[0] for r in conn.execute("SELECT type FROM observations"))
    ents = db.rows(conn.execute("""SELECT e.name, e.kind, count(DISTINCT o.article_id) c FROM observation_entities oe
        JOIN entities e ON e.id=oe.entity_id JOIN observations o ON o.id=oe.observation_id
        GROUP BY e.id ORDER BY c DESC LIMIT 12"""))
    dims = db.rows(conn.execute("""SELECT dimension, count(*) c, count(DISTINCT article_id) a FROM observations
        WHERE dimension IS NOT NULL AND dimension!='' GROUP BY dimension ORDER BY a DESC, c DESC LIMIT 12"""))
    return {"articles": len(arts), "observations": sum(epi.values()), "months": sorted(by_month.items()),
            "theme_month": theme_month, "publication_theme": pub_theme, "predictions": dict(pred),
            "epistemic": dict(epi), "types": dict(types), "top_entities": ents, "recurring_dimensions": dims}
