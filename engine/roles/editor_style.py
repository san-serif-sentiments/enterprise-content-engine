from __future__ import annotations
import logging, re
from typing import Dict, Any, Tuple
from pathlib import Path
import json

log = logging.getLogger("editor_style")

BASE = Path(__file__).resolve().parents[2]
STYLE_PATHS = [
    BASE / "docs/governance/style.yml",
    BASE / "engine/policies/style.yml",
]

def _load_style() -> Dict[str, Any]:
    # Support yaml or json-in-yaml
    text = ""
    for p in STYLE_PATHS:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            break
    if not text:
        return {}
    try:
        import yaml  # optional
        return yaml.safe_load(text)
    except Exception:
        return json.loads(text)  # if stored as JSON

def _to_sentence_case(h: str) -> str:
    h = h.strip()
    if not h: return h
    return h[0].upper() + h[1:].lower()

def _enforce_active_voice(text: str) -> str:
    # Heuristic: trim “is/are/was/were ... by” passives
    return re.sub(r"\b(is|are|was|were)\s+(\w+ed)\s+by\b", r"\2", text, flags=re.I)

def _limit_sentence_length(text: str, max_words: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    fixed = []
    for s in parts:
        words = s.split()
        if len(words) > max_words:
            # split long sentences at a comma/semicolon if possible
            s = re.sub(r",\s+", ". ", s, count=1)
        fixed.append(s)
    return " ".join(fixed)

def _remove_forbidden(text: str, forbidden: list[str]) -> str:
    for term in forbidden:
        text = re.sub(rf"\b{re.escape(term)}\b", "", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()

def _enforce_tense_present(text: str) -> str:
    # Heuristic nudge: replace “will ” with present
    return re.sub(r"\bwill\s+(\w+)", r"\1", text, flags=re.I)

def _process_markdown(md: str, style: Dict[str, Any]) -> str:
    if style.get("active_voice"): md = _enforce_active_voice(md)
    if style.get("tense") == "present": md = _enforce_tense_present(md)
    if (fw := style.get("forbidden")): md = _remove_forbidden(md, fw)
    if (mx := style.get("sentence_max")): md = _limit_sentence_length(md, int(mx))
    # Headings to sentence-case
    lines = []
    for line in md.splitlines():
        if line.startswith("#"):
            head = line.lstrip("#").strip()
            fixed = _to_sentence_case(head)
            line = "#" * (len(line) - len(line.lstrip("#"))) + " " + fixed
        lines.append(line)
    return "\n".join(lines)

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce style.yml over generated artifacts in-memory."""
    style = _load_style()
    keys = [
        "api_reference_md",
        "user_guide_md",
        "release_notes_md",
        # KB if present:
    ]
    changed = 0
    for k in keys:
        if k in context and isinstance(context[k], str):
            before = context[k]
            after = _process_markdown(before, style)
            if after != before:
                context[k] = after
                changed += 1
    log.info("style enforced on %d artifacts", changed)
    return {}
