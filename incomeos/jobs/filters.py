from __future__ import annotations

import re
from typing import Iterable, List, Optional

DEFAULT_FOCUS_SKILLS: tuple[str, ...] = (
    "Python",
    "Testing",
    "Data Engineering",
    "C++",
    "Docker",
    "CMake",
)


def _build_skill_pattern(skill_names: Iterable[str]) -> re.Pattern:
    keywords = [s.lower() for s in skill_names]
    return re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)


def is_relevant(
    title: str,
    description: str,
    tags: Optional[Iterable[str]] = None,
    skill_names: Optional[List[str]] = None,
) -> bool:
    """Shared relevance check — extracted from incomeos/search/web_scout.py.

    Returns True when *title*, *description*, or *tags* contain at least one
    of the provided *skill_names*.  When *skill_names* is ``None`` or empty
    the project's DEFAULT_FOCUS_SKILLS are used instead.
    """
    keywords = tuple(skill_names) if skill_names else DEFAULT_FOCUS_SKILLS
    pattern = _build_skill_pattern(keywords)
    haystack = f"{title} {description} {' '.join(tags or [])}"
    return bool(pattern.search(haystack))
