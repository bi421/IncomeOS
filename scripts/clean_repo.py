#!/usr/bin/env python3
"""Safely normalize IncomeOS repository root artifacts.

Default mode is dry-run. Use --apply to perform filesystem moves.
The cleanup rules mirror the Phase 1 repository policy and are intentionally
fail-closed: existing destination files are never overwritten.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROOT_TO_COVER_LETTERS = "cover_*.txt"
ROOT_TO_DOCS = (
    "ARCHITECTURE_*.md",
    "COMPREHENSIVE_AUDIT_REPORT.md",
    "*_source.txt",
)
ROOT_TO_SCRIPTS = (
    "M1_APPLY.ps1",
    "M2_APPLY.ps1",
    "bot.py",
    "update_readme.py",
)


def planned_moves() -> list[tuple[Path, Path]]:
    """Return deterministic source/destination moves for root artifacts."""
    moves: list[tuple[Path, Path]] = []

    for pattern in (ROOT_TO_COVER_LETTERS,):
        moves.extend((p, ROOT / "cover_letters" / p.name) for p in ROOT.glob(pattern))

    for pattern in ROOT_TO_DOCS:
        moves.extend((p, ROOT / "docs" / p.name) for p in ROOT.glob(pattern))

    for name in ROOT_TO_SCRIPTS:
        source = ROOT / name
        if source.exists():
            moves.append((source, ROOT / "scripts" / name))

    return sorted(set(moves), key=lambda pair: str(pair[0]).lower())


def apply_moves(moves: list[tuple[Path, Path]]) -> None:
    """Apply moves without overwriting existing files."""
    for source, destination in moves:
        if not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite: {destination}")
        shutil.move(str(source), str(destination))


def main() -> int:
    """Run the Phase 1 repository cleanup."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform the moves")
    args = parser.parse_args()

    moves = planned_moves()
    for source, destination in moves:
        print(f"{'MOVE' if args.apply else 'PLAN'} {source.relative_to(ROOT)} -> {destination.relative_to(ROOT)}")

    if args.apply:
        apply_moves(moves)
        print(f"APPLIED {len(moves)} moves")
    else:
        print(f"DRY-RUN {len(moves)} moves; rerun with --apply to modify the tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
