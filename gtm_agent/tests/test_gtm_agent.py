import os
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent.gtm_agent import send_prospect_email


def call_send(prospect, **kwargs):
    return send_prospect_email.func(
        prospect,
        "Subject",
        "Body",
        SimpleNamespace(config={}),
        from_rep={"name": "Rep", "email": "rep@example.com"},
        **kwargs,
    )


def test_disqualified_prospect_is_blocked_without_message_id():
    result = call_send({"prospect_id": "LEAD-1", "email": "lead@example.com", "disqualified": True})

    assert result == {
        "status": "blocked",
        "reason": "prospect is flagged disqualified",
        "prospect_id": "LEAD-1",
    }


def test_non_disqualified_prospect_is_sent():
    result = call_send({"prospect_id": "LEAD-2", "email": "lead@example.com", "disqualified": False})

    assert result["status"] == "sent"
    assert result["message_id"].startswith("msg-")


def test_disqualified_prospect_can_be_sent_with_explicit_override():
    result = call_send(
        {"prospect_id": "LEAD-3", "email": "lead@example.com", "disqualified": True},
        override_disqualified=True,
    )

    assert result["status"] == "sent"
    assert result["message_id"].startswith("msg-")
