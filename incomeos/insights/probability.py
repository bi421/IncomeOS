from typing import Any
from .statistical import StatisticalEngine

class ProbabilityEngine:
    def __init__(self, user_skills: list[str], user_experience_years: int = 3):
        self.user_skills = [s.lower() for s in user_skills]
        self.user_experience_years = user_experience_years
        self.history = []  # Өмнөх магадлалуудыг хадгалах

    def calculate(self, job: dict[str, Any], analysis: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
        # 1. Ур чадварын тохирол (40%)
        skill_score = analysis.get("match_score", 0) / 100

        # 2. Туршлагын тохирол (30%)
        exp_required = analysis.get("experience_years", 0)
        exp_score = 0.8 if exp_required == 0 else min(1.0, self.user_experience_years / exp_required)

        # 3. Зах зээлийн эрэлт (20%)
        demand_score = 1.0 if research.get("market_demand") == "HIGH" else 0.6

        # 4. Компанийн эрсдэл (10%)
        risk_score = 0.9 if research.get("risk_level") == "LOW" else 0.5

        # Нийт оноо (weighted average)
        raw_prob = (skill_score * 0.4) + (exp_score * 0.3) + (demand_score * 0.2) + (risk_score * 0.1)
        prob = raw_prob * 100

        # Хэрэв түүх байгаа бол Bayesian шинэчлэлт хийх
        if self.history:
            prior = sum(self.history) / len(self.history)
            # Шинэ магадлалд Bayesian update хийх
            # likelihood = prob / 100 (шинэ мэдээллийн магадлал)
            likelihood = prob / 100
            prior_prob = prior / 100
            # evidence_strength нь түүхийн хэмжээнээс хамаарна
            evidence_strength = min(0.9, len(self.history) / 100)
            updated = StatisticalEngine.bayesian_update(prior_prob, likelihood, evidence_strength)
            prob = updated * 100

        # Variance / Std Dev тооцоолох (түүхээс)
        if len(self.history) > 1:
            variance = StatisticalEngine.variance(self.history)
            std_dev = StatisticalEngine.std_dev(self.history)
            lower, upper = StatisticalEngine.confidence_interval(prob, std_dev, len(self.history))
        else:
            variance = 0.0
            std_dev = 0.0
            lower = max(0, prob - 15)
            upper = min(100, prob + 15)

        # Түүхэнд нэмэх
        self.history.append(prob)

        # Зөвлөмж
        if prob >= 70:
            recommendation = "✅ Өндөр магадлалтай. Шууд өргөдлөө явуулаарай."
        elif prob >= 40:
            recommendation = "🟡 Дунд магадлалтай. Cover letter-ээ сайжруулаарай."
        else:
            recommendation = "🔴 Бага магадлалтай. Дутагдаж буй ур чадвараа судал."

        return {
            "probability": round(prob, 2),
            "variance": round(variance, 2),
            "std_dev": round(std_dev, 2),
            "confidence_interval": (round(lower, 2), round(upper, 2)),
            "skill_score": round(skill_score * 100, 2),
            "experience_score": round(exp_score * 100, 2),
            "demand_score": round(demand_score * 100, 2),
            "risk_score": round(risk_score * 100, 2),
            "recommendation": recommendation
        }
