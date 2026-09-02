
from __future__ import annotations

import ast
import html
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedJob:
    job_id: str
    title: str
    company: str
    url: str
    description: str
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": (
        "python",
        "python 3",
    ),
    "C++": (
        "c++",
        "cpp",
    ),
    "Docker": (
        "docker",
        "docker environments",
    ),
    "CMake": (
        "cmake",
        "cmake build",
    ),
    "Testing": (
        "automated testing",
        "test automation",
        "testing",
        "pytest",
        "unit testing",
        "integration testing",
    ),
    "Data Engineering": (
        "data engineering",
        "data pipeline",
        "data pipelines",
        "data processing",
        "etl",
        "data infrastructure",
    ),
    "Flask": (
        "flask",
    ),
    "SQLite": (
        "sqlite",
    ),
    "Pydantic": (
        "pydantic",
    ),
    "Polars": (
        "polars",
    ),
    "Pandas": (
        "pandas",
    ),
    "NumPy": (
        "numpy",
        "numpy",
    ),
}


def parse_raw_job(raw_data: str | dict) -> dict:
    if isinstance(raw_data, dict):
        return raw_data

    if not isinstance(raw_data, str):
        raise TypeError(
            "raw_data must be str or dict"
        )

    value = raw_data.strip()

    if not value:
        raise ValueError(
            "raw_data is empty"
        )

    parsed = ast.literal_eval(value)

    if not isinstance(parsed, dict):
        raise ValueError(
            "raw_data must decode to a dictionary"
        )

    return parsed


def clean_html(value: str) -> str:
    text = html.unescape(
        value or ""
    )

    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"</(p|li|h1|h2|h3|h4|h5|h6|div|br|ul|ol)>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = html.unescape(text)

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n[ \t]+",
        "\n",
        text,
    )

    return text.strip()


def _section(
    description: str,
    starts: tuple[str, ...],
    stops: tuple[str, ...],
) -> str:
    lower = description.lower()

    start_positions = [
        lower.find(marker.lower())
        for marker in starts
    ]

    valid_starts = [
        position
        for position in start_positions
        if position >= 0
    ]

    if not valid_starts:
        return ""

    start = min(valid_starts)
    end = len(description)

    for marker in stops:
        position = lower.find(
            marker.lower(),
            start + 1,
        )

        if position >= 0:
            end = min(end, position)

    return description[start:end]


def _find_skills(
    text: str,
    available_skills: tuple[str, ...],
) -> tuple[str, ...]:
    lower = text.lower()

    found: list[str] = []

    for skill in available_skills:
        aliases = SKILL_ALIASES.get(
            skill,
            (skill.lower(),),
        )

        if any(
            re.search(
                rf"(?<!\w){re.escape(alias.lower())}(?!\w)",
                lower,
            )
            for alias in aliases
        ):
            found.append(skill)

    return tuple(
        sorted(
            set(found),
            key=str.lower,
        )
    )


def extract_requirements(
    *,
    description: str,
    available_skills: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required_section = _section(
        description,
        starts=(
            "required skills",
            "required skills & experiences",
            "required background & skills",
            "required skills and experience",
            "required:",
        ),
        stops=(
            "preferred skills",
            "preferred background",
            "nice to have",
            "nice to haves",
            "benefits",
            "salary",
            "compensation",
        ),
    )

    preferred_section = _section(
        description,
        starts=(
            "preferred skills",
            "preferred background",
            "nice to have",
            "nice to haves",
        ),
        stops=(
            "benefits",
            "salary",
            "compensation",
        ),
    )

    required = _find_skills(
        required_section,
        available_skills,
    )

    preferred = _find_skills(
        preferred_section,
        available_skills,
    )

    preferred = tuple(
        skill
        for skill in preferred
        if skill not in required
    )

    return required, preferred


def parse_job_record(
    *,
    job_id: str | int,
    title: str,
    company: str,
    url: str,
    raw_data: str | dict,
    available_skills: tuple[str, ...],
) -> ParsedJob:
    data = parse_raw_job(
        raw_data
    )

    raw_description = str(
        data.get(
            "description",
            "",
        )
    )

    description = clean_html(
        raw_description
    )

    required, preferred = extract_requirements(
        description=description,
        available_skills=available_skills,
    )

    return ParsedJob(
        job_id=str(job_id),
        title=str(
            data.get(
                "title",
                title,
            )
        ),
        company=str(
            data.get(
                "company_name",
                company,
            )
        ),
        url=str(
            data.get(
                "url",
                url,
            )
        ),
        description=description,
        required_skills=required,
        preferred_skills=preferred,
    )
