from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import ActionResult, ActionState, ExecutionLog

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
            error_log TEXT,
            executed_command TEXT,
            externally_submitted INTEGER NOT NULL DEFAULT 0,
            externally_confirmed INTEGER NOT NULL DEFAULT 0
        )
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(executions)")}
    migrations = {
        "executed_command": "TEXT",
        "externally_submitted": "INTEGER NOT NULL DEFAULT 0",
        "externally_confirmed": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, definition in migrations.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE executions ADD COLUMN {column} {definition}")
    conn.commit()
    return conn

def log_start(opp_name: str, command: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO executions (opportunity_name, action_command, status, started_at) VALUES (?, ?, ?, ?)",
        (opp_name, command, ActionState.PLANNED.value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return cur.lastrowid

def log_finish(log_id: int, result: ActionResult) -> None:
    conn = get_db()
    conn.execute(
        """
        UPDATE executions
        SET status=?, finished_at=?, exit_code=?, output_log=?, error_log=?,
            executed_command=?, externally_submitted=?, externally_confirmed=?
        WHERE id=?
        """,
        (
            result.state.value,
            datetime.now().isoformat(),
            result.exit_code,
            result.output_log,
            result.error_log,
            " ".join(result.executed_command),
            int(result.externally_submitted),
            int(result.externally_confirmed),
            log_id,
        )
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
        return ExecutionLog(
            id=row[0],
            opportunity_name=row[1],
            action_command=row[2],
            state=_state_from_database(row[3]),
            started_at=datetime.fromisoformat(row[4]),
            finished_at=datetime.fromisoformat(row[5]) if row[5] else None,
            exit_code=row[6],
            output_log=row[7] or "",
            error_log=row[8] or "",
            executed_command=row[9] or "",
            externally_submitted=bool(row[10]),
            externally_confirmed=bool(row[11]),
        )
    return None


def _state_from_database(value: str) -> ActionState:
    """Read legacy status values without treating them as business success."""
    legacy = {"success": ActionState.EXECUTED, "running": ActionState.PLANNED}
    if value in legacy:
        return legacy[value]
    try:
        return ActionState(value)
    except ValueError:
        return ActionState.FAILED
