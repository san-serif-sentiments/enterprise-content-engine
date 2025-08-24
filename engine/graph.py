# engine/graph.py
from __future__ import annotations

import os
import time
from typing import Callable, List, Dict, Any, Tuple

# Core roles (always present)
from .roles import (
    intake_router, researcher, writer_tech, writer_support, writer_inapp,
    editor_style, editor_factual, compliance_guard, publisher,
)

# Optional roles (present only if the files exist)
try:
    from .roles import writer_comms  # internal comms (announcement + exec brief)
    HAS_COMMS = True
except Exception:
    HAS_COMMS = False

try:
    from .roles import ingestor_web  # fetch public URLs into context["web_docs"]
    HAS_WEB = True
except Exception:
    HAS_WEB = False


Role = Callable[[Dict[str, Any]], Dict[str, Any]]

def _role_name(fn: Role) -> str:
    return getattr(fn, "__name__", str(fn))


def _env_list(key: str) -> List[str]:
    raw = os.getenv(key, "")
    return [s.strip() for s in raw.split(",") if s.strip()]


# --------------------------- Packet registry ------------------------------

# Deterministic, explicit sequences. Only add optional roles when available.
PACKETS: Dict[str, List[Role]] = {
    "tech-release": [
        intake_router, researcher, writer_tech, writer_inapp,
        editor_style, editor_factual, compliance_guard, publisher,
    ],
    "kb-update": [
        intake_router, researcher, writer_support,
        editor_style, editor_factual, compliance_guard, publisher,
    ],
    "inapp-update": [
        intake_router, researcher, writer_inapp,
        editor_style, editor_factual, compliance_guard, publisher,
    ],
    "all": [
        intake_router, researcher, writer_tech, writer_inapp, writer_support,
        editor_style, editor_factual, compliance_guard, publisher,
    ],
}

# Optional packets wired only if the optional roles exist
if HAS_WEB:
    PACKETS["web-to-kb"] = [
        intake_router, ingestor_web, researcher, writer_support,
        editor_style, editor_factual, compliance_guard, publisher,
    ]

if HAS_COMMS:
    PACKETS["comms-update"] = [
        intake_router, researcher, writer_tech, writer_inapp,
        editor_style, editor_factual, compliance_guard,
        writer_comms, publisher,
    ]


def list_packets() -> List[str]:
    """Return available packet names (stable order)."""
    # Keep a stable order that starts with the core ones.
    core = ["tech-release", "kb-update", "inapp-update", "all"]
    extras = [p for p in PACKETS.keys() if p not in core]
    return core + sorted(extras)


# --------------------------- Runner ---------------------------------------

def _should_skip(name: str, include: List[str], exclude: List[str]) -> bool:
    if include and name not in include:
        return True
    if exclude and name in exclude:
        return True
    return False


def _run_sequence(
    sequence: List[Role],
    *,
    stop_on_error: bool = True,
    dry_run: bool = False,
    include_roles: List[str] | None = None,
    exclude_roles: List[str] | None = None,
) -> Tuple[Dict[str, Any], List[Tuple[str, float]]]:
    """
    Execute roles in order with timing and selective include/exclude.

    stop_on_error: if False, continue on role errors (logs only).
    dry_run: if True, skip publisher role (compute only).
    include_roles / exclude_roles: lists of role names to keep/skip.
    """
    ctx: Dict[str, Any] = {}
    timings: List[Tuple[str, float]] = []
    include_roles = include_roles or []
    exclude_roles = exclude_roles or []

    for role in sequence:
        name = _role_name(role)
        if _should_skip(name, include_roles, exclude_roles):
            timings.append((f"{name} (skipped)", 0.0))
            continue
        if dry_run and name == "publisher":
            timings.append(("publisher (dry-run skipped)", 0.0))
            continue

        start = time.perf_counter()
        try:
            out = role.run(ctx)
            if not isinstance(out, dict):
                raise TypeError(f"{name}.run() must return dict, got {type(out)}")
            ctx.update(out)
        except Exception as e:
            # Structured error; either abort or continue
            timings.append((f"{name} (error: {e})", time.perf_counter() - start))
            if stop_on_error:
                raise
            # else keep going
        else:
            timings.append((name, time.perf_counter() - start))

    return ctx, timings


def run(mode: str, packet: str | None = None,
        *,
        stop_on_error: bool | None = None,
        dry_run: bool | None = None) -> Dict[str, Any]:
    """
    Run a packet or 'all' with sane defaults and env overrides.

    Env overrides:
      ECE_INCLUDE_ROLES=role1,role2   # run only these roles (by name)
      ECE_EXCLUDE_ROLES=roleA,roleB   # skip these roles (by name)
      ECE_STOP_ON_ERROR=0|1           # default: 1
      ECE_DRY_RUN=0|1                  # default: 0
    """
    # Resolve packet/sequence
    if mode == "all":
        sequence = PACKETS["all"]
        selected = "all"
    else:
        if not packet or packet not in PACKETS:
            raise ValueError(f"Unknown or missing packet: {packet!r}. Options: {list_packets()}")
        sequence = PACKETS[packet]
        selected = packet

    # Resolve behavior flags (CLI args win; else env; else defaults)
    if stop_on_error is None:
        stop_on_error = os.getenv("ECE_STOP_ON_ERROR", "1") != "0"
    if dry_run is None:
        dry_run = os.getenv("ECE_DRY_RUN", "0") == "1"

    include_roles = _env_list("ECE_INCLUDE_ROLES")
    exclude_roles = _env_list("ECE_EXCLUDE_ROLES")

    # Announce selection (simple print to align with your current logging style)
    print(f"[graph] Running packet: {selected} | stop_on_error={stop_on_error} | dry_run={dry_run}")
    if include_roles:
        print(f"[graph] Include only: {include_roles}")
    if exclude_roles:
        print(f"[graph] Exclude: {exclude_roles}")

    # Execute
    ctx, timings = _run_sequence(
        sequence,
        stop_on_error=stop_on_error,
        dry_run=dry_run,
        include_roles=include_roles,
        exclude_roles=exclude_roles,
    )

    # Report timings
    total = sum(t for _, t in timings)
    print("[graph] Timings:")
    for name, secs in timings:
        print(f"  - {name:<30s} {secs:7.3f}s")
    print(f"[graph] Total: {total:0.3f}s")

    return ctx
