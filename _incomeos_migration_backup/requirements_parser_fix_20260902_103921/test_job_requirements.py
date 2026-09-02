from incomeos.jobs.requirements import (
    parse_job_record,
)


def test_literal_repr_and_html():
    raw = repr(
        {
            "description": """
                <h2>Required Skills</h2>
                <ul>
                    <li>Python</li>
                    <li>Docker</li>
                    <li>Kubernetes</li>
                </ul>
                <h2>Preferred Skills</h2>
                <p>Go</p>
            """
        }
    )

    result = parse_job_record(
        {"id": 1},
        raw_data=raw,
    )

    assert result.required_skills == (
        "Python",
        "Docker",
        "Kubernetes",
    )

    assert result.preferred_skills == (
        "Go",
    )


def test_preferred_python_is_not_required():
    raw = repr(
        {
            "description": """
                <h2>Required Background & Skills</h2>
                <p>Linux, Kubernetes, AWS</p>
                <h2>Preferred Background & Skills</h2>
                <p>Python or Go</p>
            """
        }
    )

    result = parse_job_record(
        {"id": 1},
        raw_data=raw,
    )

    assert "Python" not in result.required_skills
    assert "Python" in result.preferred_skills
    assert "Linux" in result.required_skills
    assert "Kubernetes" in result.required_skills
    assert "AWS" in result.required_skills


def test_required_python_is_required():
    raw = repr(
        {
            "description": """
                <h2>Required Skills and Experience</h2>
                <p>Python, SQL, Docker</p>
                <h2>Preferred</h2>
                <p>Go</p>
            """
        }
    )

    result = parse_job_record(
        {"id": 1},
        raw_data=raw,
    )

    assert "Python" in result.required_skills
    assert "SQL" in result.required_skills
    assert "Docker" in result.required_skills
    assert "Go" in result.preferred_skills


def test_empty_raw_data_is_safe():
    result = parse_job_record(
        {
            "id": 1,
            "title": "Legacy Job",
        },
        raw_data=None,
    )

    assert result.required_skills == ()
    assert result.preferred_skills == ()
