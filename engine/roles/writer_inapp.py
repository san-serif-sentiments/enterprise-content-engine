"""Create in-app guidance artifacts."""
from __future__ import annotations
from typing import Dict, Any
import json
from . import get_logger


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate tooltips and walkthrough."""
    logger = get_logger("writer_inapp")
    tooltips = [
        {"id": "tip-backup", "feature": "backup", "text": "Use Run Now for immediate backup", "placement": "right", "role_visibility": "admin", "when": "onHover", "variant": "info"},
        {"id": "tip-restore", "feature": "restore", "text": "Provide full target path", "placement": "bottom", "role_visibility": "admin", "when": "onFocus", "variant": "info"},
        {"id": "tip-policy", "feature": "policy", "text": "Save policy after validation", "placement": "top", "role_visibility": "admin", "when": "onClick", "variant": "info"},
        {"id": "tip-dashboard", "feature": "dashboard", "text": "Check metrics for success", "placement": "left", "role_visibility": "admin", "when": "onLoad", "variant": "info"},
    ]
    tooltips_json = json.dumps(tooltips, ensure_ascii=False, indent=2)
    walkthrough_yaml = (
        "flow_id: restore-setup\n"
        "source: intake/inapp/hints.md\n"
        "steps:\n"
        "  - id: step1\n"
        "    text: Configure backup policy\n"
        "    success_criteria: Policy saved\n"
        "    when: after-login\n"
        "  - id: step2\n"
        "    text: Start first backup\n"
        "    success_criteria: Job scheduled\n"
        "    when: policy-complete\n"
    )
    logger.info("in-app guidance created")
    return {"tooltips_json": tooltips_json, "walkthrough_yaml": walkthrough_yaml}
