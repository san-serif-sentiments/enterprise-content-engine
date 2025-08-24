# engine/roles/editor_style.py
from __future__ import annotations
import logging, re, json
from typing import Dict, Any, List
from pathlib import Path

log = logging.getLogger("editor_style")

BASE = Path(__file__).resolve().parents[2]
STYLE_PATHS = [
    BASE / "docs/governance/style.yml",
    BASE / "engine/policies/style.yml",
]

def _load_style() -> Dict[str, Any]:
    text = ""
    for p in STYLE_PATHS:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            break
    if not text:
        return {}
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return {}

_FM_BLOCK = re.compile(r"(?s)^---\n.*?\n---\n")
_CODE_FENCE = re.compile(r"(?m)^```")
_HEADING = re.compile(r"(?m)^(#{1,6})\s+(.*)$")
_BULLET  = re.compile(r"(?m)^\s{0,3}[-*+]\s")
_LINK_OR_CODE_INLINE = re.compile(r"`[^`]*`|\[[^\]]+\]\([^)]+\)")

ARTIFACT_KEYS = [
    "api_reference_md",
    "user_guide_md",
    "release_notes_md",
    "comms_announce_md",
    "comms_exec_brief_md",
]

def _split_front_matter(md: str):
    if not md.startswith("---\n"):
        return None, md
    m = _FM_BLOCK.match(md)
    if not m:
        return None, md
    return m.group(0), md[m.end():]

def _segment_code_fences(body: str):
    parts: List[tuple[str, str]] = []
    last = 0
    toggle = "text"
    for m in _CODE_FENCE.finditer(body):
        i = m.start()
        parts.append((toggle, body[last:i]))
        toggle = "code" if toggle == "text" else "text"
        last = i
    parts.append((toggle, body[last:]))
    # reattach opening ``` to code segments
    stitched: List[tuple[str, str]] = []
    i = 0
    while i < len(parts):
        kind, seg = parts[i]
        if kind == "code":
            seg = "```" + seg
            # if next is text and starts with ``` treat as closing fence
            if i + 1 < len(parts) and parts[i+1][0] == "text":
                nxt = parts[i+1][1]
                if nxt.startswith("```"):
                    seg = seg + "```"
                    parts[i+1] = ("text", nxt[3:])
            stitched.append((kind, seg))
        else:
            stitched.append((kind, seg))
        i += 1
    return stitched

def _to_sentence_case(h: str) -> str:
    h = h.strip()
    if not h:
        return h
    words = h.split()
    out = []
    for idx, w in enumerate(words):
        if re.fullmatch(r"[A-Z]{2,4}s?", w):
            out.append(w)
        elif idx == 0:
            out.append(w[:1].upper() + w[1:].lower())
        else:
            out.append(w.lower())
    return " ".join(out)

def _enforce_active_voice(t: str) -> str:
    return re.sub(r"\b(is|are|was|were)\s+(\w+ed)\s+by\b", r"\2", t, flags=re.I)

def _enforce_tense_present(t: str) -> str:
    return re.sub(r"\bwill\s+(\w+)\b", r"\1", t, flags=re.I)

def _limit_sentence_length(t: str, max_words: int) -> str:
    if _BULLET.search(t) or t.strip().startswith("|"):
        return t
    parts = re.split(r"(?<=[.!?])\s+", t)
    fixed = []
    for s in parts:
        words = s.split()
        if len(words) > max_words:
            s = re.sub(r",\s+|;\s+| — ", ". ", s, count=1)
        fixed.append(s)
    return " ".join(fixed)

def _remove_forbidden(t: str, forbidden: list[str]) -> str:
    tokens: List[tuple[str, str]] = []
    pos = 0
    for m in _LINK_OR_CODE_INLINE.finditer(t):
        if m.start() > pos:
            tokens.append(("plain", t[pos:m.start()]))
        tokens.append(("lock", m.group(0)))
        pos = m.end()
    if pos < len(t):
        tokens.append(("plain", t[pos:]))

    def scrub(seg: str) -> str:
        out = seg
        for term in forbidden:
            out = re.sub(rf"\b{re.escape(term)}\b", "", out, flags=re.I)
        return re.sub(r"\s{2,}", " ", out)

    return "".join(seg if k == "lock" else scrub(seg) for k, seg in tokens).strip()

def _normalize_body(body: str, style: Dict[str, Any]) -> str:
    segments = _segment_code_fences(body)

    active = bool(style.get("active_voice"))
    present = (style.get("tense") == "present")
    forbidden = style.get("forbidden") or []
    sent_max = int(style.get("sentence_max") or 0)

    out_segments: List[str] = []
    for kind, seg in segments:
        if kind == "code":
            out_segments.append(seg)
            continue

        lines = seg.splitlines()
        new_lines: List[str] = []
        for line in lines:
            m = _HEADING.match(line)
            if m:
                hashes, title = m.groups()
                new_lines.append(f"{hashes} {_to_sentence_case(title)}")
                continue
            if _BULLET.match(line) or line.strip().startswith("|"):
                tmp = line
                if forbidden:
                    tmp = _remove_forbidden(tmp, forbidden)
                new_lines.append(tmp)
                continue
            tmp = line
            if forbidden:
                tmp = _remove_forbidden(tmp, forbidden)
            if active:
                tmp = _enforce_active_voice(tmp)
            if present:
                tmp = _enforce_tense_present(tmp)
            if sent_max and tmp.strip():
                tmp = _limit_sentence_length(tmp, sent_max)
            new_lines.append(tmp)
        out_segments.append("\n".join(new_lines))

    body2 = "\n".join(out_segments)
    body2 = re.sub(r"[ \t]+$", "", body2, flags=re.M)
    body2 = re.sub(r"\n{3,}", "\n\n", body2)
    return body2.strip() + "\n"

def _process_markdown(md: str, style: Dict[str, Any]) -> str:
    if not isinstance(md, str) or not md.strip():
        return md
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    fm, body = _split_front_matter(md)
    fm = fm or ""
    styled_body = _normalize_body(body, _load_style() if style is None else style)
    return f"{fm}{styled_body}"

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    style = _load_style()
    out: Dict[str, Any] = {}
    changed = 0

    for k in ARTIFACT_KEYS:
        val = context.get(k)
        if isinstance(val, str) and val.strip():
            styled = _process_markdown(val, style)
            if styled != val:
                out[k] = styled
                changed += 1

    kb = context.get("kb_files")
    if isinstance(kb, dict):
        styled_kb = {}
        for name, val in kb.items():
            if isinstance(val, str) and val.strip():
                newv = _process_markdown(val, style)
                styled_kb[name] = newv
                if newv != val:
                    changed += 1
            else:
                styled_kb[name] = val
        out["kb_files"] = styled_kb

    log.info("style enforced on %d artifacts", changed)
    return out
