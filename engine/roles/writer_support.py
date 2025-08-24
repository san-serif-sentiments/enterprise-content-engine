"""Generate structured KB articles from heterogeneous intake sources."""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Any, List, Iterable, Tuple, Optional

from . import get_logger

BASE = Path(__file__).resolve().parents[2]
TODAY = date.today().isoformat()

# ---------------------------- data model ----------------------------------

@dataclass
class Signal:
    topic: str                  # e.g., "restore", "policy"
    text: str                   # raw snippet
    source: str                  # file path or logical origin
    weight: int = 1              # simple weighting (e.g., frequency)

@dataclass
class TopicBundle:
    topic: str
    symptoms: List[str] = field(default_factory=list)
    causes: List[str] = field(default_factory=list)
    resolutions: List[str] = field(default_factory=list)
    verifications: List[str] = field(default_factory=list)
    preventions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)  # for final "Source" line

# ---------------------------- intake readers ------------------------------

def _read_feedback_csv(path: Path) -> Iterable[Signal]:
    if not path.exists():
        return []
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    out = []
    for r in rows:
        query = (r.get("query") or "").strip()
        tag = (r.get("ticket_tag") or "").strip().lower()
        freq = int(((r.get("frequency") or "1").strip() or "1"))
        if not tag and query:
            tag = _infer_topic(query)
        if tag:
            out.append(Signal(topic=tag, text=query, source=str(path), weight=max(freq, 1)))
    return out

def _read_markdown_folder(folder: Path, default_topic: str) -> Iterable[Signal]:
    out = []
    if not folder.exists():
        return out
    for p in sorted(folder.glob("*.md")):
        txt = p.read_text(encoding="utf-8")
        topic = _infer_topic(txt) or default_topic
        out.append(Signal(topic=topic, text=txt, source=str(p), weight=1))
    return out

def _read_logs_folder(folder: Path) -> Iterable[Signal]:
    out = []
    if not folder.exists():
        return out
    for p in sorted(folder.glob("*.txt")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        lines = [ln.strip() for ln in txt.splitlines() if _looks_like_error(ln)]
        if not lines:
            continue
        topic = _infer_topic("\n".join(lines)) or "restore"
        out.append(Signal(topic=topic, text="\n".join(lines[:20]), source=str(p), weight=1))
    return out

def _read_openapi_title(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    try:
        import yaml
        spec = yaml.safe_load(raw)
    except Exception:
        try:
            spec = json.loads(raw)
        except Exception:
            return None
    info = (spec or {}).get("info", {})
    return info.get("title")

# ---------------------------- heuristics ----------------------------------

TOPIC_KEYWORDS = {
    "restore": [r"\brestore\b", r"\balternate path\b", r"\btargetPath\b", r"\b500\b"],
    "policy":  [r"\bpolicy\b", r"\bretention\b", r"\bschedule\b", r"\bconflict\b"],
    "backup":  [r"\bbackup\b", r"\bRPO\b", r"\bthroughput\b"],
}

ERROR_PATTERNS = [
    r"\b(4\d{2}|5\d{2})\b",
    r"\bpermission denied\b",
    r"\bnot writable\b",
    r"\bpath (does not exist|missing)\b",
    r"\btimeout\b",
]

CAUSE_HINTS = [
    r"\bpermission(s)?\b",
    r"\bnot writable\b",
    r"\bmissing path\b",
    r"\bconflict\b",
    r"\bendpoint protection|antivirus\b",
]

RESOLUTION_HINTS = [
    r"\bcreate\b|\bmkdir\b",
    r"\bgrant\b|\bchmod\b|\bchown\b|\badmin\b",
    r"\bdisable\b.*(av|antivirus|endpoint)",
    r"\bretry\b|\bre-run\b",
    r"\bverify\b",
]

def _infer_topic(text: str) -> Optional[str]:
    t = text.lower()
    for topic, patterns in TOPIC_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, t):
                return topic
    return None

def _looks_like_error(line: str) -> bool:
    if not line.strip():
        return False
    l = line.lower()
    return any(re.search(p, l) for p in ERROR_PATTERNS)

def _extract_bullets(text: str) -> Tuple[List[str], List[str], List[str]]:
    t = text.lower()
    symptoms, causes, resolutions = [], [], []
    for ln in text.splitlines():
        if _looks_like_error(ln) or "fails" in ln.lower() or "error" in ln.lower():
            s = _clean_bullet(ln)
            if s: symptoms.append(s)
    for pat in CAUSE_HINTS:
        if re.search(pat, t):
            causes.append(_phrase_from_hint(pat))
    for pat in RESOLUTION_HINTS:
        if re.search(pat, t):
            resolutions.append(_phrase_from_hint(pat))
    return _dedup(symptoms), _dedup(causes), _dedup(resolutions)

def _phrase_from_hint(pattern: str) -> str:
    mapping = {
        r"\bpermission(s)?\b": "Insufficient permissions on destination.",
        r"\bnot writable\b": "Destination path is not writable.",
        r"\bmissing path\b": "Destination path does not exist.",
        r"\bconflict\b": "Policy conflict during schedule/path override.",
        r"\bendpoint protection|antivirus\b": "Endpoint protection/antivirus blocked writes.",
        r"\bcreate\b|\bmkdir\b": "Create the destination path before restore.",
        r"\bgrant\b|\bchmod\b|\bchown\b|\badmin\b": "Run restore with admin rights or grant write permissions.",
        r"\bdisable\b.*(av|antivirus|endpoint)": "Temporarily disable endpoint protection and re-try.",
        r"\bretry\b|\bre-run\b": "Re-run the job after applying fixes.",
        r"\bverify\b": "Verify success with file presence/integrity checks.",
    }
    return mapping.get(pattern, "Follow documented resolution steps.")

def _clean_bullet(s: str) -> str:
    s = s.strip().lstrip("-•*").strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s

def _dedup(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if not x: continue
        key = x.lower()
        if key not in seen:
            seen.add(key); out.append(x)
    return out

def _slugify(text: str) -> str:
    text = text or "kb"
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "kb"

# ---------------------------- synthesis -----------------------------------

def _bundle_signals(signals: Iterable[Signal]) -> Dict[str, TopicBundle]:
    bundles: Dict[str, TopicBundle] = {}
    for s in signals:
        b = bundles.setdefault(s.topic, TopicBundle(topic=s.topic))
        sym, cau, res = _extract_bullets(s.text)
        for _ in range(max(1, s.weight)):
            b.symptoms.extend(sym)
            b.causes.extend(cau)
            b.resolutions.extend(res)
        b.sources.append(s.source)
    for b in bundles.values():
        b.symptoms = _dedup(b.symptoms[:8])
        b.causes = _dedup(b.causes[:8])
        b.resolutions = _dedup(b.resolutions[:8])
        ver = []
        if any("permissions" in r.lower() or "admin" in r.lower() for r in b.resolutions):
            ver.append("Attempt restore as admin; confirm files created at destination.")
        if any("create the destination path" in r.lower() for r in b.resolutions):
            ver.append("Confirm destination path exists pre-restore and contains restored files after run.")
        if any("endpoint protection" in r.lower() for r in b.resolutions):
            ver.append("Re-enable AV and confirm restores continue to succeed.")
        if not ver:
            ver.append("Confirm files exist at target path and pass integrity checks.")
        b.verifications = _dedup(ver)
        prev = []
        if any("permissions" in c.lower() for c in b.causes):
            prev.append("Grant least-privilege write access on restore destinations.")
        if any("not writable" in c.lower() or "missing" in c.lower() for c in b.causes):
            prev.append("Pre-create and validate alternate paths during policy setup.")
        if any("endpoint protection" in c.lower() for c in b.causes):
            prev.append("Allowlist agent processes/paths in endpoint protection policies.")
        if any("policy conflict" in c.lower() for c in b.causes):
            prev.append("Avoid overlapping policies; review path overrides after changes.")
        if not prev:
            prev.append("Schedule periodic test restores to validate readiness.")
        b.preventions = _dedup(prev)
    return bundles

def _render_kb(topic: str, b: TopicBundle, api_title: Optional[str]) -> str:
    title_map = {
        "restore": "Restore — Alternate Path Failures",
        "policy": "Backup Policy — Conflict Resolution",
        "backup": "Backup — Throughput & Scheduling",
    }
    title = title_map.get(topic, f"{topic.title()} — Troubleshooting")
    refs: List[str] = []
    if api_title:
        refs.append(f"[API Reference](../api-reference/reference.md)")
    refs.append(f"[Tenant Admin Guide](../user-guide/tenant-admin.md#restore-data)")
    refs.append(f"[Release Notes](../release-notes/2025-08.md#known-issues)")
    def bullets(name: str, items: List[str]) -> str:
        if not items: return f"## {name}\n- (none)\n\n"
        return "## " + name + "\n" + "\n".join(f"- {i}" for i in items) + "\n\n"
    md = (
        f"---\n"
        f"title: {title}\n"
        f"owner: support\n"
        f"status: active\n"
        f"tags: [kb, {topic}]\n"
        f"last_reviewed: {TODAY}\n"
        f"---\n"
    )
    md += bullets("Symptoms", b.symptoms)
    md += bullets("Possible Causes", b.causes)
    steps = []
    for r in b.resolutions:
        steps.append(r if r[0].isupper() else r.capitalize())
    if steps:
        md += "## Resolution\n" + "\n".join(f"- {s}" for s in steps) + "\n\n"
    else:
        md += "## Resolution\n- Follow steps in the user guide.\n\n"
    md += bullets("Verification", b.verifications)
    md += bullets("Prevention", b.preventions)
    md += "## References\n" + "\n".join(f"- {ref}" for ref in _dedup(refs)) + "\n\n"
    src = ", ".join(sorted(set(b.sources))) if b.sources else "intake/support/feedback.csv"
    md += f"Source: {src}\n"
    return md

# ---------------------------- role entry ----------------------------------

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_logger("writer_support")
    signals: List[Signal] = []
    signals += list(_read_feedback_csv(BASE / "intake/support/feedback.csv"))
    signals += list(_read_markdown_folder(BASE / "intake/support/incidents", default_topic="restore"))
    signals += list(_read_markdown_folder(BASE / "intake/support/notes", default_topic="policy"))
    signals += list(_read_logs_folder(BASE / "intake/logs"))
    brief = BASE / "intake/tech-docs/brief.md"
    if brief.exists():
        signals.append(Signal(topic=_infer_topic(brief.read_text(encoding='utf-8')) or "backup",
                              text=brief.read_text(encoding='utf-8'),
                              source=str(brief), weight=1))
    bundles = _bundle_signals(signals)
    kb_files: Dict[str, str] = {}
    if not bundles:
        logger.info("no signals found; producing minimal placeholder KB")
        kb_files["getting-started.md"] = (
            "---\n"
            "title: Troubleshooting — Getting Started\n"
            "owner: support\n"
            "status: active\n"
            "tags: [kb]\n"
            f"last_reviewed: {TODAY}\n"
            "---\n"
            "## Symptoms\n- (none)\n\n"
            "## Possible Causes\n- (none)\n\n"
            "## Resolution\n- Ensure intake/support/feedback.csv is populated.\n\n"
            "## Verification\n- Run a test restore and confirm file presence.\n\n"
            "## Prevention\n- Add feedback exports to the intake folder regularly.\n\n"
            "## References\n- [Tenant Admin Guide](../user-guide/tenant-admin.md)\n\n"
            "Source: intake/support\n"
        )
    else:
        api_title = _read_openapi_title(BASE / "intake/tech-docs/openapi.yaml")
        for topic, bundle in bundles.items():
            name = f"{topic}-troubleshooting.md" if topic not in ("restore", "policy") else {
                "restore": "restore-errors.md",
                "policy": "policy-conflicts.md",
            }[topic]
            kb_files[name] = _render_kb(topic, bundle, api_title)
    # integrate ingested web docs
    for doc in context.get("web_docs", []):
        try:
            slug = _slugify(doc.get("title") or doc.get("url"))
            name = f"{slug}.md"
            kb_files[name] = f"""---
title: {doc.get("title") or doc.get("url")}
owner: support
status: draft
tags: [kb, external]
last_reviewed: {TODAY}
---

## Summary
{doc.get("summary")}

## Why it matters
Provides external insights relevant to enterprise AI adoption.

## Guidance
{doc.get("notes") or "Review carefully before applying in production."}

Source: {doc.get("url")}
"""
        except Exception as e:
            logger.info("failed to convert web doc: %s", e)
    logger.info("kb articles created (total=%d)", len(kb_files))
    return {"kb_files": kb_files}
