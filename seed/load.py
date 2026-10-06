"""Load the synthetic sample corpus into the database."""
from app import analysis, db, store
from app.ingest import ingest, now

from .data import ARTICLES, LINKS, THEMES


def load(conn):
    with db.tx(conn):
        for name, desc, status, origin in THEMES:
            conn.execute("INSERT OR IGNORE INTO themes(name,description,origin,status,created_at) VALUES (?,?,?,?,?)",
                         (name, desc, origin, status, now()))
        keymap = {}
        for a in sorted(ARTICLES, key=lambda a: a["date"]):
            aid = ingest(conn, "text", a["text"].encode(), None, "text/plain", a["title"], a["publication"],
                         a.get("author"), a["date"], a.get("issue"), is_sample=True)
            out = {"thesis": a["thesis"], "dimensions": [{"name": n, "why": w} for n, w in a["dims"]],
                   "suggested_themes": [],
                   "observations": [{**{k: v for k, v in o.items() if k != "key"},
                                     "themes": o["themes"] or a["themes"],
                                     "modality": o["modality"] or "none"} for o in a["obs"]]}
            _, ids = store.save_analysis(conn, aid, out, "seed-curated", "hand-authored sample analysis",
                                         "article-analysis-v1", theme_origin=None)
            for o, oid in zip(a["obs"], ids):
                keymap[f"{a['slug']}:{o['key']}"] = oid
                q = conn.execute("SELECT quote FROM observations WHERE id=?", (oid,)).fetchone()[0]
                assert q and q.strip(" .") == o["quote"].strip(" ."), (a["slug"], o["key"], q, o["quote"])
        for src, dst, rel, note in LINKS:
            store.add_link(conn, keymap[src], keymap[dst], rel, note, 1.0, "seed-curated")
        for (aid,) in conn.execute("SELECT id FROM articles ORDER BY date").fetchall():
            store.link_article(conn, aid)
        analysis.update_prediction_status(conn)
