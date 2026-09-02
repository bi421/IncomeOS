import re
from typing import Any

class JobAnalyzer:
    def __init__(self, user_skills: list[str]):
        self.user_skills = [s.lower().strip() for s in user_skills]

    def analyze(self, job: dict[str, Any]) -> dict[str, Any]:
        text = (job.get("title", "") + " " + job.get("desc", "") + " " + job.get("raw", "")).lower()

        # 1. Шаардлагатай ур чадвар
        required_skills = self._extract_required_skills(text)
        optional_skills = self._extract_optional_skills(text)

        # 2. Туршлага (years)
        experience_years = self._extract_experience(text)

        # 3. Тохирлын оноо
        match_skills = [s for s in required_skills if s in self.user_skills]
        match_score = len(match_skills) / max(len(required_skills), 1)

        # 4. Дутагдаж буй ур чадвар
        missing_skills = [s for s in required_skills if s not in self.user_skills]

        return {
            "required_skills": required_skills,
            "optional_skills": optional_skills,
            "experience_years": experience_years,
            "match_score": round(match_score * 100, 2),
            "match_skills": match_skills,
            "missing_skills": missing_skills,
            "is_good_fit": match_score >= 0.4
        }

    def _extract_required_skills(self, text: str) -> list[str]:
        # Жишээ ур чадварууд (бодит байдал дээр NLP эсвэл LLM)
        common = ["python", "fastapi", "django", "flask", "postgresql", "mysql",
                  "docker", "kubernetes", "aws", "azure", "redis", "git", "ci/cd",
                  "machine learning", "data engineering", "testing", "api"]
        found = [s for s in common if s in text]
        return found

    def _extract_optional_skills(self, text: str) -> list[str]:
        optional = ["react", "vue", "angular", "javascript", "typescript", "java", "ruby", "c++"]
        found = [s for s in optional if s in text]
        return found

    def _extract_experience(self, text: str) -> int:
        # Regex: "X+ years", "X+ year" гэх мэт
        match = re.search(r"(\d+)\s*(?:\+)?\s*(?:years?|yrs?)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
