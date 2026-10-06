"""Article analyzers. All analyzers return the same structured output (ANALYSIS_SCHEMA)."""

PROMPT_VERSION = "article-analysis-v1"

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
Turn the article into structured, atomic observations. Rules:
- Omit fields/types that are not meaningfully present. Never invent.
- Every observation must quote an exact verbatim span of the article as provenance.
- Distinguish source_fact (reported facts/data), author_interpretation (the author's arguments and framing)
  and ai_inference (your own inferences, e.g. second-order effects, unstated assumptions).
- Infer the analytical dimensions that suit this article (e.g. economic mechanisms, institutional incentives),
  and attach observations to them via `dimension`.
- `modality` captures how far the development has gone: discussed, proposed, committed, implemented,
  constrained, doubted, reversed (or none).
- `signal` names the recurring development so it can be tracked across articles; reuse labels from the
  list of known signals when the observation is about the same development.
- Use theme names from the known theme list when appropriate; propose new ones in suggested_themes."""


def available():
    from . import llm
    return {"llm": llm.provider() is not None, "provider": llm.provider(), "model": llm.model_name()}


def analyze(article, context, prefer="auto"):
    """Returns (output, analyzer_name, model)."""
    from . import llm, local
    if prefer != "local" and llm.provider():
        return llm.analyze(article, context), "llm:" + llm.provider(), llm.model_name()
    return local.analyze(article, context), "local-heuristic", "local-heuristic-v1"
