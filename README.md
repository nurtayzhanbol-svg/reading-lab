# Reading Lab

A local-first web app for analytical reading of long-form journalism. Articles are turned into
structured, provenance-linked observations that accumulate into themes, timelines and
cross-article patterns.

```
ingest → atomic observations (with exact source passages) → links between articles
       → themes → how themes change over time → corpus-level patterns → cited Q&A
```

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000
# open http://localhost:8000
```

On first start the database (`data/readinglab.sqlite`, override with `READINGLAB_DB`) is seeded
with 12 synthetic sample articles (Nov 2025 – Sep 2026, four themes, four fictional publications)
so the cross-article features can be explored right away. Set `READINGLAB_NO_SEED=1` to start empty.

### LLM (optional)

Without an API key everything runs offline: a deterministic heuristic analyzer extracts
observations from new articles, and questions are answered by assembling cited observations.
For model-quality analysis, theme syntheses and generated answers, set one of:

```bash
export OPENAI_API_KEY=...        # or
export ANTHROPIC_API_KEY=...
export READINGLAB_MODEL=...      # optional model override
```

All model calls use JSON-schema structured output. Articles can be re-analysed at any time;
the raw document is never modified and earlier analysis runs are kept.

## What's in it

- **Library**: articles grouped by month and issue. Add articles by pasting text or uploading a
  PDF, with optional title, publication, date, author and issue.
- **Article**: reading view with the extracted passages underlined (colour-coded as *reported*,
  *author's view* or *AI inference*). Analysis panel: thesis, inferred dimensions for this article,
  observations by type, connections to earlier and later articles, and Ask. Every observation opens
  its source passage. On mobile the analysis is a bottom sheet.
- **Themes**: evolving objects with a lifecycle stage (emerging / strengthening / established /
  weakening / obsolete) and a stated reason, current state, developments, a timeline, tracked
  signals with their trajectory (discussed → proposed → committed → implemented, or constrained /
  doubted / reversed), competing interpretations, contradictions, predictions, open questions and
  evidence. The AI suggests new themes, which you can accept or dismiss.
- **Patterns**: what changed in a time window, developments that show up in several themes,
  entities that connect themes, recurring assumptions, disagreements between sources, prediction
  outcomes (supported / contradicted / open), strengthening and weakening signals, theme
  co-occurrence, and a few corpus statistics.
- **Ask**: questions scoped to an article, issue, theme or the whole library. Time references
  ("six months ago", "last 3 months") are understood, and answers cite observations (`[O12]`)
  that open their source passages.

## Data model (`app/db.py`)

Each layer is stored separately, so analysis can be recomputed without touching the sources:

| Layer | Tables |
|---|---|
| Raw sources (immutable bytes + sha256) | `raw_documents` |
| Extracted content | `articles`, `passages` (paragraphs with character offsets) |
| Analysis history | `analysis_runs` (analyzer, model, prompt version, current flag) |
| Atomic knowledge | `observations` (type, epistemic class, confidence, modality, signal, quote + offsets), `entities` |
| Connections | `observation_links` (supports / contradicts / evolves / repeats; curated or auto) |
| Themes | `themes`, `observation_themes` |
| Generated syntheses | `theme_syntheses` |

The time model (`app/analysis.py`) is heuristic and always explains itself: a signal's stage comes
from how many articles mention it recently compared with earlier, how long ago it was last
mentioned, and how firmly the latest article describes it compared with the first one.

## Code map

- `app/ingest.py`: extractor registry (text, PDF via pypdf), passage segmentation
- `app/analyzers/`: analysis contract; `llm.py` (OpenAI/Anthropic structured outputs), `local.py` (offline)
- `app/store.py`: persistence, quote→passage resolution, theme assignment, cross-article linking
- `app/analysis.py`: theme synthesis, lifecycle stages, patterns, statistics, prediction tracking
- `app/chat.py`: scoped retrieval and cited answers
- `static/`: dependency-free SPA (hash routing, responsive)
- `seed/`: sample corpus with hand-written analyses and links

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

## Limitations

- The offline analyzer only scores sentences on cue words; it finds candidate claims and predictions
  but cannot judge them like a model can. The sample corpus uses hand-written analyses.
- Automatic links between articles come from embedding similarity plus a shared signal, so they
  can miss things or link things that aren't really related. Hand-curated links are labelled as such.
- Single-user, local only; no authentication.
