import math
from typing import Any

class StatisticalEngine:
    @staticmethod
    def variance(data: list[float]) -> float:
        if len(data) < 2:
            return 0.0
        mean = sum(data) / len(data)
        return sum((x - mean) ** 2 for x in data) / (len(data) - 1)

    @staticmethod
    def std_dev(data: list[float]) -> float:
        return math.sqrt(StatisticalEngine.variance(data))

    @staticmethod
    def confidence_interval(prob: float, std_dev: float, n: int = 1) -> tuple[float, float]:
        # 95% confidence interval (Z-score ~ 1.96)
        margin = 1.96 * (std_dev / math.sqrt(max(n, 1)))
        lower = max(0, prob - margin)
        upper = min(100, prob + margin)
        return lower, upper

    @staticmethod
    def bayesian_update(prior_prob: float, likelihood: float, evidence_strength: float = 0.5) -> float:
        # P(A|B) = P(B|A) * P(A) / P(B)
        # evidence_strength нь шинэ мэдээллийн итгэлцлийг илэрхийлнэ (0-1)
        posterior = (likelihood * prior_prob) / ((likelihood * prior_prob) + (1 - likelihood) * (1 - prior_prob) * (1 - evidence_strength))
        return min(100, max(0, posterior))
