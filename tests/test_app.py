import io
import os
import tempfile

import pytest

os.environ["READINGLAB_DB"] = os.path.join(tempfile.mkdtemp(), "test.sqlite")
for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(k, None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ARTICLE = """Shipping lines bet on a long Red Sea detour

Container shipping companies have committed to routing vessels around the Cape of Good Hope for the rest of the year. Freight rates between Shanghai and Rotterdam have roughly doubled since January.

Executives argue the detour is now the base case rather than a temporary disruption. Analysts expect rates to stay high until at least 2027, although new ship deliveries could create overcapacity.

The plan assumes that fuel prices remain stable. It is unclear whether insurers will return to the route if the conflict eases. If rates fall, carriers that ordered new ships may face losses."""


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        yield client


def test_seed_corpus_loaded(c):
    arts = c.get("/api/articles").json()
    assert len(arts) == 12
    assert all(a["n_obs"] > 0 for a in arts)


def test_observations_keep_exact_provenance(c):
    a = c.get("/api/articles/7").json()
    text = a["article"]["text"]
    for o in a["observations"]:
        assert o["epistemic"] in ("source_fact", "author_interpretation", "ai_inference")
        if o["quote_start"] is not None:
            assert text[o["quote_start"]:o["quote_end"]].lower() == o["quote"].lower()


def test_paste_ingest_offline_analysis(c):
    r = c.post("/api/articles", data={"text": ARTICLE, "publication": "Test Gazette", "date": "2026-09-30", "issue": "Test Gazette, 30 Sep 2026"})
    assert r.status_code == 200, r.text
    aid = r.json()["id"]
    a = c.get(f"/api/articles/{aid}").json()
    assert a["article"]["title"].startswith("Shipping lines")
    assert a["run"]["analyzer"] .startswith("local")
    types = {o["type"] for o in a["observations"]}
    assert "prediction" in types and "assumption" in types
    for o in a["observations"]:
        assert o["quote"] and o["passage_id"]
    # re-analysis keeps the raw document and adds a new run
    c.post(f"/api/articles/{aid}/reanalyze?analyzer=local")
    a2 = c.get(f"/api/articles/{aid}").json()
    assert len(a2["runs"]) == 2 and a2["article"]["text"] == a["article"]["text"]
    assert c.get(f"/api/issues/{a['article']['issue_id']}").json()["articles"]


def test_pdf_ingest(c):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    cv = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in ["Europe's grid operators plan record investment", "",
                 "Grid operators have committed to doubling investment in transmission lines by 2030.",
                 "Analysts expect connection queues to shrink only slowly because transformer supply remains constrained."]:
        cv.drawString(40, y, line); y -= 18
    cv.save()
    r = c.post("/api/articles", files={"file": ("grid.pdf", buf.getvalue(), "application/pdf")}, data={"date": "2026-10-01"})
    assert r.status_code == 200, r.text
    a = c.get(f"/api/articles/{r.json()['id']}").json()
    assert a["article"]["extractor"].startswith("pdf")
    assert "transmission lines" in a["article"]["text"]
    assert a["observations"]


def test_empty_ingest_rejected(c):
    assert c.post("/api/articles", data={"text": "   "}).status_code == 400


def test_themes_and_temporal_analysis(c):
    themes = c.get("/api/themes").json()
    names = {t["name"]: t for t in themes}
    assert {"European rearmament", "AI infrastructure", "GLP-1 drugs"} <= set(names)
    t = c.get(f"/api/themes/{names['European rearmament']['id']}").json()
    assert t["stage"] in ("emerging", "strengthening", "established", "weakening", "obsolete")
    assert t["developments"] and t["signals"] and t["timeline"]
    sig = next(s for s in t["signals"] if s["key"] == "artillery shell production")
    mods = [o["modality"] for o in sig["trajectory"] if o["modality"]]
    assert mods[0] == "proposed" and mods[-1] == "implemented"


def test_patterns(c):
    p = c.get("/api/patterns?days=365").json()
    assert p["recurring_assumptions"] and p["cross_theme_links"] and p["disagreements"]
    statuses = {x["prediction_status"] for x in p["predictions"]}
    assert {"supported", "contradicted", "open"} <= statuses


def test_ask_returns_citations(c):
    r = c.post("/api/ask", json={"scope": "library", "question": "Which predictions were supported by later articles?"}).json()
    assert r["citations"] and "[O" in r["answer"]
    tid = c.get("/api/themes").json()[0]["id"]
    r = c.post("/api/ask", json={"scope": "theme", "id": tid, "question": "What changed during the last 3 months?"}).json()
    assert r["answer"]
