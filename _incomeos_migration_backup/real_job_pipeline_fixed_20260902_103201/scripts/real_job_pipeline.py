
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

from incomeos.decision.job_decision import persist_job_decision
from incomeos.decision.persistence import DecisionStore
from incomeos.skills.aggregator import build_master_profile
from incomeos.applications.engine import apply_to_jobs


def _table_columns(
    conn: sqlite3.Connection,
    table: str,
) -> tuple[str, ...]:
    rows = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return tuple(
        str(row[1])
        for row in rows
    )


def _pick_column(
    columns: tuple[str, ...],
    candidates: tuple[str, ...],
) -> str | None:
    lower = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]

    return None


def discover_job_table(
    db_path: str | Path,
) -> tuple[str, tuple[str, ...]]:
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(
            f"job database not found: {db_path}"
        )

    conn = sqlite3.connect(db_path)

    try:
        tables = tuple(
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            ).fetchall()
        )

        if not tables:
            raise ValueError(
                "job database contains no tables"
            )

        best = None

        for table in tables:
            columns = _table_columns(
                conn,
                table,
            )

            score = 0

            if _pick_column(
                columns,
                ("id", "job_id"),
            ):
                score += 3

            if _pick_column(
                columns,
                ("title", "job_title"),
            ):
                score += 3

            if _pick_column(
                columns,
                ("url", "job_url", "link"),
            ):
                score += 2

            if _pick_column(
                columns,
                ("company", "company_name", "employer"),
            ):
                score += 1

            candidate = (
                score,
                table,
                columns,
            )

            if best is None or candidate[0] > best[0]:
                best = candidate

        assert best is not None

        if best[0] < 5:
            raise ValueError(
                "could not identify a compatible job table"
            )

        return best[1], best[2]

    finally:
        conn.close()


def load_jobs(
    db_path: str | Path,
    limit: int,
) -> tuple[dict[str, Any], ...]:
    table, columns = discover_job_table(
        db_path
    )

    id_column = _pick_column(
        columns,
        ("id", "job_id"),
    )
    title_column = _pick_column(
        columns,
        ("title", "job_title"),
    )
    url_column = _pick_column(
        columns,
        ("url", "job_url", "link"),
    )
    company_column = _pick_column(
        columns,
        ("company", "company_name", "employer"),
    )

    assert id_column
    assert title_column

    selected = [
        id_column,
        title_column,
    ]

    if company_column:
        selected.append(company_column)

    if url_column:
        selected.append(url_column)

    conn = sqlite3.connect(
        db_path
    )

    try:
        rows = conn.execute(
            f"""
            SELECT {", ".join(selected)}
            FROM {table}
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    jobs = []

    for row in rows:
        data = {
            "id": row[0],
            "title": row[1],
        }

        offset = 2

        if company_column:
            data["company"] = row[offset]
            offset += 1
        else:
            data["company"] = ""

        if url_column:
            data["url"] = row[offset]
        else:
            data["url"] = ""

        jobs.append(data)

    return tuple(jobs)


def run(
    *,
    jobs_db: str | Path = "data/jobs/incomeos_jobs.sqlite3",
    decisions_db: str | Path = "data/decisions.db",
    repos_root: str | Path = "data/github_repos",
    limit: int = 10,
    opportunity_name: str = "Python Automation",
    apply: bool = False,
) -> int:
    jobs_db = Path(jobs_db)

    print("=" * 72)
    print("INCOMEOS — REAL LOCAL JOB PIPELINE")
    print("=" * 72)

    print()
    print(f"JOB DB     : {jobs_db}")
    print(f"REPOSITORY : {repos_root}")
    print(f"DECISIONS  : {decisions_db}")
    print(f"LIMIT      : {limit}")
    print(f"APPLY MODE : {apply}")

    print()
    print("[1/5] Building current evidence/profile...")

    profile = build_master_profile(
        repos_root
    )

    print(
        f"Skills available: {len(profile.skills)}"
    )

    print()
    print("[2/5] Discovering real job table...")

    table, columns = discover_job_table(
        jobs_db
    )

    print(f"Job table: {table}")
    print(
        "Columns: "
        + ", ".join(columns)
    )

    print()
    print("[3/5] Loading real jobs...")

    jobs = load_jobs(
        jobs_db,
        limit,
    )

    if not jobs:
        print(
            "No jobs found."
        )
        return 0

    print(
        f"Loaded jobs: {len(jobs)}"
    )

    print()
    print("[4/5] Evaluating concrete job decisions...")

    store = DecisionStore(
        decisions_db
    )

    decided = []

    for job in jobs:
        # Current local job DB may not contain structured requirements.
        # In that case, use the explicit opportunity skill as the required
        # requirement rather than inventing requirements from job title.
        job_for_fit = dict(job)

        job_for_fit["required_skills"] = (
            opportunity_name == "Python Automation"
            and ["Python"]
            or []
        )

        if not job_for_fit["required_skills"]:
            continue

        from incomeos.decision.job_decision import persist_job_decision

        result = persist_job_decision(
            job=job_for_fit,
            opportunity_name=opportunity_name,
            profile={
                "capabilities": (),
                "skills": profile.skills,
            },
            store=store,
            apply_threshold=1.0,
        )

        decided.append(
            (
                job,
                result,
            )
        )

        print(
            f"{job['id']} | "
            f"{job['title']} | "
            f"fit={result.fit.fit_score:.3f} | "
            f"decision={result.decision.decision} | "
            f"id={result.decision.decision_id}"
        )

    print()
    print("[5/5] Application boundary...")

    apply_candidates = [
        job
        for job, result in decided
        if result.decision.decision == "APPLY"
    ]

    print(
        f"APPLY candidates: {len(apply_candidates)}"
    )

    if apply and apply_candidates:
        print(
            "Preparing applications for first APPLY candidate skill."
        )

        apply_to_jobs(
            "Python",
            limit=min(
                limit,
                len(apply_candidates),
            ),
            open_browser=False,
            data_dir=Path("data"),
        )

    print()
    print("PIPELINE RESULT")
    print("===============")
    print(
        f"REAL JOBS READ          : {len(jobs)}"
    )
    print(
        f"DECISIONS PERSISTED     : {len(decided)}"
    )
    print(
        f"APPLY CANDIDATES        : {len(apply_candidates)}"
    )
    print(
        "EXTERNAL SUBMISSION     : NOT PERFORMED"
    )
    print(
        "BROWSER                  : NOT OPENED"
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run IncomeOS against the real local job database."
    )

    parser.add_argument(
        "--jobs-db",
        default="data/jobs/incomeos_jobs.sqlite3",
    )

    parser.add_argument(
        "--decisions-db",
        default="data/decisions.db",
    )

    parser.add_argument(
        "--repos-root",
        default="data/github_repos",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--opportunity",
        default="Python Automation",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="prepare local application artifacts; never submits externally",
    )

    args = parser.parse_args()

    return run(
        jobs_db=args.jobs_db,
        decisions_db=args.decisions_db,
        repos_root=args.repos_root,
        limit=args.limit,
        opportunity_name=args.opportunity,
        apply=args.apply,
    )


if __name__ == "__main__":
    raise SystemExit(main())
