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
    app_module.Config.OUTLOOK_FORM_WEBHOOK_TOKEN = "outlook-test-token"
    app_module.Config.OUTLOOK_SENDER_UPN = "sender@example.com"
    app_module.Config.GODADDY_LIVE_SYNC_ENABLED = False
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
    assert body["workflow_stage"] == app_module.WORKFLOW_STAGE["PROGRAM_INFO_READY"]
    assert body["has_contact"] is True
    assert body["last_inbound_at"]
    assert "latest_message_preview" in body


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


def test_outlook_form_webhook_accepts_and_dedupes(client):
    payload = {
        "event_id": "outlook-form-evt-001",
        "createdDateTime": "2026-02-20T09:45:00Z",
        "responses": [
            {"name": "full_name", "value": "Form Lead"},
            {"name": "email", "value": "forms@example.com"},
            {"name": "question", "value": "Can you share program details?"},
        ],
    }
    headers = {"X-Outlook-Token": "outlook-test-token"}

    first = client.post("/api/webhooks/outlook-form", json=payload, headers=headers)
    assert first.status_code == 200
    first_data = first.get_json()
    assert first_data["duplicate"] is False
    assert first_data["source"] == app_module.LEAD_SOURCE["OUTLOOK_FORM"]

    second = client.post("/api/webhooks/outlook-form", json=payload, headers=headers)
    assert second.status_code == 200
    second_data = second.get_json()
    assert second_data["duplicate"] is True
    assert second_data["lead_id"] == first_data["lead_id"]


def test_outlook_form_webhook_missing_contact_skips_draft(client):
    payload = {
        "id": "outlook-form-no-contact",
        "responses": [
            {"name": "full_name", "value": "No Contact"},
            {"name": "question", "value": "Looking for help"},
        ],
    }
    res = client.post(
        "/api/webhooks/outlook-form",
        json=payload,
        headers={"X-Outlook-Token": "outlook-test-token"},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["draft_generated"] is False

    lead_state = client.get(f"/api/leads/{body['lead_id']}")
    assert lead_state.status_code == 200
    assert lead_state.get_json()["latest_draft"] is None
    assert lead_state.get_json()["workflow_stage"] == app_module.WORKFLOW_STAGE["AWAITING_HUMAN_RESPONSE"]


def test_outlook_form_webhook_rejects_missing_auth(client):
    payload = {"event_id": "outlook-form-unauthorized", "email": "blocked@example.com"}
    res = client.post("/api/webhooks/outlook-form", json=payload)
    assert res.status_code == 401
    assert "authentication" in res.get_json()["error"].lower()


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

    bad_page = client.get(
        f"/api/leads/{lead_id}/audit?limit=not-a-number",
        headers=_admin_headers()
    )
    assert bad_page.status_code == 400
    assert bad_page.get_json()["code"] == "invalid_pagination"


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


def test_godaddy_contactless_lead_maps_to_awaiting_email(client):
    payload = {
        "event_id": "gd-evt-001",
        "conversation": {"id": "conv-1", "contact_id": "contact-1"},
        "contact": {"name": "Guest User 1"},
        "message": {"id": "msg-1", "text": "Can I get pricing?", "created_at": "2026-03-18T18:00:00Z"},
    }
    res = client.post("/api/webhooks/godaddy", json=payload, headers={"X-GoDaddy-Token": "godaddy-test-token"})
    assert res.status_code == 200
    lead_id = res.get_json()["lead_id"]

    lead_res = client.get(f"/api/leads/{lead_id}")
    assert lead_res.status_code == 200
    lead = lead_res.get_json()
    assert lead["has_contact"] is False
    assert lead["workflow_stage"] == app_module.WORKFLOW_STAGE["AWAITING_EMAIL"]
    assert lead["needs_response"] is True


def test_lead_board_endpoint_returns_workflow_counts_and_reconciliation(client):
    _create_manual_lead(client, email="board@example.com", auto_generate_draft=True)
    board_res = client.get("/api/leads/board?limit=20&stale_after_hours=48")
    assert board_res.status_code == 200
    body = board_res.get_json()
    assert body["count"] >= 1
    assert "workflow_counts" in body
    assert "reconciliation" in body
    assert "timestamp" in body
    assert body["reconciliation"]["stale_count"] >= 0


def test_build_godaddy_sync_event_maps_contact_form_fields():
    conversation = {
        "id": 822998992,
        "subject": "Contact Form: Contact Us",
        "display_subject": "Contact Form: Contact Us",
        "updated_at": "2026-03-20T03:32:12.488Z",
        "newest_message_timestamp": "2026-03-20T03:32:12.381Z",
        "data": {
            "Name (First, Last)": "kyle schiltroth",
            "Phone": "2047618439",
            "Email": "Kschiltroth@gmail.com",
            "How Can We Help You?": "I'm looking for alcohol treatment and wondering about the cost and availability",
        },
        "last_message": {
            "id": 1900915140,
            "created_at": "2026-03-20T03:32:12.381Z",
            "body": "",
            "user": {
                "id": 852715239,
                "email": "Kschiltroth@gmail.com",
                "staff?": False,
                "friendly_name": "Kschiltroth@gmail.com",
                "identities": [
                    {"type": "email", "identifier": "Kschiltroth@gmail.com"},
                ],
            },
        },
    }

    event = app_module._build_godaddy_sync_event(conversation, messages=[])
    normalized = app_module.normalize_godaddy_event(event)

    assert event["contact"]["name"] == "kyle schiltroth"
    assert event["contact"]["email"] == "kschiltroth@gmail.com"
    assert event["contact"]["phone"] == "2047618439"
    assert "alcohol treatment" in event["message"]["text"].lower()
    assert normalized["external_contact_key"] == "godaddy:852715239"
    assert normalized["has_contact"] is True


def test_lead_board_live_sync_includes_sync_summary(client, monkeypatch):
    app_module.Config.GODADDY_LIVE_SYNC_ENABLED = True
    monkeypatch.setattr(
        app_module,
        "sync_godaddy_live_conversations",
        lambda max_pages=None, page_size=None: {
            "success": True,
            "source": app_module.LEAD_SOURCE["GODADDY_CHAT"],
            "checked_at": "2026-03-20T10:00:00Z",
            "upstream_count": 1,
            "ingested_count": 1,
            "duplicate_count": 0,
            "snapshots": [
                {
                    "conversation": {"id": "conv-live", "contact_id": "contact-live", "updated_at": "2026-03-20T10:00:00Z"},
                    "contact": {"id": "contact-live", "name": "Live Lead", "email": "live@example.com"},
                    "message": {"id": "msg-live", "text": "Need help", "created_at": "2026-03-20T10:00:00Z"},
                }
            ],
        },
    )

    board_res = client.get("/api/leads/board?limit=20&stale_after_hours=48&sync_live=1")
    assert board_res.status_code == 200
    body = board_res.get_json()
    assert body["live_sync"]["success"] is True
    assert body["live_sync"]["upstream_count"] == 1
    assert body["reconciliation"]["upstream_count"] == 1


def test_reconcile_endpoint_detects_missing_and_newer_upstream_activity(client):
    payload = {
        "event_id": "gd-evt-002",
        "conversation": {"id": "conv-2", "contact_id": "contact-2", "updated_at": "2026-03-18T10:00:00Z"},
        "contact": {"id": "contact-2", "name": "Taylor", "email": "taylor@example.com"},
        "message": {"id": "msg-2", "text": "Interested in boot camp", "created_at": "2026-03-18T10:00:00Z"},
    }
    created = client.post("/api/webhooks/godaddy", json=payload, headers={"X-GoDaddy-Token": "godaddy-test-token"})
    assert created.status_code == 200

    reconcile_res = client.post(
        "/api/leads/reconcile",
        json={
            "source": app_module.LEAD_SOURCE["GODADDY_CHAT"],
            "upstream_conversations": [
                {
                    "conversation": {"id": "conv-2", "contact_id": "contact-2", "updated_at": "2026-03-19T12:00:00Z"},
                    "contact": {"id": "contact-2", "name": "Taylor", "email": "taylor@example.com"},
                    "message": {"id": "msg-3", "text": "Following up", "created_at": "2026-03-19T12:00:00Z"},
                },
                {
                    "conversation": {"id": "conv-missing", "contact_id": "contact-missing", "updated_at": "2026-03-19T08:00:00Z"},
                    "contact": {"id": "contact-missing", "name": "Missing Lead"},
                    "message": {"id": "msg-missing", "text": "Need help now", "created_at": "2026-03-19T08:00:00Z"},
                },
            ],
        },
    )
    assert reconcile_res.status_code == 200
    reconciliation = reconcile_res.get_json()["reconciliation"]
    assert reconciliation["missing_count"] == 1
    assert reconciliation["mismatch_count"] == 1
    assert reconciliation["missing_leads"][0]["is_missing_from_pipeline"] is True
