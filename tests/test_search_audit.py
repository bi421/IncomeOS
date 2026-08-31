from incomeos.audit.engine import audit_documents
from incomeos.search.engine import search_documents
from incomeos.search.models import SearchDocument


def documents():
    return (
        SearchDocument(
            repository="demo",
            path="main.py",
            language="Python",
            category="Python",
            content="def hello():\n    return 'Python Testing'\n",
        ),
        SearchDocument(
            repository="demo",
            path="engine.cpp",
            language="C++",
            category="C++",
            content="void run_quant_engine() {}\n",
        ),
        SearchDocument(
            repository="demo",
            path="Dockerfile",
            language="Docker",
            category="Docker",
            content="FROM python:3.14\n",
        ),
    )


def test_search_finds_python():
    results = search_documents(documents(), "Python")

    assert results
    assert results[0].path == "main.py"
    assert "python" in results[0].matched_terms


def test_search_is_empty_for_unknown_term():
    results = search_documents(documents(), "Rust")

    assert results == ()


def test_search_supports_multiple_terms():
    results = search_documents(documents(), "Python Testing")

    assert results
    assert results[0].path == "main.py"
    assert results[0].score == 1.0


def test_search_respects_limit():
    results = search_documents(documents(), "Python", limit=1)

    assert len(results) == 1


def test_empty_query_returns_empty():
    assert search_documents(documents(), "") == ()


def test_audit_counts_documents():
    report = audit_documents(documents())

    assert report.repository_count == 1
    assert report.document_count == 3
    assert report.finding_count >= 0


def test_audit_detects_secret_marker():
    docs = (
        SearchDocument(
            repository="demo",
            path="config.py",
            language="Python",
            category="Python",
            content="api_key = 'AKIAIOSFODNN7EXAMPLE'\n",
        ),
    )

    report = audit_documents(docs)

    assert any(
        finding.category == "credential_marker"
        for finding in report.findings
    )


def test_audit_report_counts_are_consistent():
    report = audit_documents(documents())

    assert report.critical_count + report.warning_count + report.info_count == report.finding_count


def _cred(content: str, path: str = "config.py") -> SearchDocument:
    return SearchDocument(
        repository="demo",
        path=path,
        language="Python",
        category="Python",
        content=content,
    )


def test_audit_detects_real_credential():
    docs = (_cred("password = 'ghp_secrettoken1234567890abcdef'\n"),)

    report = audit_documents(docs)

    assert any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_ignores_example_placeholder():
    docs = (_cred("api_key = 'example'\n"),)

    report = audit_documents(docs)

    assert not any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_ignores_dummy_and_changeme_placeholders():
    docs = (
        _cred("secret = 'dummy'\n"),
        _cred("token = 'changeme'\n"),
    )

    report = audit_documents(docs)

    assert not any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_ignores_credential_in_comment():
    docs = (_cred("# api_key = 'AKIAIOSFODNN7EXAMPLE'\n"),)

    report = audit_documents(docs)

    assert not any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_ignores_credentials_in_docstrings_and_strings():
    docs = (
        _cred('"""api_key = AKIAIOSFODNN7EXAMPLE"""\n'),
        _cred('msg = "api_key = AKIAIOSFODNN7EXAMPLE"\n'),
    )

    report = audit_documents(docs)

    assert not any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_detects_dict_json_credential():
    docs = (_cred('settings = {"api_key": "ghp_secrettoken1234567890abcdef"}\n'),)

    report = audit_documents(docs)

    matches = [f for f in report.findings if f.category == "credential_marker"]
    assert matches


def test_audit_long_credential_is_critical_short_is_warning():
    long_doc = (_cred("api_key = 'AKIAIOSFODNN7EXAMPLE'\n"),)
    short_doc = (_cred("api_key = 'shorttoken123'\n"),)

    long_report = audit_documents(long_doc)
    short_report = audit_documents(short_doc)

    long_cred = [f for f in long_report.findings if f.category == "credential_marker"]
    short_cred = [f for f in short_report.findings if f.category == "credential_marker"]

    assert long_cred and long_cred[0].severity == "critical"
    assert short_cred and short_cred[0].severity == "warning"


def test_audit_multiline_credential_detected():
    docs = (_cred("API_KEY = \n'AKIAIOSFODNN7EXAMPLE'\n"),)

    report = audit_documents(docs)

    assert any(
        finding.category == "credential_marker" for finding in report.findings
    )


def test_audit_empty_content_flagged():
    docs = (_cred(""),)

    report = audit_documents(docs)

    assert report.document_count == 1
    assert any(finding.category == "empty_file" for finding in report.findings)


def test_audit_counts_stay_consistent_with_credentials():
    docs = (_cred("api_key = 'AKIAIOSFODNN7EXAMPLE'\n"),)

    report = audit_documents(docs)

    assert report.critical_count + report.warning_count + report.info_count == report.finding_count
    assert report.critical_count >= 1
