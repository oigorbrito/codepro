"""Dependency-free checks for the Arkx greenfield foundation."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "docs/project-contract.md",
    "docs/experimental-protocol.md",
    "docs/architecture.md",
    "docs/decisions/0001-greenfield-bootstrap.md",
    "experiments/README.md",
    "src/README.md",
    "tests/README.md",
)

INVARIANTS = (
    "NO_COMPONENT_HAS_TENURE",
    "SCIENTIFIC_SIGNAL != LOCAL_PASS",
    "UPSTREAM_EVIDENCE != LOCAL_EVIDENCE",
    "HYPOTHESIS != IMPLEMENTATION",
    "IMPLEMENTATION != EXECUTED",
    "EXECUTED != ACCEPTED",
    "ACCEPTED != PROMOTED",
    "DONOR != PRODUCT_DEPENDENCY",
    "MECHANISM_PASS != EXECUTOR_ADOPTED",
    "BLOCKED != PASS",
    "NOT_EXECUTED != PASS",
    "NO_SILENT_FALLBACK",
    "NO_SILENT_EXECUTOR_SWITCH",
    "NO_SILENT_SCOPE_EXPANSION",
)


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        print("Missing foundation files:")
        print("\n".join(f"- {path}" for path in missing))
        return 1

    contract = (ROOT / "docs/project-contract.md").read_text(encoding="utf-8")
    absent = [invariant for invariant in INVARIANTS if invariant not in contract]
    if absent:
        print("Missing contract invariants:")
        print("\n".join(f"- {invariant}" for invariant in absent))
        return 1

    print(f"Foundation check passed: {len(REQUIRED_FILES)} files and {len(INVARIANTS)} invariants verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

