from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from typing import Any
from .models import JobOffer

class Storage:
    def __init__(self, path: Path = Path("data/normalized.db")):
        self.path = path
        self._init_db()

    def _init_db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                title TEXT,
                company TEXT,
                url TEXT UNIQUE,
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT,
                location_text TEXT,
                country TEXT,
                remote INTEGER,
                description TEXT,
                created_at TEXT,
                raw_data TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save(self, offer: JobOffer):
        conn = sqlite3.connect(str(self.path))
        conn.execute("""
            INSERT OR IGNORE INTO job_offers (
                source, title, company, url,
                salary_min, salary_max, salary_currency,
                location_text, country, remote,
                description, created_at, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            offer.source, offer.title, offer.company, str(offer.url),
            offer.salary.min if offer.salary else None,
            offer.salary.max if offer.salary else None,
            offer.salary.currency if offer.salary else "USD",
            offer.location.text,
            offer.location.country,
            1 if offer.location.remote else 0,
            offer.description,
            offer.created_at,
            json.dumps(offer.raw_data)
        ))
        conn.commit()
        conn.close()
