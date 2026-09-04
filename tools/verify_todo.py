"""Verify and synchronize AUTO TODO checkboxes.

Usage:
    python tools/verify_todo.py
        Run verification commands and update TODO.md automatically.

    python tools/verify_todo.py --check
        Run verification commands without modifying TODO.md. Exit non-zero if
        any AUTO verification fails or an AUTO checkbox is inconsistent.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODO = ROOT / "TODO.md"

CHECKS: dict[str, tuple[str, list[str]]] = {
    "full_tests": (
        "Full pytest suite",
        [sys.executable, "-m", "pytest", "-q"],
    ),
    "compile_incomeos": (
        "Compile incomeos",
        [sys.executable, "-m", "compileall", "-q", "incomeos"],
    ),
    "compile_scripts": (
        "Compile scripts",
        [sys.executable, "-m", "compileall", "-q", "scripts"],
    ),
    "security_test": (
        "Repository security regression",
        [sys.executable, "-m", "pytest", "-q", "tests/test_repository_security.py"],
    ),
    "real_pipeline_test": (
        "Real job pipeline execution",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_real_job_pipeline_execution.py",
        ],
    ),
}

MARKER_RE = re.compile(r"<!-- verify:([a-zA-Z0-9_]+) -->$")
BOX_RE = re.compile(r"^(\s*- \[)([ xX])(\].*?)(\s*<!-- verify:[^>]+ -->)\s*$")


def run_check(name: str, command: list[str]) -> bool:
    label = CHECKS[name][0]
    print(f"[VERIFY] {label}: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"[VERIFY] {label}: {status}")
    return result.returncode == 0


def collect_markers(text: str) -> set[str]:
    return {match.group(1) for match in MARKER_RE.finditer(text)}


def synchronize(text: str, results: dict[str, bool]) -> tuple[str, list[str]]:
    changed: list[str] = []
    output: list[str] = []

    for line in text.splitlines(keepends=True):
        match = BOX_RE.match(line.rstrip("\r\n"))
        if not match:
            output.append(line)
            continue

        marker_match = MARKER_RE.search(match.group(4))
        if not marker_match:
            output.append(line)
            continue

        name = marker_match.group(1)
        if name not in results:
            output.append(line)
            continue

        desired = "x" if results[name] else " "
        current = match.group(2).lower()
        if current != desired:
            changed.append(name)
            newline = "\n" if line.endswith("\n") else ""
            output.append(match.group(1) + desired + match.group(3) + match.group(4) + newline)
        else:
            output.append(line)

    return "".join(output), changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify AUTO checks without modifying TODO.md",
    )
    args = parser.parse_args()

    if not TODO.exists():
        print(f"ERROR: missing {TODO}")
        return 2

    text = TODO.read_text(encoding="utf-8")
    markers = collect_markers(text)
    unknown = markers - CHECKS.keys()
    if unknown:
        print(f"ERROR: unknown verification markers: {sorted(unknown)}")
        return 2

    results = {
        name: run_check(name, CHECKS[name][1])
        for name in CHECKS
        if name in markers
    }

    synchronized, changed = synchronize(text, results)

    if args.check:
        if changed:
            print(f"ERROR: TODO.md AUTO checkboxes are stale: {', '.join(changed)}")
            return 1
        print("[VERIFY] TODO.md AUTO checkboxes are synchronized.")
    else:
        if changed:
            TODO.write_text(synchronized, encoding="utf-8", newline="\n")
            print(f"[VERIFY] Updated TODO.md: {', '.join(changed)}")
        else:
            print("[VERIFY] TODO.md already synchronized.")

    failed = [name for name, passed in results.items() if not passed]
    if failed:
        print(f"[VERIFY] Failed checks: {', '.join(failed)}")
        return 1

    print("[VERIFY] All AUTO checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
