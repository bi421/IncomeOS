from __future__ import annotations
import json
import socket
import sqlite3
import urllib.error
from pathlib import Path
from typing import Any

from.database import JobDatabase
from.result import SourceRunResult

def _valid_job(job: Any) -> bool:
    if isinstance(job, dict):
        return bool(job.get("title") and job.get("url"))
    # Job dataclass
    title = getattr(job, "title", "")
    url = getattr(job, "url", "") or getattr(job, "source_url", "")
    return bool(title and url)

def _get_source(name: str):
    if name == "arbeitnow":
        from.sources.arbeitnow import ArbeitnowSource
        return ArbeitnowSource()
    elif name == "remoteok":
        from.sources.remoteok import RemoteOKSource
        return RemoteOKSource()
    raise ValueError(f"Unknown source: {name}")

def _to_dict(job: Any) -> dict[str, Any]:
    if isinstance(job, dict):
        return job
    if hasattr(job, "to_dict"):
        return job.to_dict()
    return {
        "source": getattr(job, "source", ""),
        "title": getattr(job, "title", ""),
        "url": getattr(job, "url", "") or getattr(job, "source_url", ""),
        "company": getattr(job, "company", ""),
        "description": getattr(job, "description", ""),
        "created_at": getattr(job, "created_at", ""),
        "raw_data": str(getattr(job, "raw_data", {})),
    }

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
            dict_jobs = [_to_dict(j) for j in raw]
            validated_jobs = [j for j in dict_jobs if _valid_job(j)]
            skipped = len(dict_jobs) - len(validated_jobs)
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