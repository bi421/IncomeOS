from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping


@dataclass(frozen=True)
class EvidenceClaim:
    """A claim that is explicitly backed by repository evidence."""

    claim_id: str
    text: str
    source: str


@dataclass(frozen=True)
class GeneratedApplication:
    """Generate application artifacts without introducing unsupported claims."""

    cover_letter: str
    resume_summary: str
    claim_ids: tuple[str, ...]
    prompt: str


LLM = Callable[[str], str]


class EvidenceBoundGenerator:
    """Generate application material without introducing unsupported claims."""

    def __init__(self, profile_path: str | Path) -> None:
        self.profile_path = Path(profile_path)
        self.profile = self._load_profile()
        self.claims = self._load_claims()

    def _load_profile(self) -> Mapping[str, object]:
        data = json.loads(self.profile_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("master skill profile must be a JSON object")
        return data

    def _load_claims(self) -> tuple[EvidenceClaim, ...]:
        raw = self.profile.get("verified_evidence", [])
        claims: list[EvidenceClaim] = []
        if not isinstance(raw, list):
            return ()
        for item in raw:
            if not isinstance(item, dict):
                continue
            claim_id = str(item.get("id", "")).strip()
            text = str(item.get("claim", "")).strip()
            source = str(item.get("source", "")).strip()
            if claim_id and text and source:
                claims.append(EvidenceClaim(claim_id, text, source))
        return tuple(claims)

    def _skills(self) -> tuple[str, ...]:
        raw = self.profile.get("skills", [])
        if not isinstance(raw, list):
            return ()
        result: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    result.append(name)
        return tuple(result)

    def _truth_policy(self) -> str:
        raw = str(
            self.profile.get(
                "profile_truth_policy",
                "Repository evidence may be AI-assisted; confidence does not imply independent mastery.",
            )
        ).strip()
        return raw

    def build_prompt(self, job_description: str) -> str:
        """Build a strict prompt whose allowed claims are explicit."""
        if not job_description.strip():
            raise ValueError("job_description must not be empty")
        evidence = "
".join(
            f"- [{claim.claim_id}] {claim.text} (source: {claim.source})"
            for claim in self.claims
        ) or "- No metric-level evidence is available; make no metric claims."
        skills = ", ".join(self._skills()) or "none"
        return f"""You are an evidence-bound job application writer.

TARGET JOB DESCRIPTION:
{job_description.strip()}

DOCUMENTED PROJECT SKILLS:
{skills}

PROFILE TRUTH POLICY:
{self._truth_policy()}

ALLOWED EVIDENCE CLAIMS:
{evidence}

RULES:
1. Use only the documented project skills and evidence claims above.
2. Treat repository/project skill evidence as AI-assisted unless separate verified
   evidence explicitly supports a stronger claim.
3. Never claim independent mastery, years of experience, employment history,
   certifications, metrics, deployments, technologies, or outcomes that are not
   explicitly supported.
4. Do not convert confidence into a claim of mastery.
5. If evidence is missing, omit the claim rather than filling the gap.
6. Return JSON with keys: claim_ids, cover_letter, resume_summary.
7. Every claim_ids value must exactly match an allowed evidence claim id.
8. The cover letter and resume summary must remain consistent with claim_ids.
"""

    def _validate(
        self,
        payload: Mapping[str, object],
    ) -> tuple[str, str, tuple[str, ...]]:
        allowed = {claim.claim_id for claim in self.claims}
        raw_ids = payload.get("claim_ids", [])
        if not isinstance(raw_ids, list):
            raise ValueError("LLM output claim_ids must be a list")
        claim_ids = tuple(str(value) for value in raw_ids)
        unknown = set(claim_ids) - allowed
        if unknown:
            raise ValueError(f"LLM used unsupported evidence ids: {sorted(unknown)}")
        cover = str(payload.get("cover_letter", "")).strip()
        resume = str(payload.get("resume_summary", "")).strip()
        if not cover or not resume:
            raise ValueError("LLM output must contain non-empty application text")
        return cover, resume, claim_ids

    def generate(
        self,
        job_description: str,
        llm: LLM | None = None,
    ) -> GeneratedApplication:
        """Generate deterministic fallback or validate a supplied LLM result."""
        prompt = self.build_prompt(job_description)
        if llm is None:
            skill_text = ", ".join(self._skills()) or "documented engineering project work"
            claims = tuple(self.claims)
            claim_ids = tuple(claim.claim_id for claim in claims)
            evidence_text = " ".join(claim.text for claim in claims)
            cover = (
                f"I am interested in this role because my documented project work "
                f"includes {skill_text}. {evidence_text}".strip()
            )
            resume = (
                f"Documented project skills: {skill_text}. "
                f"Verified evidence claims: {evidence_text}".strip()
            )
            return GeneratedApplication(cover, resume, claim_ids, prompt)

        raw = llm(prompt)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM output must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("LLM output must be a JSON object")
        cover, resume, claim_ids = self._validate(payload)
        return GeneratedApplication(cover, resume, claim_ids, prompt)
