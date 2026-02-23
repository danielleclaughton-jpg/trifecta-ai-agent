import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "lead_pipeline_test.db"
    app_module.lead_store = app_module.LeadPipelineStore(str(db_path))
    app_module.Config.GODADDY_WEBHOOK_TOKEN = "godaddy-test-token"
    app_module.Config.DIALPAD_WEBHOOK_TOKEN = "dialpad-test-token"
    app_module.Config.OUTLOOK_SENDER_UPN = "sender@example.com"

    monkeypatch.setattr(
        app_module,
        "call_anthropic",
        lambda *args, **kwargs: json.dumps(
            {
                "subject": "Program Information",
                "body_html": (
                    "Hi there,<br>Our 28-Day Virtual Intensive One-on-One Boot Camp is $2,499 CAD."
                    "<br>Book here: https://outlook.office.com/bookwithme/user/test<br>Warmly,<br>Danielle B."
                ),
                "body_text": (
                    "Hi there, Our 28-Day Virtual Intensive One-on-One Boot Camp is $2,499 CAD. "
                    "Book here: https://outlook.office.com/bookwithme/user/test Warmly, Danielle B."
                ),
                "confidence": 0.9,
                "risk_flags": [],
                "citations_used": ["approved-facts"],
            }
        ),
    )

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_godaddy_webhook_is_idempotent(client):
    payload = {
        "event_id": "evt-001",
        "type": "message.received",
        "contact": {"id": "c-1", "name": "Alex", "email": "alex@example.com"},
        "conversation": {"id": "conv-1"},
        "message": {"id": "m-1", "text": "Tell me about your 28-day program"},
    }
    headers = {"X-GoDaddy-Token": "godaddy-test-token"}

    first = client.post("/api/webhooks/godaddy", json=payload, headers=headers)
    assert first.status_code == 200
    first_data = first.get_json()
    assert first_data["duplicate"] is False

    second = client.post("/api/webhooks/godaddy", json=payload, headers=headers)
    assert second.status_code == 200
    second_data = second.get_json()
    assert second_data["duplicate"] is True
    assert second_data["lead_id"] == first_data["lead_id"]

    queried = client.post("/api/leads/query", json={"limit": 10})
    assert queried.status_code == 200
    assert queried.get_json()["count"] == 1


def test_godaddy_webhook_rejects_missing_auth(client):
    payload = {"event_id": "evt-unauth", "contact": {"email": "noauth@example.com"}}
    res = client.post("/api/webhooks/godaddy", json=payload)
    assert res.status_code == 401


def test_approve_send_sets_program_info_sent(client, monkeypatch):
    monkeypatch.setattr(app_module.graph_client, "send_mail", lambda **kwargs: {})

    lead_res = client.post(
        "/api/leads",
        json={
            "name": "Casey",
            "email": "casey@example.com",
            "source": app_module.LEAD_SOURCE["MANUAL"],
            "initial_question": "Need details",
            "auto_generate_draft": True,
        },
    )
    assert lead_res.status_code in [200, 201]
    lead_id = lead_res.get_json()["id"]

    approve_res = client.post(
        f"/api/leads/{lead_id}/approve-send",
        json={"approved_by": "qa-user"},
    )
    assert approve_res.status_code == 200
    assert approve_res.get_json()["status"] == "sent"

    lead_state = client.get(f"/api/leads/{lead_id}")
    assert lead_state.status_code == 200
    assert lead_state.get_json()["status"] == app_module.LEAD_STATUS["PROGRAM_INFO_SENT"]


def test_reject_sets_needs_human_review(client):
    lead_res = client.post(
        "/api/leads",
        json={
            "name": "Jordan",
            "email": "jordan@example.com",
            "source": app_module.LEAD_SOURCE["MANUAL"],
            "initial_question": "Is this private?",
            "auto_generate_draft": True,
        },
    )
    assert lead_res.status_code in [200, 201]
    lead_id = lead_res.get_json()["id"]

    reject_res = client.post(
        f"/api/leads/{lead_id}/reject",
        json={"rejected_by": "qa-user", "reason": "Need custom rewrite"},
    )
    assert reject_res.status_code == 200
    assert reject_res.get_json()["status"] == "rejected"

    lead_state = client.get(f"/api/leads/{lead_id}")
    assert lead_state.status_code == 200
    assert lead_state.get_json()["status"] == app_module.LEAD_STATUS["NEEDS_HUMAN_REVIEW"]
