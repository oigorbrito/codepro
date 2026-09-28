"""Small deterministic mutation probe for critical CodePro fail-closed invariants.

This is intentionally not a general mutation-testing framework. It introduces a
few high-value known-bad changes in temporary source copies and verifies that
focused tests fail against every mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    path: str
    needle: str
    replacement: str
    test_module: str


MUTATIONS = (
    Mutation(
        "p0-pass-without-evidence",
        "src/arkx/evidence.py",
        "if status is ExecutionStatus.PASS and not refs:",
        "if status is ExecutionStatus.PASS and False:",
        "tests.test_p0_telemetry",
    ),
    Mutation(
        "p3-negative-budget",
        "src/arkx/routing.py",
        'for name in ("max_path_escalations", "max_attempts"):\n'
        '            value = getattr(self, name)\n'
        '            if isinstance(value, bool) or not isinstance(value, int) or value < 0:',
        'for name in ("max_path_escalations", "max_attempts"):\n'
        '            value = getattr(self, name)\n'
        '            if isinstance(value, bool) or not isinstance(value, int) or value < -1:',
        "tests.test_routing",
    ),
    Mutation(
        "p5-zero-required-regressions",
        "src/arkx/verification.py",
        "if not required:",
        "if False and not required:",
        "tests.test_verification",
    ),
    Mutation(
        "promotion-trust-forged-assessment",
        "src/arkx/promotion.py",
        "if assessment.content_hash != canonical_assessment.content_hash:",
        "if False and assessment.content_hash != canonical_assessment.content_hash:",
        "tests.test_promotion",
    ),
    Mutation(
        "command-enable-shell",
        "src/arkx/command.py",
        '"shell": False,',
        '"shell": True,',
        "tests.test_command",
    ),
    Mutation(
        "qualification-ignore-ambiguity",
        "src/arkx/qualification.py",
        "if len(candidates) > 1:",
        "if False and len(candidates) > 1:",
        "tests.test_qualification",
    ),
    Mutation(
        "governance-ignore-scope-denial",
        "src/arkx/governance.py",
        "if not set(request.requested_scope).issubset(grant.authorized_scope):",
        "if False and not set(request.requested_scope).issubset(grant.authorized_scope):",
        "tests.test_governance",
    ),
    Mutation(
        "spine-ignore-request-scope",
        "src/arkx/spine.py",
        "normalized_signals.candidate_files is not None\n"
        "        and any(\n"
        "            not _path_within_requested_scope(path, request.requested_scope)\n"
        "            for path in normalized_signals.candidate_files\n"
        "        )",
        "normalized_signals.candidate_files is not None\n"
        "        and False",
        "tests.test_spine",
    ),
)


def _environment(source_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(source_root), str(ROOT)))
    return env


def _run_tests(source_root: Path, modules: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "unittest", *modules],
        cwd=ROOT,
        env=_environment(source_root),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _mutated_source(mutation: Mutation, destination: Path) -> Path:
    source_root = destination / "src"
    shutil.copytree(ROOT / "src", source_root)
    target = destination / mutation.path
    content = target.read_text(encoding="utf-8")
    if content.count(mutation.needle) != 1:
        raise RuntimeError(
            f"{mutation.mutation_id}: expected exactly one mutation anchor, "
            f"found {content.count(mutation.needle)}"
        )
    target.write_text(
        content.replace(mutation.needle, mutation.replacement, 1),
        encoding="utf-8",
    )
    return source_root


def main() -> int:
    modules = tuple(sorted({mutation.test_module for mutation in MUTATIONS}))
    baseline = _run_tests(ROOT / "src", modules)
    if baseline.returncode != 0:
        print("MUTATION_BASELINE_FAILED", file=sys.stderr)
        print(baseline.stdout, file=sys.stderr)
        print(baseline.stderr, file=sys.stderr)
        return 2

    survived: list[str] = []
    for mutation in MUTATIONS:
        with TemporaryDirectory(prefix="arkx-mutation-") as directory:
            source_root = _mutated_source(mutation, Path(directory))
            result = _run_tests(source_root, (mutation.test_module,))
        if result.returncode == 0:
            survived.append(mutation.mutation_id)
            print(f"SURVIVED {mutation.mutation_id}")
        else:
            print(f"KILLED {mutation.mutation_id}")

    if survived:
        print("MUTATION_PROBE_FAILED " + ",".join(survived), file=sys.stderr)
        return 1

    print(f"MUTATION_PROBE_PASS killed={len(MUTATIONS)} survived=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
