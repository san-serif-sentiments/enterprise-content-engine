"""Analyze sources for insights."""
from __future__ import annotations
from typing import Dict, Any, List
import pathlib
import json
from . import get_logger

BASE = pathlib.Path(__file__).resolve().parent.parent.parent


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract API and support insights."""
    logger = get_logger("researcher")
    sources = context.get("sources", {})
    openapi = sources.get("openapi", {})
    endpoints: List[Dict[str, Any]] = []
    for path, methods in openapi.get("paths", {}).items():
        for method, detail in methods.items():
            params = [p["name"] for p in detail.get("parameters", [])]
            endpoints.append({"method": method.upper(), "path": path, "params": params})
    api_summary = ", ".join(f"{e['method']} {e['path']}" for e in endpoints)

    docs_openapi_path = BASE / "docs/samples/api-reference/openapi.yaml"
    diffs: List[str] = []
    if docs_openapi_path.exists() and openapi:
        with open(docs_openapi_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if existing != openapi:
            diffs = [f"{e['method']} {e['path']}" for e in endpoints]
    feedback = sources.get("feedback", [])
    top_queries = sorted(feedback, key=lambda r: int(r["frequency"]), reverse=True)
    support_insights = {"top_queries": top_queries}
    logger.info("research complete")
    return {
        "api_summary": api_summary,
        "diffs": diffs,
        "support_insights": support_insights,
        "endpoints": endpoints,
    }
