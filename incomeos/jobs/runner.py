from __future__ import annotations
import json
import socket
import sqlite3
import urllib.error
from pathlib import Path
from .database import JobDatabase
from .result import SourceRunResult

def _valid_job(job) -> bool:
    """Validate the common Job adapter contract before persistence."""
    return bool(getattr(job, "title", "") and getattr(job, "source_url", ""))

# Эх үүсвэрүүдийг динамикаар импортлох
def _get_source(name: str):
    if name == "arbeitnow":
        from .sources.arbeitnow import ArbeitnowSource
        return ArbeitnowSource()
    elif name == "remoteok":
        from .sources.remoteok import RemoteOKSource
        return RemoteOKSource()
    raise ValueError(f"Unknown source: {name}")

def run_pipeline(
    data_dir: Path,
    sources: tuple[str, ...] = ("arbeitnow", "remoteok"),
) -> list[SourceRunResult]:
    db_path = data_dir / "jobs" / "incomeos_jobs.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = JobDatabase(db_path)
    results: list[SourceRunResult] = []

    for name in sources:
        try:
            raw = list(_get_source(name).fetch())

            validated_jobs = [j for j in raw if _valid_job(j)]
            skipped = len(raw) - len(validated_jobs)

            inserted, existing = db.upsert_many(
                [job.to_dict() for job in validated_jobs]
            )

            results.append(SourceRunResult(
                source=name,
                fetched=len(raw),
                validated=len(validated_jobs),
                inserted=inserted,
                existing=existing,
                skipped=skipped,
                failed=False,
            ))
        except (urllib.error.URLError, socket.timeout,
                json.JSONDecodeError, sqlite3.Error,
                ValueError, TypeError) as exc:
            results.append(SourceRunResult(
                source=name,
                fetched=0,
                inserted=0,
                existing=0,
                failed=True,
                error=str(exc),
            ))
        except Exception as exc:
            results.append(SourceRunResult(
                source=name,
                fetched=0,
                inserted=0,
                existing=0,
                failed=True,
                error=f"Unexpected: {exc}",
            ))
    return results
