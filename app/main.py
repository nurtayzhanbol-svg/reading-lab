import json
import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import analysis, chat, db, store
from .analyzers import PROMPT_VERSION, analyze, available
from .analyzers import llm
from .ingest import ingest, now

STATIC = os.path.join(os.path.dirname(__file__), "..", "static")
app = FastAPI(title="Reading Lab")
conn = db.connect()
db.init(conn)


@app.on_event("startup")
def _seed():
    if not conn.execute("SELECT 1 FROM articles LIMIT 1").fetchone() and os.environ.get("READINGLAB_NO_SEED") != "1":
        from seed.load import load
        load(conn)


def run_analysis(article_id, prefer="auto"):
    art = store.article_dict(conn, article_id)
    out, analyzer, model = analyze(art, store.analysis_context(conn), prefer)
    with db.tx(conn):
        store.save_analysis(conn, article_id, out, analyzer, model, PROMPT_VERSION)
        store.auto_assign(conn, article_id)
        store.link_article(conn, article_id)
        analysis.update_prediction_status(conn)


@app.get("/api/config")
def config():
    return available()


@app.get("/api/articles")
def list_articles(q: Optional[str] = None):
    rows = db.rows(conn.execute("""SELECT a.id, a.title, a.author, a.date, a.is_sample, p.name publication,
        i.id issue_id, i.title issue, length(a.text) chars,
        (SELECT analysis_runs.output_json FROM analysis_runs WHERE article_id=a.id AND is_current=1) run,
        (SELECT count(*) FROM observations WHERE article_id=a.id) n_obs
        FROM articles a LEFT JOIN publications p ON p.id=a.publication_id LEFT JOIN issues i ON i.id=a.issue_id
        ORDER BY a.date DESC, a.id DESC"""))
    tmap = {}
    for r in conn.execute("""SELECT o.article_id, t.id, t.name, count(*) c FROM observation_themes ot
            JOIN themes t ON t.id=ot.theme_id AND t.status='active' JOIN observations o ON o.id=ot.observation_id
            GROUP BY o.article_id, t.id ORDER BY c DESC"""):
        tmap.setdefault(r[0], []).append({"id": r[1], "name": r[2]})
    for r in rows:
        run = db.loads(r.pop("run"), {}) or {}
        r["thesis"] = run.get("thesis")
        r["themes"] = tmap.get(r["id"], [])[:4]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in (r["title"] + (r["thesis"] or "") + (r["publication"] or "")).lower()]
    return rows


def obs_with_meta(where, params):
    obs = analysis.all_obs(conn, where, params)
    ids = [o["id"] for o in obs]
    themes = {}
    for r in conn.execute(f"""SELECT ot.observation_id, t.id, t.name, ot.origin FROM observation_themes ot
            JOIN themes t ON t.id=ot.theme_id WHERE t.status='active' AND ot.observation_id IN ({','.join('?' * len(ids))})""", ids):
        themes.setdefault(r[0], []).append({"id": r[1], "name": r[2], "origin": r[3]})
    for o in obs:
        o["themes"] = themes.get(o["id"], [])
        o["entities"] = db.loads(o["entities"], [])
    return obs


@app.get("/api/articles/{aid}")
def get_article(aid: int):
    art = store.article_dict(conn, aid)
    if not art:
        raise HTTPException(404)
    passages = db.rows(conn.execute("SELECT id, idx, text, char_start, char_end FROM passages WHERE article_id=? ORDER BY idx", (aid,)))
    run = conn.execute("SELECT * FROM analysis_runs WHERE article_id=? AND is_current=1", (aid,)).fetchone()
    runs = db.rows(conn.execute("SELECT id, analyzer, model, prompt_version, created_at, is_current FROM analysis_runs WHERE article_id=? ORDER BY id DESC", (aid,)))
    out = db.loads(run["output_json"], {}) if run else {}
    obs = obs_with_meta("o.article_id=?", (aid,))
    ids = {o["id"] for o in obs}
    allb = {o["id"]: o for o in analysis.all_obs(conn)}
    conns = []
    for l in analysis.links(conn, ids):
        mine, other = (l["src_id"], l["dst_id"]) if l["src_id"] in ids else (l["dst_id"], l["src_id"])
        if other in ids or other not in allb:
            continue
        conns.append({"relation": l["relation"], "note": l["note"], "origin": l["origin"], "score": l["score"],
                      "direction": "later" if l["src_id"] == mine else "earlier",
                      "mine": mine, "other": analysis.brief(allb[other])})
    art.pop("raw_document_id", None)
    return {"article": art, "passages": passages, "thesis": out.get("thesis"), "dimensions": out.get("dimensions", []),
            "run": dict(run) | {"output_json": None} if run else None, "runs": runs,
            "observations": obs, "connections": conns}


@app.post("/api/articles")
async def add_article(text: Optional[str] = Form(None), file: Optional[UploadFile] = File(None),
                      title: Optional[str] = Form(None), publication: Optional[str] = Form(None),
                      author: Optional[str] = Form(None), date: Optional[str] = Form(None),
                      issue: Optional[str] = Form(None), analyzer: str = Form("auto")):
    if file is not None and file.filename:
        content = await file.read()
        kind = "pdf" if (file.filename.lower().endswith(".pdf") or file.content_type == "application/pdf") else "text"
        fname, mime = file.filename, file.content_type
    elif text and text.strip():
        content, kind, fname, mime = text.encode(), "text", None, "text/plain"
    else:
        raise HTTPException(400, "Provide text or a file")
    try:
        with db.tx(conn):
            aid = ingest(conn, kind, content, fname, mime, title or None, publication or None, author or None,
                         date or None, issue or None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    try:
        run_analysis(aid, analyzer)
    except Exception as e:
        return {"id": aid, "analysis_error": f"{type(e).__name__}: {e}"}
    return {"id": aid}


@app.post("/api/articles/{aid}/reanalyze")
def reanalyze(aid: int, analyzer: str = "auto"):
    run_analysis(aid, analyzer)
    return {"ok": True}


@app.delete("/api/articles/{aid}")
def delete_article(aid: int):
    with db.tx(conn):
        conn.execute("DELETE FROM articles WHERE id=?", (aid,))
        analysis.update_prediction_status(conn)
    return {"ok": True}


@app.get("/api/issues/{iid}")
def get_issue(iid: int):
    i = conn.execute("SELECT i.*, p.name publication FROM issues i LEFT JOIN publications p ON p.id=i.publication_id WHERE i.id=?", (iid,)).fetchone()
    if not i:
        raise HTTPException(404)
    arts = [a for a in list_articles() if a["issue_id"] == iid]
    return {"issue": dict(i), "articles": arts}


@app.get("/api/observations/{oid}")
def get_observation(oid: int):
    o = obs_with_meta("o.id=?", (oid,))
    if not o:
        raise HTTPException(404)
    o = o[0]
    p = conn.execute("SELECT * FROM passages WHERE id=?", (o["passage_id"],)).fetchone()
    o["passage"] = dict(p) if p else None
    run = conn.execute("SELECT analyzer, model, prompt_version, created_at FROM analysis_runs r JOIN observations o ON o.run_id=r.id WHERE o.id=?", (oid,)).fetchone()
    o["run"] = dict(run) if run else None
    allb = {x["id"]: x for x in analysis.all_obs(conn)}
    o["links"] = [{"relation": l["relation"], "note": l["note"], "origin": l["origin"],
                   "direction": "later" if l["src_id"] == oid else "earlier",
                   "other": analysis.brief(allb[l["dst_id"] if l["src_id"] == oid else l["src_id"]])}
                  for l in analysis.links(conn, [oid])]
    return o


@app.get("/api/themes")
def list_themes():
    out = []
    for t in db.rows(conn.execute("SELECT * FROM themes ORDER BY status, name")):
        obs = analysis.theme_obs(conn, t["id"])
        stage, why = analysis.theme_stage(obs)
        months = {}
        for o in obs:
            if o["date"]:
                months[o["date"][:7]] = months.get(o["date"][:7], 0) + 1
        out.append({**t, "n_obs": len(obs), "n_articles": len({o["article_id"] for o in obs}), "stage": stage,
                    "stage_reason": why, "months": months, "last": obs[-1]["date"] if obs else None})
    return out


class ThemeIn(BaseModel):
    name: str
    description: Optional[str] = None
    keywords: list[str] = []


@app.post("/api/themes")
def create_theme(t: ThemeIn):
    with db.tx(conn):
        tid = conn.execute("INSERT INTO themes(name,description,origin,status,keywords,created_at) VALUES (?,?,?,?,?,?)",
                           (t.name, t.description, "user", "active", json.dumps(t.keywords), now())).lastrowid
        store.relink_all(conn)
        analysis.update_prediction_status(conn)
    return {"id": tid}


class ThemePatch(BaseModel):
    status: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


@app.patch("/api/themes/{tid}")
def patch_theme(tid: int, p: ThemePatch):
    with db.tx(conn):
        for k in ("status", "name", "description"):
            v = getattr(p, k)
            if v is not None:
                conn.execute(f"UPDATE themes SET {k}=? WHERE id=?", (v, tid))
        if p.status == "active":
            store.relink_all(conn)
    return {"ok": True}


@app.get("/api/themes/{tid}")
def get_theme(tid: int):
    r = analysis.compute_theme(conn, tid)
    if not r:
        raise HTTPException(404)
    return r


@app.post("/api/themes/{tid}/synthesize")
def synthesize(tid: int):
    if not llm.provider():
        raise HTTPException(400, "No LLM configured; the structured synthesis is computed locally.")
    t = conn.execute("SELECT name FROM themes WHERE id=?", (tid,)).fetchone()
    obs = analysis.theme_obs(conn, tid)
    blocks = "\n".join(f"[O{o['id']}] ({o['date']}, {o['publication']}, {o['type']}, {o['epistemic']}, "
                       f"stage={o['modality'] or '-'}, signal={o['signal_key']}) {o['statement']}" for o in obs)
    res = llm.synthesize_theme(t["name"], blocks)
    with db.tx(conn):
        conn.execute("INSERT INTO theme_syntheses(theme_id,method,created_at,content_json) VALUES (?,?,?,?)",
                     (tid, f"llm:{llm.provider()}:{llm.model_name()}", now(), json.dumps(res)))
    return res


@app.get("/api/patterns")
def get_patterns(days: int = 90):
    return analysis.patterns(conn, days)


@app.get("/api/stats")
def get_stats():
    return analysis.stats(conn)


class AskIn(BaseModel):
    scope: str = "library"
    id: Optional[int] = None
    question: str


@app.post("/api/ask")
def ask(a: AskIn):
    return chat.ask(conn, a.scope, a.id, a.question)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))
