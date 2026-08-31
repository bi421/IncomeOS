from incomeos.skills.detector import detect_skills
from incomeos.skills.github_analyzer import RepositoryEvidence
from incomeos.skills.models import EvidenceDimension


def test_detector_finds_python():
    evidence = (
        RepositoryEvidence(
            repository="demo",
            evidence_type="direct_code",
            source="main.py",
            detail="Python source file detected.",
            dimension=EvidenceDimension.IMPLEMENTATION,
        ),
    )

    skills = detect_skills(evidence)

    names = {skill.skill for skill in skills}

    assert "Python" in names


def test_detector_finds_cpp_and_cmake():
    evidence = (
        RepositoryEvidence(
            repository="demo",
            evidence_type="direct_code",
            source="engine.cpp",
            detail="C/C++ source or header detected.",
            dimension=EvidenceDimension.IMPLEMENTATION,
        ),
        RepositoryEvidence(
            repository="demo",
            evidence_type="build_system",
            source="CMakeLists.txt",
            detail="CMake build configuration detected.",
            dimension=EvidenceDimension.ENGINEERING,
        ),
    )

    skills = detect_skills(evidence)

    names = {skill.skill for skill in skills}

    assert "C++" in names
    assert "CMake" in names


def test_implementation_is_stronger_than_presence():
    presence = (
        RepositoryEvidence(
            repository="demo",
            evidence_type="dependency",
            source="requirements.txt",
            detail="Python dependency manifest detected.",
            dimension=EvidenceDimension.PRESENCE,
        ),
    )

    implementation = (
        RepositoryEvidence(
            repository="demo",
            evidence_type="direct_code",
            source="main.py",
            detail="Python source file detected.",
            dimension=EvidenceDimension.IMPLEMENTATION,
        ),
    )

    presence_result = detect_skills(presence)
    implementation_result = detect_skills(implementation)

    presence_python = next(
        item
        for item in presence_result
        if item.skill == "Python"
    )

    implementation_python = next(
        item
        for item in implementation_result
        if item.skill == "Python"
    )

    assert (
        implementation_python.strength
        > presence_python.strength
    )


def test_validation_evidence_is_preserved():
    evidence = (
        RepositoryEvidence(
            repository="demo",
            evidence_type="test",
            source="tests/test_demo.py",
            detail="Test-related file detected.",
            dimension=EvidenceDimension.VALIDATION,
        ),
    )

    skills = detect_skills(evidence)

    testing = next(
        item
        for item in skills
        if item.skill == "Testing"
    )

    assert (
        testing.dimension
        == EvidenceDimension.VALIDATION
    )
