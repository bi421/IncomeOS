from __future__ import annotations
import json
import re
from typing import Any, Optional
from dataclasses import dataclass, field

@dataclass
class SkillRequirement:
    name: str
    level: str  # "essential", "preferred", "nice_to_have"
    description: str = ""

@dataclass
class JobAnalysis:
    title: str
    company: str
    url: str
    raw_description: str
    mongolian_summary: str          # Монгол хэл дээрх хураангуй
    essential_skills: list[str]     # Заавал шаардлагатай ур чадвар
    preferred_skills: list[str]     # Давуу тал болох ур чадвар
    skill_match_score: float        # 0-1
    is_match: bool                  # Тохирч байна уу?
    reason: str                     # Яагаад тохирч/тохирохгүй байна
    required_actions: list[str] = field(default_factory=list)  # Юу хийх вэ

class JobAnalyzer:
    def __init__(self, user_skills: list[str], user_experience: str = ""):
        self.user_skills = [s.lower().strip() for s in user_skills]
        self.user_experience = user_experience

    def analyze(self, raw_job: dict[str, Any]) -> JobAnalysis:
        """Ажлын байрны тодорхойлолтыг шинжлэх (LLM-гүйгээр энгийн шүүлтүүр)"""
        title = raw_job.get("title", "")
        company = raw_job.get("company", "Unknown")
        url = raw_job.get("url", "")
        description = raw_job.get("description", "")

        # 1. Монгол хэлний хураангуй (энгийн орчуулга)
        mongolian_summary = self._generate_mongolian_summary(title, company)

        # 2. Шаардлагатай ур чадваруудыг гаргаж авах
        essential, preferred = self._extract_skills_from_description(description)

        # 3. Таны ур чадвартай харьцуулах
        essential_match = [s for s in essential if s.lower() in self.user_skills]
        preferred_match = [s for s in preferred if s.lower() in self.user_skills]

        match_score = len(essential_match) / max(len(essential), 1)
        is_match = match_score >= 0.4  # 40%+ тохирч байвал авах

        # 4. Шалтгаан тайлбар
        if is_match:
            reason = f"✅ Таны {len(essential_match)}/{len(essential)} заавал ур чадвар тохирч байна."
            if preferred_match:
                reason += f" Мөн {len(preferred_match)} давуу ур чадвар тохирч байна."
            required_actions = ["Хамрах бичиг бэлтгэх", "Өргөдөл явуулах"]
        else:
            missing = [s for s in essential if s.lower() not in self.user_skills]
            reason = f"❌ Дараах заавал ур чадварууд танд байхгүй: {', '.join(missing[:3])}"
            required_actions = ["Суралцах", "Холбогдох төсөл хийх", "Энэ ажлыг алгасах"]

        return JobAnalysis(
            title=title,
            company=company,
            url=url,
            raw_description=description[:500],
            mongolian_summary=mongolian_summary,
            essential_skills=essential[:5],
            preferred_skills=preferred[:3],
            skill_match_score=round(match_score, 2),
            is_match=is_match,
            reason=reason,
            required_actions=required_actions
        )

    def _generate_mongolian_summary(self, title: str, company: str) -> str:
        return f"📌 **{title}** – {company} компанид ажиллах боломж. Дэлгэрэнгүй мэдээллийг доороос харна уу."

    def _extract_skills_from_description(self, text: str) -> tuple[list[str], list[str]]:
        # Жишээ ур чадварын жагсаалт (бодит байдал дээр NLP эсвэл LLM ашиглах)
        common_skills = [
            "python", "java", "javascript", "typescript", "c++", "react",
            "node", "docker", "kubernetes", "aws", "azure", "gcp",
            "sql", "postgresql", "mongodb", "fastapi", "django", "flask",
            "machine learning", "data engineering", "devops", "ci/cd",
            "testing", "api", "microservices", "git", "linux", "redis"
        ]
        text_lower = text.lower()
        essential = []
        preferred = []
        for skill in common_skills:
            if skill in text_lower:
                if skill in self.user_skills:
                    essential.append(skill)
                else:
                    preferred.append(skill)
        return essential[:10], preferred[:5]
