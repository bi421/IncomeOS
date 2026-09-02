
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import sqlite3
from pathlib import Path
from typing import Any


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class VerificationRecord:
    verification_id: int | None
    proposal_id: int
    decision_id: str
    job_id: str
    skill: str
    status: VerificationStatus
    verifier_note: str
    evidence_source: str
    evidence_text: str
    verified_at: str | None


class VerificationStore:
    def __init__(
        self,
        db_path: str | Path = "data/verification.db",
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id INTEGER NOT NULL UNIQUE,
                    decision_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    skill TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verifier_note TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    evidence_text TEXT NOT NULL,
                    verified_at TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_verifications_skill
                ON verifications(skill)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_verifications_status
                ON verifications(status)
                """
            )

            conn.commit()
        finally:
            conn.close()

    def verify(
        self,
        *,
        proposal_id: int,
        decision_id: str,
        job_id: str,
        skill: str,
        evidence_source: str,
        evidence_text: str,
        verifier_note: str = "",
    ) -> VerificationRecord:
        if proposal_id <= 0:
            raise ValueError(
                "proposal_id must be positive"
            )

        if not decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not job_id.strip():
            raise ValueError(
                "job_id must not be empty"
            )

        if not skill.strip():
            raise ValueError(
                "skill must not be empty"
            )

        if not evidence_source.strip():
            raise ValueError(
                "verification requires evidence_source"
            )

        if not evidence_text.strip():
            raise ValueError(
                "verification requires evidence_text"
            )

        verified_at = datetime.now(
            timezone.utc
        ).isoformat()

        conn = self._connect()

        try:
            existing = conn.execute(
                """
                SELECT id
                FROM verifications
                WHERE proposal_id=?
                """,
                (proposal_id,),
            ).fetchone()

            if existing is not None:
                raise ValueError(
                    "proposal has already been verified/rejected"
                )

            cursor = conn.execute(
                """
                INSERT INTO verifications (
                    proposal_id,
                    decision_id,
                    job_id,
                    skill,
                    status,
                    verifier_note,
                    evidence_source,
                    evidence_text,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    decision_id,
                    job_id,
                    skill,
                    VerificationStatus.VERIFIED.value,
                    verifier_note,
                    evidence_source,
                    evidence_text,
                    verified_at,
                ),
            )

            conn.commit()

            return VerificationRecord(
                verification_id=int(cursor.lastrowid),
                proposal_id=proposal_id,
                decision_id=decision_id,
                job_id=job_id,
                skill=skill,
                status=VerificationStatus.VERIFIED,
                verifier_note=verifier_note,
                evidence_source=evidence_source,
                evidence_text=evidence_text,
                verified_at=verified_at,
            )
        finally:
            conn.close()

    def reject(
        self,
        *,
        proposal_id: int,
        decision_id: str,
        job_id: str,
        skill: str,
        reason: str,
        evidence_source: str = "",
        evidence_text: str = "",
    ) -> VerificationRecord:
        if proposal_id <= 0:
            raise ValueError(
                "proposal_id must be positive"
            )

        if not reason.strip():
            raise ValueError(
                "rejection reason must not be empty"
            )

        conn = self._connect()

        try:
            existing = conn.execute(
                """
                SELECT id
                FROM verifications
                WHERE proposal_id=?
                """,
                (proposal_id,),
            ).fetchone()

            if existing is not None:
                raise ValueError(
                    "proposal already has a verification decision"
                )

            cursor = conn.execute(
                """
                INSERT INTO verifications (
                    proposal_id,
                    decision_id,
                    job_id,
                    skill,
                    status,
                    verifier_note,
                    evidence_source,
                    evidence_text,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    decision_id,
                    job_id,
                    skill,
                    VerificationStatus.REJECTED.value,
                    reason,
                    evidence_source,
                    evidence_text,
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
                ),
            )

            conn.commit()

            return VerificationRecord(
                verification_id=int(cursor.lastrowid),
                proposal_id=proposal_id,
                decision_id=decision_id,
                job_id=job_id,
                skill=skill,
                status=VerificationStatus.REJECTED,
                verifier_note=reason,
                evidence_source=evidence_source,
                evidence_text=evidence_text,
                verified_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )
        finally:
            conn.close()

    def list_verified(
        self,
        skill: str | None = None,
    ) -> tuple[VerificationRecord, ...]:
        conn = self._connect()

        try:
            if skill is None:
                rows = conn.execute(
                    """
                    SELECT
                        id,
                        proposal_id,
                        decision_id,
                        job_id,
                        skill,
                        status,
                        verifier_note,
                        evidence_source,
                        evidence_text,
                        verified_at
                    FROM verifications
                    WHERE status=?
                    ORDER BY id
                    """,
                    (VerificationStatus.VERIFIED.value,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT
                        id,
                        proposal_id,
                        decision_id,
                        job_id,
                        skill,
                        status,
                        verifier_note,
                        evidence_source,
                        evidence_text,
                        verified_at
                    FROM verifications
                    WHERE status=? AND skill=?
                    ORDER BY id
                    """,
                    (
                        VerificationStatus.VERIFIED.value,
                        skill,
                    ),
                ).fetchall()
        finally:
            conn.close()

        return tuple(
            VerificationRecord(
                verification_id=int(row[0]),
                proposal_id=int(row[1]),
                decision_id=row[2],
                job_id=row[3],
                skill=row[4],
                status=VerificationStatus(row[5]),
                verifier_note=row[6],
                evidence_source=row[7],
                evidence_text=row[8],
                verified_at=row[9],
            )
            for row in rows
        )
