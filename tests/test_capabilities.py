from incomeos.skills.capabilities import (
    build_capabilities,
)


def test_capabilities_are_built():
    capabilities = build_capabilities(
        "data/github_repos"
    )

    assert len(capabilities) >= 1


def test_python_capability_exists():
    capabilities = build_capabilities(
        "data/github_repos"
    )

    names = {
        capability.name
        for capability in capabilities
    }

    assert "Python Application Development" in names


def test_data_capability_exists():
    capabilities = build_capabilities(
        "data/github_repos"
    )

    names = {
        capability.name
        for capability in capabilities
    }

    assert "Data Processing & Pipeline Development" in names


def test_capability_confidence_is_bounded():
    capabilities = build_capabilities(
        "data/github_repos"
    )

    for capability in capabilities:
        assert 0.0 <= capability.confidence <= 1.0


def test_capability_has_evidence():
    capabilities = build_capabilities(
        "data/github_repos"
    )

    for capability in capabilities:
        assert capability.evidence_count >= 1
        assert capability.repository_count >= 1
