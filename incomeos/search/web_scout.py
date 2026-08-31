from __future__ import annotations
import json
import re
from datetime import datetime
from typing import List, Dict
import requests
import feedparser
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

def _extract_urls_from_markdown(md: str) -> List[Dict[str, str]]:
    """Markdown-аас ажлын зарын холбоосуудыг ялгаж авах."""
    jobs = []
    # [Title](URL) pattern
    for match in re.finditer(r'\[([^\]]+)\]\((https?://[^\)]+)\)', md):
        title, url = match.group(1), match.group(2)
        # Зөвхөн ажлын зарын холбоосуудыг шүүх
        if any(domain in url.lower() for domain in [
            'jobs.lever.co', 'boards.greenhouse.io', 'apply.workable.com',
            'linkedin.com/jobs', 'angel.co', 'wellfound.com', 'remoteok.com',
            'weworkremotely.com', 'authenticjobs.com', 'stackoverflow.com/jobs'
        ]):
            jobs.append({'title': title.strip(), 'url': url.strip()})
    return jobs

def _search_github_curated_lists(skill_names: List[str], max_per_repo: int = 10) -> List[Dict]:
    """GitHub дээрх curated job list-үүдээс ажлын заруудыг парс хийх."""
    print(f"📚 GitHub Curated Lists парс хийж байна...")
    
    repos = [
        'lukasz-madon/awesome-remote-job',
        'engineerapart/TheRemoteFreelancer',
        'ugglr/Remote-Developer-jobs-directory'
    ]
    
    opportunities = []
    for repo in repos:
        try:
            url = f'https://api.github.com/repos/{repo}/readme'
            headers = {'Accept': 'application/vnd.github.v3.raw'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                jobs = _extract_urls_from_markdown(resp.text)
                for job in jobs[:max_per_repo]:
                    opportunities.append({
                        'title': job['title'],
                        'url': job['url'],
                        'snippet': f'From {repo}',
                        'matched_skills': skill_names,
                        'source': 'github_curated',
                        'found_at': datetime.now().isoformat(),
                    })
                print(f"  ✅ {repo}: {len(jobs)} боломж олдлоо")
        except Exception as e:
            print(f"  ⚠️ {repo}: {e}")
    
    return opportunities

def _search_rss_feeds(skill_names: List[str], max_per_feed: int = 10) -> List[Dict]:
    """RSS feed-үүдээс ажлын заруудыг авах."""
    print(f"📡 RSS Feeds-ээс хайж байна...")
    
    feeds = [
        ('We Work Remotely', 'https://weworkremotely.com/categories/remote-programming-jobs.rss'),
        ('RemoteOK', 'https://remoteok.com/feed'),
    ]
    
    opportunities = []
    skill_pattern = re.compile('|'.join([re.escape(s.lower()) for s in skill_names]), re.IGNORECASE)
    
    for name, feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries[:30]:  # Эхний 30 entry-г шалгах
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                
                # Чадварын дагуу шүүх
                if skill_pattern.search(title + ' ' + summary):
                    opportunities.append({
                        'title': title,
                        'url': link,
                        'snippet': summary[:200] if summary else '',
                        'matched_skills': skill_names,
                        'source': f'rss_{name.lower().replace(" ", "_")}',
                        'found_at': datetime.now().isoformat(),
                    })
                    count += 1
                    if count >= max_per_feed:
                        break
            print(f"  ✅ {name}: {count} тохирох ажлын зар олдлоо")
        except Exception as e:
            print(f"  ⚠️ {name}: {e}")
    
    return opportunities

def _search_remoteok_api(skill_names: List[str], max_results: int = 10) -> List[Dict]:
    """RemoteOK JSON API ашиглах."""
    print(f"🌐 RemoteOK API-аас хайж байна...")
    
    opportunities = []
    try:
        resp = requests.get('https://remoteok.com/api', timeout=10, 
                           headers={'User-Agent': 'IncomeOS/1.0'})
        if resp.status_code == 200:
            jobs = resp.json()[1:]  # Эхний элемент нь metadata
            skill_pattern = re.compile('|'.join([re.escape(s.lower()) for s in skill_names]), re.IGNORECASE)
            
            for job in jobs[:100]:
                position = job.get('position', '')
                description = job.get('description', '')
                if skill_pattern.search(position + ' ' + description):
                    opportunities.append({
                        'title': position,
                        'url': job.get('url', ''),
                        'snippet': f"{job.get('company', '')} - {job.get('location', '')}",
                        'matched_skills': skill_names,
                        'source': 'remoteok_api',
                        'found_at': datetime.now().isoformat(),
                    })
                    if len(opportunities) >= max_results:
                        break
            print(f"  ✅ RemoteOK: {len(opportunities)} тохирох ажлын зар")
    except Exception as e:
        print(f"  ⚠️ RemoteOK: {e}")
    
    return opportunities

def _search_general_jobs(skill_names: List[str], max_results: int = 5) -> List[Dict]:
    """DuckDuckGo-оор ерөнхий хайлт."""
    print(f"🔍 Ерөнхий хайлт (DuckDuckGo)...")
    
    skills_query = " AND ".join([f'"{s}"' for s in skill_names[:2]])
    query = f"{skills_query} AND (remote OR freelance) AND (upwork OR freelancer OR wellfound.com)"
    
    opportunities = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results, safesearch="off")
            for r in results:
                opportunities.append({
                    'title': r.get('title', 'Unknown'),
                    'url': r.get('href', ''),
                    'snippet': r.get('body', ''),
                    'matched_skills': skill_names,
                    'source': 'general_search',
                    'found_at': datetime.now().isoformat(),
                })
    except Exception as e:
        print(f"  ⚠️ DuckDuckGo: {e}")
    
    return opportunities

def search_opportunities(repos_root: str, max_results: int = 5) -> List[Dict]:
    _ensure_web_table()
    profile = build_master_profile(repos_root)
    
    top_skills = sorted(
        [(s.name, s.confidence) for s in profile.skills if s.confidence > 0.6],
        key=lambda x: x[1], reverse=True
    )[:3]
    
    if not top_skills:
        print("⚠️ Хангалттай өндөр оноотой чадвар олдсонгүй.")
        return []
    
    skill_names = [s[0] for s in top_skills]
    print(f"🎯 Таны зорилтот чадварууд: {', '.join(skill_names)}\n")
    
    # Бүх эх үүсвэрээс хайх
    all_opportunities = []
    all_opportunities.extend(_search_github_curated_lists(skill_names))
    all_opportunities.extend(_search_rss_feeds(skill_names))
    all_opportunities.extend(_search_remoteok_api(skill_names))
    all_opportunities.extend(_search_general_jobs(skill_names, max_results))
    
    # Database-д хадгалах
    conn = get_db()
    for opp in all_opportunities:
        conn.execute(
            "INSERT INTO web_opportunities (title, url, snippet, matched_skills, source, found_at) VALUES (?, ?, ?, ?, ?, ?)",
            (opp['title'], opp['url'], opp['snippet'], json.dumps(opp['matched_skills']), opp['source'], opp['found_at']),
        )
    conn.commit()
    conn.close()
    
    return all_opportunities

if __name__ == "__main__":
    print("🚀 IncomeOS Multi-Source Web Scout\n")
    results = search_opportunities("data/github_repos", max_results=5)
    
    print(f"\n✅ Нийт {len(results)} боломж олдлоо:\n")
    
    # Эх үүсвэрээр бүлэглэж харуулах
    by_source = {}
    for r in results:
        src = r.get('source', 'unknown')
        by_source.setdefault(src, []).append(r)
    
    for source, items in by_source.items():
        print(f"📦 {source.upper()} ({len(items)}):")
        for i, r in enumerate(items[:3], 1):  # Эхний 3-г харуулах
            print(f"  [{i}] {r['title']}")
            print(f"      🔗 {r['url']}\n")
