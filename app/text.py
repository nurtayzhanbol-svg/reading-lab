"""Small text utilities: tokenising, sentence splitting, hashed TF vectors.

The local embedding is a hashed bag of stemmed words + bigrams. It is only a
retrieval aid; the knowledge model is the structured observations and links.
"""
import hashlib
import math
import re

import numpy as np

DIM = 2048
STOP = set("""a about above after again against all am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have
having he her here hers herself him himself his how i if in into is it its itself just me more most my
myself no nor not now of off on once only or other our ours ourselves out over own same she should so some
such than that the their theirs them themselves then there these they this those through to too under until
up very was we were what when where which while who whom why will with would you your yours yourself also
may might must one two new said says say year years many much even still yet however would could
its it's than then there's whether within without across per via upon among amid like""".split())

_word = re.compile(r"[A-Za-z][A-Za-z\-']+|\d+(?:\.\d+)?%?")


def stem(w):
    w = w.lower().strip("'-")
    for suf in ("ations", "ation", "ments", "ment", "ings", "ing", "ies", "ers", "ed", "es", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(text):
    return [stem(t) for t in _word.findall(text or "") if t.lower() not in STOP and len(t) > 1]


def _h(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def embed(text):
    toks = tokens(text)
    v = np.zeros(DIM, dtype=np.float32)
    feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
    for f in feats:
        h = _h(f)
        v[h % DIM] += 1.0 if "_" not in f else 0.6
    n = np.linalg.norm(v)
    return v / n if n else v


def to_blob(v):
    return np.asarray(v, dtype=np.float32).tobytes()


def from_blob(b):
    return np.frombuffer(b, dtype=np.float32) if b else np.zeros(DIM, dtype=np.float32)


def cosine(a, b):
    return float(np.dot(a, b))


_sent = re.compile(r"(?<=[.!?])[\"”’)]?\s+(?=[\"“‘(]?[A-Z0-9])")


def sentences(text):
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if para:
            out.extend(s.strip() for s in _sent.split(para) if s.strip())
    return out


def keywords(texts, k=8):
    from collections import Counter
    c = Counter()
    for t in texts:
        c.update(set(tokens(t)))
    return [w for w, _ in c.most_common(k)]


def norm_ws(s):
    return " ".join((s or "").split())


def idf_weights(docs):
    from collections import Counter
    df = Counter()
    for d in docs:
        df.update(set(tokens(d)))
    n = max(len(docs), 1)
    return {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}
