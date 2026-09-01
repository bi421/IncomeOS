from incomeos.jobs.filters import is_relevant


def test_testingenieur_does_not_match_testing():
    assert not is_relevant(
        title="Testingenieur (m/w/d) Medizintechnik / Imaging & X-Ray",
        description="Medical imaging and laboratory testing.",
        tags=[],
        skill_names=["Testing"],
    )


def test_solutions_architect_does_not_pass_from_description_testing():
    assert not is_relevant(
        title="Solutions Architect",
        description="Design solutions with Python and testing experience.",
        tags=[],
        skill_names=["Python", "Testing"],
    )


def test_quality_manager_does_not_pass_from_description_testing():
    assert not is_relevant(
        title="Quality Manager – Quality Control & Quality Assurance",
        description="Quality control, quality assurance and testing processes.",
        tags=[],
        skill_names=["Testing"],
    )


def test_qa_engineer_still_matches():
    assert is_relevant(
        title="Senior QA Engineer",
        description="Automated testing with Python.",
        tags=[],
        skill_names=["Testing"],
    )


def test_software_test_engineer_still_matches():
    assert is_relevant(
        title="Software Test Engineer",
        description="Build automated testing systems.",
        tags=[],
        skill_names=["Testing"],
    )


def test_python_backend_engineer_still_matches():
    assert is_relevant(
        title="Python Backend Engineer",
        description="Build backend APIs with Python.",
        tags=[],
        skill_names=["Python"],
    )


def test_python_based_title_still_matches():
    assert is_relevant(
        title="Python-based Backend Developer",
        description="Build APIs.",
        tags=[],
        skill_names=["Python"],
    )


def test_cplusplus_title_still_matches():
    assert is_relevant(
        title="C++ Engineer",
        description="Systems development.",
        tags=[],
        skill_names=["C++"],
    )
