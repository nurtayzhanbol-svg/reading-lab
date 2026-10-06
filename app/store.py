"""Persisting analyses as observations, resolving provenance, linking across articles."""
import json
from difflib import SequenceMatcher

import numpy as np

from . import db
from .ingest import now
from .text import cosine, embed, from_blob, norm_ws, to_blob, tokens

MOD_RANK = {"discussed": 0, "proposed": 1, "committed": 2, "implemented": 3, "constrained": 3,
            "doubted": -1, "reversed": -2}


def article_dict(conn, article_id):
    a = conn.execute("""SELECT a.*, p.name AS publication, i.title AS issue FROM articles a
                        LEFT JOIN publications p ON p.id=a.publication_id LEFT JOIN issues i ON i.id=a.issue_id
                        WHERE a.id=?""", (article_id,)).fetchone()
    return dict(a) if a else None


def resolve_quote(conn, article_id, text, quote):
    """Return (passage_id, start, end, quote_found). Exact match first, then fuzzy best passage."""
    passages = db.rows(conn.execute("SELECT * FROM passages WHERE article_id=? ORDER BY idx", (article_id,)))
    q = norm_ws(quote).strip(" .\"'“”")
    if q:
        idx = text.find(q)
        if idx < 0:
            low = text.lower().find(q.lower())
            idx = low
        if idx >= 0:
            for p in passages:
                if p["char_start"] <= idx < p["char_end"] + 1:
                    return p["id"], idx, idx + len(q), True
    # fuzzy: best passage by token overlap, then best sentence-ish window inside it
    qt = set(tokens(quote))
    best, bs = None, 0.0
    for p in passages:
        pt = set(tokens(p["text"]))
        s = len(qt & pt) / (len(qt) or 1)
        if s > bs:
            best, bs = p, s
    if not best:
        return None, None, None, False
    sm = SequenceMatcher(None, best["text"].lower(), q.lower(), autojunk=False)
    m = sm.find_longest_match(0, len(best["text"]), 0, len(q))
    start = best["char_start"] + m.a
    return best["id"], start, start + max(m.size, 1), False


def theme_id_for(conn, name, create_origin=None, description=None):
    name = (name or "").strip()
    if not name:
        return None
    r = conn.execute("SELECT id FROM themes WHERE lower(name)=lower(?)", (name,)).fetchone()
    if r:
        return r["id"]
    if not create_origin:
        return None
    return conn.execute("INSERT INTO themes(name,description,origin,status,created_at) VALUES (?,?,?,?,?)",
                        (name, description, create_origin, "suggested" if create_origin == "ai" else "active",
                         now())).lastrowid


def entity_id(conn, name, kind):
    r = conn.execute("SELECT id FROM entities WHERE lower(name)=lower(?)", (name,)).fetchone()
    if r:
        return r["id"]
    return conn.execute("INSERT INTO entities(name,kind) VALUES (?,?)", (name, kind)).lastrowid


def analysis_context(conn):
    themes = [r["name"] for r in conn.execute("SELECT name FROM themes WHERE status!='rejected'")]
    signals = [r["signal_key"] for r in conn.execute(
        "SELECT signal_key, count(*) c FROM observations WHERE signal_key IS NOT NULL AND signal_key!='' "
        "GROUP BY signal_key ORDER BY c DESC")]
    return {"themes": themes, "signals": signals}


def save_analysis(conn, article_id, output, analyzer, model, prompt_version, theme_origin="ai"):
    art = article_dict(conn, article_id)
    conn.execute("UPDATE analysis_runs SET is_current=0 WHERE article_id=?", (article_id,))
    # Observations of superseded runs are regenerable from analysis_runs.output_json.
    conn.execute("DELETE FROM observations WHERE article_id=?", (article_id,))
    run_id = conn.execute(
        "INSERT INTO analysis_runs(article_id,analyzer,model,prompt_version,created_at,output_json,is_current)"
        " VALUES (?,?,?,?,?,?,1)", (article_id, analyzer, model, prompt_version, now(), json.dumps(output))).lastrowid
    for t in output.get("suggested_themes", []):
        theme_id_for(conn, t["name"], create_origin=theme_origin, description=t.get("description"))
    ids = []
    for o in output.get("observations", []):
        pid, qs, qe, _ = resolve_quote(conn, article_id, art["text"], o.get("quote") or o["statement"])
        quote = art["text"][qs:qe] if qs is not None else None
        sig = (o.get("signal") or "").strip().lower() or None
        mod = o.get("modality") if o.get("modality") in MOD_RANK else None
        oid = conn.execute(
            "INSERT INTO observations(run_id,article_id,type,dimension,statement,epistemic,confidence,modality,"
            "passage_id,quote,quote_start,quote_end,entities,date,signal_key,embedding)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, article_id, o["type"], o.get("dimension") or None, o["statement"], o["epistemic"],
             o.get("confidence"), mod, pid, quote, qs, qe, json.dumps(o.get("entities", [])), art["date"], sig,
             to_blob(embed(o["statement"] + " " + (o.get("quote") or ""))))).lastrowid
        for e in o.get("entities", []):
            conn.execute("INSERT OR IGNORE INTO observation_entities VALUES (?,?)",
                         (oid, entity_id(conn, e["name"], e.get("kind"))))
        for tn in o.get("themes", []):
            tid = theme_id_for(conn, tn, create_origin=theme_origin)
            if tid:
                conn.execute("INSERT OR IGNORE INTO observation_themes VALUES (?,?,1,?)", (oid, tid, "analysis"))
        ids.append(oid)
    return run_id, ids


def _current_obs(conn, where="1=1", params=()):
    q = f"""SELECT o.*, p.name AS publication FROM observations o JOIN articles a ON a.id=o.article_id
            LEFT JOIN publications p ON p.id=a.publication_id WHERE {where}"""
    return db.rows(conn.execute(q, params))


def theme_centroids(conn):
    out = {}
    for t in db.rows(conn.execute("SELECT * FROM themes WHERE status='active'")):
        vecs = [from_blob(r["embedding"]) for r in conn.execute(
            "SELECT o.embedding FROM observations o JOIN observation_themes ot ON ot.observation_id=o.id "
            "WHERE ot.theme_id=? AND ot.origin!='auto'", (t["id"],))]
        base = embed(t["name"] + " " + (t["description"] or "") + " " + " ".join(db.loads(t["keywords"], [])))
        v = (np.mean(vecs, axis=0) * 0.7 + base * 0.3) if vecs else base
        n = np.linalg.norm(v)
        out[t["id"]] = v / n if n else v
    return out


def auto_assign(conn, article_id, threshold=0.22):
    """Assign themes to un-themed observations by similarity; derive missing signal keys."""
    cents = theme_centroids(conn)
    obs = _current_obs(conn, "o.article_id=?", (article_id,))
    others = _current_obs(conn, "o.article_id!=? AND o.signal_key IS NOT NULL", (article_id,))
    other_vecs = [(o, from_blob(o["embedding"])) for o in others]
    art_themes = article_theme_ids(conn, article_id)
    for o in obs:
        v = from_blob(o["embedding"])
        has = conn.execute("SELECT 1 FROM observation_themes WHERE observation_id=?", (o["id"],)).fetchone()
        if not has and cents:
            scored = sorted(((cosine(v, c) + (0.05 if tid in art_themes else 0), tid) for tid, c in cents.items()),
                            reverse=True)
            if scored[0][0] >= threshold:
                conn.execute("INSERT OR IGNORE INTO observation_themes VALUES (?,?,?,?)",
                             (o["id"], scored[0][1], round(scored[0][0], 3), "auto"))
        if not o["signal_key"]:
            best, bs = None, 0.0
            for p, pv in other_vecs:
                s = cosine(v, pv)
                if s > bs:
                    best, bs = p, s
            if best and bs >= 0.42:
                key = best["signal_key"]
            else:
                key = " ".join(sorted(set(t for t in tokens(o["statement"]) if len(t) > 3 and not t.isdigit()),
                                      key=lambda t: -len(t))[:3])
            conn.execute("UPDATE observations SET signal_key=? WHERE id=?", (key or None, o["id"]))


def article_theme_ids(conn, article_id):
    return {r["theme_id"] for r in conn.execute(
        "SELECT DISTINCT ot.theme_id FROM observation_themes ot JOIN observations o ON o.id=ot.observation_id "
        "WHERE o.article_id=?", (article_id,))}


def add_link(conn, src, dst, relation, note=None, score=None, origin="auto"):
    if src == dst:
        return
    conn.execute("INSERT OR IGNORE INTO observation_links(src_id,dst_id,relation,note,score,origin)"
                 " VALUES (?,?,?,?,?,?)", (src, dst, relation, note, score, origin))


def link_article(conn, article_id, max_links=2):
    """Connect this article's observations to observations in other articles.
    Links always point from the older observation to the newer one."""
    conn.execute("DELETE FROM observation_links WHERE origin='auto' AND (src_id IN (SELECT id FROM observations "
                 "WHERE article_id=?) OR dst_id IN (SELECT id FROM observations WHERE article_id=?))",
                 (article_id, article_id))
    mine = _current_obs(conn, "o.article_id=?", (article_id,))
    others = _current_obs(conn, "o.article_id!=?", (article_id,))
    ov = [(p, from_blob(p["embedding"])) for p in others]
    for o in mine:
        v = from_blob(o["embedding"])
        cands = []
        for p, pv in ov:
            sim = cosine(v, pv)
            same = o["signal_key"] and o["signal_key"] == p["signal_key"]
            if not ((same and sim >= 0.2) or sim >= 0.6):
                continue
            cands.append((sim + (0.3 if same else 0), sim, same, p))
        cands.sort(key=lambda c: -c[0])
        for score, sim, same, p in cands[:max_links]:
            old, new = (p, o) if (p["date"] or "") <= (o["date"] or "") else (o, p)
            if conn.execute("SELECT 1 FROM observation_links WHERE (src_id=? AND dst_id=?) OR (src_id=? AND dst_id=?)",
                            (old["id"], new["id"], new["id"], old["id"])).fetchone():
                continue
            rel, note = _relation(old, new, same, sim)
            if rel:
                add_link(conn, old["id"], new["id"], rel, note, round(score, 3))


def _relation(old, new, same_signal, sim):
    mo, mn = old["modality"], new["modality"]
    if old["type"] == "prediction" and (new["date"] or "") > (old["date"] or ""):
        if mn in ("doubted", "reversed"):
            return "contradicts", "later source casts doubt on this prediction"
        if new["epistemic"] == "source_fact" and same_signal and MOD_RANK.get(mn, -9) >= 2:
            return "supports", "later reported development is consistent with this prediction"
    if same_signal and mo and mn and mo != mn:
        if (MOD_RANK[mo] >= 2 and MOD_RANK[mn] < 0) or (MOD_RANK[mn] >= 2 and MOD_RANK[mo] < 0):
            return "contradicts", f"{mo} vs {mn}"
        return "evolves", f"{mo} \u2192 {mn}"
    if sim >= 0.5 or same_signal:
        return ("repeats" if old["type"] == new["type"] else "supports"), None
    return None, None


def relink_all(conn):
    for r in conn.execute("SELECT id FROM articles ORDER BY date").fetchall():
        auto_assign(conn, r["id"])
    for r in conn.execute("SELECT id FROM articles ORDER BY date").fetchall():
        link_article(conn, r["id"])
