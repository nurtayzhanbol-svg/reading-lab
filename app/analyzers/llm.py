"""LLM provider (OpenAI or Anthropic) using structured outputs. Configured via env:
OPENAI_API_KEY or ANTHROPIC_API_KEY, optional READINGLAB_MODEL."""
import json
import os

import httpx

from . import ANALYSIS_SCHEMA, SYSTEM_PROMPT

TIMEOUT = 180


def provider():
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def model_name():
    p = provider()
    if not p:
        return None
    return os.environ.get("READINGLAB_MODEL") or ("gpt-4.1" if p == "openai" else "claude-sonnet-4-5")


def structured(system, user, schema, name="output"):
    p = provider()
    if p == "openai":
        r = httpx.post("https://api.openai.com/v1/chat/completions", timeout=TIMEOUT,
                       headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                       json={"model": model_name(),
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                             "response_format": {"type": "json_schema",
                                                 "json_schema": {"name": name, "schema": schema, "strict": True}}})
        r.raise_for_status()
        return json.loads(r.json()["choices"][0]["message"]["content"])
    if p == "anthropic":
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=TIMEOUT,
                       headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                       json={"model": model_name(), "max_tokens": 8000, "system": system,
                             "messages": [{"role": "user", "content": user}],
                             "tools": [{"name": name, "description": "Return the structured result.", "input_schema": schema}],
                             "tool_choice": {"type": "tool", "name": name}})
        r.raise_for_status()
        for block in r.json()["content"]:
            if block.get("type") == "tool_use":
                return block["input"]
        raise RuntimeError("no tool output")
    raise RuntimeError("no LLM provider configured")


def analyze(article, context):
    user = (f"Known themes: {json.dumps(context.get('themes', []))}\n"
            f"Known signals: {json.dumps(context.get('signals', [])[:80])}\n\n"
            f"Publication: {article.get('publication') or 'unknown'}\nDate: {article.get('date') or 'unknown'}\n"
            f"Title: {article['title']}\n\nARTICLE:\n{article['text']}")
    return structured(SYSTEM_PROMPT, user, ANALYSIS_SCHEMA, "article_analysis")


ANSWER_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["answer", "citations"],
    "properties": {
        "answer": {"type": "string", "description": "Markdown answer. Cite observations inline as [O123]."},
        "citations": {"type": "array", "items": {"type": "integer"}},
    },
}


def answer(question, scope_desc, context_blocks):
    system = ("You answer questions about the user's personal reading corpus using ONLY the observations given. "
              "Cite every claim with observation ids like [O12]. Separate what sources reported, what authors "
              "argued, and your own inferences (label those 'Inference:'). Pay attention to dates: explain how "
              "things changed over time when relevant. If the corpus does not contain the answer, say so.")
    user = f"Scope: {scope_desc}\n\nOBSERVATIONS:\n{context_blocks}\n\nQUESTION: {question}"
    return structured(system, user, ANSWER_SCHEMA, "answer")


SYNTH_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["current_state", "how_it_changed", "competing_interpretations", "what_to_watch"],
    "properties": {k: {"type": "string", "description": "Markdown, cite [O123]."} for k in
                   ["current_state", "how_it_changed", "competing_interpretations", "what_to_watch"]},
}


def synthesize_theme(theme_name, context_blocks):
    system = ("Write a synthesis of a theme in the user's reading corpus from the dated observations given. "
              "Cite observation ids like [O12] for every statement. Be concise and analytical; note how the "
              "narrative evolved over time, which signals strengthened or weakened, and where sources disagree.")
    return structured(system, f"THEME: {theme_name}\n\nOBSERVATIONS (chronological):\n{context_blocks}",
                      SYNTH_SCHEMA, "theme_synthesis")
