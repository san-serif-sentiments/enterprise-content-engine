"""Write artifacts to the docs folder."""
# engine/roles/publisher.py
from __future__ import annotations
from typing import Dict, Any, List
import pathlib, datetime
from . import get_logger

BASE = pathlib.Path(__file__).resolve().parents[2]

def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_logger("publisher")
    written: List[str] = []

    mapping = {
        "api_reference_md": BASE / "docs/samples/api-reference/reference.md",
        "user_guide_md":    BASE / "docs/samples/user-guide/tenant-admin.md",
        "release_notes_md": BASE / "docs/samples/release-notes/2025-08.md",
        "tooltips_json":    BASE / "docs/samples/in-app-guidance/tooltips.json",
        "walkthrough_yaml": BASE / "docs/samples/in-app-guidance/walkthrough.yaml",
    }

    # Handle KB either as separate keys or a dict
    kb_files = context.get("kb_files", {})
    if isinstance(kb_files, dict):
        for name, content in kb_files.items():
            tgt = BASE / f"docs/samples/kb-articles/{name}"
            write(tgt, content); written.append(str(tgt))

    for key, path in mapping.items():
        val = context.get(key)
        if isinstance(val, str) and val.strip():
            write(path, val); written.append(str(path))

    # metrics/decisions append (if present)
    metrics = context.get("metrics_md")
    if isinstance(metrics, str) and metrics.strip():
        write(BASE / "docs/evidence/metrics.md", metrics)
        written.append("docs/evidence/metrics.md")

    decisions_path = BASE / "docs/evidence/decisions.md"
    if decisions_path.exists():
        decisions = decisions_path.read_text(encoding="utf-8")
    else:
        decisions = ""
    entry = f"- {datetime.date.today()}: pipeline executed"
    if entry not in decisions:
        decisions += ("\n" if decisions and not decisions.endswith("\n") else "") + entry + "\n"
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(decisions, encoding="utf-8")
        written.append("docs/evidence/decisions.md")

    summary = f"{len(written)} artifacts written"
    logger.info(summary)
    return {"written_paths": written, "summary": summary}
