"""Gather intake materials."""
from __future__ import annotations
import csv
import json
from typing import Dict, Any
import pathlib
from . import get_logger

BASE = pathlib.Path(__file__).resolve().parent.parent.parent


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Read intake files and return targets, risks, and sources."""
    logger = get_logger("intake_router")
    sources: Dict[str, Any] = {}
    brief_path = BASE / "intake/tech-docs/brief.md"
    openapi_path = BASE / "intake/tech-docs/openapi.yaml"
    feedback_path = BASE / "intake/support/feedback.csv"
    hints_path = BASE / "intake/inapp/hints.md"

    sources["brief"] = brief_path.read_text(encoding="utf-8")
    if openapi_path.exists():
        with open(openapi_path, "r", encoding="utf-8") as f:
            sources["openapi"] = json.load(f)
    if feedback_path.exists():
        with open(feedback_path, newline="", encoding="utf-8") as f:
            sources["feedback"] = list(csv.DictReader(f))
    if hints_path.exists():
        sources["hints"] = hints_path.read_text(encoding="utf-8")

    targets = ["api-reference", "user-guide", "release-notes", "kb", "in-app"]
    risks = ["api-reference", "release-notes"]
    logger.info("intake gathered")
    return {"targets": targets, "risks": risks, "sources": sources}
