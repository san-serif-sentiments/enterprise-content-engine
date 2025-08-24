# engine/roles/writer_inapp.py
from __future__ import annotations
import json, logging
from typing import Dict, Any
from . import get_logger

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_logger("writer_inapp")

    tooltips = [
        {
            "id": "tt-policy-create",
            "feature": "Backup Policy",
            "text": "Create your first backup policy—set retention and schedule.",
            "placement": "right",
            "role_visibility": ["TenantAdmin"],
            "when": "firstLogin && !hasPolicy",
            "variant": "A"
        },
        {
            "id": "tt-restore-start",
            "feature": "Restore",
            "text": "Restore a file from your latest backup. Use an alternate path to verify integrity.",
            "placement": "bottom",
            "role_visibility": ["TenantAdmin","Support"],
            "when": "hasBackups && !hasRestore",
            "variant": "A"
        }
    ]
    walkthrough_yaml = (
        "flow_id: first-policy-setup\n"
        "steps:\n"
        "  - id: step-1\n"
        "    text: Open Backup Policies and select 'Create Policy'.\n"
        "    success_criteria: policyFormOpened\n"
        "    when: firstLogin && !hasPolicy\n"
        "  - id: step-2\n"
        "    text: Set retention and schedule, then save.\n"
        "    success_criteria: policySaved\n"
        "    when: policyFormOpened\n"
    )

    logger.info("in-app guidance created")
    return {
        "tooltips_json": json.dumps(tooltips, indent=2),
        "walkthrough_yaml": walkthrough_yaml,
    }
