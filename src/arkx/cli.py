"""Minimal dependency-free Dekon command-line interface."""

from __future__ import annotations

import argparse
import platform
import sys
from collections.abc import Sequence

from . import __version__


_SUPPORTED_MIN = (3, 12)
_SUPPORTED_MAX = (3, 14)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dekon",
        description="Deterministic CLI boundary for the Dekon software-engineering chassis.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "doctor",
        help="Check whether the local Python runtime can execute the current chassis.",
        description="Check the local runtime and core package import boundary.",
    )
    return parser


def _doctor() -> int:
    version = sys.version_info[:2]
    supported = _SUPPORTED_MIN <= version <= _SUPPORTED_MAX

    checks = (
        ("python", supported, platform.python_version()),
        ("core", True, "importable"),
    )
    for name, ok, detail in checks:
        state = "PASS" if ok else "FAIL"
        print(f"{name}: {state} ({detail})")

    overall = all(ok for _, ok, _ in checks)
    print(f"status: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "doctor":
        return _doctor()

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
