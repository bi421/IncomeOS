from __future__ import annotations

from dataclasses import dataclass

from .detector import detect_skills
from .github_analyzer import analyze_repository
from .models import Skill


@dataclass(frozen=True)
class ProfileReport:
    repository: str
    skills: tuple[Skill, ...]

    @property
    def skill_count(self) -> int:
        return len(self.skills)


def build_profile(repository_path: str) -> ProfileReport:
    evidence = analyze_repository(repository_path)
    skill_evidence = detect_skills(evidence)

    from .evidence import build_skills

    skills = build_skills(list(skill_evidence))

    repository_name = (
        evidence[0].repository
        if evidence
        else repository_path
    )

    return ProfileReport(
        repository=repository_name,
        skills=skills,
    )