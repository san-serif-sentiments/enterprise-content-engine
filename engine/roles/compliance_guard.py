"""Apply compliance and risk policies."""
from __future__ import annotations
from typing import Dict, Any
import json
import re
import pathlib
from . import get_logger

BASE = pathlib.Path(__file__).resolve().parent.parent
COMPLIANCE = json.loads((BASE / "policies/compliance.yml").read_text())
RISK = json.loads((BASE / "policies/risk.yml").read_text())


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Check for source lines, PII, and risk gates."""
    logger = get_logger("compliance_guard")
    texts = {
        "api-reference": context.get("api_reference_md", ""),
        "user-guide": context.get("user_guide_md", ""),
        "release-notes": context.get("release_notes_md", ""),
    }
    texts.update({k: v for k, v in context.get("kb_files", {}).items()})

    for name, text in texts.items():
        if text and COMPLIANCE.get("sources_required") and "Source:" not in text:
            raise ValueError(f"{name} missing source")
        for pat in COMPLIANCE.get("pii_redact", []):
            if re.search(pat, text):
                raise ValueError(f"PII detected in {name}")
        if name in RISK["risk_band"].get("L2", []):
            if "Checklist:" not in text:
                raise ValueError(f"risk gate missing for {name}")
    logger.info("compliance passed")
    return {"approved": True, "notes": "All checks passed"}
