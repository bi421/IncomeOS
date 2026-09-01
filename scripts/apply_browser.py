from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.decision import DecisionEngine
from incomeos.applications import apply_to_jobs
from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities

def main():
    print("\n🌐 OPENING BROWSER FOR APPLICATIONS")
    profile = build_master_profile("data/github_repos")
    matches = match_opportunities(profile)
    if not matches:
        print("No opportunities")
        return
    top = matches[0]
    skills = list(top.opportunity.required_skills)
    limit_per_skill = 5

    for skill in skills:
        print(f"\n📌 Opening {limit_per_skill} jobs for skill: {skill}")
        apply_to_jobs(skill, limit=limit_per_skill, open_browser=True)

if __name__ == "__main__":
    main()
