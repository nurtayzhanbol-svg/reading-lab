"""Deterministic offline analyzer. Much weaker than an LLM: it selects and classifies
verbatim sentences using cue words. Every observation is a quoted sentence, so
provenance is exact; statements are the sentences themselves (no paraphrase)."""
import re
from collections import Counter

import numpy as np

from ..text import embed, sentences, tokens

CUES = [
    ("prediction", 3, r"\b(will|expects?|expected to|forecast|projected|by 20\d\d|likely to|set to|predict)"),
    ("uncertainty", 4, r"\b(uncertain|unclear|unknown|remains to be seen|not clear|no one knows)\b"),
    ("uncertainty", 2, r"\b(may|might|could|risk|depends on)\b"),
    ("assumption", 2, r"\b(assum|presum|takes for granted|if .* then|provided that|on the premise)"),
    ("counterargument", 3, r"\b(critics|sceptics|skeptics|opponents|others argue|on the other hand|yet |but critics)\b"),
    ("question", 3, r"\?$"),
    ("event", 2, r"\b(announced|agreed|signed|approved|launched|voted|met|unveiled|opened|cancelled|have committed|has committed|decided)\b"),
    ("evidence", 2, r"(\d+(\.\d+)?\s?(%|per cent|percent|bn|billion|million|trillion|gigawatt|GW|TWh))|\b(data|survey|study|figures|according to|doubled|tripled|halved|rose|fell|risen|fallen)\b"),
    ("implication", 2, r"\b(means that|implies|as a result|consequence|therefore|so that|which would)\b"),
    ("argument", 1, r"\b(because|argues?|the case for|the reason|should|must)\b"),
]
MODALITY_CUES = [
    ("reversed", r"\b(scrapped|abandoned|reversed|cancel+ed|withdrew|u-turn)\b"),
    ("doubted", r"\b(doubt|sceptic|skeptic|unlikely|overstated|hype|fail(ed|ing)? to)\b"),
    ("constrained", r"\b(bottleneck|constraint|shortage|cannot keep up|struggl|backlog|capacity)\b"),
    ("implemented", r"\b(began|delivered|built|opened|launched|came online|started|is now)\b"),
    ("committed", r"\b(committed|pledged|agreed|approved|signed|promised|budgeted)\b"),
    ("proposed", r"\b(proposed?|plans? to|calls? for|wants? to|aims? to)\b"),
    ("discussed", r"\b(discuss|debat|consider|talk of|mooted)\b"),
]
DIMENSIONS = {
    "economic mechanisms": "price cost demand supply inflation market margin subsidy tariff wage invest",
    "geopolitical incentives": "security alliance nato china russia war deterrence sovereignty rival",
    "technological constraints": "chip compute power grid capacity technology model data efficiency",
    "regulatory consequences": "regulat law rule approval licens antitrust policy mandate",
    "business implications": "compan firm revenue profit shareholder industry contract customer",
    "demographic effects": "population ageing birth fertility workforce migration retire",
    "institutional incentives": "government ministry parliament election budget bureaucr procurement",
    "risks": "risk danger threat fail shortage vulnerab",
}
COUNTRIES = set("""China Russia Ukraine Germany France Poland Britain UK Italy Spain Japan India America
United States US USA Europe EU Taiwan Korea Brazil Mexico Canada Sweden Finland Norway Denmark
Netherlands Ireland Israel Iran Turkey Saudi Arabia Texas Virginia Arizona Baltic Estonia Latvia
Lithuania""".split())
ORG_HINT = re.compile(r"\b(Inc|Corp|Group|Bank|Commission|Ministry|Council|Agency|Fund|Institute|"
                      r"NATO|OECD|IMF|Union|Authority|Parliament|Pentagon|University|Labs?|Energy)\b")
_ent = re.compile(r"\b([A-Z][a-zA-Z&\.\-]+(?:\s+(?:of\s+|de\s+)?[A-Z][a-zA-Z&\.\-]+)*)")
SKIP = set("The A An In On At But And Yet This That These Those It Its For If When While As Such Some Most "
           "Many Few One Two Three Last Next Since After Before Over Under Even Still Much More However Meanwhile "
           "Europe's".split())


def _entities(sent, first):
    out = []
    for m in _ent.finditer(sent):
        name = m.group(1).strip(". ")
        if m.start() == 0 and " " not in name:
            if name not in COUNTRIES:
                continue
        words = name.split()
        while words and words[0] in SKIP:
            words = words[1:]
        name = " ".join(words)
        if len(name) < 2 or name in SKIP:
            continue
        kind = "country" if name in COUNTRIES else "organization" if ORG_HINT.search(name) or name.isupper() else \
            "person" if len(words) == 2 else "concept"
        out.append({"name": name, "kind": kind})
    seen, uniq = set(), []
    for e in out:
        if e["name"].lower() not in seen:
            seen.add(e["name"].lower())
            uniq.append(e)
    return uniq


def _modality(s):
    for m, rx in MODALITY_CUES:
        if re.search(rx, s, re.I):
            return m
    return "none"


def _dimension(toks):
    best, score = "", 0
    for name, words in DIMENSIONS.items():
        sc = sum(1 for t in toks for w in words.split() if t.startswith(w))
        if sc > score:
            best, score = name, sc
    return best if score >= 2 else ""


def analyze(article, context):
    sents = sentences(article["text"])
    if not sents:
        return {"thesis": "", "dimensions": [], "observations": [], "suggested_themes": []}
    vecs = np.stack([embed(s) for s in sents])
    centroid = vecs.mean(axis=0)
    central = vecs @ centroid
    n_head = max(3, len(sents) // 5)
    has_num = np.array([0.15 if re.search(r"\d", x) else 0.0 for x in sents])
    title = (article.get("title") or "").strip().lower()
    short = np.array([1.0 if len(x) < 40 or x.strip().lower() == title or not x.rstrip().endswith((".", "!", "?", "\"", "”")) else 0.0 for x in sents])
    thesis_i = int(np.argmax((central - has_num - short)[:n_head]))
    scored = []
    for i, s in enumerate(sents):
        best, w = None, 0
        for typ, weight, rx in CUES:
            if re.search(rx, s, re.I) and weight > w:
                best, w = typ, weight
        typ = best or "claim"
        score = central[i] + 0.15 * w + (0.1 if i < 3 else 0)
        scored.append((score, i, typ))
    scored.sort(reverse=True)
    chosen, per_type = [], Counter()
    for score, i, typ in scored:
        if i == thesis_i or per_type[typ] >= 4 or len(sents[i]) < 40:
            continue
        per_type[typ] += 1
        chosen.append((i, typ))
        if len(chosen) >= 16:
            break
    chosen.sort()
    dims = Counter()
    obs = []
    for i, typ in [(thesis_i, "claim")] + chosen:
        s = sents[i]
        toks = tokens(s)
        dim = _dimension(toks)
        if dim:
            dims[dim] += 1
        reported = re.search(r"\d|\b(according to|said|says|reported|announced)\b", s, re.I)
        opinion = re.search(r"\b(argue|should|must|we think|in our view|seems|appears)\b", s, re.I)
        epi = "source_fact" if (typ in ("evidence", "event", "fact") or reported) and not opinion else "author_interpretation"
        obs.append({"type": typ, "statement": s, "epistemic": epi, "confidence": 0.5,
                    "modality": _modality(s), "dimension": dim, "quote": s,
                    "entities": _entities(s, i == 0), "themes": [], "signal": ""})
    kw = Counter(t for s in sents for t in set(tokens(s)) if len(t) > 4).most_common(3)
    return {
        "thesis": sents[thesis_i],
        "dimensions": [{"name": d, "why": f"{c} selected sentences use this vocabulary (keyword heuristic)."}
                       for d, c in dims.most_common(4)],
        "observations": obs,
        "suggested_themes": [{"name": " / ".join(w for w, _ in kw[:2]).title(),
                              "description": "Keyword cluster suggested by the offline analyzer."}] if kw else [],
    }
