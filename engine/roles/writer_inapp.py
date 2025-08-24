# engine/roles/writer_inapp.py
from __future__ import annotations
import json
from typing import Dict, Any
from . import get_logger


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_logger("writer_inapp")

    # --- Tooltips (JSON) ---
    tooltips = [
        {
            "id": "tt-policy-create",
            "version": "1.0",
            "owner": "docs-team",
            "feature": "Backup Policy",
            "text": "Create your first backup policy—set retention and schedule.",
            "placement": "right",
            "role_visibility": ["TenantAdmin"],
            "when": "firstLogin && !hasPolicy",
            "variant": "A",
            "measure": {
                "event": "policyCreated",
                "success_criteria": "policySaved",
                "goal": "firstPolicyCreated"
            },
            "expires_on": "2025-10-15"
        },
        {
            "id": "tt-restore-start",
            "version": "1.0",
            "owner": "docs-team",
            "feature": "Restore",
            "text": "Restore a file from your latest backup. Use an alternate path to verify integrity.",
            "placement": "bottom",
            "role_visibility": ["TenantAdmin", "Support"],
            "when": "hasBackups && !hasRestore",
            "variant": "A",
            "measure": {
                "event": "restoreStarted",
                "success_criteria": "restoreCompleted",
                "goal": "firstRestoreCompleted"
            },
            "expires_on": "2025-10-15"
        },
        {
            "id": "tt-backup-run-now",
            "version": "1.0",
            "owner": "docs-team",
            "feature": "Backup",
            "text": "Run your first backup now to validate the policy.",
            "placement": "top",
            "role_visibility": ["TenantAdmin"],
            "when": "hasPolicy && !hasBackup",
            "variant": "A",
            "measure": {
                "event": "backupStarted",
                "success_criteria": "backupSucceeded",
                "goal": "firstBackupSucceeded"
            },
            "expires_on": "2025-10-15"
        },
        {
            "id": "tt-policy-verify",
            "version": "1.0",
            "owner": "docs-team",
            "feature": "Backup Policy",
            "text": "Verify next run time and retention in Policy Summary.",
            "placement": "right",
            "role_visibility": ["TenantAdmin"],
            "when": "hasPolicy && hasBackup",
            "variant": "B",
            "measure": {
                "event": "policyViewed",
                "success_criteria": "summaryViewed",
                "goal": "policyVerified"
            },
            "expires_on": "2025-10-15"
        }
    ]

    # --- Walkthrough (YAML) ---
    walkthrough_yaml = (
        "flow_id: first-policy-setup\n"
        "version: '1.0'\n"
        "owner: docs-team\n"
        "audience:\n"
        "  - TenantAdmin\n"
        "when: firstLogin && !hasPolicy\n"
        "steps:\n"
        "  - id: step-1\n"
        "    text: Open Backup Policies and select Create Policy.\n"
        "    success_criteria: policyFormOpened\n"
        "    when: firstLogin && !hasPolicy\n"
        "  - id: step-2\n"
        "    text: Set retention and schedule, then save.\n"
        "    success_criteria: policySaved\n"
        "    when: policyFormOpened\n"
        "  - id: step-3\n"
        "    text: Run your first backup to validate the policy.\n"
        "    success_criteria: backupSucceeded\n"
        "    when: hasPolicy && !hasBackup\n"
        "  - id: step-4\n"
        "    text: Restore a file to an alternate path to verify data.\n"
        "    success_criteria: restoreCompleted\n"
        "    when: hasBackup\n"
        "metrics:\n"
        "  activation_goal: firstPolicyCreated\n"
        "  success_events:\n"
        "    - policySaved\n"
        "    - backupSucceeded\n"
        "    - restoreCompleted\n"
        "source: intake/tech-docs/brief.md\n"
    )

    logger.info("in-app guidance created")
    return {
        "tooltips_json": json.dumps(tooltips, indent=2, ensure_ascii=False),
        "walkthrough_yaml": walkthrough_yaml,
    }
