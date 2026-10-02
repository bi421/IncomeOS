from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class OutreachDraft:
    """Prepared recruiter outreach; preparation never sends it."""

    channel: str
    recipient: str
    subject: str
    body: str
    proof_links: tuple[str, ...]


def prepare_outreach(
    *,
    channel: str,
    recipient: str,
    job_title: str,
    company: str,
    proven_skills: Sequence[str],
    proof_links: Sequence[str],
) -> OutreachDraft:
    """Create customized outreach from supplied evidence only."""
    if channel not in {"email", "linkedin"}:
        raise ValueError("channel must be 'email' or 'linkedin'")
    if not recipient.strip():
        raise ValueError("recipient must not be empty")
    skills = ", ".join(dict.fromkeys(s.strip() for s in proven_skills if s.strip()))
    links = tuple(dict.fromkeys(link.strip() for link in proof_links if link.strip()))
    link_text = "\n".join(f"- {link}" for link in links) or "- No proof link supplied."
    body = (
        f"Hello,\n\n"
        f"I am interested in the {job_title} opportunity at {company}. "
        f"My evidence-backed skills include {skills or 'the skills documented in my profile'}.\n\n"
        f"Relevant proof of work:\n{link_text}\n\n"
        f"I would be glad to discuss the role and share additional evidence where relevant.\n"
    )
    subject = f"Application: {job_title} — {company}"
    return OutreachDraft(channel, recipient, subject, body, links)


def send_outreach(
    draft: OutreachDraft,
    *,
    confirmed_by_user: bool,
    sender: Callable[[OutreachDraft], None],
) -> None:
    """Send only after explicit human confirmation."""
    if not confirmed_by_user:
        raise PermissionError(
            "external outreach requires explicit user confirmation"
        )
    sender(draft)
