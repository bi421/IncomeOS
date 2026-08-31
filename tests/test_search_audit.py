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
            content="api_key = 'example'\n",
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
