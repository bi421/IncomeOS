from incomeos.executor.outreach import prepare_outreach, send_outreach


def test_outreach_is_customized_and_grounded():
    draft = prepare_outreach(
        channel="email",
        recipient="recruiter@example.test",
        job_title="Python Engineer",
        company="Example Co",
        proven_skills=["Python", "Python"],
        proof_links=["https://github.com/bi421/IncomeOS"],
    )
    assert draft.subject == "Application: Python Engineer — Example Co"
    assert "Python" in draft.body
    assert draft.proof_links == ("https://github.com/bi421/IncomeOS",)


def test_external_send_requires_confirmation():
    draft = prepare_outreach(
        channel="linkedin",
        recipient="recruiter",
        job_title="Python Engineer",
        company="Example Co",
        proven_skills=["Python"],
        proof_links=[],
    )
    sent = []
    try:
        send_outreach(draft, confirmed_by_user=False, sender=sent.append)
    except PermissionError:
        pass
    else:
        raise AssertionError("unconfirmed outreach was sent")
    assert sent == []


def test_confirmed_send_calls_sender_once():
    draft = prepare_outreach(
        channel="email",
        recipient="recruiter@example.test",
        job_title="Python Engineer",
        company="Example Co",
        proven_skills=["Python"],
        proof_links=[],
    )
    sent = []
    send_outreach(draft, confirmed_by_user=True, sender=sent.append)
    assert sent == [draft]
