"""Deterministic orchestration flow."""
from __future__ import annotations
from typing import Callable, List, Dict, Any
from .roles import (
    intake_router,
    researcher,
    writer_tech,
    writer_support,
    writer_inapp,
    editor_style,
    editor_factual,
    compliance_guard,
    publisher,
)

Role = Callable[[Dict[str, Any]], Dict[str, Any]]

ORDER: List[Role] = [
    intake_router,
    researcher,
    writer_tech,
    writer_support,
    writer_inapp,
    editor_style,
    editor_factual,
    compliance_guard,
    publisher,
]

PACKETS: Dict[str, List[Role]] = {
    "tech-release": [intake_router, researcher, writer_tech, editor_style, editor_factual, compliance_guard, publisher],
    "kb-update": [intake_router, researcher, writer_support, editor_style, editor_factual, compliance_guard, publisher],
    "inapp-update": [intake_router, researcher, writer_inapp, editor_style, editor_factual, compliance_guard, publisher],
}


def run(mode: str, packet: str | None = None) -> None:
    context: Dict[str, Any] = {}
    sequence = ORDER if mode == "all" else PACKETS.get(packet, ORDER)
    for role in sequence:
        context.update(role.run(context))
