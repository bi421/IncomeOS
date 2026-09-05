from __future__ import annotations

from .github_analyzer import RepositoryEvidence
from .models import EvidenceDimension, EvidenceType, SkillEvidence


SKILL_RULES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "C++": ("c++",),
    "CMake": ("cmake",),
    "Testing": ("test",),
    "Docker": ("docker",),
    "Data Engineering": ("data",),
    "Flask": ("flask",),
    "SQLite": ("sqlite",),
    "Pydantic": ("pydantic",),
    "Polars": ("polars",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
}


def detect_skills(
    evidence: tuple[RepositoryEvidence, ...],
) -> tuple[SkillEvidence, ...]:
    detected: list[SkillEvidence] = []

    for skill, keywords in SKILL_RULES.items():
        matches = [
            item
            for item in evidence
            if _skill_matches(item, skill, keywords)
        ]

        if not matches:
            continue

        best = max(
            matches,
            key=lambda item: (
                _dimension_priority(item.dimension),
                _evidence_priority(item.evidence_type),
            ),
        )

        detected.append(
            SkillEvidence(
                skill=skill,
                evidence_type=_map_evidence_type(best),
                source=best.source,
                description=_describe(skill, best),
                strength=_calculate_strength(best),
                dimension=best.dimension,
            )
        )

    return tuple(detected)


def _skill_matches(
    evidence: RepositoryEvidence,
    skill: str,
    keywords: tuple[str, ...],
) -> bool:
    source = evidence.source.lower()
    detail = evidence.detail.lower()

    if skill == "Python":
        return (
            source.endswith(".py")
            or "python" in source
            or "python" in detail
        )

    if skill == "C++":
        return source.endswith(
            (".cpp", ".cc", ".cxx", ".h", ".hpp")
        )

    if skill == "CMake":
        return source.lower().endswith(
            "cmakelists.txt"
        )

    if skill == "Testing":
        return (
            evidence.dimension == EvidenceDimension.VALIDATION
            or "test" in source
            or "test" in detail
        )

    if skill == "Docker":
        return (
            source.lower().endswith("dockerfile")
            or "docker" in source
            or "docker" in detail
        )

    if skill == "Data Engineering":
        data_terms = (
            "data",
            "database",
            "loader",
            "dataset",
            "csv",
            "parquet",
            "market_data",
            "data_engine",
        )

        return any(
            term in source
            or term in detail
            for term in data_terms
        )

    text = f"{source} {detail}"

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def _dimension_priority(
    dimension: EvidenceDimension,
) -> int:
    priorities = {
        EvidenceDimension.IMPLEMENTATION: 5,
        EvidenceDimension.VALIDATION: 4,
        EvidenceDimension.ENGINEERING: 3,
        EvidenceDimension.USAGE: 2,
        EvidenceDimension.PRESENCE: 1,
    }

    return priorities[dimension]


def _evidence_priority(
    evidence_type: str,
) -> int:
    priorities = {
        "direct_code": 5,
        "test": 4,
        "deployment": 3,
        "build_system": 3,
        "configuration": 2,
        "dependency": 1,
    }

    return priorities.get(evidence_type, 0)


def _calculate_strength(
    evidence: RepositoryEvidence,
) -> float:
    base = {
        EvidenceDimension.PRESENCE: 0.40,
        EvidenceDimension.USAGE: 0.70,
        EvidenceDimension.ENGINEERING: 0.70,
        EvidenceDimension.VALIDATION: 0.80,
        EvidenceDimension.IMPLEMENTATION: 0.75,
    }[evidence.dimension]

    if evidence.evidence_type == "deployment":
        base = 1.0

    if evidence.evidence_type == "direct_code":
        base += 0.10

    if evidence.evidence_type == "test":
        base += 0.05

    return min(round(base, 4), 1.0)

def _map_evidence_type(
    evidence: RepositoryEvidence,
) -> EvidenceType:
    mapping = {
        "direct_code": EvidenceType.CODE,
        "test": EvidenceType.TEST,
        "deployment": EvidenceType.DEPLOYMENT,
        "configuration": EvidenceType.REPOSITORY,
        "dependency": EvidenceType.REPOSITORY,
        "build_system": EvidenceType.CODE,
    }

    return mapping.get(
        evidence.evidence_type,
        EvidenceType.REPOSITORY,
    )


def _describe(
    skill: str,
    evidence: RepositoryEvidence,
) -> str:
    return (
        f"{skill} detected from "
        f"{evidence.dimension.value} evidence "
        f"at {evidence.source}."
    )
