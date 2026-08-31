from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import ExecutionLog

DB_PATH = Path("data/incomeos.db")

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_name TEXT NOT NULL,
            action_command TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            exit_code INTEGER,
            output_log TEXT,
            error_log TEXT
        )
    """)
    conn.commit()
    return conn

def log_start(opp_name: str, command: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO executions (opportunity_name, action_command, status, started_at) VALUES (?, ?, ?, ?)",
        (opp_name, command, "running", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return cur.lastrowid

def log_finish(log_id: int, status: str, exit_code: int, output: str, error: str):
    conn = get_db()
    conn.execute(
        "UPDATE executions SET status=?, finished_at=?, exit_code=?, output_log=?, error_log=? WHERE id=?",
        (status, datetime.now().isoformat(), exit_code, output, error, log_id)
    )
    conn.commit()
    conn.close()

def get_recent_execution(opp_name: str, hours: int = 24) -> Optional[ExecutionLog]:
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM executions WHERE opportunity_name=? AND started_at > datetime('now', '-' || ? || ' hours') ORDER BY started_at DESC LIMIT 1",
        (opp_name, hours)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return ExecutionLog(id=row[0], opportunity_name=row[1], action_command=row[2], status=row[3],
                            started_at=datetime.fromisoformat(row[4]), finished_at=datetime.fromisoformat(row[5]) if row[5] else None,
                            exit_code=row[6], output_log=row[7] or "", error_log=row[8] or "")
    return None
