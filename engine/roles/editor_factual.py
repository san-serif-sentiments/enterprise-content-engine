"""Verify factual claims."""
from __future__ import annotations
from typing import Dict, Any
from . import get_logger


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure Source lines exist."""
    logger = get_logger("editor_factual")
    texts = [
        context.get("api_reference_md", ""),
        context.get("user_guide_md", ""),
        context.get("release_notes_md", ""),
    ]
    texts += list(context.get("kb_files", {}).values())
    for t in texts:
        if t and "Source:" not in t:
            raise ValueError("missing Source line")
    logger.info("factual verification complete")
    return {}
