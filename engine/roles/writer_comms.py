# engine/roles/writer_comms.py
"""Generate internal comms (announcement + exec brief) from Release Notes, robust & deterministic."""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, Any, List, Tuple
from . import get_logger


# -------- helpers --------

def _extract_section(md: str, heading: str) -> str:
    """
    Return block under '## <heading>' up to the next '## ' or EOF.
    Case-insensitive; requires a newline after the heading to avoid bleed.
    """
    if not md:
        return ""
    pat = rf"(?ims)^\s*##\s*{re.escape(heading)}\s*\n(.*?)(?=^\s*##\s|\Z)"
    m = re.search(pat, md)
    return m.group(1) if m else ""


# Strip inline callout fragments appended in bullets by formatters (Impact/Actions/Workaround/Notes).
_INLINE_CALLOUT = re.compile(
    r"""
    \s+-\s+\*\*                         # space-dash-space-**
    (Impact|Actions?|Workaround|Notes?) # known labels
    \*\*:\s*.*$                         # closing **: and remainder of line
    """,
    re.IGNORECASE | re.VERBOSE,
)

def _sanitize_highlight(text: str) -> str:
    t = _INLINE_CALLOUT.sub("", text)
    t = re.sub(r"\s*##\s.*$", "", t)        # trim accidental header bleed
    t = re.sub(r"\s{2,}", " ", t).strip()   # normalize whitespace
    return t

def _is_code_bullet(s: str) -> bool:
    s = s.strip()
    if s.startswith("```"):
        return True
    if s.startswith("`"):
        return True
    if re.fullmatch(r"`[^`]+`", s):  # lone code fragment bullet
        return True
    return False

def _bullets(block: str, limit: int | None = None) -> List[str]:
    """Extract '-' bullets, sanitize, and drop code-only bullets."""
    if not block:
        return []
    raw = re.findall(r"^\s*-\s+(.*)$", block, flags=re.M)
    items: List[str] = []
    for item in raw:
        if _is_code_bullet(item):
            continue
        cleaned = _sanitize_highlight(item)
        if cleaned:
            items.append(cleaned)
    if limit is not None:
        items = items[:limit]
    return items

def _first_sentence(s: str) -> str:
    m = re.search(r"(.+?[.!?])(\s|$)", s)
    return m.group(1) if m else s.strip()

def _links() -> List[str]:
    return [
        "API Reference: docs/samples/api-reference/reference.md",
        "User Guide: docs/samples/user-guide/tenant-admin.md",
        "Release Notes: docs/samples/release-notes/2025-08.md",
    ]


# Capture explicit "Impact:" text inside a bullet (bold or plain label)
_IMPACT_LINE = re.compile(
    r"^\s{0,6}-\s+(?:\*\*)?Impact:(?:\*\*)?\s*(.+)$",
    flags=re.M | re.I
)


# -------- derivation --------

def _derive_highlights(ctx: Dict[str, Any]) -> List[str]:
    rn = ctx.get("release_notes_md", "") or ""

    # Prefer actual Highlights bullets
    hl = _bullets(_extract_section(rn, "Highlights"), limit=6)

    # Helper: fetch first "real" bullet from a section (not labels)
    def _first_real_bullet(section_name: str) -> str | None:
        block = _extract_section(rn, section_name)
        if not block:
            return None
        for line in re.findall(r"^\s*-\s+(.*)$", block, flags=re.M):
            text = line.strip()
            # Skip label bullets (Impact/Actions/Workaround/Notes)
            if re.match(r"^\*?\*?(Impact|Actions?|Workaround|Notes?)\*?\*?:\s*", text, flags=re.I):
                continue
            if _is_code_bullet(text):
                continue
            return _first_sentence(_sanitize_highlight(text))
        return None

    enh_first = _first_real_bullet("Enhancements")
    fix_first = _first_real_bullet("Fixes")

    # Merge, dedupe case-insensitively, cap to 4
    combined: List[str] = []
    for s in (hl + [x for x in (enh_first, fix_first) if x]):
        if s and s.lower() not in {c.lower() for c in combined}:
            combined.append(s)

    if combined:
        return combined[:4]

    # Fallback: Known Issues / Known issues / Issues first bullet, else safe generic
    for sec in ("Known issues", "Known Issues", "Issues"):
        ki_block = _extract_section(rn, sec)
        if ki_block:
            ki = re.findall(r"^\s*-\s+(.*)$", ki_block, flags=re.M)
            if ki:
                return [_first_sentence(_sanitize_highlight(ki[0]))]
    return ["Backup list & Restore APIs simplify tenant management."]

def _derive_impact(ctx: Dict[str, Any]) -> List[str]:
    """Extract Impact lines across Enhancements/Fixes/Known issues; fallback to TL;DR fragments."""
    rn = ctx.get("release_notes_md", "") or ""
    out: List[str] = []

    for sec in ("Enhancements", "Fixes", "Known issues", "Known Issues", "Issues"):
        block = _extract_section(rn, sec)
        if not block:
            continue
        for m in _IMPACT_LINE.finditer(block):
            s = _first_sentence((m.group(1) or "").strip("* ").strip())
            if s:
                out.append(s)

    # Deduplicate preserving order
    seen, uniq = set(), []
    for s in out:
        k = s.lower()
        if k not in seen:
            seen.add(k); uniq.append(s)

    if uniq:
        return uniq[:4]

    # Fallback: derive from enriched TL;DR
    return [_first_sentence(h) for h in _derive_highlights(ctx)[:2]]

def _derive_default_actions() -> List[str]:
    return [
        "Support: point customers to updated KBs for restore and policy conflicts.",
        "Sales/CS: reference new APIs in automation pitches.",
        "PM/Eng: monitor restore success rate and conflict deflection.",
    ]


# -------- renderers --------

def _mk_announcement_md(today: str, highlights: List[str], impact: List[str]) -> str:
    return (
        "---\n"
        f"title: Internal Announcement — {today}\n"
        "owner: comms\n"
        "status: draft\n"
        "tags: [internal-comms, announcement]\n"
        f"last_reviewed: {today}\n"
        "---\n"
        "## Audience\n"
        "- Product, Engineering, Support, Sales, CS\n\n"
        "## Summary (TL;DR)\n"
        + "\n".join(f"- {h}" for h in highlights) + "\n\n"
        "## Impact\n"
        + "\n".join(f"- {i}" for i in impact) + "\n\n"
        "## Actions\n"
        + "\n".join(f"- {a}" for a in _derive_default_actions()) + "\n\n"
        "## Links\n"
        + "\n".join(f"- {l}" for l in _links()) + "\n\n"
        "Source: docs/samples/release-notes/2025-08.md\n"
    )

def _mk_exec_brief_md(today: str, highlights: List[str], impact: List[str]) -> str:
    return (
        "---\n"
        f"title: Executive Brief — {today}\n"
        "owner: comms\n"
        "status: draft\n"
        "tags: [internal-comms, exec]\n"
        f"last_reviewed: {today}\n"
        "---\n"
        "## What Shipped\n"
        + "\n".join(f"- {h}" for h in highlights) + "\n\n"
        "## Why It Matters\n"
        + "\n".join(f"- {i}" for i in impact) + "\n\n"
        "## Risks & Mitigations\n"
        "- Low risk of performance regressions — mitigated via staged rollout and monitoring.\n\n"
        "## Metrics to Watch\n"
        "- Restore success rate (RTO proxy)\n"
        "- Time-to-first-policy after onboarding\n"
        "- KB deflection on policy conflicts\n\n"
        "## References\n"
        + "\n".join(f"- {l}" for l in _links()) + "\n\n"
        "Source: docs/samples/release-notes/2025-08.md\n"
    )

def _mk_slack_text(today: str, highlights: List[str]) -> str:
    lines = [
        f"*Release update — {today}*",
        "*TL;DR:*",
        *(f"• {h}" for h in highlights[:4]),
        "",
        "Links:",
        *(f"- {l}" for l in _links()),
    ]
    return "\n".join(lines) + "\n"

def _mk_email_text(today: str, highlights: List[str], impact: List[str]) -> str:
    lines = [
        f"Subject: Release Update — {today}",
        "",
        "TL;DR:",
        *(f"- {h}" for h in highlights[:5]),
        "",
        "Impact:",
        *(f"- {i}" for i in impact[:4]),
        "",
        "Links:",
        *(f"- {l}" for l in _links()),
        "",
        "Source: docs/samples/release-notes/2025-08.md",
    ]
    return "\n".join(lines) + "\n"


# -------- role entry (with diagnostics) --------

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    log = get_logger("writer_comms")
    today = date.today().isoformat()

    # DIAG 1: show the start of RN the comms writer actually sees (from context, not disk)
    rn_head = (context.get("release_notes_md", "") or "")[:320].replace("\n", " ↵ ")
    log.info("RN head (first 320 chars): %s", rn_head)

    # Extract from Release Notes (robust to missing sections)
    highlights = _derive_highlights(context)
    impact = _derive_impact(context)

    # DIAG 2: show counts and a sample
    log.info(
        "comms extraction: highlights=%d impacts=%d | H=%s | I=%s",
        len(highlights), len(impact),
        "; ".join(highlights[:6]),
        "; ".join(impact[:6]),
    )

    announce_md = _mk_announcement_md(today, highlights, impact)
    exec_brief_md = _mk_exec_brief_md(today, highlights, impact)

    # Channel-specific plain-text variants (publisher writes via extra_artifacts)
    slack_txt = _mk_slack_text(today, highlights)
    email_txt = _mk_email_text(today, highlights, impact)

    extras: List[Tuple[str, str]] = [
        ("docs/samples/internal-comms/announcement-slack.txt", slack_txt),
        ("docs/samples/internal-comms/announcement-email.txt", email_txt),
    ]

    log.info("internal comms drafts created")
    return {
        "comms_announce_md": announce_md,
        "comms_exec_brief_md": exec_brief_md,
        "extra_artifacts": extras,
    }
