"""Ingestion: raw upload -> stored raw document -> extracted text + passages.

Extractors are registered by kind so new formats (HTML, EPUB, ...) can be added.
"""
import hashlib
import io
import re
from datetime import datetime, timezone

EXTRACTORS = {}


def extractor(kind):
    def deco(fn):
        EXTRACTORS[kind] = fn
        return fn
    return deco


def _paragraphs_from_lines(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # de-hyphenate line breaks
    paras = []
    for block in re.split(r"\n\s*\n", text):
        p = " ".join(block.split())
        if p:
            paras.append(p)
    return paras


@extractor("text")
def extract_text(content: bytes):
    return _paragraphs_from_lines(content.decode("utf-8", errors="replace"))


@extractor("pdf")
def extract_pdf(content: bytes):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = [(p.extract_text() or "") for p in reader.pages]
    text = "\n\n".join(pages)
    paras = _paragraphs_from_lines(text)
    # PDFs often lack blank lines between paragraphs; split very long blocks on sentence-ending newlines.
    if len(paras) <= max(2, len(pages)):
        paras = []
        for page in pages:
            buf = []
            for line in page.splitlines():
                line = line.strip()
                if not line:
                    continue
                buf.append(line)
                if re.search(r"[.!?\"”]$", line) and len(" ".join(buf)) > 350:
                    paras.append(re.sub(r"(\w)- (\w)", r"\1\2", " ".join(buf)))
                    buf = []
            if buf:
                paras.append(" ".join(buf))
    return paras


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_or_create(conn, table, name, **extra):
    if not name:
        return None
    if table == "publications":
        r = conn.execute("SELECT id FROM publications WHERE lower(name)=lower(?)", (name,)).fetchone()
        if r:
            return r["id"]
        return conn.execute("INSERT INTO publications(name) VALUES (?)", (name,)).lastrowid
    raise ValueError(table)


def get_or_create_issue(conn, publication_id, title, date):
    if not title:
        return None
    r = conn.execute("SELECT id FROM issues WHERE publication_id IS ? AND lower(title)=lower(?)",
                     (publication_id, title)).fetchone()
    if r:
        return r["id"]
    return conn.execute("INSERT INTO issues(publication_id,title,date) VALUES (?,?,?)",
                        (publication_id, title, date)).lastrowid


def ingest(conn, kind, content: bytes, filename=None, mime=None, title=None, publication=None,
           author=None, date=None, issue=None, is_sample=False):
    if kind not in EXTRACTORS:
        raise ValueError(f"unsupported kind {kind}")
    paras = EXTRACTORS[kind](content)
    if not paras:
        raise ValueError("no text could be extracted")
    if not title:
        first = paras[0]
        if len(first) < 140 and not first.endswith("."):
            title = first
            paras = paras[1:] or paras
        else:
            title = (filename or first[:80]).rsplit(".", 1)[0]
    raw_id = conn.execute(
        "INSERT INTO raw_documents(kind,filename,mime,content,sha256,created_at) VALUES (?,?,?,?,?,?)",
        (kind, filename, mime, content, hashlib.sha256(content).hexdigest(), now())).lastrowid
    pub_id = get_or_create(conn, "publications", publication)
    issue_id = get_or_create_issue(conn, pub_id, issue, date)
    text = "\n\n".join(paras)
    art_id = conn.execute(
        "INSERT INTO articles(raw_document_id,publication_id,issue_id,title,author,date,text,extractor,is_sample,created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (raw_id, pub_id, issue_id, title, author, date, text, kind + "-v1", int(is_sample), now())).lastrowid
    pos = 0
    for i, p in enumerate(paras):
        conn.execute("INSERT INTO passages(article_id,idx,text,char_start,char_end) VALUES (?,?,?,?,?)",
                     (art_id, i, p, pos, pos + len(p)))
        pos += len(p) + 2
    return art_id
