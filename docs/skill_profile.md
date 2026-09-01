\# Skill Profile — Evidence-Based



> \*\*Principle:\*\* This list includes only capabilities that have been repeatedly exercised on real projects and confirmed by actual terminal output. A capability is never counted as proven just because a folder for it exists, or because it was tried once with no verified result.



\---



\## 1. Python Development



\- Structuring multi-package codebases, managing module/package architecture

\- Writing and debugging functions/classes inside large codebases (3,500+ tests)

\- Using `pytest`, `py\_compile`, `compileall` for verification — run hundreds of times across projects

\- Resolving Python 3.x environment compatibility issues (venv, PATH, install conflicts)



\*\*Evidence:\*\* AI Trading OS (test suite grew 150 → 3,572 over time), ResearchOS (2,314 → 3,572 passing), TrueROAS (108 passing tests)



\---



\## 2. Software Testing \& QA



\- Writing/fixing unit tests, catching regressions

\- Diagnosing test-isolation bugs (e.g., found a test that was leaking into a production database and fixed it by isolating it to a tmp\_path)

\- Cross-checking AI tools' reported test counts against actual terminal output and catching inflated/false claims — a repeated, documented practice



\*\*Evidence:\*\* Caught an AI's "111 passed" claim against a real run of 82; caught another AI's "1582 passed" claim against a real run of 1843 passed / 10 failed



\---



\## 3. Codebase Forensic Audit



\- Inspecting repository structure, tracing import chains via grep to document what's actually live (e.g., `main.py → core/paper\_engine.py → engine/strategy.py`)

\- Distinguishing committed vs. uncommitted code, and code that's wired in vs. dead/orphaned

\- Finding and fixing risk surfaces like unsafe `subprocess`/`shell=True` usage (done today, live, on the IncomeOS project)

\- Distinguishing runtime-verified evidence from code that exists in source but has never actually executed



\*\*Evidence:\*\* Discovered that new modules built by an AI tool (risk\_manager, score.py) had passing tests but were never wired into the live import chain, via grep verification



\---



\## 4. Git / GitHub Workflow



\- Managing branches, HEAD, working tree, commit history

\- Diffing, distinguishing untracked/modified files, establishing a clean baseline

\- Merging pull requests (e.g., PR #1, commit 3aad087)



\---



\## 5. PowerShell Automation (Windows environment)



\- Writing and running diagnostic scripts

\- Process/filesystem inspection

\- Automating test/compile pipelines

\- Repeated, hands-on experience diagnosing and fixing encoding issues (BOM, console codepage)



\---



\## 6. Backtest Engineering



\- Building and running backtest engines (Python and C++)

\- Detecting and fixing look-ahead bias (documented real session: the BACKTEST-01 fix)

\- Modeling spread/slippage cost

\- Understanding and explaining the difference between an unrealistic result (-332 USD, no costs modeled) and a realistic one (-3,254 USD, costs modeled)



\*\*Important caveat:\*\* All backtests to date have run on datasets in the thousand-row range (5,829 H1 candles, 1,554 D1 bars) — there is \*\*no\*\* experience working with million-row-scale datasets.



\---



\## 7. Probability / Statistical Analysis (limited, but real)



\- Used an `EmpiricalProbabilityEstimator` to compute real probability estimates on XAUUSD

\- Experience accepting an honest negative result (reported no statistically significant edge, rather than dressing up the result as a success)

\- Designed the architecture for correlation, covariance, regression, and distribution/volatility computation (ResearchOS Statistics Engine)



\*\*Currently unproven — AVOID claiming these:\*\* Monte Carlo simulation (only a folder name exists, no verified working result), bootstrap resampling, event study — none of these have been implemented, tested, and confirmed working, so they should not be listed as demonstrated skills yet.



\---



\## 8. Technical Debugging Methodology



\- Reading error logs, isolating root causes

\- Following the sequence: hypothesis → AI-generated command → output verification → root-cause isolation

\- Repeated, hands-on experience with very low-level issues like encoding/BOM problems

\- \*\*Core principle:\*\* Only literal terminal output counts as proof — AI tool claims are never accepted without independent verification



\---



\## 9. AI-Assisted Software Engineering



Uses AI as more than a "code generator" — follows a repeated, disciplined workflow:



```

Have AI generate code → run the command yourself →

verify the output → make the next decision only

based on confirmed results

```



This workflow has repeatedly caught false or inflated AI reports (a fabricated backtest report, inflated test counts, a feature shown as "implemented" in a diagram that was actually never built).



\---



\## Freelance/Remote Services This Supports



| Service | Description |

|---|---|

| \*\*Python code audit\*\* | Review a repository to identify bugs, risks, dead code, and failing tests |

| \*\*Python test fixing\*\* | Diagnose and fix a failing pytest suite, add regression tests |

| \*\*Repository health audit\*\* | Check Git structure, import chains, untracked code, security risks (e.g. `shell=True`) |

| \*\*Windows/Python environment troubleshooting\*\* | Diagnose Python version, dependency, encoding, PATH, PowerShell, build/test issues |

| \*\*Technical documentation\*\* | Write READMEs, audit reports, verification reports |



\---



\## Titles NOT Currently Justified (deliberately excluded — evidence isn't there yet)



\- Senior Software Engineer ❌

\- Senior Data Scientist ❌

\- ML Engineer ❌

\- DevOps Engineer ❌

\- Production Backend Engineer ❌

\- Professional Quant Trader ❌



\## Specific Techniques NOT Currently Justified (removed from this list)



\- Monte Carlo simulation (a folder exists; no working, verified result)

\- Bootstrap resampling (no evidence it was ever implemented)

\- Event study (no evidence it was ever implemented)

\- The description "large dataset" (current data volumes are in the thousands of rows, not millions)

