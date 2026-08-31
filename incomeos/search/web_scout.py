from __future__ import annotations

import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from duckduckgo_search import DDGS
from incomeos.skills.aggregator import build_master_profile
from incomeos.tracking.database import get_db


def _ensure_web_table() -> None:
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS web_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            snippet TEXT,
            matched_skills TEXT,
            found_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def search_opportunities(
    repos_root: str,
    max_results: int = 5,
) -> List[Dict]:
    _ensure_web_table()
    profile = build_master_profile(repos_root)

    top_skills = sorted(
        [(s.name, s.confidence) for s in profile.skills if s.confidence > 0.5],
        key=lambda x: x[1],
        reverse=True,
    )[:2]

    if not top_skills:
        print("No strong skills found (confidence > 0.5). Skipping web search.")
        return []

    skill_names = [s[0] for s in top_skills]
    query = " ".join([f'"{name}"' for name in skill_names]) + " freelance OR remote OR contract job"
    print(f"Searching: {query}")

    opportunities: List[Dict] = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results, safesearch="moderate")
            for r in results:
                opportunities.append({
                    "title": r.get("title", "Unknown"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "matched_skills": skill_names,
                    "found_at": datetime.now().isoformat(),
                })
    except Exception as e:
        print(f"Web search failed: {e}")
        return []

    conn = get_db()
    for opp in opportunities:
        conn.execute(
            "INSERT INTO web_opportunities (title, url, snippet, matched_skills, found_at) VALUES (?, ?, ?, ?, ?)",
            (opp["title"], opp["url"], opp["snippet"], json.dumps(opp["matched_skills"]), opp["found_at"]),
        )
    conn.commit()
    conn.close()

    return opportunities


if __name__ == "__main__":
    results = search_opportunities("data/github_repos", max_results=3)
    print(f"\nFound {len(results)} opportunities:")
    for r in results:
        print(f"  - {r['title']}")
        print(f"    URL: {r['url']}")
        print(f"    Skills: {r['matched_skills']}")
        print()
