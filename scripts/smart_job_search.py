from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.jobs.integration import get_jobs_by_skill
from incomeos.job_analyzer import JobAnalyzer

def main():
    print("\n" + "=" * 60)
    print("  🧠 SMART JOB ANALYZER – ТАНЫ ӨМНӨӨС АЖИЛЛАНА")
    print("=" * 60)

    # 1. Таны ур чадварыг татаж авах
    profile = build_master_profile("data/github_repos")
    user_skills = [s.name.lower() for s in profile.skills[:8]]  # Топ 8 ур чадвар
    print(f"📊 Таны илэрсэн ур чадвар: {', '.join(user_skills)}")

    # 2. Ажлын байрнуудыг татаж авах
    all_jobs = []
    for skill in ["python", "data", "devops"]:
        jobs = get_jobs_by_skill(skill, limit=20)
        all_jobs.extend(jobs)
    print(f"📥 Нийт {len(all_jobs)} ажлын байр олдлоо.")

    # 3. Шинжлэх
    analyzer = JobAnalyzer(user_skills)
    matches = []
    skipped = 0

    for job in all_jobs:
        analysis = analyzer.analyze(job)
        if analysis.is_match:
            matches.append(analysis)
        else:
            skipped += 1

    # 4. Дэлгэрэнгүй танилцуулга
    print(f"\n✅ Тохирсон ажлын байр: {len(matches)}")
    print(f"❌ Шүүгдсэн: {skipped}\n")

    for i, match in enumerate(matches[:10], 1):
        print("=" * 60)
        print(f"{i}. {match.title} – {match.company}")
        print(f"   URL: {match.url}")
        print(f"   📊 Тохирлын оноо: {match.skill_match_score*100:.0f}%")
        print(f"   📝 {match.reason}")
        print(f"   🔧 Заавал ур чадвар: {', '.join(match.essential_skills)}")
        print(f"   📌 Монгол хэлний хураангуй: {match.mongolian_summary}")
        print(f"   🚀 Үйлдэл: {', '.join(match.required_actions)}")

    print("\n" + "=" * 60)
    print(f"✅ Шинжилгээ дууслаа. {len(matches)} ажил тохирч байна.")
    print("📌 Дээрх URL-уудыг нээгээд өргөдлөө явуулна уу.")

    # 5. Тохирсон ажлуудыг файлд хадгалах
    if matches:
        output = Path("data") / "matched_jobs.txt"
        with open(output, "w", encoding="utf-8") as f:
            f.write("ТОХИРСОН АЖЛЫН БАЙРНУУД\n")
            f.write("=" * 60 + "\n\n")
            for m in matches:
                f.write(f"📌 {m.title} – {m.company}\n")
                f.write(f"   URL: {m.url}\n")
                f.write(f"   Оноо: {m.skill_match_score*100:.0f}%\n")
                f.write(f"   Шалтгаан: {m.reason}\n\n")
        print(f"💾 Тохирсон ажлуудыг {output} файлд хадгалсан.")
