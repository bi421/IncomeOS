from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Tuple
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests

from incomeos.jobs.filters import is_relevant
from incomeos.skills.aggregator import build_master_profile
from incomeos.tracking.database import get_db


def _canonical_url(value: str) -> str:
    parts = urlsplit((value or "").strip())
    if not parts.scheme or not parts.netloc:
        return (value or "").strip()
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, "")
    )


def _ensure_web_table() -> None:
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS web_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            snippet TEXT,
            matched_skills TEXT,
            source TEXT DEFAULT 'general',
            found_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _search_remotive_api(
    skill_names: List[str], max_results: int = 15
) -> Tuple[List[Dict], str | None]:
    """Fetch real Remotive listings; source failure remains visible to caller."""
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
        for job in jobs:
            if not skill_names or is_relevant(
                job.get("title", ""),
                job.get("description", ""),
                None,
                skill_names,
            ):
                opportunities.append(
                    {
                        "title": job.get("title", "Unknown"),
                        "url": job.get("url", ""),
                        "snippet": f"{job.get('company_name', '')} — "
                        f"{job.get('candidate_required_location', '')}",
                        "matched_skills": skill_names,
                        "source": "remotive_api",
                        "found_at": datetime.now().isoformat(),
                    }
                )
        print(f"  ✅ Remotive: {len(opportunities)} тохирох ажлын зар")
        return opportunities, None
    except requests.exceptions.RequestException as exc:
        return [], f"Remotive request failed: {exc}"
    except (ValueError, KeyError) as exc:
        return [], f"Remotive response parse failed: {exc}"


def _search_arbeitnow_api(
    skill_names: List[str], max_results: int = 15
) -> Tuple[List[Dict], str | None]:
    """Fetch real Arbeitnow listings; source failure remains visible to caller."""
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
        for job in jobs:
            if not skill_names or is_relevant(
                job.get("title", ""),
                job.get("description", ""),
                job.get("tags", []),
                skill_names,
            ):
                opportunities.append(
                    {
                        "title": job.get("title", "Unknown"),
                        "url": job.get("url", ""),
                        "snippet": f"{job.get('company_name', '')} — "
                        f"{job.get('location', '')}",
                        "matched_skills": skill_names,
                        "source": "arbeitnow_api",
                        "found_at": datetime.now().isoformat(),
                    }
                )
                if len(opportunities) >= max_results:
                    break
        print(f"  ✅ Arbeitnow: {len(opportunities)} тохирох ажлын зар")
        return opportunities, None
    except requests.exceptions.RequestException as exc:
        return [], f"Arbeitnow request failed: {exc}"
    except (ValueError, KeyError) as exc:
        return [], f"Arbeitnow response parse failed: {exc}"


def _search_rss_feeds(
    skill_names: List[str], max_per_feed: int = 10
) -> Tuple[List[Dict], str | None]:
    """Fetch matching jobs from RSS feeds."""
    print("📡 RSS Feeds-ээс хайж байна...")

    feeds = [
        ("We Work Remotely", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
        ("RemoteOK", "https://remoteok.com/feed"),
    ]

    opportunities: List[Dict] = []
    errors: List[str] = []

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

                if not skill_names or is_relevant(title, summary, None, skill_names):
                    opportunities.append(
                        {
                            "title": title,
                            "url": link,
                            "snippet": summary[:200] if summary else "",
                            "matched_skills": skill_names,
                            "source": f"rss_{name.lower().replace(' ', '_')}",
                            "found_at": datetime.now().isoformat(),
                        }
                    )
                    count += 1
                    if count >= max_per_feed:
                        break
            print(f"  ✅ {name}: {count} тохирох ажлын зар олдлоо")
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            print(f"  ⚠️ {name}: {exc}")

    return opportunities, "; ".join(errors) if errors else None


def search_opportunities(repos_root: str, max_results: int = 15) -> List[Dict]:
    """Return at most max_results unique opportunities across all sources.

    max_results is a global output bound, not a per-source bound. A new call
    performs a fresh source fetch; this function does not terminate after the
    first successful result set.
    """
    if max_results < 1:
        raise ValueError("max_results must be >= 1")

    _ensure_web_table()
    profile = build_master_profile(repos_root)

    top_skills = sorted(
        [(s.name, s.confidence) for s in profile.skills if s.confidence > 0.6],
        key=lambda x: x[1],
        reverse=True,
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

    unique: List[Dict] = []
    seen_urls: set[str] = set()
    for opp in all_opportunities:
        url = _canonical_url(str(opp.get("url", "")))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        normalized = dict(opp)
        normalized["url"] = url
        unique.append(normalized)
        if len(unique) >= max_results:
            break

    if unique:
        conn = get_db()
        for opp in unique:
            conn.execute(
                "INSERT INTO web_opportunities "
                "(title, url, snippet, matched_skills, source, found_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    opp["title"],
                    opp["url"],
                    opp["snippet"],
                    json.dumps(opp["matched_skills"]),
                    opp["source"],
                    opp["found_at"],
                ),
            )
        conn.commit()
        conn.close()

    if source_errors:
        print("\n⚠️  Дараах эх сурвалжуудаас алдаа гарсан тул дүн бүрэн биш байж болзошгүй:")
        for error in source_errors:
            print(f"   - {error}")

    return unique


if __name__ == "__main__":
    print("🚀 IncomeOS Multi-Source Web Scout\n")
    results = search_opportunities("data/github_repos", max_results=15)

    print(f"\n✅ Нийт {len(results)} боломж олдлоо:\n")

    by_source: Dict[str, List[Dict]] = {}
    for result in results:
        source = result.get("source", "unknown")
        by_source.setdefault(source, []).append(result)

    for source, items in by_source.items():
        print(f"📦 {source.upper()} ({len(items)}):")
        for index, result in enumerate(items[:5], 1):
            print(f"  [{index}] {result['title']}")
            print(f"      🔗 {result['url']}\n")

    if not results:
        print(
            "Илэрц олдоогүй тохиолдолд дээрх алдааны мэдээллийг шалгана уу — "
            "хайлт нэг ч эх сурвалжид хүрч чадаагүй байж магадгүй."
        )
