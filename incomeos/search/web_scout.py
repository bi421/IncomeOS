from __future__ import annotations
import json
import re
from datetime import datetime
from typing import List, Dict, Tuple
import requests
import feedparser
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


# ---------------------------------------------------------------------------
# Individual job-posting sources
#
# Each source function returns (opportunities, error_message).
# error_message is None on success (even if 0 matches were found — that is a
# legitimate "no match" result, not a failure). It is set to a human-readable
# string when the source could not be reached or returned something unusable,
# so failures are visible to the caller instead of silently producing an
# empty list that looks identical to "genuinely no jobs found".
# ---------------------------------------------------------------------------

def _search_remotive_api(skill_names: List[str], max_results: int = 15) -> Tuple[List[Dict], str | None]:
    """Remotive-ийн үнэгүй, нээлттэй API-аас бодит, тусдаа ажлын зар авах.
    Баримт бичиг: https://remotive.com/api/remote-jobs (auth шаардахгүй)."""
    print("🌐 Remotive API-аас хайж байна...")
    opportunities: List[Dict] = []
    try:
        search_term = skill_names[0] if skill_names else "python"
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": search_term, "limit": max_results},
            timeout=15,
            headers={"User-Agent": "IncomeOS/1.0 (job-search tool)"},
        )
        if resp.status_code != 200:
            return [], f"Remotive HTTP {resp.status_code}: {resp.text[:200]}"

        jobs = resp.json().get("jobs", [])
        skill_pattern = re.compile(
            "|".join(re.escape(s.lower()) for s in skill_names), re.IGNORECASE
        )
        for job in jobs:
            haystack = f"{job.get('title', '')} {job.get('description', '')}"
            if not skill_names or skill_pattern.search(haystack):
                opportunities.append({
                    "title": job.get("title", "Unknown"),
                    "url": job.get("url", ""),
                    "snippet": f"{job.get('company_name', '')} — {job.get('candidate_required_location', '')}",
                    "matched_skills": skill_names,
                    "source": "remotive_api",
                    "found_at": datetime.now().isoformat(),
                })
        print(f"  ✅ Remotive: {len(opportunities)} тохирох ажлын зар")
        return opportunities, None
    except requests.exceptions.RequestException as e:
        return [], f"Remotive request failed: {e}"
    except (ValueError, KeyError) as e:
        return [], f"Remotive response parse failed: {e}"


def _search_arbeitnow_api(skill_names: List[str], max_results: int = 15) -> Tuple[List[Dict], str | None]:
    """Arbeitnow-ийн үнэгүй, нээлттэй API-аас бодит ажлын зар авах.
    Баримт бичиг: https://www.arbeitnow.com/api/job-board-api (auth шаардахгүй)."""
    print("🌐 Arbeitnow API-аас хайж байна...")
    opportunities: List[Dict] = []
    try:
        resp = requests.get(
            "https://www.arbeitnow.com/api/job-board-api",
            timeout=15,
            headers={"User-Agent": "IncomeOS/1.0 (job-search tool)"},
        )
        if resp.status_code != 200:
            return [], f"Arbeitnow HTTP {resp.status_code}: {resp.text[:200]}"

        jobs = resp.json().get("data", [])
        skill_pattern = re.compile(
            "|".join(re.escape(s.lower()) for s in skill_names), re.IGNORECASE
        )
        for job in jobs:
            haystack = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}"
            if not skill_names or skill_pattern.search(haystack):
                opportunities.append({
                    "title": job.get("title", "Unknown"),
                    "url": job.get("url", ""),
                    "snippet": f"{job.get('company_name', '')} — {job.get('location', '')}",
                    "matched_skills": skill_names,
                    "source": "arbeitnow_api",
                    "found_at": datetime.now().isoformat(),
                })
                if len(opportunities) >= max_results:
                    break
        print(f"  ✅ Arbeitnow: {len(opportunities)} тохирох ажлын зар")
        return opportunities, None
    except requests.exceptions.RequestException as e:
        return [], f"Arbeitnow request failed: {e}"
    except (ValueError, KeyError) as e:
        return [], f"Arbeitnow response parse failed: {e}"


def _search_rss_feeds(skill_names: List[str], max_per_feed: int = 10) -> Tuple[List[Dict], str | None]:
    """RSS feed-үүдээс ажлын заруудыг авах."""
    print("📡 RSS Feeds-ээс хайж байна...")

    feeds = [
        ("We Work Remotely", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
        ("RemoteOK", "https://remoteok.com/feed"),
    ]

    opportunities: List[Dict] = []
    errors: List[str] = []
    skill_pattern = re.compile(
        "|".join(re.escape(s.lower()) for s in skill_names), re.IGNORECASE
    )

    for name, feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            if feed.get("bozo") and not feed.entries:
                errors.append(f"{name}: feed unreadable ({feed.get('bozo_exception')})")
                print(f"  ⚠️ {name}: feed unreadable — {feed.get('bozo_exception')}")
                continue

            count = 0
            for entry in feed.entries[:30]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                if skill_pattern.search(title + " " + summary):
                    opportunities.append({
                        "title": title,
                        "url": link,
                        "snippet": summary[:200] if summary else "",
                        "matched_skills": skill_names,
                        "source": f"rss_{name.lower().replace(' ', '_')}",
                        "found_at": datetime.now().isoformat(),
                    })
                    count += 1
                    if count >= max_per_feed:
                        break
            print(f"  ✅ {name}: {count} тохирох ажлын зар олдлоо")
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  ⚠️ {name}: {e}")

    return opportunities, "; ".join(errors) if errors else None


def search_opportunities(repos_root: str, max_results: int = 15) -> List[Dict]:
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

    all_opportunities: List[Dict] = []
    source_errors: List[str] = []

    for search_fn in (_search_remotive_api, _search_arbeitnow_api, _search_rss_feeds):
        opps, err = search_fn(skill_names)
        all_opportunities.extend(opps)
        if err:
            source_errors.append(f"[{search_fn.__name__}] {err}")

    if all_opportunities:
        conn = get_db()
        for opp in all_opportunities:
            conn.execute(
                "INSERT INTO web_opportunities (title, url, snippet, matched_skills, source, found_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (opp["title"], opp["url"], opp["snippet"], json.dumps(opp["matched_skills"]),
                 opp["source"], opp["found_at"]),
            )
        conn.commit()
        conn.close()

    if source_errors:
        print("\n⚠️  Дараах эх сурвалжуудаас алдаа гарсан тул дүн бүрэн биш байж болзошгүй:")
        for e in source_errors:
            print(f"   - {e}")

    return all_opportunities


if __name__ == "__main__":
    print("🚀 IncomeOS Multi-Source Web Scout\n")
    results = search_opportunities("data/github_repos", max_results=15)

    print(f"\n✅ Нийт {len(results)} боломж олдлоо:\n")

    by_source: Dict[str, List[Dict]] = {}
    for r in results:
        src = r.get("source", "unknown")
        by_source.setdefault(src, []).append(r)

    for source, items in by_source.items():
        print(f"📦 {source.upper()} ({len(items)}):")
        for i, r in enumerate(items[:5], 1):
            print(f"  [{i}] {r['title']}")
            print(f"      🔗 {r['url']}\n")

    if not results:
        print("Илэрц олдоогүй тохиолдолд дээрх алдааны мэдээллийг шалгана уу — "
              "хайлт нэг ч эх сурвалжид хүрч чадаагүй байж магадгүй.")