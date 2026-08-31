from __future__ import annotations
import json
from datetime import datetime
from typing import List, Dict
from duckduckgo_search import DDGS
from incomeos.skills.aggregator import build_master_profile
from incomeos.tracking.database import get_db

def search_opportunities(repos_root: str, max_results: int = 5) -> List[Dict]:
    """Автоном интернэт хайлт хийж, ур чадварт тохирох боломжуудыг олж ирнэ."""
    profile = build_master_profile(repos_root)
    
    # Хамгийн өндөр оноотой 2 ур чадварыг авна
    top_skills = sorted(
        [(s.skill, s.confidence) for s in profile.skills if s.confidence > 0.5],
        key=lambda x: x[1],
        reverse=True
    )[:2]
    
    if not top_skills:
        return []
        
    skill_query = " AND ".join([f'"{skill}" freelance OR remote OR contract' for skill, _ in top_skills])
    
    opportunities = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(skill_query, max_results=max_results, safesearch='moderate')
            for r in results:
                opportunities.append({
                    "title": r.get("title", "Unknown"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "matched_skills": [s[0] for s in top_skills],
                    "found_at": datetime.now().isoformat()
                })
    except Exception as e:
        print(f"⚠️ Web search failed: {e}")
        return []

    # Үр дүнг database-д хадгалах (шинэ хүснэгт эсвэл executions руу)
    conn = get_db()
    for opp in opportunities:
        conn.execute(
            """INSERT INTO web_opportunities (title, url, snippet, matched_skills, found_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (opp["title"], opp["url"], opp["snippet"], json.dumps(opp["matched_skills"]), opp["found_at"])
        )
    conn.commit()
    conn.close()
    
    return opportunities