"""Generate technical documentation."""
from __future__ import annotations
from typing import Dict, Any, List
from . import get_logger


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create API reference, user guide, and release notes."""
    logger = get_logger("writer_tech")
    endpoints: List[Dict[str, Any]] = context.get("endpoints", [])
    diffs: List[str] = context.get("diffs", [])

    api_reference_md = (
        "---\n"
        "title: Druva Backup & Restore API Reference\n"
        "owner: docs-team\n"
        "status: active\n"
        "tags: [api-reference]\n"
        "last_reviewed: 2025-08-01\n"
        "---\n"
        "Authentication uses bearer tokens.\n\n"
        "Pagination uses limit and offset.\n\n"
        "### List backups\n\n"
        "```bash\n"
        "curl -H \"Authorization: Bearer TOKEN\" \\\n  \"https://api.example.com/v1/backups?tenantId=123\"\n"
        "```\n\n"
        "### Start restore\n\n"
        "```bash\n"
        "curl -X POST -H \"Authorization: Bearer TOKEN\" \\\n  -d '{\"backupId\":\"b1\",\"targetPath\":\"/tmp\"}' \\\n  \"https://api.example.com/v1/restores\"\n"
        "```\n\n"
        "Checklist: PM, Eng\n\n"
        "Source: intake/tech-docs/openapi.yaml\n"
    )

    user_guide_md = (
        "---\n"
        "title: Tenant Admin Guide\n"
        "owner: docs-team\n"
        "status: active\n"
        "tags: [user-guide]\n"
        "last_reviewed: 2025-08-01\n"
        "---\n"
        "## Configure backup policy\n"
        "1. Navigate to Policies.\n"
        "2. Define scope and schedule.\n"
        "3. Save.\n\n"
        "## Run backup\n"
        "1. Open Backup page.\n"
        "2. Select tenant.\n"
        "3. Click Run Now.\n\n"
        "## Restore data\n"
        "1. Open Restores.\n"
        "2. Choose backup.\n"
        "3. Provide target path.\n"
        "4. Submit.\n\n"
        "Verification: Files appear in target path.\n"
        "Rollback: Re-run backup with previous settings.\n\n"
        "Source: intake/tech-docs/brief.md\n"
    )

    release_notes_md = (
        "---\n"
        "title: August 2025 Release Notes\n"
        "owner: docs-team\n"
        "status: active\n"
        "tags: [release-notes]\n"
        "last_reviewed: 2025-08-01\n"
        "---\n"
        "## Highlights\n"
        "- Backup list and restore API simplify tenant management.\n\n"
        "## Enhancements\n"
        "- Improved restore performance.\n\n"
        "## Fixes\n"
        "- Addressed policy conflict errors.\n\n"
        "## Known issues\n"
        "- Slow backup on large datasets.\n\n"
    )
    release_notes_md += "### API changes\n" + "\n".join(f"- {e['method']} {e['path']}" for e in endpoints) + "\n\n"
    release_notes_md += "Checklist: PM, Eng\n\nSource: intake/tech-docs/openapi.yaml\n"

    logger.info("technical docs created")
    return {
        "api_reference_md": api_reference_md,
        "user_guide_md": user_guide_md,
        "release_notes_md": release_notes_md,
    }
