"""Canonical CodePro CLI facade during the staged namespace migration."""

import argparse
import json
import platform
import sys
from collections.abc import Sequence

from . import __version__
from .baseline import main as baseline_main
from .performance_baseline import main as performance_baseline_main


SUPPORTED_PYTHON_MIN = (3, 12)
SUPPORTED_PYTHON_MAX = (3, 14)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codepro",
        description="Empirical, executor-agnostic CodePro chassis.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    doctor = commands.add_parser("doctor", help="Check the installed package and Python runtime.")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    commands.add_parser("baseline", help="Run the deterministic, no-network baseline fixture.")
    performance = commands.add_parser("baseline-cost", help="Measure local overhead without changing behavior.")
    performance.add_argument("--workspace", default=".")
    performance.add_argument("--output", required=True)
    performance.add_argument("--samples", type=int, default=5)
    return parser


def _doctor(*, as_json: bool) -> int:
    supported = SUPPORTED_PYTHON_MIN <= sys.version_info[:2] <= SUPPORTED_PYTHON_MAX
    payload = {
        "package": "codepro",
        "version": __version__,
        "python": platform.python_version(),
        "python_supported": supported,
        "runtime_dependencies": [],
        "status": "PASS" if supported else "FAIL",
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"package: PASS (codepro {__version__})")
        state = "PASS" if supported else "FAIL"
        print(f"python: {state} ({platform.python_version()})")
        print(f"status: {payload['status']}")
    return 0 if supported else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return _doctor(as_json=args.as_json)
    if args.command == "baseline":
        return baseline_main()
    if args.command == "baseline-cost":
        return performance_baseline_main([
            "--workspace", args.workspace,
            "--output", args.output,
            "--samples", str(args.samples),
        ])
    build_parser().print_help()
    return 2

__all__ = ("build_parser", "main")


if __name__ == "__main__":
    raise SystemExit(main())
