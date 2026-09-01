from __future__ import annotations
from pathlib import Path
import sqlite3
import json
from typing import Any

def get_jobs_db_path(data_dir: Path = Path("data")) -> Path:
    return data_dir / "jobs" / "incomeos_jobs.sqlite3"

def _parse_raw(raw_data: Any) -> dict:
    if raw_data is None:
        return {}
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except:
            return {}
    if isinstance(raw_data, dict):
        return raw_data
    return {}

def _get_company(raw_data: Any) -> str:
    data = _parse_raw(raw_data)
    # Бүх боломжит түлхүүрүүд
    for key in ["company_name", "company", "Company", "employer", "organization"]:
        if key in data and data[key]:
            val = data[key]
            if isinstance(val, str):
                return val.strip()
            return str(val)
    return "Unknown"

def _get_description(raw_data: Any) -> str:
    data = _parse_raw(raw_data)
    for key in ["description", "Description", "desc"]:
        if key in data and data[key]:
            val = data[key]
            if isinstance(val, str):
                return val.strip()[:500]
            return str(val)[:500]
    return ""

def get_jobs_by_skill(skill: str, limit: int = 10, db_path: Path | None = None) -> list[dict[str, Any]]:
    if db_path is None:
        db_path = get_jobs_db_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT id, source, title, url, created_at, raw_data FROM jobs WHERE title LIKE ? OR raw_data LIKE ? LIMIT ?",
        (f"%{skill}%", f"%{skill}%", limit)
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        raw = d.get("raw_data")
        d["company"] = _get_company(raw)
        d["description"] = _get_description(raw)
        result.append(d)
    return result

def count_jobs_by_skill(skill: str, db_path: Path | None = None) -> int:
    if db_path is None:
        db_path = get_jobs_db_path()
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE title LIKE ? OR raw_data LIKE ?",
        (f"%{skill}%", f"%{skill}%")
    )
    count = cur.fetchone()[0]
    conn.close()
    return count

def count_jobs_by_skills(skills: list[str], db_path: Path | None = None) -> dict[str, int]:
    return {skill: count_jobs_by_skill(skill, db_path) for skill in skills}
