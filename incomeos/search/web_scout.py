from __future__ import annotations
import json
from datetime import datetime
from typing import List, Dict
from ddgs import DDGS
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
            source TEXT DEFAULT 'general',
            found_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def search_opportunities(repos_root: str, max_results: int = 5) -> List[Dict]:
    _ensure_web_table()
    
    # БИДНИЙ ШИНЭЧЛЭСЭН БОДИТ ЧАДВАРУУД (Job Titles)
    target_roles = [
        "Python code audit",
        "QA automation freelance", 
        "repository health check",
        "data pipeline validation",
        "technical debugging"
    ]
    
    # Хайлтын асуулгыг эдгээр үгс болон платформ руу чиглүүлнэ
    roles_query = " OR ".join([f'"{role}"' for role in target_roles])
    query = f"({roles_query}) AND (remote OR freelance OR contract OR hiring) AND (upwork OR freelancer OR wellfound.com OR remoteok.com OR github.com)"
    
    print(f"🎯 Зорилтот хайлт: {roles_query}")
    print(f"🔍 Хайж байна: {query[:100]}...\n")
    
    opportunities: List[Dict] = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results, safesearch="off")
            for r in results:
                opportunities.append({
                    "title": r.get("title", "Unknown"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "matched_skills": target_roles,
                    "source": "targeted_roles",
                    "found_at": datetime.now().isoformat(),
                })
    except Exception as e:
        print(f"⚠️ Web search failed: {e}")
        return []
        
    conn = get_db()
    for opp in opportunities:
        conn.execute(
            "INSERT INTO web_opportunities (title, url, snippet, matched_skills, source, found_at) VALUES (?, ?, ?, ?, ?, ?)",
            (opp["title"], opp["url"], opp["snippet"], json.dumps(opp["matched_skills"]), opp["source"], opp["found_at"]),
        )
    conn.commit()
    conn.close()
    
    return opportunities

if __name__ == "__main__":
    print("🚀 IncomeOS Web Scout (Targeted Roles) эхэллээ...\n")
    results = search_opportunities("data/github_repos", max_results=5)
    print(f"✅ Нийт {len(results)} бодит боломж олдлоо:\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['title']}")
        print(f"    🔗 {r['url']}\n")
