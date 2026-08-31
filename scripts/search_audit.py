from __future__ import annotations

import json
import sys
from pathlib import Path


# Allow direct execution:
# python scripts\search_audit.py
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from incomeos.audit.engine import audit_repositories
from incomeos.search.engine import index_repositories, search_documents


def main() -> None:
    root = ROOT / "data" / "github_repos"
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    documents = index_repositories(root)
    audit = audit_repositories(root)

    print("INCOMEOS SEARCH & AUDIT")
    print("=======================")
    print(f"Repositories : {audit.repository_count}")
    print(f"Documents    : {audit.document_count}")
    print(f"Findings     : {audit.finding_count}")
    print(f"Critical     : {audit.critical_count}")
    print(f"Warnings     : {audit.warning_count}")
    print(f"Info         : {audit.info_count}")

    print()
    print("SEARCH SAMPLE")
    print("-------------")

    for query in (
        "Python",
        "Testing",
        "Data Engineering",
        "C++",
        "Docker",
    ):
        results = search_documents(documents, query, limit=5)

        print(f"\n[{query}]")

        for result in results:
            print(
                f"{result.repository} | "
                f"{result.path} | "
                f"{result.category} | "
                f"score={result.score:.3f}"
            )

    payload = {
        "repository_count": audit.repository_count,
        "document_count": audit.document_count,
        "finding_count": audit.finding_count,
        "critical_count": audit.critical_count,
        "warning_count": audit.warning_count,
        "info_count": audit.info_count,
        "findings": [
            {
                "severity": finding.severity,
                "category": finding.category,
                "message": finding.message,
                "repository": finding.repository,
                "source": finding.source,
            }
            for finding in audit.findings
        ],
    }

    output = report_dir / "search_audit_report.json"

    output.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(f"SAVED: {output}")


if __name__ == "__main__":
    main()
