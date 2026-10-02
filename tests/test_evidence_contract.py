import pytest

from incomeos.skills.models import EvidenceDimension, EvidenceType, SkillEvidence


def test_evidence_contract_accepts_valid_boundary_values():
    low = SkillEvidence(skill="Python", evidence_type=EvidenceType.CODE, source="repo/file.py", description="documented implementation", strength=0.0, dimension=EvidenceDimension.IMPLEMENTATION)
    high = SkillEvidence(skill="Python", evidence_type=EvidenceType.TEST, source="tests/test_python.py", description="documented validation", strength=1.0, dimension=EvidenceDimension.VALIDATION)
    assert low.strength == 0.0
    assert high.strength == 1.0


def test_evidence_contract_rejects_empty_skill():
    with pytest.raises(ValueError, match="skill"):
        SkillEvidence(skill=" ", evidence_type=EvidenceType.CODE, source="repo/file.py", description="evidence", strength=0.5)


def test_evidence_contract_rejects_empty_source():
    with pytest.raises(ValueError, match="source"):
        SkillEvidence(skill="Python", evidence_type=EvidenceType.CODE, source=" ", description="evidence", strength=0.5)


def test_evidence_contract_rejects_strength_outside_range():
    for strength in (-0.01, 1.01):
        with pytest.raises(ValueError, match="strength"):
            SkillEvidence(skill="Python", evidence_type=EvidenceType.CODE, source="repo/file.py", description="evidence", strength=strength)
