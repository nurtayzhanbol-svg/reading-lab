"""Article analyzers. All analyzers return the same structured output (ANALYSIS_SCHEMA)."""

PROMPT_VERSION = "article-analysis-v2"

OBS_TYPES = ["claim", "evidence", "fact", "event", "argument", "assumption", "uncertainty",
             "prediction", "implication", "counterargument", "question", "insight", "dimension"]
EPISTEMIC = ["source_fact", "author_interpretation", "ai_inference"]
MODALITY = ["discussed", "proposed", "committed", "implemented", "constrained", "doubted", "reversed"]

ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["thesis", "dimensions", "observations", "suggested_themes"],
    "properties": {
        "thesis": {"type": "string", "description": "One or two sentences: the article's central argument."},
        "dimensions": {
            "type": "array",
            "description": "Analytical dimensions that are useful for THIS article (not a fixed taxonomy).",
            "items": {"type": "object", "additionalProperties": False, "required": ["name", "why"],
                      "properties": {"name": {"type": "string"}, "why": {"type": "string"}}}},
        "observations": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["type", "statement", "epistemic", "confidence", "modality", "dimension",
                             "quote", "entities", "themes", "signal"],
                "properties": {
                    "type": {"type": "string", "enum": OBS_TYPES},
                    "statement": {"type": "string", "description": "Atomic, self-contained statement."},
                    "epistemic": {"type": "string", "enum": EPISTEMIC,
                                  "description": "source_fact = reported fact/data; author_interpretation = the author's view; ai_inference = your own inference."},
                    "confidence": {"type": "number", "description": "0..1 confidence that the statement is a faithful reading of the source."},
                    "modality": {"type": "string", "enum": MODALITY + ["none"],
                                 "description": "Stage of the underlying development as described in the text."},
                    "dimension": {"type": "string", "description": "Name of one of the dimensions, or empty."},
                    "quote": {"type": "string", "description": "Exact verbatim span from the article supporting the statement."},
                    "entities": {"type": "array", "items": {
                        "type": "object", "additionalProperties": False, "required": ["name", "kind"],
                        "properties": {"name": {"type": "string"}, "kind": {"type": "string"}}}},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "signal": {"type": "string", "description": "Short lowercase label for the recurring development this observation is about, e.g. 'european defence spending'."},
                },
            },
        },
        "suggested_themes": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "description"],
            "properties": {"name": {"type": "string"}, "description": {"type": "string"}}}},
    },
}

SYSTEM_PROMPT = """You are an analytical reading assistant for a serious reader of long-form journalism.
Turn the article into 10-20 structured, atomic observations. Rules:
- Omit types that are not meaningfully present. Never invent facts.
- `statement`: a concise standalone sentence (max ~25 words) naming its subject, so it reads correctly
  outside the article. `quote`: an exact verbatim span of the article that supports it (copy characters exactly).
- `epistemic` must be classified carefully:
  * source_fact: checkable facts, data, figures and events the article reports (what happened, who did what).
  * author_interpretation: arguments, judgements, framings, forecasts and assumptions made by the author
    OR by people the article quotes ("executives argue", "analysts expect", "the plan assumes").
  * ai_inference: your own reading that the article does not state: unstated assumptions, second-order
    implications, tensions with known signals. Include 1-4 of these; quote the passage that prompted them.
- `confidence` (0-1) is how sure you are the statement is a faithful, well-supported reading. Calibrate:
  plain reported facts ~0.85-0.95, interpretations ~0.6-0.8, your inferences ~0.4-0.7. Avoid 1.0.
- Infer the analytical dimensions that suit this article (lowercase, 1-3 words, e.g. "economic mechanisms",
  "institutional incentives"), and attach observations to them via `dimension`.
- `modality` captures how far the development has gone: discussed, proposed, committed, implemented,
  constrained, doubted, reversed (or none).
- `signal`: a short lowercase label for the recurring development so it can be tracked across articles.
  Reuse a label from the known signals whenever the observation is about the same development.
- `themes`: use names from the known theme list when they fit; otherwise propose a new theme in
  suggested_themes (only if the article really opens a topic) and use that name."""


def available():
    from . import llm
    return {"llm": llm.provider() is not None, "provider": llm.provider(), "model": llm.model_name()}


def analyze(article, context, prefer="auto"):
    """Returns (output, analyzer_name, model)."""
    from . import llm, local
    if prefer != "local" and llm.provider():
        return llm.analyze(article, context), "llm:" + llm.provider(), llm.model_name()
    return local.analyze(article, context), "local-heuristic", "local-heuristic-v1"
