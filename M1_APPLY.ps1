# M1_APPLY.ps1
# Run this from the IncomeOS project root: C:\Users\User\Desktop\IncomeOS
$ErrorActionPreference = 'Stop'

Write-Host '== M1: backup ==' -ForegroundColor Cyan
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = ".\_backup_$stamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item .\incomeos\skills\aggregator.py "$backupDir\aggregator.py.bak" -Force
if (Test-Path .\incomeos\capabilities) { Copy-Item .\incomeos\capabilities "$backupDir\capabilities_old" -Recurse -Force }

Write-Host '== M1: capabilities/models.py ==' -ForegroundColor Cyan
New-Item -ItemType Directory -Path .\incomeos\capabilities -Force | Out-Null
if (-not (Test-Path .\incomeos\capabilities\__init__.py)) { New-Item -ItemType File -Path .\incomeos\capabilities\__init__.py -Force | Out-Null }
$modelsContent = @'
from __future__ import annotations

from dataclasses import dataclass, field

from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel, classify_capability_level


@dataclass(frozen=True)
class CapabilityEvidence:
    """
    A single addressable evidence record backing a Capability.

    M1 derives these from the facts MasterSkill already carries
    (repositories, verified_decision_ids) so nothing upstream changes.
    M2's GitHub-evidence -> domain-capability extraction will populate
    these directly instead of deriving them.
    """

    repository: str
    verified: bool = False
    decision_id: str = ""


@dataclass(frozen=True)
class Capability:
    """
    M1 abstraction layer: MasterSkill -> Capability.

    Intentionally 1:1 with the underlying skill for now (name == skill.name,
    skills == (skill.name,)), so incomeos.jobs.fit.evaluate_job_fit keeps
    working unmodified against a CapabilityProfile. M2 will introduce
    many-skills-per-capability grouping here.
    """

    name: str
    skills: tuple[str, ...]
    confidence: float
    level: str
    evidence: tuple[CapabilityEvidence, ...] = field(default_factory=tuple)
    evidence_count: int = 0
    repositories: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "confidence": self.confidence,
            "level": self.level,
        }


@dataclass(frozen=True)
class CapabilityProfile:
    """
    Drop-in replacement for MasterSkillProfile as a `profile` argument to
    evaluate_job_fit: exposes `.capabilities` so
    incomeos.jobs.fit._extract_capabilities picks it up via its
    getattr(profile, "capabilities", ()) fallback branch.
    """

    repository_count: int
    capabilities: tuple[Capability, ...]


def capability_from_master_skill(skill: MasterSkill) -> Capability:
    level, _ = classify_capability_level(
        confidence=skill.confidence,
        evidence_count=skill.evidence_count,
        repository_count=len(skill.repositories),
    )

    repo_evidence = tuple(
        CapabilityEvidence(repository=repository, verified=False)
        for repository in skill.repositories
    )

    verified_evidence = tuple(
        CapabilityEvidence(repository="verified", verified=True, decision_id=decision_id)
        for decision_id in skill.verified_decision_ids
    )

    return Capability(
        name=skill.name,
        skills=(skill.name,),
        confidence=skill.confidence,
        level=level.value,
        evidence=repo_evidence + verified_evidence,
        evidence_count=skill.evidence_count,
        repositories=skill.repositories,
    )


def build_capability_profile(profile: MasterSkillProfile) -> CapabilityProfile:
    return CapabilityProfile(
        repository_count=profile.repository_count,
        capabilities=tuple(
            capability_from_master_skill(skill) for skill in profile.skills
        ),
    )

'@
Set-Content -Path .\incomeos\capabilities\models.py -Value $modelsContent -Encoding UTF8

Write-Host '== M1: fix aggregator.py (missing import sqlite3) ==' -ForegroundColor Cyan
$aggregatorContent = @'

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import EvidenceDimension
from .portfolio import build_portfolio


DIMENSION_WEIGHTS: dict[EvidenceDimension, float] = {
    EvidenceDimension.PRESENCE: 0.40,
    EvidenceDimension.USAGE: 0.70,
    EvidenceDimension.ENGINEERING: 0.75,
    EvidenceDimension.VALIDATION: 0.90,
    EvidenceDimension.IMPLEMENTATION: 1.00,
}

VERIFIED_EVIDENCE_BONUS = 0.05
MAX_VERIFIED_EVIDENCE_BONUS = 0.15


@dataclass(frozen=True)
class MasterSkill:
    name: str
    confidence: float
    evidence_count: int
    repositories: tuple[str, ...]
    verified_evidence_count: int = 0
    verified_decision_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class MasterSkillProfile:
    repository_count: int
    skill_record_count: int
    skills: tuple[MasterSkill, ...]


def _load_verified_records(
    root: Path,
) -> tuple[object, ...]:
    """
    Load human-verified outcome evidence when the verification ledger exists.

    The ledger is optional. A missing database produces an empty set and
    therefore preserves the previous profile behavior.

    Verified outcomes never create a new skill by themselves. They may only
    strengthen a skill that already has real project evidence.
    """

    db_path = root.parent.parent / "verification.db"

    if not db_path.exists():
        db_path = Path("data/verification.db")

    if not db_path.exists():
        return ()

    try:
        from incomeos.skills.verification import VerificationStore

        store = VerificationStore(db_path)
        return store.list_verified()
    except (OSError, ValueError, sqlite3.Error, ImportError):
        return ()


def _verified_skill_map(
    root: Path,
) -> dict[str, tuple[object, ...]]:
    records = _load_verified_records(root)

    grouped: dict[str, list[object]] = {}

    for record in records:
        skill = str(
            getattr(record, "skill", "")
        ).strip()

        if not skill:
            continue

        grouped.setdefault(
            skill,
            [],
        ).append(record)

    return {
        skill: tuple(items)
        for skill, items in grouped.items()
    }


def build_master_profile(
    root: str | Path,
) -> MasterSkillProfile:
    root_path = Path(root)

    portfolio = build_portfolio(root_path)
    verified_by_skill = _verified_skill_map(root_path)

    aggregated: dict[str, dict] = {}

    for report in portfolio.repositories:
        for skill in report.skills:
            name = skill.name

            if name not in aggregated:
                aggregated[name] = {
                    "repository_scores": {},
                    "evidence_count": 0,
                    "repositories": set(),
                }

            repository = report.repository

            if repository not in aggregated[name]["repository_scores"]:
                aggregated[name]["repository_scores"][repository] = 0.0

            for evidence in skill.evidence:
                dimension_weight = DIMENSION_WEIGHTS[
                    evidence.dimension
                ]

                weighted_strength = (
                    float(evidence.strength)
                    * dimension_weight
                )

                aggregated[name]["repository_scores"][repository] = max(
                    aggregated[name]["repository_scores"][repository],
                    weighted_strength,
                )

                aggregated[name]["evidence_count"] += 1

            aggregated[name]["repositories"].add(repository)

    master_skills: list[MasterSkill] = []

    for name, data in aggregated.items():
        repository_scores = data["repository_scores"]

        if not repository_scores:
            raw_confidence = 0.0
        else:
            strongest_score = max(
                repository_scores.values()
            )

            repository_count = len(repository_scores)

            repetition_bonus = min(
                0.20,
                0.05 * max(repository_count - 1, 0),
            )

            raw_confidence = min(
                1.0,
                strongest_score + repetition_bonus,
            )

        verified_records = verified_by_skill.get(
            name,
            (),
        )

        verified_count = len(
            verified_records
        )

        verified_bonus = min(
            MAX_VERIFIED_EVIDENCE_BONUS,
            VERIFIED_EVIDENCE_BONUS
            * verified_count,
        )

        confidence = min(
            1.0,
            raw_confidence + verified_bonus,
        )

        master_skills.append(
            MasterSkill(
                name=name,
                confidence=round(
                    confidence,
                    4,
                ),
                evidence_count=data["evidence_count"],
                repositories=tuple(
                    sorted(data["repositories"])
                ),
                verified_evidence_count=verified_count,
                verified_decision_ids=tuple(
                    sorted(
                        {
                            str(
                                getattr(
                                    record,
                                    "decision_id",
                                    "",
                                )
                            )
                            for record in verified_records
                            if getattr(
                                record,
                                "decision_id",
                                "",
                            )
                        }
                    )
                ),
            )
        )

    master_skills.sort(
        key=lambda skill: (
            -skill.confidence,
            -skill.evidence_count,
            -skill.verified_evidence_count,
            skill.name.lower(),
        )
    )

    return MasterSkillProfile(
        repository_count=portfolio.repository_count,
        skill_record_count=portfolio.total_skill_count,
        skills=tuple(master_skills),
    )


def save_master_profile(
    profile: MasterSkillProfile,
    output: str | Path,
) -> Path:
    output_path = Path(output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "repository_count": profile.repository_count,
        "skill_record_count": profile.skill_record_count,
        "unique_skill_count": len(profile.skills),
        "skills": [
            asdict(skill)
            for skill in profile.skills
        ],
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path

'@
Set-Content -Path .\incomeos\skills\aggregator.py -Value $aggregatorContent -Encoding UTF8

Write-Host '== M1: tests/test_capabilities.py ==' -ForegroundColor Cyan
$testContent = @'
from incomeos.capabilities.models import (
    Capability,
    build_capability_profile,
    capability_from_master_skill,
)
from incomeos.jobs.fit import JobRequirement, evaluate_job_fit
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel


def _master_skill(**overrides) -> MasterSkill:
    defaults = dict(
        name="Python",
        confidence=0.95,
        evidence_count=3,
        repositories=("repo-a", "repo-b"),
        verified_evidence_count=0,
        verified_decision_ids=(),
    )
    defaults.update(overrides)
    return MasterSkill(**defaults)


def test_capability_from_master_skill_is_1_to_1():
    skill = _master_skill()

    capability = capability_from_master_skill(skill)

    assert capability.name == "Python"
    assert capability.skills == ("Python",)
    assert capability.confidence == skill.confidence
    assert capability.level == CapabilityLevel.A.value
    assert capability.repositories == skill.repositories


def test_capability_level_matches_classify_capability_level():
    weak_skill = _master_skill(
        name="Rust",
        confidence=0.60,
        evidence_count=1,
        repositories=("repo-a",),
    )

    capability = capability_from_master_skill(weak_skill)

    assert capability.level == CapabilityLevel.B.value


def test_capability_evidence_includes_verified_decisions():
    skill = _master_skill(
        verified_evidence_count=1,
        verified_decision_ids=("dec-123",),
    )

    capability = capability_from_master_skill(skill)

    verified = [item for item in capability.evidence if item.verified]

    assert len(verified) == 1
    assert verified[0].decision_id == "dec-123"


def test_build_capability_profile_preserves_repository_count():
    profile = MasterSkillProfile(
        repository_count=4,
        skill_record_count=10,
        skills=(_master_skill(),),
    )

    capability_profile = build_capability_profile(profile)

    assert capability_profile.repository_count == 4
    assert len(capability_profile.capabilities) == 1
    assert isinstance(capability_profile.capabilities[0], Capability)


def test_capability_profile_is_backward_compatible_with_job_fit():
    profile = MasterSkillProfile(
        repository_count=2,
        skill_record_count=5,
        skills=(
            _master_skill(name="Python"),
            _master_skill(
                name="Docker",
                confidence=0.55,
                evidence_count=1,
                repositories=("repo-a",),
            ),
        ),
    )

    capability_profile = build_capability_profile(profile)

    result = evaluate_job_fit(
        job_id="m1-job-1",
        requirements=(
            JobRequirement("Python", CapabilityLevel.B),
            JobRequirement("Docker", CapabilityLevel.B),
        ),
        profile=capability_profile,
    )

    assert result.matched_requirements == ("Python", "Docker") or set(
        result.matched_requirements
    ) == {"Python", "Docker"}
    assert result.missing_requirements == ()
    assert result.fit_score == 1.0

'@
Set-Content -Path .\tests\test_capabilities.py -Value $testContent -Encoding UTF8

Write-Host '== M1: running full test suite ==' -ForegroundColor Cyan
python -m pytest -q
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host 'PASS: all tests green (backup at $backupDir)' -ForegroundColor Green
} else {
    Write-Host 'FAIL: pytest exited $exitCode. Restore from $backupDir if needed.' -ForegroundColor Red
}
exit $exitCode