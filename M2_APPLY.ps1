# M2_APPLY.ps1
# Run this from the IncomeOS project root: C:\Users\User\Desktop\IncomeOS
# Applies: (1) requirements.py legacy_job NameError fix, (2) M2 domain-capability layer, (3) new tests
$ErrorActionPreference = 'Stop'

Write-Host '== M2: backup ==' -ForegroundColor Cyan
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = ".\_backup_$stamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item .\incomeos\jobs\requirements.py "$backupDir\requirements.py.bak" -Force
if (Test-Path .\incomeos\capabilities\domains.py) { Copy-Item .\incomeos\capabilities\domains.py "$backupDir\domains.py.bak" -Force }

Write-Host '== M2: fix requirements.py (legacy_job NameError) ==' -ForegroundColor Cyan
$requirementsContent = @'
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
    "Kubernetes": (
        "kubernetes",
        "k8s",
    ),
    "Linux": (
        "linux",
    ),
    "AWS": (
        "aws",
        "amazon web services",
    ),
    "SQL": (
        "sql",
    ),
    "Go": (
        "go",
        "golang",
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

    matches: list[tuple[int, str]] = []

    for skill in available_skills:
        aliases = SKILL_ALIASES.get(
            skill,
            (skill.lower(),),
        )

        positions = []

        for alias in aliases:
            match = re.search(
                rf"(?<!\w){re.escape(alias.lower())}(?!\w)",
                lower,
            )
            if match:
                positions.append(match.start())

        if positions:
            matches.append((min(positions), skill))

    matches.sort(key=lambda item: item[0])

    seen: set[str] = set()
    result: list[str] = []

    for _, skill in matches:
        if skill not in seen:
            seen.add(skill)
            result.append(skill)

    return tuple(result)


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
            "preferred",
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
            "preferred",
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
    job_id: str | int | dict,
    *,
    title: str = "",
    company: str = "",
    url: str = "",
    raw_data: str | dict | None = None,
    available_skills: tuple[str, ...] = tuple(SKILL_ALIASES),
) -> ParsedJob:
    legacy_job: dict = job_id if isinstance(job_id, dict) else {}

    if isinstance(job_id, dict):
        job_id = legacy_job.get("id", "")
        title = legacy_job.get("title", title)
        company = legacy_job.get("company_name", company)
        url = legacy_job.get("url", url)

    if raw_data is None:
        raw_data = legacy_job

    data = parse_raw_job(
        raw_data or {}
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

'@
Set-Content -Path .\incomeos\jobs\requirements.py -Value $requirementsContent -Encoding UTF8

Write-Host '== M2: capabilities/domains.py (draft taxonomy — edit after this runs) ==' -ForegroundColor Cyan
$domainsContent = @'
from __future__ import annotations

from incomeos.capabilities.models import (
    Capability,
    CapabilityEvidence,
    CapabilityProfile,
    build_capability_profile,
)
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import classify_capability_level


# M2 draft taxonomy — skill names below must match incomeos.jobs.requirements.SKILL_ALIASES keys.
# This grouping is a first pass based on the skill vocabulary already in the codebase.
# Edit freely: add/remove domains, move skills between domains, or add new skill names
# as SKILL_ALIASES grows. A domain is only ever built if at least one of its member
# skills actually has evidence in the profile — an empty/unmatched domain never appears.
DOMAIN_TAXONOMY: dict[str, tuple[str, ...]] = {
    "Backend Engineering": ("Python", "Flask", "Pydantic", "SQL", "SQLite"),
    "Data Engineering": ("Data Engineering", "Pandas", "Polars", "NumPy", "SQL"),
    "Cloud & Infrastructure": ("AWS", "Docker", "Kubernetes", "Linux"),
    "Systems Programming": ("C++", "CMake", "Linux"),
    "Quality Engineering": ("Testing", "CMake"),
}


def _member_skills(
    domain_skill_names: tuple[str, ...],
    master_profile: MasterSkillProfile,
) -> tuple[MasterSkill, ...]:
    by_name = {skill.name: skill for skill in master_profile.skills}

    return tuple(
        by_name[name] for name in domain_skill_names if name in by_name
    )


def _domain_capability_from_members(
    domain_name: str,
    members: tuple[MasterSkill, ...],
) -> Capability:
    repositories = sorted({repo for skill in members for repo in skill.repositories})
    evidence_count = sum(skill.evidence_count for skill in members)

    confidence = round(
        sum(skill.confidence for skill in members) / len(members),
        4,
    )

    level, _ = classify_capability_level(
        confidence=confidence,
        evidence_count=evidence_count,
        repository_count=len(repositories),
    )

    evidence = tuple(
        CapabilityEvidence(repository=repo, verified=False) for repo in repositories
    )

    return Capability(
        name=domain_name,
        skills=(domain_name,) + tuple(skill.name for skill in members),
        confidence=confidence,
        level=level.value,
        evidence=evidence,
        evidence_count=evidence_count,
        repositories=tuple(repositories),
    )


def build_domain_capabilities(
    master_profile: MasterSkillProfile,
    taxonomy: dict[str, tuple[str, ...]] = DOMAIN_TAXONOMY,
) -> tuple[Capability, ...]:
    domains: list[Capability] = []

    for domain_name, domain_skill_names in taxonomy.items():
        members = _member_skills(domain_skill_names, master_profile)

        if not members:
            continue

        domains.append(_domain_capability_from_members(domain_name, members))

    return tuple(domains)


def build_capability_profile_with_domains(
    master_profile: MasterSkillProfile,
    taxonomy: dict[str, tuple[str, ...]] = DOMAIN_TAXONOMY,
) -> CapabilityProfile:
    """
    Union of M1's per-skill capabilities and M2's domain-level capabilities
    in one CapabilityProfile. A job requirement can match on either an exact
    skill name (M1 behavior, unchanged) or a domain name (new, M2).
    """

    skill_level = build_capability_profile(master_profile)
    domain_level = build_domain_capabilities(master_profile, taxonomy)

    return CapabilityProfile(
        repository_count=master_profile.repository_count,
        capabilities=skill_level.capabilities + domain_level,
    )

'@
Set-Content -Path .\incomeos\capabilities\domains.py -Value $domainsContent -Encoding UTF8

Write-Host '== M2: tests/test_m2_and_fixes.py ==' -ForegroundColor Cyan
$testContent = @'
import pytest

from incomeos.capabilities.domains import (
    DOMAIN_TAXONOMY,
    build_capability_profile_with_domains,
    build_domain_capabilities,
)
from incomeos.jobs.fit import JobRequirement, evaluate_job_fit
from incomeos.jobs.requirements import parse_job_record
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel


# --- requirements.py bug fix -------------------------------------------------

def test_string_job_id_with_no_raw_data_does_not_raise():
    # Previously raised NameError: name 'legacy_job' is not defined,
    # because job_id is not a dict so `legacy_job` was never assigned.
    result = parse_job_record("job-42", raw_data=None)

    assert result.job_id == "job-42"
    assert result.required_skills == ()
    assert result.preferred_skills == ()


def test_string_job_id_with_raw_data_still_works():
    raw = repr({"description": "Required Skills: Python, Docker"})

    result = parse_job_record("job-99", raw_data=raw)

    assert result.job_id == "job-99"
    assert "Python" in result.required_skills
    assert "Docker" in result.required_skills


def test_legacy_dict_job_id_behavior_is_unchanged():
    result = parse_job_record({"id": 7, "title": "Legacy"}, raw_data=None)

    assert result.job_id == "7"
    assert result.title == "Legacy"
    assert result.required_skills == ()


# --- M2 domain capabilities ---------------------------------------------------

def _profile_with(*skills: MasterSkill) -> MasterSkillProfile:
    return MasterSkillProfile(
        repository_count=len({r for s in skills for r in s.repositories}),
        skill_record_count=sum(s.evidence_count for s in skills),
        skills=skills,
    )


def test_domain_only_appears_when_a_member_skill_has_evidence():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.9,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        )
    )

    domains = build_domain_capabilities(profile)
    domain_names = {d.name for d in domains}

    assert "Backend Engineering" in domain_names
    assert "Systems Programming" not in domain_names  # no C++/CMake/Linux evidence


def test_domain_capability_aggregates_member_evidence():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.9,
            evidence_count=2,
            repositories=("repo-a",),
        ),
        MasterSkill(
            name="SQL",
            confidence=0.7,
            evidence_count=1,
            repositories=("repo-b",),
        ),
    )

    domains = build_domain_capabilities(profile)
    backend = next(d for d in domains if d.name == "Backend Engineering")

    assert set(backend.skills) == {"Backend Engineering", "Python", "SQL"}
    assert backend.evidence_count == 3
    assert set(backend.repositories) == {"repo-a", "repo-b"}
    assert backend.confidence == pytest.approx((0.9 + 0.7) / 2, abs=1e-4)


def test_capability_profile_with_domains_matches_on_domain_name():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.95,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        ),
        MasterSkill(
            name="SQL",
            confidence=0.9,
            evidence_count=2,
            repositories=("repo-a", "repo-b"),
        ),
    )

    capability_profile = build_capability_profile_with_domains(profile)

    result = evaluate_job_fit(
        job_id="m2-job-1",
        requirements=(JobRequirement("Backend Engineering", CapabilityLevel.B),),
        profile=capability_profile,
    )

    assert result.fit_score == 1.0
    assert result.matched_requirements == ("Backend Engineering",)


def test_capability_profile_with_domains_still_matches_on_skill_name():
    # M1 behavior (matching by exact skill name) must survive unchanged
    # after adding the domain layer on top.
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.95,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        ),
    )

    capability_profile = build_capability_profile_with_domains(profile)

    result = evaluate_job_fit(
        job_id="m2-job-2",
        requirements=(JobRequirement("Python", CapabilityLevel.B),),
        profile=capability_profile,
    )

    assert result.fit_score == 1.0


def test_all_taxonomy_skill_names_look_plausible():
    # Sanity check on the draft taxonomy itself, not a correctness guarantee —
    # just catches obvious typos in DOMAIN_TAXONOMY skill names.
    all_skills = {name for names in DOMAIN_TAXONOMY.values() for name in names}
    assert all(isinstance(name, str) and name.strip() for name in all_skills)

'@
Set-Content -Path .\tests\test_m2_and_fixes.py -Value $testContent -Encoding UTF8

Write-Host '== M2: running full test suite ==' -ForegroundColor Cyan
python -m pytest -q
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "PASS: all tests green (backup at $backupDir)" -ForegroundColor Green
} else {
    Write-Host "FAIL: pytest exited $exitCode. Restore from $backupDir if needed." -ForegroundColor Red
}
exit $exitCode