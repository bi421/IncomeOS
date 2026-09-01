from __future__ import annotations
import json
import socket
import sqlite3
import urllib.error
from pathlib import Path
from typing import Any

from .database import JobDatabase
from .result import SourceRunResult

# Энгийн валидаци
def _valid_job(job: dict[str, Any]) -> bool:
    return bool(job.get("title") and job.get("url"))

# Эх үүсвэрүүдийг динамикаар импортлох
def _get_source(name: str):
    if name == "arbeitnow":
        from .sources import arbeitnow
        return arbeitnow
    elif name == "remoteok":
        from .sources import remoteok
        return remoteok
    raise ValueError(f"Unknown source: {name}")

def run_pipeline(data_dir: Path) -> list[SourceRunResult]:
    db_path = data_dir / "jobs" / "incomeos_jobs.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = JobDatabase(db_path)
    results: list[SourceRunResult] = []

    sources = ["arbeitnow", "remoteok"]
    for name in sources:
        try:
            source = _get_source(name)
            raw = list(source.fetch())

            validated_jobs = [j for j in raw if _valid_job(j)]
            skipped = len(raw) - len(validated_jobs)

            inserted, existing = db.upsert_many(validated_jobs)

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