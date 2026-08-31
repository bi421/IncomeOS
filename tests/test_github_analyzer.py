from incomeos.skills.github_analyzer import analyze_repository


def test_repository_analyzer_detects_python(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\n",
        encoding="utf-8",
    )

    (tmp_path / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    evidence = analyze_repository(tmp_path)

    types = {item.evidence_type for item in evidence}

    assert "configuration" in types
    assert "direct_code" in types


def test_repository_analyzer_detects_cpp_and_cmake(tmp_path):
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.20)\n",
        encoding="utf-8",
    )

    (tmp_path / "engine.cpp").write_text(
        "int main() { return 0; }\n",
        encoding="utf-8",
    )

    evidence = analyze_repository(tmp_path)

    types = {item.evidence_type for item in evidence}

    assert "build_system" in types
    assert "direct_code" in types


def test_python_source_is_implementation_evidence(tmp_path):
    (tmp_path / "main.py").write_text(
        "def hello():\n    return 'world'\n",
        encoding="utf-8",
    )

    evidence = analyze_repository(tmp_path)

    python_evidence = [
        item
        for item in evidence
        if item.source == "main.py"
    ]

    assert len(python_evidence) == 1
    assert python_evidence[0].dimension.value == "implementation"


def test_requirements_is_presence_evidence(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "pytest\n",
        encoding="utf-8",
    )

    evidence = analyze_repository(tmp_path)

    requirement_evidence = [
        item
        for item in evidence
        if item.source == "requirements.txt"
    ]

    assert len(requirement_evidence) == 1
    assert requirement_evidence[0].dimension.value == "presence"
