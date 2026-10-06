"""SQLite storage. Layers are kept separate so analysis can be recomputed:

raw_documents -> articles/passages (extracted) -> analysis_runs -> observations
-> observation_links / observation_themes -> theme_syntheses (generated).
"""
import json
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("READINGLAB_DB", os.path.join(os.path.dirname(__file__), "..", "data", "readinglab.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS publications (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS issues (
  id INTEGER PRIMARY KEY, publication_id INTEGER REFERENCES publications(id),
  title TEXT NOT NULL, date TEXT, UNIQUE(publication_id, title)
);
-- Original uploads, never modified.
CREATE TABLE IF NOT EXISTS raw_documents (
  id INTEGER PRIMARY KEY, kind TEXT NOT NULL, filename TEXT, mime TEXT,
  content BLOB NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL
);
-- Extracted, normalised article text (derived from raw_documents by an extractor).
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY, raw_document_id INTEGER REFERENCES raw_documents(id),
  publication_id INTEGER REFERENCES publications(id), issue_id INTEGER REFERENCES issues(id),
  title TEXT NOT NULL, author TEXT, date TEXT, text TEXT NOT NULL,
  extractor TEXT NOT NULL, is_sample INTEGER DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS passages (
  id INTEGER PRIMARY KEY, article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  idx INTEGER NOT NULL, text TEXT NOT NULL, char_start INTEGER NOT NULL, char_end INTEGER NOT NULL
);
-- One row per analysis attempt; old runs are kept, one is current.
CREATE TABLE IF NOT EXISTS analysis_runs (
  id INTEGER PRIMARY KEY, article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  analyzer TEXT NOT NULL, model TEXT, prompt_version TEXT, created_at TEXT NOT NULL,
  output_json TEXT NOT NULL, is_current INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS themes (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT,
  origin TEXT NOT NULL DEFAULT 'user', status TEXT NOT NULL DEFAULT 'active',
  keywords TEXT DEFAULT '[]', created_at TEXT NOT NULL
);
-- Atomic observations. epistemic: source_fact | author_interpretation | ai_inference
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  type TEXT NOT NULL, dimension TEXT, statement TEXT NOT NULL,
  epistemic TEXT NOT NULL, confidence REAL, modality TEXT,
  passage_id INTEGER REFERENCES passages(id), quote TEXT, quote_start INTEGER, quote_end INTEGER,
  entities TEXT DEFAULT '[]', date TEXT, signal_key TEXT,
  prediction_status TEXT, embedding BLOB
);
CREATE TABLE IF NOT EXISTS observation_themes (
  observation_id INTEGER REFERENCES observations(id) ON DELETE CASCADE,
  theme_id INTEGER REFERENCES themes(id) ON DELETE CASCADE,
  weight REAL DEFAULT 1, origin TEXT, PRIMARY KEY (observation_id, theme_id)
);
-- relation: supports | contradicts | evolves | repeats | resolves
CREATE TABLE IF NOT EXISTS observation_links (
  id INTEGER PRIMARY KEY,
  src_id INTEGER REFERENCES observations(id) ON DELETE CASCADE,
  dst_id INTEGER REFERENCES observations(id) ON DELETE CASCADE,
  relation TEXT NOT NULL, note TEXT, score REAL, origin TEXT NOT NULL,
  UNIQUE(src_id, dst_id, relation)
);
CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, kind TEXT
);
CREATE TABLE IF NOT EXISTS observation_entities (
  observation_id INTEGER REFERENCES observations(id) ON DELETE CASCADE,
  entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
  PRIMARY KEY (observation_id, entity_id)
);
CREATE TABLE IF NOT EXISTS theme_syntheses (
  id INTEGER PRIMARY KEY, theme_id INTEGER REFERENCES themes(id) ON DELETE CASCADE,
  method TEXT NOT NULL, created_at TEXT NOT NULL, content_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_obs_article ON observations(article_id);
CREATE INDEX IF NOT EXISTS ix_obs_run ON observations(run_id);
CREATE INDEX IF NOT EXISTS ix_obs_signal ON observations(signal_key);
CREATE INDEX IF NOT EXISTS ix_pass_article ON passages(article_id);
"""


def connect(path=None):
    path = path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init(conn):
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def tx(conn):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def rows(cur):
    return [dict(r) for r in cur.fetchall()]


def loads(s, default=None):
    if s is None:
        return default
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return default
