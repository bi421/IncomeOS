"""REAL JOB DATA PIPELINE source smoke test.

Fetches real records from each configured source.
Does not store, apply, execute, or schedule anything.
"""

from incomeos.jobs.sources.registry import build_sources


def main() -> None:
    print("=" * 70)
    print("INCOMEOS REAL JOB SOURCE SMOKE TEST")
    print("=" * 70)

    total = 0

    for source in build_sources():
        jobs = list(source.fetch())

        print()
        print("SOURCE:", source.source_name)
        print("COUNT:", len(jobs))

        for job in jobs[:3]:
            print("  TITLE:", job.title)
            print("  COMPANY:", job.company)
            print("  URL:", job.source_url)
            print("  LOCATION:", job.location)
            print()

        total += len(jobs)

    print("=" * 70)
    print("TOTAL REAL JOB RECORDS:", total)
    print("=" * 70)


if __name__ == "__main__":
    main()
