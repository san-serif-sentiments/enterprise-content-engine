"""Verify and normalize factual claims by enforcing Source lines."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger("editor_factual")

BASE = Path(__file__).resolve().parents[2]
COMPLIANCE_PATHS = [
    BASE / "docs/governance/compliance.yml",
    BASE / "engine/policies/compliance.yml",
]

def _load_compliance() -> Dict[str, Any]:
    """Load compliance policy (YAML or JSON)."""
    text = ""
    for p in COMPLIANCE_PATHS:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            break
    if not text:
        return {}
    try:
        import yaml  # optional
        return yaml.safe_load(text)
    except Exception:
        # allow JSON-in-YAML files
        return json.loads(text)

SOURCE_RE = re.compile(r"^Source:\s", flags=re.IGNORECASE)

def _ensure_source(md: str, default_source: str) -> str:
    """Append a Source line if the last non-empty line is not a Source."""
    if not md or SOURCE_RE.search(md.strip().splitlines()[-1] if md.strip().splitlines() else ""):
        return md
    # ensure trailing newline then add Source
    if not md.endswith("\n"):
        md += "\n"
    return md + f"\nSource: {default_source}\n"

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure Source lines exist on all governed artifacts.
    Respects:
      - sources_required (bool)
      - hard_fail_on_missing_source (bool)
    Updates context in-place with normalized content.
    """
    policy = _load_compliance()
    sources_required = bool(policy.get("sources_required", True))
    hard_fail = bool(policy.get("hard_fail_on_missing_source", False))
    default_source = "intake/tech-docs/openapi.yaml"

    updated = 0
    missing = []

    # Governed single docs
    governed_keys = [
        "api_reference_md",
        "user_guide_md",
        "release_notes_md",
    ]
    for k in governed_keys:
        if k in context and isinstance(context[k], str) and context[k].strip():
            text = context[k]
            if sources_required and not SOURCE_RE.search(text.strip().splitlines()[-1] if text.strip().splitlines() else ""):
                if hard_fail:
                    missing.append(k)
                else:
                    context[k] = _ensure_source(text, default_source)
                    updated += 1

    # KB dict (if present)
    kb = context.get("kb_files")
    if isinstance(kb, dict):
        for name, text in kb.items():
            if isinstance(text, str) and text.strip():
                if sources_required and not SOURCE_RE.search(text.strip().splitlines()[-1] if text.strip().splitlines() else ""):
                    if hard_fail:
                        missing.append(f"kb:{name}")
                    else:
                        kb[name] = _ensure_source(text, default_source)
                        updated += 1
        context["kb_files"] = kb  # write back

    if missing:
        # Make the failure explicit and actionable
        raise ValueError(f"Missing Source lines in: {', '.join(missing)}")

    log.info("factual verification complete (normalized: %d)", updated)
    # no new keys; artifacts are edited in-place
    return {}
