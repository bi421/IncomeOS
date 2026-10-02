from __future__ import annotations

import re
from collections.abc import Iterable

from incomeos.jobs.models.job import Job


_WORD = re.compile(r"[a-z0-9+#.\-]+", re.IGNORECASE)


def _contains_skill(text: str, skill: str) -> bool:
    skill = skill.strip().lower()
    if not skill:
        return False
    haystack = text.lower()
    if skill in haystack:
        return True
    tokens = set(_WORD.findall(haystack))
    required = [x for x in _WORD.findall(skill) if len(x) > 1]
    return bool(required) and all(x in tokens for x in required)


def match_job(job: Job, skills: Iterable[str]) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
    """Score a job only from explicit skill names; never invent requirements."""
    unique = tuple(dict.fromkeys(s.strip() for s in skills if s.strip()))
    if not unique:
        return 0.0, (), ()

    text = f"{job.title} {job.description}"
    matched = tuple(skill for skill in unique if _contains_skill(text, skill))
    missing = tuple(skill for skill in unique if skill not in matched)
    score = len(matched) / len(unique)
    return score, matched, missing
