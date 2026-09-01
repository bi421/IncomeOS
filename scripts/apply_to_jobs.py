from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.decision import DecisionEngine
from incomeos.applications import run_application_pipeline

def main():
    print("\n" + "=" * 60)
    print("  📬 AUTOMATED JOB APPLICATION SYSTEM")
    print("=" * 60)

    # 1. Шийдвэр гаргах
    decision = DecisionEngine.decide("data/github_repos", force=True)
    if not decision or not decision.is_actionable:
        print("❌ No actionable decision found. Run pipeline first.")
        return

    print(f"🎯 Target Opportunity: {decision.opportunity_name}")
    required_skills = list(decision.action.opportunity_name) # Бидэнд жагсаалт хэрэгтэй

    # 2. Бодит боломжийн шаардлагатай ур чадварыг авах
    # Аюулгүй байдлын үүднээс Python кодыг шууд ашиглах
    from incomeos.skills.aggregator import build_master_profile
    from incomeos.opportunities.engine import match_opportunities
    profile = build_master_profile("data/github_repos")
    matches = match_opportunities(profile)
    if matches:
        top = matches[0]
        skills = list(top.opportunity.required_skills)
    else:
        skills = ["Python", "Testing"]  # fallback

    print(f"🔧 Required Skills: {skills}")

    # 3. Өргөдөл явуулах
    run_application_pipeline(decision.opportunity_name, skills, limit_per_skill=3)

    # 4. Дүн
    print("\n" + "=" * 60)
    print("  📊 APPLICATIONS LOG")
    print("=" * 60)
    import sqlite3
    db_path = Path("data") / "applications.db"
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cur = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]}")
        conn.close()
    else:
        print("   No applications logged yet.")

if __name__ == "__main__":
    main()
