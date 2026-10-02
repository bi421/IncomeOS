# Evidence Aggregation Formula

IncomeOS confidence is an evidence signal, not a professional-level claim.

For each skill and repository:

    weighted_strength = evidence.strength × DIMENSION_WEIGHTS[evidence.dimension]

For a skill, the strongest weighted score from each repository is retained. Let S be the strongest repository score. A repetition bonus is added: min(0.20, 0.05 × (repository_count - 1)). Project-evidence confidence is clamped to [0, 1]. Human-verified records may add 0.05 per verified record, capped at 0.15, and the final confidence is clamped to [0, 1].

Formally:

    raw = min(1, S + min(0.20, 0.05 × max(repository_count - 1, 0)))
    final = min(1, raw + min(0.15, 0.05 × verified_evidence_count))

Implementation: `incomeos/skills/aggregator.py`.

This score is not job seniority, employability, or professional certification. Capability A/B/UNKNOWN is classified separately by evidence breadth in `incomeos/skills/levels.py`.
