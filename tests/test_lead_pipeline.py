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
    app_module.Config.API_KEY = ""
    monkeypatch.setattr(app_module, "INTERNAL_API_KEY", "internal-test-key")

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


def _admin_headers():
    return {"X-API-Key": "internal-test-key"}


def _create_manual_lead(client, **overrides):
    payload = {
        "name": "Test Lead",
        "email": "lead@example.com",
        "source": app_module.LEAD_SOURCE["MANUAL"],
        "initial_question": "Need details",
        "auto_generate_draft": False,
    }
    payload.update(overrides)
    res = client.post("/api/leads", json=payload)
    assert res.status_code in [200, 201]
    return res.get_json()


def test_create_manual_lead_without_contact_skips_draft_generation(client):
    res = client.post(
        "/api/leads",
        json={
            "name": "No Contact",
            "source": app_module.LEAD_SOURCE["MANUAL"],
            "initial_question": "How does this work?",
            "auto_generate_draft": True,
        },
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["draft_generated"] is False
    assert body["lead"]["latest_draft"] is None


def test_create_manual_lead_is_idempotent_for_duplicate_source_event(client):
    payload = {
        "source_event_id": "manual-event-001",
        "name": "Duplicate Lead",
        "email": "dup@example.com",
        "source": app_module.LEAD_SOURCE["MANUAL"],
        "auto_generate_draft": False,
    }
    first = client.post("/api/leads", json=payload)
    assert first.status_code == 201
    second = client.post("/api/leads", json=payload)
    assert second.status_code == 200
    assert second.get_json()["duplicate"] is True
    assert second.get_json()["id"] == first.get_json()["id"]


def test_query_leads_by_status_and_source(client):
    _create_manual_lead(client, email="source1@example.com")
    client.post(
        "/api/webhooks/dialpad",
        json={"id": "dial-1", "type": "sms.received", "sms": {"from_number": "+12223334444", "text": "Info?"}},
        headers={"X-Dialpad-Token": "dialpad-test-token"},
    )

    queried = client.post(
        "/api/leads/query",
        json={
            "status": app_module.LEAD_STATUS["INQUIRY_RECEIVED"],
            "source": app_module.LEAD_SOURCE["MANUAL"],
            "limit": 10,
        },
    )
    assert queried.status_code == 200
    body = queried.get_json()
    assert body["count"] >= 1
    assert all(l["status"] == app_module.LEAD_STATUS["INQUIRY_RECEIVED"] for l in body["leads"])
    assert all(l["source"] == app_module.LEAD_SOURCE["MANUAL"] for l in body["leads"])


def test_generate_draft_endpoint_for_existing_lead(client):
    lead = _create_manual_lead(client, email="draftme@example.com", auto_generate_draft=False)
    lead_id = lead["id"]

    draft_res = client.post(f"/api/leads/{lead_id}/draft")
    assert draft_res.status_code == 200
    body = draft_res.get_json()
    assert body["status"] == "drafted"
    assert body["draft"]["subject"] == "Program Information"


def test_generate_draft_endpoint_rejects_missing_contact(client):
    lead = _create_manual_lead(client, email="", phone="", auto_generate_draft=False, name="No Draft Contact")
    draft_res = client.post(f"/api/leads/{lead['id']}/draft")
    assert draft_res.status_code == 400
    assert "no contact method" in draft_res.get_json()["error"].lower()


def test_reject_sets_needs_human_review(client):
    lead = _create_manual_lead(client, email="review@example.com", auto_generate_draft=True)
    lead_id = lead["id"]

    reject_res = client.post(
        f"/api/leads/{lead_id}/reject",
        json={"rejected_by": "qa-user", "reason": "Need custom rewrite"},
    )
    assert reject_res.status_code == 200
    assert reject_res.get_json()["status"] == "rejected"

    lead_state = client.get(f"/api/leads/{lead_id}")
    assert lead_state.status_code == 200
    assert lead_state.get_json()["status"] == app_module.LEAD_STATUS["NEEDS_HUMAN_REVIEW"]


def test_get_lead_detail_returns_events_and_draft(client):
    lead = _create_manual_lead(client, email="detail@example.com", auto_generate_draft=True)
    lead_detail = client.get(f"/api/leads/{lead['id']}")
    assert lead_detail.status_code == 200
    body = lead_detail.get_json()
    assert isinstance(body["recent_events"], list)
    assert len(body["recent_events"]) >= 1
    assert body["latest_draft"] is not None


def test_dialpad_webhook_ingestion_is_idempotent(client):
    payload = {
        "id": "dial-evt-001",
        "type": "sms.received",
        "contact": {"name": "Alex"},
        "sms": {"id": "sms-1", "from_number": "+12345678900", "text": "Tell me about your program"},
    }
    headers = {"X-Dialpad-Token": "dialpad-test-token"}

    first = client.post("/api/webhooks/dialpad", json=payload, headers=headers)
    assert first.status_code == 200
    first_data = first.get_json()
    assert first_data["duplicate"] is False

    second = client.post("/api/webhooks/dialpad", json=payload, headers=headers)
    assert second.status_code == 200
    second_data = second.get_json()
    assert second_data["duplicate"] is True
    assert second_data["lead_id"] == first_data["lead_id"]


def test_dialpad_webhook_missing_contact_does_not_generate_draft(client):
    payload = {"id": "dial-evt-no-contact", "type": "call.ended", "call": {"id": "call-2"}}
    res = client.post(
        "/api/webhooks/dialpad",
        json=payload,
        headers={"X-Dialpad-Token": "dialpad-test-token"},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["draft_generated"] is False

    lead_res = client.get(f"/api/leads/{body['lead_id']}")
    assert lead_res.status_code == 200
    assert lead_res.get_json()["latest_draft"] is None


def test_patch_lead_rejects_invalid_transition(client):
    lead = _create_manual_lead(client, email="invalid-transition@example.com", auto_generate_draft=False)
    patch_res = client.patch(
        f"/api/leads/{lead['id']}",
        json={"status": app_module.LEAD_STATUS["PROGRAM_INFO_SENT"], "updated_by": "qa-user"},
        headers=_admin_headers(),
    )
    assert patch_res.status_code == 400
    assert patch_res.get_json()["error"] == "Invalid status transition"


def test_patch_lead_updates_info_and_status(client):
    lead = _create_manual_lead(client, email="patch@example.com", auto_generate_draft=True)
    patch_res = client.patch(
        f"/api/leads/{lead['id']}",
        json={
            "name": "Updated Name",
            "phone": "(123) 555-0000",
            "status": app_module.LEAD_STATUS["NEEDS_HUMAN_REVIEW"],
            "updated_by": "danielle",
        },
        headers=_admin_headers(),
    )
    assert patch_res.status_code == 200
    patched = patch_res.get_json()["lead"]
    assert patched["name"] == "Updated Name"
    assert patched["phone"] == "1235550000"
    assert patched["status"] == app_module.LEAD_STATUS["NEEDS_HUMAN_REVIEW"]


def test_get_lead_audit_requires_api_key_and_returns_entries(client):
    lead = _create_manual_lead(client, email="audit@example.com", auto_generate_draft=True)
    lead_id = lead["id"]
    client.post(
        f"/api/leads/{lead_id}/reject",
        json={"rejected_by": "qa-user", "reason": "Needs edits"},
    )

    unauthorized = client.get(f"/api/leads/{lead_id}/audit")
    assert unauthorized.status_code == 401

    authorized = client.get(f"/api/leads/{lead_id}/audit", headers=_admin_headers())
    assert authorized.status_code == 200
    body = authorized.get_json()
    assert body["count"] >= 2
    assert any(entry["action"] in {"lead_created", "draft_rejected"} for entry in body["audit"])


def test_delete_lead_soft_archives(client):
    lead = _create_manual_lead(client, email="archive@example.com")
    res = client.delete(f"/api/leads/{lead['id']}", headers=_admin_headers())
    assert res.status_code == 200
    assert res.get_json()["status"] == "archived"

    lead_detail = client.get(f"/api/leads/{lead['id']}")
    assert lead_detail.status_code == 200
    assert lead_detail.get_json()["status"] == app_module.LEAD_STATUS["ARCHIVED"]


def test_lead_admin_metrics_returns_funnel_stats(client, monkeypatch):
    monkeypatch.setattr(app_module.graph_client, "send_mail", lambda **kwargs: {})

    sent_lead = _create_manual_lead(client, email="sent@example.com", auto_generate_draft=True)
    client.post(f"/api/leads/{sent_lead['id']}/approve-send", json={"approved_by": "qa-user"})
    _create_manual_lead(client, email="new1@example.com", auto_generate_draft=False)
    _create_manual_lead(client, email="new2@example.com", auto_generate_draft=False)

    metrics_res = client.get("/api/leads/metrics", headers=_admin_headers())
    assert metrics_res.status_code == 200
    body = metrics_res.get_json()
    assert body["total_leads"] == 3
    assert isinstance(body["by_status"], list)
    assert isinstance(body["by_source"], list)
    assert body["conversion_rate"] > 0
