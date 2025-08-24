# engine/roles/publisher.py
"""Write artifacts to the docs folder (atomic, idempotent, complete)."""
from __future__ import annotations

from typing import Dict, Any, List, Tuple
from pathlib import Path
import hashlib
import tempfile
import datetime

from . import get_logger

BASE = Path(__file__).resolve().parents[2]

# ---------- helpers ---------------------------------------------------------

def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(BASE))
    except Exception:
        return str(p)

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")

def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = _sha256(content)
    # Skip write if content unchanged (noise-free commits)
    if path.exists() and _sha256(_read_text(path)) == h:
        return
    # Atomic replace
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as tf:
        tf.write(content)
        tmp_name = tf.name
    Path(tmp_name).replace(path)

def _write_if_string(target: Path, content: Any, written: List[str]) -> None:
    if isinstance(content, str) and content.strip():
        _atomic_write(target, content)
        written.append(_rel(target))

# ---------- role ------------------------------------------------------------

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Writes:
      - Core docs (API ref, User guide, Release notes)
      - In-app artifacts (tooltips.json, walkthrough.yaml)
      - KB articles from context['kb_files'] dict
      - Evidence (metrics.md)
      - Decisions log (append unique entry per day)
      - Internal comms drafts (announcement.md, exec-brief.md)
      - Optional extras from context['extra_artifacts']: List[Tuple[path, content]]
    """
    logger = get_logger("publisher")
    written: List[str] = []

    # 1) KB articles (dict name -> content)
    kb_files = context.get("kb_files", {})
    if isinstance(kb_files, dict):
        kb_dir = BASE / "docs/samples/kb-articles"
        for name, content in kb_files.items():
            if not isinstance(name, str):
                continue
            target = kb_dir / name
            _write_if_string(target, content, written)

    # 2) Core mapping
    mapping = {
        "api_reference_md": BASE / "docs/samples/api-reference/reference.md",
        "user_guide_md":    BASE / "docs/samples/user-guide/tenant-admin.md",
        "release_notes_md": BASE / "docs/samples/release-notes/2025-08.md",
        "tooltips_json":    BASE / "docs/samples/in-app-guidance/tooltips.json",
        "walkthrough_yaml": BASE / "docs/samples/in-app-guidance/walkthrough.yaml",
    }
    for key, target in mapping.items():
        _write_if_string(target, context.get(key), written)

    # 3) Evidence (metrics)
    metrics = context.get("metrics_md")
    if isinstance(metrics, str) and metrics.strip():
        _write_if_string(BASE / "docs/evidence/metrics.md", metrics, written)

    # 4) Decisions log (append once per day)
    decisions_path = BASE / "docs/evidence/decisions.md"
    today_entry = f"- {datetime.date.today()}: pipeline executed"
    existing = _read_text(decisions_path)
    if today_entry not in existing:
        content = (existing + ("\n" if existing and not existing.endswith("\n") else "") + today_entry + "\n") if existing else today_entry + "\n"
        _atomic_write(decisions_path, content)
        written.append(_rel(decisions_path))

    # 5) Internal comms
    _write_if_string(
        BASE / "docs/samples/internal-comms/announcement.md",
        context.get("comms_announce_md"),
        written,
    )
    _write_if_string(
        BASE / "docs/samples/internal-comms/exec-brief.md",
        context.get("comms_exec_brief_md"),
        written,
    )

    # 6) Optional extras: List[Tuple[str|Path, str]]
    extras = context.get("extra_artifacts", [])
    if isinstance(extras, list):
        for item in extras:
            try:
                raw_path, content = item
                target = BASE / Path(str(raw_path))
                _write_if_string(target, content, written)
            except Exception:
                # ignore malformed entries; keep publisher robust
                continue

    # Deduplicate and sort for deterministic summaries
    written = sorted(dict.fromkeys(written))

    summary = f"{len(written)} artifacts written"
    for p in written:
        logger.info(p)
    logger.info(summary)

    return {"written_paths": written, "summary": summary}
