"""Apply compliance and risk policies (front-matter aware, CI-configurable)."""
from __future__ import annotations

import logging
import re
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

log = logging.getLogger("compliance_guard")

BASE = Path(__file__).resolve().parents[2]
COMPLIANCE_PATHS = [
    BASE / "docs/governance/compliance.yml",
    BASE / "engine/policies/compliance.yml",
]
RISK_PATHS = [
    BASE / "docs/governance/risk.yml",
    BASE / "engine/policies/risk.yml",
]

# --- loaders ---------------------------------------------------------------

def _load_yaml_or_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # optional
        return yaml.safe_load(text) or {}
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return {}

def _load_first(paths) -> Dict[str, Any]:
    for p in paths:
        if p.exists():
            return _load_yaml_or_json(p)
    return {}

def _load_configs() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    compliance = _load_first(COMPLIANCE_PATHS)
    risk = _load_first(RISK_PATHS)
    return compliance, risk

# --- helpers ---------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)

def _parse_frontmatter(md: str) -> Dict[str, Any]:
    """Extract YAML front-matter into a dict; return {} if none/bad."""
    if not md:
        return {}
    m = FRONTMATTER_RE.match(md)
    if not m:
        return {}
    raw = m.group(1)
    try:
        import yaml  # optional
        return yaml.safe_load(raw) or {}
    except Exception:
        try:
            return json.loads(raw)
        except Exception:
            return {}

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"
)

def _has_pii(text: str, checks: list[str]) -> Optional[str]:
    if not text:
        return None
    for c in checks or []:
        if c.lower() == "email" and EMAIL_RE.search(text):
            return "email"
        if c.lower() == "phone" and PHONE_RE.search(text):
            return "phone"
        # allow custom regex tokens if needed
        try:
            rx = re.compile(c)
            if rx.search(text):
                return c
        except re.error:
            pass
    return None

# --- main ------------------------------------------------------------------

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce compliance using front-matter + policy files.
    Behavior is controlled by compliance.yml flags:
      - sources_required (bool)            # rely on editor_factual to add; we warn here
      - hard_fail_missing_source (bool)
      - hard_fail_missing_gates (bool)
      - hard_fail_pii (bool)
      - approvals_required: { api_and_release_notes: [...], kb_major_changes: [...] }
    Risk bands in risk.yml:
      risk_band:
        L1: [...]
        L2: ["public-docs", "release-notes", "api-reference", "in-app"]
    """
    compliance, risk = _load_configs()
    notes: list[str] = []
    errors: list[str] = []

    sources_required = bool(compliance.get("sources_required", True))
    hard_fail_missing_source = bool(compliance.get("hard_fail_missing_source", False))
    hard_fail_missing_gates = bool(compliance.get("hard_fail_missing_gates", False))
    hard_fail_pii = bool(compliance.get("hard_fail_pii", False))

    approvals_required = compliance.get("approvals_required", {})
    l2_set = set((risk.get("risk_band", {}) or {}).get("L2", []))

    # Collect governed texts
    items: list[tuple[str, str]] = []
    if isinstance(context.get("api_reference_md"), str):
        items.append(("api-reference", context["api_reference_md"]))
    if isinstance(context.get("user_guide_md"), str):
        items.append(("user-guide", context["user_guide_md"]))
    if isinstance(context.get("release_notes_md"), str):
        items.append(("release-notes", context["release_notes_md"]))
    kb = context.get("kb_files", {})
    if isinstance(kb, dict):
        for name, body in kb.items():
            if isinstance(body, str):
                # treat all KB as "kb-article"
                items.append((f"kb:{name}", body))

    for name, text in items:
        fm = _parse_frontmatter(text)

        # 1) Source presence (warn or fail; editor_factual normally inserts)
        if sources_required and "Source:" not in text:
            msg = f"{name} missing Source line"
            if hard_fail_missing_source:
                errors.append(msg)
            else:
                notes.append(msg)

        # 2) PII detection
        pii_hit = _has_pii(text, compliance.get("pii_redact", []))
        if pii_hit:
            msg = f"PII detected ({pii_hit}) in {name}"
            if hard_fail_pii:
                errors.append(msg)
            else:
                notes.append(msg)

        # 3) Risk band gates (front-matter aware)
        tags = set(fm.get("tags", []) or [])
        risk_band = fm.get("risk_band")
        approvals = fm.get("approvals", {}) or {}

        requires_l2 = bool(tags & l2_set)  # if doc is tagged as one of L2 types
        if requires_l2:
            if risk_band != "L2":
                msg = f"{name} expected risk_band L2 (tags={list(tags)})"
                if hard_fail_missing_gates:
                    errors.append(msg)
                else:
                    notes.append(msg)

            # approvals for API & Release Notes (per policy)
            need = set(approvals_required.get("api_and_release_notes", []))
            if name in ("api-reference", "release-notes") and need:
                have = {k for k, v in approvals.items() if v}
                if not need.issubset(have):
                    msg = f"{name} missing approvals {sorted(need - have)}"
                    if hard_fail_missing_gates:
                        errors.append(msg)
                    else:
                        notes.append(msg)

    # Log results
    for n in notes:
        log.info("compliance: %s", n)

    if errors:
        # Fail decisively with actionable message(s)
        raise ValueError("; ".join(errors))

    log.info("compliance passed")
    return {"approved": True, "compliance_notes": notes}
