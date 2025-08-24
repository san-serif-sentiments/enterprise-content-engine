"""CLI orchestrator for the agentic workflow."""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Dict, List

from . import graph

def _setup_logging(verbosity: int) -> None:
    level = logging.DEBUG if verbosity > 0 else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

def _print_summary(ctx: Dict[str, Any]) -> None:
    log = logging.getLogger("run")
    written: List[str] = []
    # Prefer explicit list from publisher; fall back to any known keys
    if isinstance(ctx.get("written_paths"), list):
        written = list(ctx["written_paths"])
    else:
        # fallback: scan well-known keys that map to files
        for k in (
            "api_reference_md", "user_guide_md", "release_notes_md",
            "tooltips_json", "walkthrough_yaml"
        ):
            if k in ctx:
                written.append(k)

    summary = ctx.get("summary") or f"{len(written)} artifacts written"
    log.info("SUMMARY: %s", summary)
    if written:
        for p in written:
            log.info("  - %s", p)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run agentic documentation pipeline")
    parser.add_argument("--all", action="store_true", help="run end-to-end")
    parser.add_argument("--update", action="store_true", help="recompute outputs (same as --all)")
    parser.add_argument("--packet", help="run a specific packet", default=None)
    parser.add_argument("--list", action="store_true", help="list available packets and exit")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase log verbosity")

    args = parser.parse_args()
    _setup_logging(args.verbose)
    log = logging.getLogger("run")

    # List available packets
    if args.list:
        try:
            packets = list(getattr(graph, "PACKETS", {}).keys())
        except Exception:
            packets = []
        if not packets:
            print("No packets found. Ensure engine/graph.py defines PACKETS.", file=sys.stderr)
            sys.exit(1)
        print("Available packets:")
        for p in packets:
            print(f"  - {p}")
        sys.exit(0)

    try:
        if args.all or args.update:
            log.info("Running full pipeline: all")
            ctx = graph.run("all")
        elif args.packet:
            # Validate packet name early for clearer errors
            packets = list(getattr(graph, "PACKETS", {}).keys())
            if packets and args.packet not in packets:
                log.error("Unknown packet '%s'. Try one of: %s", args.packet, ", ".join(packets))
                sys.exit(2)
            log.info("Running packet: %s", args.packet)
            ctx = graph.run("packet", args.packet)
        else:
            parser.print_help()
            sys.exit(0)

        if not isinstance(ctx, dict):
            log.error("Graph returned unexpected type: %r", type(ctx))
            sys.exit(1)

        _print_summary(ctx)
        sys.exit(0)

    except Exception as e:
        log.exception("Pipeline failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
