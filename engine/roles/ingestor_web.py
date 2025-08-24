# engine/roles/ingestor_web.py
"""Ingest public URLs -> clean text + short summary (deterministic)."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Dict, Any, List, Tuple
from pathlib import Path
from . import get_logger

UA = "enterprise-content-engine/1.0 (+https://localhost)"
MAX_BYTES = 2_000_000  # 2 MB max fetch
TIMEOUT = 20  # seconds

class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._in_script = False
        self._in_style = False
        self._in_title = False
        self.title_parts: List[str] = []
        self.parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in ("script", "noscript"):
            self._in_script = True
        elif t == "style":
            self._in_style = True
        elif t == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "noscript"):
            self._in_script = False
        elif t == "style":
            self._in_style = False
        elif t == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_script or self._in_style:
            return
        text = (data or "").strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        else:
            self.parts.append(text)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()


def _detect_charset(raw: bytes, header_charset: str | None) -> str:
    # 1) HTTP header if present
    if header_charset:
        return header_charset
    # 2) meta charset in first 4KB
    head = raw[:4096].decode("ascii", errors="ignore")
    m = re.search(r'charset=["\']?([A-Za-z0-9_\-]+)', head, flags=re.I)
    if m:
        return m.group(1)
    # 3) default
    return "utf-8"


def _fetch(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read(MAX_BYTES)
        # headers may be http.client.HTTPMessage
        hdrs = getattr(resp, "headers", None)
        header_charset = None
        if hdrs is not None:
            try:
                header_charset = hdrs.get_content_charset()
            except Exception:
                header_charset = None
    charset = _detect_charset(raw, header_charset)
    return raw.decode(charset, errors="replace")


def _extract(html: str) -> Tuple[str, str]:
    p = _StripHTML()
    p.feed(html)
    # collapse whitespace
    text = " ".join(p.parts)
    text = re.sub(r"\s{2,}", " ", text).strip()
    title = p.title or ""
    return (title, text)


def _summarize(text: str, max_sentences: int = 5) -> str:
    # Simple extractive summary: first N sufficiently-long sentences
    sents = re.split(r"(?<=[.!?])\s+", text)
    picked: List[str] = []
    for s in sents:
        if len(s.split()) >= 7:
            picked.append(s.strip())
        if len(picked) >= max_sentences:
            break
    summary = " ".join(picked).strip()
    return summary


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_logger("ingestor_web")
    urls_path = Path("intake/web/urls.txt")
    prompts_path = Path("intake/web/prompts.md")

    if not urls_path.exists():
        logger.info("no URLs in intake/web/urls.txt")
        return {"web_docs": []}

    urls = [
        ln.strip()
        for ln in urls_path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]

    if not urls:
        logger.info("no usable URLs in intake/web/urls.txt")
        return {"web_docs": []}

    notes = prompts_path.read_text(encoding="utf-8") if prompts_path.exists() else ""

    docs: List[Dict[str, Any]] = []
    for u in urls:
        try:
            html = _fetch(u)
            title, text = _extract(html)
            summary = _summarize(text)
            docs.append({
                "url": u,
                "title": title or u,
                "summary": summary,
                "text": text[:200_000],  # hard cap to keep context small
                "notes": notes,
            })
            logger.info("ingested: %s", u)
        except (HTTPError, URLError) as e:
            logger.info("failed ingest %s: %s", u, e)
        except Exception as e:
            logger.info("failed ingest %s: %s", u, e)

    return {"web_docs": docs}
