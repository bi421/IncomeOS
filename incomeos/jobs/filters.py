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

# A skill name matching somewhere in a job's free-text description is a weak
# signal on its own. Matching is token-aware so that:
#   "testing" does NOT match "Testingenieur"
#   "data" does NOT match unrelated words containing "data"
#
# A match in TITLE or TAGS is strong evidence.
# A match only in DESCRIPTION requires corroboration from a technical role
# hint in the title.

_TECH_ROLE_HINTS = (
    "developer",
    "engineer",
    "engineering",
    "programmer",
    "software",
    "backend",
    "back-end",
    "frontend",
    "front-end",
    "full stack",
    "full-stack",
    "devops",
    "sre",
    "site reliability",
    "data scientist",
    "data engineer",
    "qa",
    "test engineer",
    "sdet",
    "coder",
)

_EXCLUDE_TITLE_TERMS = (
    "counsel",
    "attorney",
    "legal",
    "regulatory",
    "compliance officer",
    "recruiter",
    "recruiting",
    "talent acquisition",
    "marketing",
    "sales",
    "account executive",
    "business development",
    "human resources",
    " hr ",
    "hr manager",
    "hr specialist",
    "nurse",
    "clinical",
    "physician",
    "therapist",
    "pharmacist",
    "accountant",
    "bookkeeper",
    "paralegal",
    "underwriter",
    "brand manager",
    "product manager",
    "deployment lead",
)


def _build_skill_pattern(skill_names: Iterable[str]) -> re.Pattern:
    """Build a token-aware pattern for skill matching.

    The lookarounds prevent substring false positives such as:
        testing -> Testingenieur

    while still allowing normal separators such as:
        Python-based
        Python/Backend
        C++ developer
    """
    keywords = [s.strip().lower() for s in skill_names if s and s.strip()]
    if not keywords:
        return re.compile(r"(?!x)x")

    escaped = sorted(
        (re.escape(k) for k in keywords),
        key=len,
        reverse=True,
    )

    return re.compile(
        r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)",
        re.IGNORECASE,
    )


def _build_role_hint_pattern() -> re.Pattern:
    """Build a token-aware pattern for technical role corroboration."""
    hints = [h.strip().lower() for h in _TECH_ROLE_HINTS if h and h.strip()]
    escaped = sorted(
        (re.escape(h) for h in hints),
        key=len,
        reverse=True,
    )

    return re.compile(
        r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)",
        re.IGNORECASE,
    )


_ROLE_HINT_PATTERN = _build_role_hint_pattern()


def is_relevant(
    title: str,
    description: str,
    tags: Optional[Iterable[str]] = None,
    skill_names: Optional[List[str]] = None,
) -> bool:
    """Canonical relevance check used by every job source.

    A job is relevant only if:
      - its title does NOT contain a non-technical role term, AND
      - a skill keyword appears in the title or tags (strong signal), OR
      - a skill keyword appears in the description AND the title contains
        a generic technical-role word (weak signal, needs corroboration).
    """
    title_l = (title or "").lower()

    if any(term in title_l for term in _EXCLUDE_TITLE_TERMS):
        return False

    keywords = tuple(skill_names) if skill_names else DEFAULT_FOCUS_SKILLS
    if not keywords:
        return True

    pattern = _build_skill_pattern(keywords)

    tag_text = " ".join(tags or []).lower()
    if tag_text and pattern.search(tag_text):
        return True

    if pattern.search(title_l):
        return True

    desc_l = (description or "").lower()
    if pattern.search(desc_l) and _ROLE_HINT_PATTERN.search(title_l):
        return True

    return False
