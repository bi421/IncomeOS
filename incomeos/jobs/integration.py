from __future__ import annotations
from pathlib import Path
import sqlite3
from typing import Any

def get_jobs_db_path(data_dir: Path = Path("data")) -> Path:
    return data_dir / "jobs" / "incomeos_jobs.sqlite3"

def count_jobs_by_skill(skill: str, db_path: Path | None = None) -> int:
    if db_path is None:
        db_path = get_jobs_db_path()
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    # description багана байхгүй тул зөвхөн title болон raw_data дээр хайх
    cur = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE title LIKE ? OR raw_data LIKE ?",
        (f"%{skill}%", f"%{skill}%")
    )
    count = cur.fetchone()[0]
    conn.close()
    return count

def count_jobs_by_skills(skills: list[str], db_path: Path | None = None) -> dict[str, int]:
    return {skill: count_jobs_by_skill(skill, db_path) for skill in skills}
