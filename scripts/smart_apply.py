import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.jobs.integration import get_jobs_by_skill
from incomeos.insights import JobAnalyzer, JobResearcher, ProbabilityEngine
from incomeos.skills.aggregator import build_master_profile

def main():
    print("\n" + "=" * 70)
    print("  🧠 УХААЛАГ ШИНЖИЛГЭЭТЭЙ АЖЛЫН ХАЙЛТ")
    print("=" * 70)

    # Таны ур чадвар (GitHub-с илрүүлсэн)
    profile = build_master_profile("data/github_repos")
    user_skills = [s.name.lower() for s in profile.skills[:8]]
    print(f"📊 Таны ур чадвар: {', '.join(user_skills)}")

    # Ажил татах
    jobs = []
    for skill in ["python", "data", "devops"]:
        jobs.extend(get_jobs_by_skill(skill, limit=15))
    print(f"📥 {len(jobs)} ажил олдлоо")

    analyzer = JobAnalyzer(user_skills)
    researcher = JobResearcher()
    prob_engine = ProbabilityEngine(user_skills, user_experience_years=3)

    matches = []
    for job in jobs:
        analysis = analyzer.analyze(job)
        if not analysis["is_good_fit"]:
            continue
        research = researcher.research(job)
        prob = prob_engine.calculate(job, analysis, research)

        # Бүгдийг нэгтгэх
        matches.append({
            **job,
            "analysis": analysis,
            "research": research,
            "probability": prob
        })

    # Эрэмбэлэх
    matches.sort(key=lambda x: x["probability"]["probability"], reverse=True)

    print(f"\n✅ ТОХИРСОН АЖЛУУД: {len(matches)}\n")

    for i, job in enumerate(matches[:10], 1):
        print("=" * 70)
        print(f"{i}. {job['title']} – {job['company']}")
        print(f"   🌐 {job['url']}")
        print(f"   📊 Тохирлын оноо: {job['analysis']['match_score']}%")
        print(f"   📈 Амжилтын магадлал: {job['probability']['probability']}%")
        print(f"   🔧 Дутагдаж буй ур чадвар: {', '.join(job['analysis']['missing_skills'][:3])}")
        print(f"   🏢 Салбар: {job['research']['industry']} | Хэмжээ: {job['research']['company_size']}")
        print(f"   💡 Зөвлөмж: {job['probability']['recommendation']}")

    # Хадгалах
    if matches:
        with open("data/smart_jobs.txt", "w", encoding="utf-8") as f:
            for job in matches[:20]:
                f.write(f"{job['title']} | {job['company']} | {job['url']} | {job['probability']['probability']}%\n")
        print("\n💾 data/smart_jobs.txt файлд хадгалагдсан.")

if __name__ == "__main__":
    main()
