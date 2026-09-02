
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

from incomeos.applications.engine import apply_to_jobs
from incomeos.decision.job_decision import persist_job_decision
from incomeos.decision.persistence import DecisionStore
from incomeos.skills.aggregator import build_master_profile


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
    lookup = {
        column.lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    return None


def discover_job_table(
    db_path: str | Path,
) -> tuple[str, tuple[str, ...]]:
    path = Path(db_path)

    if not path.exists():
        raise FileNotFoundError(
            f"job database not found: {path}"
        )

    conn = sqlite3.connect(path)

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

        best: tuple[int, str, tuple[str, ...]] | None = None

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

        if best is None:
            raise ValueError(
                "job database contains no tables"
            )

        if best[0] < 5:
            raise ValueError(
                "could not identify a compatible job table"
            )

        return best[1], best[2]

    finally:
        conn.close()


def load_jobs(
    db_path: str | Path,
    limit: int = 10,
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

    company_column = _pick_column(
        columns,
        ("company", "company_name", "employer"),
    )

    url_column = _pick_column(
        columns,
        ("url", "job_url", "link"),
    )

    if not id_column or not title_column:
        raise ValueError(
            "job table does not expose id and title"
        )

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
        index = 0

        job_id = row[index]
        index += 1

        title = row[index]
        index += 1

        company = ""

        if company_column:
            company = row[index]
            index += 1

        url = ""

        if url_column:
            url = row[index]

        jobs.append(
            {
                "id": job_id,
                "title": title,
                "company": company or "",
                "url": url or "",
            }
        )

    return tuple(jobs)


def run(
    *,
    jobs_db: str | Path = "data/jobs/incomeos_jobs.sqlite3",
    decisions_db: str | Path = "data/decisions.db",
    repos_root: str | Path = "data/github_repos",
    limit: int = 10,
    opportunity_name: str = "Python Automation",
    prepare: bool = False,
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
    print(f"PREPARE    : {prepare}")

    print()
    print("[1/5] Building current evidence profile...")

    master_profile = build_master_profile(
        repos_root
    )

    print(
        f"Repository count: {master_profile.repository_count}"
    )

    print(
        f"Skill count     : {len(master_profile.skills)}"
    )

    print()
    print("[2/5] Discovering job table...")

    table, columns = discover_job_table(
        jobs_db
    )

    print(
        f"TABLE   : {table}"
    )

    print(
        f"COLUMNS : {', '.join(columns)}"
    )

    print()
    print("[3/5] Loading real jobs...")

    jobs = load_jobs(
        jobs_db,
        limit=limit,
    )

    print(
        f"JOBS LOADED: {len(jobs)}"
    )

    if not jobs:
        print()
        print("No jobs available.")
        return 0

    print()
    print("[4/5] Running concrete job decisions...")

    store = DecisionStore(
        decisions_db
    )

    decided = []

    for job in jobs:
        # The existing local jobs table may not contain structured
        # skill requirements. We therefore use the explicitly selected
        # opportunity requirement instead of inferring skills from title.
        job_for_fit = dict(job)

        if opportunity_name == "Python Automation":
            job_for_fit["required_skills"] = [
                "Python"
            ]
        else:
            job_for_fit["required_skills"] = []

        if not job_for_fit["required_skills"]:
            print(
                f"SKIP {job['id']} | "
                f"{job['title']} | "
                "no explicit requirement mapping"
            )
            continue

        result = persist_job_decision(
            job=job_for_fit,
            opportunity_name=opportunity_name,
            profile={
                "capabilities": (),
                "skills": master_profile.skills,
            },
            store=store,
        )

        decided.append(
            (job, result)
        )

        print(
            f"{job['id']} | "
            f"{job['title']} | "
            f"fit={result.fit.fit_score:.3f} | "
            f"decision={result.decision.decision} | "
            f"decision_id={result.decision.decision_id}"
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

    if prepare and apply_candidates:
        print()
        print(
            "Preparing local application artifacts only."
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
        f"REAL JOBS READ       : {len(jobs)}"
    )
    print(
        f"DECISIONS PERSISTED  : {len(decided)}"
    )
    print(
        f"APPLY CANDIDATES     : {len(apply_candidates)}"
    )
    print(
        "EXTERNAL SUBMISSION  : NOT PERFORMED"
    )
    print(
        "BROWSER OPENED       : NO"
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run IncomeOS against the local real job database."
        )
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
        "--prepare",
        action="store_true",
        help=(
            "create local application artifacts only; "
            "never submit externally"
        ),
    )

    args = parser.parse_args()

    return run(
        jobs_db=args.jobs_db,
        decisions_db=args.decisions_db,
        repos_root=args.repos_root,
        limit=args.limit,
        opportunity_name=args.opportunity,
        prepare=args.prepare,
    )


if __name__ == "__main__":
    raise SystemExit(main())
