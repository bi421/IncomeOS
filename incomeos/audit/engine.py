from __future__ import annotations

import re
from pathlib import Path

from incomeos.search.engine import index_repositories
from incomeos.search.models import AuditFinding, AuditReport, SearchDocument

CREDENTIAL_KEYWORDS = ("password", "api_key", "secret", "token", "apikey", "passwd")


def _is_suspicious_literal(value: str) -> bool:
    """Return True when `value` looks like a real hardcoded credential."""
    if not value:
        return False
    if value in {"", "''", '""'}:
        return False
    if len(value) <= 4:
        return False
    lowered = value.lower()
    if lowered.startswith(
        ("example", "placeholder", "dummy", "test_", "test-", "xxxx",
         "todo", "your_", "changeme", "secret_key_here", "password_here"),
    ):
        return False
    if lowered in {"none", "null", "undefined", "true", "false"}:
        return False
    if lowered in {k.lower() for k in CREDENTIAL_KEYWORDS}:
        return False
    if re.fullmatch(r"[0-9a-fA-F]{8,}", value) and len(value) <= 20:
        return False
    return True


def _keyword_in_code(code: str) -> bool:
    """True when a credential keyword appears as a whole word outside string literals."""
    for kw in CREDENTIAL_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", code, re.IGNORECASE):
            return True
    return False


def _credential_findings(document: SearchDocument) -> list[AuditFinding]:
    """Context-aware credential detector."""
    findings = []
    lines = document.content.splitlines()
    kw_pattern = "|".join(re.escape(k) for k in CREDENTIAL_KEYWORDS)

    for i, raw in enumerate(lines):
        stripped = raw.lstrip()

        # --- Skip comments ---
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("//", "/*", "*")):
            continue
        if stripped.startswith(("'''", '"""')):
            continue
        # Lines starting with a quote: allow if they have code content
        if stripped.startswith(("'", '"')):
            rem = stripped.lstrip("'\"")
            if rem.strip() == "":
                continue

        # --- Skip documentation files ---
        if document.path.lower().endswith((".md", ".rst", ".txt", ".adoc", ".markdown")):
            continue
        if document.category and document.category.lower() in {"documentation", "markdown", "readme"}:
            continue

        low = raw.lower()

        # --- Skip imports ---
        if re.match(r"^\s*import\s+secrets\b", low):
            continue
        if re.match(r"^\s*from\s+secrets\s+import\b", low):
            continue
        if re.match(r"^\s*import\s+(" + kw_pattern + r")\s*$", low):
            continue

        # Strip inline comments for keyword detection
        cp = raw.find("#")
        if cp >= 0:
            code_for_keyword = raw[:cp]
        else:
            code_for_keyword = raw
        """Strip string literals from code using simple iteration; no backrefs."""
        out = []
        j = 0
        n = len(code_for_keyword)
        while j < n:
            ch = code_for_keyword[j]
            if ch in ("'", '"'):
                q = ch
                j += 1
                while j < n:
                    c = code_for_keyword[j]
                    if c == "\\":
                        j += 2
                        continue
                    if c == q:
                        j += 1
                        break
                    j += 1
            else:
                out.append(ch)
                j += 1
        stripped = "".join(out)

        # --- Detect credential context ---
        has_context = False
        value = None

        # Method A: keyword as identifier in code
        if _keyword_in_code(stripped):
            has_context = True

        # Method B: dict/JSON key pattern  "keyword": "value"
        if not has_context:
            dict_pat = re.search(
                r"""['"](""" + kw_pattern + r""")['"]\s*:\s*(['"])(?:\\.|(?!\2).)*\2""",
                raw,
            )
            if dict_pat:
                has_context = True
                val_full = raw[dict_pat.start(2):dict_pat.end()]
                val_inner = val_full[1:-1]
                if _is_suspicious_literal(val_inner):
                    value = val_inner

        if not has_context:
            continue

        # --- Find value literal on the line ---
        if not value:
            for m in re.finditer(r"""(['"])(?:\\.|(?!\1).)*\1""", raw):
                inner = m.group(0)[1:-1]
                if _is_suspicious_literal(inner):
                    value = inner
                    break

        # --- Multiline: check next line if current has context but no value ---
        if not value and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            m = re.match(r"""(['"])(?:\\.|(?!\1).)*\1""", nxt)
            if m:
                inner = m.group(0)[1:-1]
                if _is_suspicious_literal(inner):
                    value = inner

        if not value:
            continue

        # --- Skip bare function signatures ---
        if re.match(r"^\s*def\b", raw):
            body = raw.split(":", 1)[-1].strip() if ":" in raw else ""
            if body == "" or body.startswith("pass"):
                continue

        # --- Severity ---
        severity = "warning"
        if len(value) >= 20:
            severity = "critical"

        display = value[:40] + ("â€¦" if len(value) > 40 else "")
        findings.append(AuditFinding(
            severity=severity,
            category="credential_marker",
            message=(
                f"Possible hardcoded credential detected near "
                f"'{raw.strip()[:80]}' (value: {display})."
            ),
            repository=document.repository,
            source=document.path,
        ))

    return findings


def _audit_document(document: SearchDocument) -> list[AuditFinding]:
    findings = []
    content = document.content
    low_content = content.lower()

    if not content.strip():
        findings.append(AuditFinding(
            severity="warning",
            category="empty_file",
            message="File contains no readable content.",
            repository=document.repository,
            source=document.path,
        ))

    if document.language == "Python":
        if "todo" in low_content:
            findings.append(AuditFinding(
                severity="info",
                category="todo",
                message="TODO marker detected.",
                repository=document.repository,
                source=document.path,
            ))
        if "pass" in low_content and "def " in low_content:
            findings.append(AuditFinding(
                severity="info",
                category="placeholder",
                message="Possible Python placeholder implementation detected.",
                repository=document.repository,
                source=document.path,
            ))

    findings.extend(_credential_findings(document))
    return findings


def audit_documents(documents: tuple[SearchDocument, ...]) -> AuditReport:
    findings = []
    for document in documents:
        findings.extend(_audit_document(document))
    repository_count = len({document.repository for document in documents})
    return AuditReport(
        repository_count=repository_count,
        document_count=len(documents),
        finding_count=len(findings),
        findings=tuple(findings),
    )


def audit_repositories(root: str | Path) -> AuditReport:
    documents = index_repositories(root)
    return audit_documents(documents)
