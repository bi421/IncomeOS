from __future__ import annotations

from pathlib import Path

from incomeos.search.engine import index_repositories
from incomeos.search.models import AuditFinding, AuditReport, SearchDocument


def _audit_document(document: SearchDocument) -> list[AuditFinding]:
    findings: list[AuditFinding] = []

    content = document.content.lower()

    if not document.content.strip():
        findings.append(
            AuditFinding(
                severity="warning",
                category="empty_file",
                message="File contains no readable content.",
                repository=document.repository,
                source=document.path,
            )
        )

    if document.language == "Python":
        if "todo" in content:
            findings.append(
                AuditFinding(
                    severity="info",
                    category="todo",
                    message="TODO marker detected.",
                    repository=document.repository,
                    source=document.path,
                )
            )

        if "pass" in content and "def " in content:
            findings.append(
                AuditFinding(
                    severity="info",
                    category="placeholder",
                    message="Possible Python placeholder implementation detected.",
                    repository=document.repository,
                    source=document.path,
                )
            )

    if "password" in content or "api_key" in content or "secret" in content:
        findings.append(
            AuditFinding(
                severity="warning",
                category="credential_marker",
                message="Potential credential/secret marker detected; manual review required.",
                repository=document.repository,
                source=document.path,
            )
        )

    return findings


def audit_documents(
    documents: tuple[SearchDocument, ...],
) -> AuditReport:
    findings: list[AuditFinding] = []

    for document in documents:
        findings.extend(_audit_document(document))

    repository_count = len(
        {document.repository for document in documents}
    )

    return AuditReport(
        repository_count=repository_count,
        document_count=len(documents),
        finding_count=len(findings),
        findings=tuple(findings),
    )


def audit_repositories(root: str | Path) -> AuditReport:
    documents = index_repositories(root)
    return audit_documents(documents)
