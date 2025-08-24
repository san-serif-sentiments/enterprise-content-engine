"""CLI orchestrator for the agentic workflow."""
from __future__ import annotations
import argparse
from . import graph

def main() -> None:
    parser = argparse.ArgumentParser(description="Run documentation pipeline")
    parser.add_argument("--all", action="store_true", help="run end-to-end")
    parser.add_argument("--update", action="store_true", help="recompute outputs")
    parser.add_argument("--packet", help="run a specific packet", default=None)
    args = parser.parse_args()
    if args.all or args.update:
        graph.run("all")
    elif args.packet:
        graph.run("packet", args.packet)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
