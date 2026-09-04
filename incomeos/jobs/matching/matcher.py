"""Skill-to-job matching.

Real implementation. Scores a job against the user's evidence-weighted
skill profile (incomeos.skills.aggregator.MasterSkillProfile), not a flat
skill-name list, so a skill with more repos/tests behind it counts more
than one only mentioned once.

No network calls, no LLM calls, no randomness. Deterministic given the
same job text and profile.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from incomeos.skills.aggregator import MasterSkillProfile
from incomeos.jobs.skill_vocab import SKILL_VOCAB as _SKILL_VOCAB


def _extract_skill_mentions(text: str) -> tuple[str, ...]:
    """Token-aware skill extraction (reuses the same guard as filters.py
    so 'testing' doesn't match 'Testingenieur')."""
    text_l = (text or "").lower()
    found = []
    for skill in _SKILL_VOCAB:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text_l):
            found.append(skill)
    return tuple(found)


@dataclass(frozen=True)
class MatchResult:
    score: float                      # 0.0-1.0
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    is_match: bool
    reason: str


def match_job(job, profile: MasterSkillProfile, threshold: float = 0.4) -> MatchResult:
    """Return a real match score for a job/profile pair.

    Score = sum(confidence of matched skills) / sum(confidence of all
    skills mentioned in the job). A skill you've only touched once
    (low confidence) contributes less than one you've shipped and
    tested repeatedly (high confidence) - this is the whole point of
    using MasterSkillProfile instead of a flat list.
    """
    text = f"{getattr(job, 'title', '')} {getattr(job, 'description', '')}"
    required = _extract_skill_mentions(text)

    if not required:
        return MatchResult(
            score=0.0,
            matched_skills=(),
            missing_skills=(),
            is_match=False,
            reason="Could not detect any skill keywords in the job text.",
        )

    confidence_by_skill = {s.name.lower(): s.confidence for s in profile.skills}

    matched = tuple(s for s in required if s in confidence_by_skill)
    missing = tuple(s for s in required if s not in confidence_by_skill)

    matched_weight = sum(confidence_by_skill[s] for s in matched)
    total_weight = matched_weight + len(missing) * 1.0
    score = matched_weight / total_weight if total_weight > 0 else 0.0

    is_match = score >= threshold

    if is_match:
        reason = (
            f"{len(matched)}/{len(required)} required skills matched "
            f"(weighted score: {score:.2f})."
        )
    else:
        reason = (
            f"Missing: {', '.join(missing[:3]) or 'unclear'} "
            f"(weighted score: {score:.2f}, threshold: {threshold})."
        )

    return MatchResult(
        score=round(score, 4),
        matched_skills=matched,
        missing_skills=missing,
        is_match=is_match,
        reason=reason,
    )