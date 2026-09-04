from __future__ import annotations
import json
import sqlite3
import urllib.error
from pathlib import Path
from typing import Any, Iterable

from incomeos.jobs.models.job import Job
from incomeos.jobs.sources import ArbeitnowSource, RemoteOKSource, WeWorkRemotelySource
from incomeos.jobs.normalization.normalizer import normalize_job
from .database import JobDatabase
from .result import SourceRunResult, PipelineRunResult

def _valid_job(job: Job) -> bool:
    return bool(job.title and job.url)

def run_pipeline(data_dir: Path) -> PipelineRunResult:
    db_path = data_dir / "jobs" / "incomeos_jobs.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = JobDatabase(db_path)

    sources = [
        ("arbeitnow", ArbeitnowSource()),
        ("remoteok", RemoteOKSource()),
        ("weworkremotely", WeWorkRemotelySource()),
    ]

    source_results: list[SourceRunResult] = []
    total_fetched = 0
    total_validated = 0
    total_inserted = 0
    total_existing = 0
    total_skipped = 0
    total_failed = 0

    for name, source in sources:
        try:
            raw_jobs = [normalize_job(j) for j in source.fetch()]
            valid_jobs = [j for j in raw_jobs if _valid_job(j)]
            inserted, existing = db.upsert_many(valid_jobs)
            skipped = len(raw_jobs) - len(valid_jobs)

            total_fetched += len(raw_jobs)
            total_validated += len(valid_jobs)
            total_inserted += inserted
            total_existing += existing
            total_skipped += skipped

            source_results.append(SourceRunResult(
                source=name,
                fetched=len(raw_jobs),
                validated=len(valid_jobs),
                inserted=inserted,
                existing=existing,
                skipped=skipped,
                failed=False,
            ))
        except Exception as exc:
            total_failed += 1
            source_results.append(SourceRunResult(
                source=name,
                fetched=0,
                validated=0,
                inserted=0,
                existing=0,
                skipped=0,
                failed=True,
                error=str(exc),
            ))

    return PipelineRunResult(
        sources=tuple(source_results),
        total_fetched=total_fetched,
        total_validated=total_validated,
        total_inserted=total_inserted,
        total_existing=total_existing,
        total_skipped=total_skipped,
        total_failed=total_failed,
    )