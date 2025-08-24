"""Apply style policies."""
from __future__ import annotations
from typing import Dict, Any
import json
from . import get_logger
import pathlib

POLICY_PATH = pathlib.Path(__file__).resolve().parent.parent / "policies/style.yml"


def enforce(text: str, policy: Dict[str, Any]) -> str:
    for phrase in policy.get("forbidden", []):
        text = text.replace(phrase, "")
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    for s in sentences:
        if len(s.split()) > policy.get("sentence_max", 26):
            raise ValueError("sentence exceeds limit")
    return text


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce style on text artifacts."""
    logger = get_logger("editor_style")
    policy = json.loads(POLICY_PATH.read_text())
    keys = [
        "api_reference_md",
        "user_guide_md",
        "release_notes_md",
    ]
    keys += [f for f in context.get("kb_files", {})]
    for key in keys:
        if key in context:
            context[key] = enforce(context[key], policy)
        elif key in context.get("kb_files", {}):
            context["kb_files"][key] = enforce(context["kb_files"][key], policy)
    logger.info("style enforced")
    return {}
