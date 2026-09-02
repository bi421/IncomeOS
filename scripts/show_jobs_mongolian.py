from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.jobs.integration import get_jobs_by_skill_with_description

def main():
    print("\n" + "=" * 60)
    print("  🎯 МОНГОЛ ХЭЛЭЭР АЖЛЫН БАЙРНЫ ТАНИЛЦУУЛГА + ШҮҮЛТҮҮР")
    print("=" * 60)

    # 1. Ур чадварын профайл
    profile = build_master_profile("data/github_repos")
    matches = match_opportunities(profile, min_skill_confidence=0.5)

    if not matches:
        print("❌ Таны хийж чадах боломж олдсонгүй.")
        return

    top = matches[0]
    skills = list(top.opportunity.required_skills)
    print(f"\n✅ Таны сонгогдсон боломж: {top.opportunity.name}")
    print(f"   Шаардлагатай ур чадварууд: {', '.join(skills)}")
    print(f"   Итгэлцүүр: {top.readiness:.2f}\n")

    print("=" * 60)
    print("  📋 ТАНЫ ХИЙЖ ЧАДАХ АЖЛЫН БАЙРНУУД")
    print("=" * 60)

    all_jobs = []
    for skill in skills:
        jobs = get_jobs_by_skill_with_description(skill, limit=3)
        for job in jobs:
            if job not in all_jobs:
                all_jobs.append(job)

    if not all_jobs:
        print("❌ Одоогоор тохирох ажлын байр олдсонгүй. Дараа дахин оролдоно уу.")
        return

    for idx, job in enumerate(all_jobs, start=1):
        print(f"\n📌 {idx}. {job.get('mongolian_description', 'Тайлбар байхгүй')}")
        print("-" * 40)

    print("\n" + "=" * 60)
    print(f"  ✅ НИЙТ {len(all_jobs)} ажлын байр олдлоо.")
    print("  📌 Дээрх холбоосууд дээр дарж, өргөдлөө явуулаарай.")
    print("=" * 60)

if __name__ == "__main__":
    main()
