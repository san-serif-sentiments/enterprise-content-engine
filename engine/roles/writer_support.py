"""Produce support knowledge base articles."""
from __future__ import annotations
from typing import Dict, Any
from . import get_logger


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate KB articles."""
    logger = get_logger("writer_support")
    restore = (
        "---\n"
        "title: Restore errors\n"
        "owner: support\n"
        "status: active\n"
        "tags: [kb, restore]\n"
        "last_reviewed: 2025-08-01\n"
        "---\n"
        "## Symptoms\n"
        "Restore fails with error code 500.\n\n"
        "## Root cause\n"
        "Policy misconfiguration causes missing path.\n\n"
        "## Resolution\n"
        "Verify path and retry.\n\n"
        "## Prevention\n"
        "Validate paths during policy setup.\n\n"
        "Source: intake/support/feedback.csv\n"
    )
    policy = (
        "---\n"
        "title: Policy conflicts\n"
        "owner: support\n"
        "status: active\n"
        "tags: [kb, policy]\n"
        "last_reviewed: 2025-08-01\n"
        "---\n"
        "## Symptoms\n"
        "Backup policy cannot save due to conflict message.\n\n"
        "## Root cause\n"
        "Overlapping retention rules.\n\n"
        "## Resolution\n"
        "Align schedules to avoid overlap.\n\n"
        "## Prevention\n"
        "Review existing policies before creating new ones.\n\n"
        "Source: intake/support/feedback.csv\n"
    )
    logger.info("kb articles created")
    return {"kb_files": {"restore-errors.md": restore, "policy-conflicts.md": policy}}
