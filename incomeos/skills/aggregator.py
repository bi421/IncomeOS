from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from.models import EvidenceDimension
from.portfolio import build_portfolio

DIMENSION_WEIGHTS: dict[EvidenceDimension, float] = {
    EvidenceDimension.PRESENCE: 0.40,
    EvidenceDimension.USAGE: 0.70,
    EvidenceDimension.ENGINEERING: 0.75,
    EvidenceDimension.VALIDATION: 0.90,
    EvidenceDimension.IMPLEMENTATION: 1.00,
}

VERIFIED_EVIDENCE_BONUS = 0.10 # 0.05 -> 0.10 болгов
MAX_VERIFIED_EVIDENCE_BONUS = 0.30 # 0.15 -> 0.30

# ШИНЭ: Баталгаажаагүй confidence-ийн тааз
UNVERIFIED_MAX_CONFIDENCE = 0.65
UNVERIFIED_PENALTY = 0.70

@dataclass(frozen=True)
class MasterSkill:
    name: str
    confidence: float
    evidence_count: int
    repositories: tuple[str,...]
    verified_evidence_count: int = 0
    verified_decision_ids: tuple[str,...] = ()

@dataclass(frozen=True)
class MasterSkillProfile:
    repository_count: int
    skill_record_count: int
    skills: tuple[MasterSkill,...]

def _load_verified_records(root: Path) -> tuple[object,...]:
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

def _verified_skill_map(root: Path) -> dict[str, tuple[object,...]]:
    records = _load_verified_records(root)
    grouped: dict[str, list[object]] = {}
    for record in records:
        skill = str(getattr(record, "skill", "")).strip()
        if not skill:
            continue
        grouped.setdefault(skill, []).append(record)
    return {skill: tuple(items) for skill, items in grouped.items()}

def build_master_profile(root: str | Path) -> MasterSkillProfile:
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
                dimension_weight = DIMENSION_WEIGHTS[evidence.dimension]
                weighted_strength = float(evidence.strength) * dimension_weight
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
            # ЗАСВАР 1: max биш avg + max хослол - 1 repo-д 1.0 өгөхгүй
            strongest_score = max(repository_scores.values())
            avg_score = sum(repository_scores.values()) / len(repository_scores)
            repository_count = len(repository_scores)
            # avg 70% + strongest 30% - ганц repo-д өндөр байхыг дарна
            base_score = avg_score * 0.7 + strongest_score * 0.3
            repetition_bonus = min(0.20, 0.05 * max(repository_count - 1, 0))
            raw_confidence = min(1.0, base_score + repetition_bonus)

        verified_records = verified_by_skill.get(name, ())
        verified_count = len(verified_records)
        verified_bonus = min(MAX_VERIFIED_EVIDENCE_BONUS, VERIFIED_EVIDENCE_BONUS * verified_count)

        # ЗАСВАР 2: verified=0 бол таазтай + penalty
        if verified_count == 0:
            confidence = min(UNVERIFIED_MAX_CONFIDENCE, raw_confidence * UNVERIFIED_PENALTY)
        else:
            confidence = min(1.0, raw_confidence + verified_bonus)

        master_skills.append(
            MasterSkill(
                name=name,
                confidence=round(confidence, 4),
                evidence_count=data["evidence_count"],
                repositories=tuple(sorted(data["repositories"])),
                verified_evidence_count=verified_count,
                verified_decision_ids=tuple(
                    sorted({
                        str(getattr(record, "decision_id", ""))
                        for record in verified_records
                        if getattr(record, "decision_id", "")
                    })
                ),
            )
        )

    master_skills.sort(key=lambda skill: (-skill.confidence, -skill.evidence_count, -skill.verified_evidence_count, skill.name.lower()))

    return MasterSkillProfile(
        repository_count=portfolio.repository_count,
        skill_record_count=portfolio.total_skill_count,
        skills=tuple(master_skills),
    )

def save_master_profile(profile: MasterSkillProfile, output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "repository_count": profile.repository_count,
        "skill_record_count": profile.skill_record_count,
        "unique_skill_count": len(profile.skills),
        "skills": [asdict(skill) for skill in profile.skills],
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path