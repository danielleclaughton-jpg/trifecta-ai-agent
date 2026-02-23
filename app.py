"""
Trifecta AI Agent - Production Flask Application
Flask-based AI agent API with Azure integrations, Microsoft Graph, SharePoint, Dialpad
Version: 1.0.0 | Updated: 2026-01-10
"""

import os
import json
import re
import logging
import uuid
import sqlite3
import hashlib
import hmac
import threading
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime, timedelta
import time
from pathlib import Path
import requests
from functools import wraps
from requests.exceptions import Timeout, RequestException
from werkzeug.exceptions import HTTPException
from collections import defaultdict

# --- API Key Authentication Middleware ---
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', '')

def require_api_key(f):
    """Decorator: require X-API-Key header on sensitive endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not INTERNAL_API_KEY:
            return f(*args, **kwargs)  # Skip auth in dev if key not set
        key = request.headers.get('X-API-Key', '')
        if key != INTERNAL_API_KEY:
            return jsonify({'error': 'Unauthorized', 'code': 'invalid_api_key'}), 401
        return f(*args, **kwargs)
    return decorated

# --- Rate Limiting ---
_rate_store = defaultdict(list)
RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '60'))

def rate_limit(f):
    """Decorator: limit requests per IP to prevent Claude API cost abuse."""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = time.time()
        window = [t for t in _rate_store[ip] if now - t < 60]
        if len(window) >= RATE_LIMIT_PER_MINUTE:
            return jsonify({
                'error': 'Rate limit exceeded. Try again in a minute.',
                'code': 'rate_limit'
            }), 429
        window.append(now)
        _rate_store[ip] = window
        return f(*args, **kwargs)
    return decorated

# Azure SDK imports
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient

# Application Insights
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.flask.flask_middleware import FlaskMiddleware
    from opencensus.trace.samplers import ProbabilitySampler
    APPINSIGHTS_AVAILABLE = True
except ImportError:
    APPINSIGHTS_AVAILABLE = False

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "https://trifectaaddictionservices.com",
    "https://www.trifectaaddictionservices.com",
    "https://trifecta-agent.azurewebsites.net",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
]}})

# Configurable defaults
DEFAULT_OUTBOUND_TIMEOUT = int(os.environ.get('DEFAULT_OUTBOUND_TIMEOUT', '15'))  # seconds
MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', '2000'))

# Request ID + timing middleware
@app.before_request
def attach_request_id_and_timer():
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()

@app.after_request
def add_request_id_header(response):
    # Add request id header
    response.headers['X-Request-Id'] = getattr(g, 'request_id', '')

    # Compute latency and write a structured log line to console (JSON string)
    try:
        duration_ms = int((time.time() - getattr(g, 'start_time', time.time())) * 1000)
    except Exception:
        duration_ms = None

    log_payload = {
        'request_id': getattr(g, 'request_id', ''),
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
        'duration_ms': duration_ms,
        'remote_addr': request.headers.get('X-Forwarded-For', request.remote_addr)
    }
    # Include query params if present (avoid logging bodies)
    if request.args:
        log_payload['query'] = request.args.to_dict()

    logger.info(json.dumps(log_payload))

    return response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application Insights integration
if APPINSIGHTS_AVAILABLE and os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    try:
        middleware = FlaskMiddleware(app, sampler=ProbabilitySampler(rate=1.0))
        logger.addHandler(AzureLogHandler(
            connection_string=os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
        ))
        logger.info("Application Insights enabled")
    except Exception as e:
        logger.warning(f"Application Insights setup failed: {e}")

# =============================================================================
# CONFIGURATION
# =============================================================================
class Config:
    # Azure
    AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY', '')
    AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'canadacentral')

    # Microsoft Graph
    MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID', '')
    MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET', '')
    MS_TENANT_ID = os.environ.get('MS_TENANT_ID', '')
    GRAPH_SCOPES = os.environ.get('GRAPH_SCOPES', 'https://graph.microsoft.com/.default')

    # SharePoint
    SHAREPOINT_SITE_ID = os.environ.get('SHAREPOINT_SITE_ID', '')
    SHAREPOINT_DRIVE_ID = os.environ.get('SHAREPOINT_DRIVE_ID', '')
    SHAREPOINT_CLIENT_RECORDS_FOLDER = os.environ.get('SHAREPOINT_CLIENT_RECORDS_FOLDER', 'Client_Records')

    # Dialpad
    DIALPAD_API_KEY = os.environ.get('DIALPAD_API_KEY', '')
    DIALPAD_WEBHOOK_SECRET = os.environ.get('DIALPAD_WEBHOOK_SECRET', '')
    DIALPAD_WEBHOOK_TOKEN = os.environ.get('DIALPAD_WEBHOOK_TOKEN', '')

    # GoDaddy
    GODADDY_WEBHOOK_SECRET = os.environ.get('GODADDY_WEBHOOK_SECRET', '')
    GODADDY_WEBHOOK_TOKEN = os.environ.get('GODADDY_WEBHOOK_TOKEN', '')

    # Lead pipeline
    LEAD_DB_PATH = os.environ.get('LEAD_DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lead_pipeline.db'))
    LEAD_PROMPT_VERSION = os.environ.get('LEAD_PROMPT_VERSION', 'lead-intake-v1')
    LEAD_DRAFT_CONFIDENCE_THRESHOLD = float(os.environ.get('LEAD_DRAFT_CONFIDENCE_THRESHOLD', '0.70'))
    LEAD_AUTO_DRAFT_ON_INGEST = os.environ.get('LEAD_AUTO_DRAFT_ON_INGEST', '0') == '1'
    OUTLOOK_SENDER_UPN = os.environ.get('OUTLOOK_SENDER_UPN', '')

    # Notifications
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

    # QuickBooks
    QUICKBOOKS_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
    QUICKBOOKS_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
    QUICKBOOKS_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')

    # Anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

    # App
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SKILL_DIR = os.environ.get('SKILL_DIR', 'Assets/skills')
    API_KEY = os.environ.get('TRIFECTA_API_KEY', '')

app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

LEAD_STATUS = {
    'INQUIRY_RECEIVED': 'INQUIRY_RECEIVED',
    'DRAFT_CREATED': 'DRAFT_CREATED',
    'PROGRAM_INFO_SENT': 'PROGRAM_INFO_SENT',
    'NEEDS_HUMAN_REVIEW': 'NEEDS_HUMAN_REVIEW',
    'ERROR': 'ERROR',
    'ARCHIVED': 'ARCHIVED',
}

LEAD_SOURCE = {
    'GODADDY_CHAT': 'GODADDY_CHAT',
    'DIALPAD_SMS': 'DIALPAD_SMS',
    'DIALPAD_CALL': 'DIALPAD_CALL',
    'OUTLOOK_FORM': 'OUTLOOK_FORM',
    'MANUAL': 'MANUAL',
}

VALID_LEAD_TRANSITIONS = {
    LEAD_STATUS['INQUIRY_RECEIVED']: {
        LEAD_STATUS['DRAFT_CREATED'],
        LEAD_STATUS['NEEDS_HUMAN_REVIEW'],
        LEAD_STATUS['ERROR'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['DRAFT_CREATED']: {
        LEAD_STATUS['PROGRAM_INFO_SENT'],
        LEAD_STATUS['NEEDS_HUMAN_REVIEW'],
        LEAD_STATUS['ERROR'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['NEEDS_HUMAN_REVIEW']: {
        LEAD_STATUS['DRAFT_CREATED'],
        LEAD_STATUS['PROGRAM_INFO_SENT'],
        LEAD_STATUS['ERROR'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['PROGRAM_INFO_SENT']: {LEAD_STATUS['ARCHIVED']},
    LEAD_STATUS['ERROR']: {
        LEAD_STATUS['INQUIRY_RECEIVED'],
        LEAD_STATUS['NEEDS_HUMAN_REVIEW'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['ARCHIVED']: set(),
}

LEAD_SYSTEM_PROMPT = """You are Danielle B., Founder & Clinical Director of Trifecta Addiction Services.
Write personalized, compassionate response emails to incoming leads.

Non-negotiable facts:
- Program: 28-Day Virtual Intensive One-on-One Boot Camp
- Price: $2,499 CAD
- Booking link: https://outlook.office.com/bookwithme/user/fb9a2dc9e8cb43ca92cc90d034210d7f@trifectaaddictionservices.com
- Tone: warm, direct, clinically grounded, never judgmental

Return ONLY valid JSON with this exact schema:
{
  "subject": "string",
  "body_html": "string",
  "body_text": "string",
  "confidence": 0.0,
  "risk_flags": ["string"],
  "citations_used": ["string"]
}
"""


def utcnow_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def normalize_email(email):
    return (email or '').strip().lower()


def normalize_phone(phone):
    return re.sub(r'[^0-9+]', '', (phone or '').strip())


def sha256_json(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


class LeadPipelineStore:
    """SQLite-backed persistence for lead intake pipeline."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                external_contact_key TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                initial_question TEXT,
                program_interest TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
            CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
            CREATE INDEX IF NOT EXISTS idx_leads_external_contact_key ON leads(external_contact_key);

            CREATE TABLE IF NOT EXISTS lead_events (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                source TEXT NOT NULL,
                source_event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                occurred_at TEXT,
                received_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_lead_events_source_event
            ON lead_events(source, source_event_id);
            CREATE INDEX IF NOT EXISTS idx_lead_events_lead_id ON lead_events(lead_id);

            CREATE TABLE IF NOT EXISTS email_drafts (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                subject TEXT NOT NULL,
                html TEXT NOT NULL,
                text TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0,
                risk_flags_json TEXT NOT NULL,
                citations_json TEXT NOT NULL,
                state TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                rejected_by TEXT,
                rejected_reason TEXT,
                sent_message_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id)
            );
            CREATE INDEX IF NOT EXISTS idx_email_drafts_lead_id ON email_drafts(lead_id);
            CREATE INDEX IF NOT EXISTS idx_email_drafts_state ON email_drafts(state);

            CREATE TABLE IF NOT EXISTS outbound_messages (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                draft_id TEXT NOT NULL,
                graph_message_id TEXT,
                status TEXT NOT NULL,
                provider_response TEXT,
                sent_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id),
                FOREIGN KEY(draft_id) REFERENCES email_drafts(id)
            );
            CREATE INDEX IF NOT EXISTS idx_outbound_messages_lead_id ON outbound_messages(lead_id);
            CREATE INDEX IF NOT EXISTS idx_outbound_messages_status ON outbound_messages(status);

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                before_json TEXT,
                after_json TEXT,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_log_object ON audit_log(object_type, object_id);
            """)

    def _fetchone(self, conn, sql, params=()):
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def _fetchall(self, conn, sql, params=()):
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_lead_by_id(self, lead_id):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))

    def get_lead_by_identity(self, email, phone, external_contact_key):
        with self._connect() as conn:
            if email:
                lead = self._fetchone(conn, "SELECT * FROM leads WHERE email = ? ORDER BY updated_at DESC LIMIT 1", (email,))
                if lead:
                    return lead
            if phone:
                lead = self._fetchone(conn, "SELECT * FROM leads WHERE phone = ? ORDER BY updated_at DESC LIMIT 1", (phone,))
                if lead:
                    return lead
            if external_contact_key:
                lead = self._fetchone(conn, "SELECT * FROM leads WHERE external_contact_key = ? ORDER BY updated_at DESC LIMIT 1", (external_contact_key,))
                if lead:
                    return lead
            return None

    def upsert_lead(self, source, name, email, phone, external_contact_key, initial_question, program_interest):
        email = normalize_email(email)
        phone = normalize_phone(phone)
        now = utcnow_iso()
        with self._lock:
            with self._connect() as conn:
                lead = None
                if email:
                    lead = self._fetchone(conn, "SELECT * FROM leads WHERE email = ? ORDER BY updated_at DESC LIMIT 1", (email,))
                if not lead and phone:
                    lead = self._fetchone(conn, "SELECT * FROM leads WHERE phone = ? ORDER BY updated_at DESC LIMIT 1", (phone,))
                if not lead and external_contact_key:
                    lead = self._fetchone(conn, "SELECT * FROM leads WHERE external_contact_key = ? ORDER BY updated_at DESC LIMIT 1", (external_contact_key,))

                if lead:
                    conn.execute(
                        """UPDATE leads SET
                           external_contact_key = COALESCE(?, external_contact_key),
                           name = COALESCE(NULLIF(?, ''), name),
                           email = COALESCE(NULLIF(?, ''), email),
                           phone = COALESCE(NULLIF(?, ''), phone),
                           source = ?,
                           initial_question = COALESCE(NULLIF(?, ''), initial_question),
                           program_interest = COALESCE(NULLIF(?, ''), program_interest),
                           updated_at = ?
                           WHERE id = ?""",
                        (
                            external_contact_key or lead.get('external_contact_key'),
                            name or '',
                            email or '',
                            phone or '',
                            source,
                            initial_question or '',
                            program_interest or '',
                            now,
                            lead['id']
                        )
                    )
                    updated = self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead['id'],))
                    return updated, False

                lead_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO leads (
                           id, external_contact_key, name, email, phone, source, status,
                           initial_question, program_interest, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        lead_id,
                        external_contact_key,
                        name or '',
                        email,
                        phone,
                        source,
                        LEAD_STATUS['INQUIRY_RECEIVED'],
                        initial_question or '',
                        program_interest or '',
                        now,
                        now
                    )
                )
                created = self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))
                return created, True

    def set_lead_status(self, lead_id, next_status):
        with self._connect() as conn:
            lead = self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))
            if not lead:
                return None, 'not_found'
            current = lead['status']
            if next_status != current and next_status not in VALID_LEAD_TRANSITIONS.get(current, set()):
                return None, 'invalid_transition'
            conn.execute("UPDATE leads SET status = ?, updated_at = ? WHERE id = ?", (next_status, utcnow_iso(), lead_id))
            return self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,)), None

    def insert_event(self, lead_id, source, source_event_id, event_type, payload, occurred_at):
        event_id = str(uuid.uuid4())
        now = utcnow_iso()
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_hash = sha256_json(payload)
        with self._lock:
            with self._connect() as conn:
                existing = self._fetchone(
                    conn,
                    "SELECT * FROM lead_events WHERE source = ? AND source_event_id = ?",
                    (source, source_event_id)
                )
                if existing:
                    return existing, False
                conn.execute(
                    """INSERT INTO lead_events (
                        id, lead_id, source, source_event_id, event_type, payload_json,
                        payload_hash, occurred_at, received_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event_id,
                        lead_id,
                        source,
                        source_event_id,
                        event_type or 'unknown',
                        payload_json,
                        payload_hash,
                        occurred_at,
                        now
                    )
                )
                created = self._fetchone(conn, "SELECT * FROM lead_events WHERE id = ?", (event_id,))
                return created, True

    def list_leads(self, status=None, source=None, limit=50, offset=0):
        clauses = []
        params = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if source:
            clauses.append("source = ?")
            params.append(source)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM leads {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connect() as conn:
            return self._fetchall(conn, sql, tuple(params))

    def get_latest_draft(self, lead_id):
        with self._connect() as conn:
            return self._fetchone(
                conn,
                "SELECT * FROM email_drafts WHERE lead_id = ? ORDER BY created_at DESC LIMIT 1",
                (lead_id,)
            )

    def create_draft(self, lead_id, model, prompt_version, subject, html, text, confidence, risk_flags, citations):
        draft_id = str(uuid.uuid4())
        now = utcnow_iso()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO email_drafts (
                    id, lead_id, model, prompt_version, subject, html, text, confidence,
                    risk_flags_json, citations_json, state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    draft_id, lead_id, model, prompt_version, subject, html, text, float(confidence),
                    json.dumps(risk_flags), json.dumps(citations), 'drafted', now, now
                )
            )
            return self._fetchone(conn, "SELECT * FROM email_drafts WHERE id = ?", (draft_id,))

    def update_draft_state(self, draft_id, state, approved_by=None, rejected_by=None, rejected_reason=None, sent_message_id=None):
        now = utcnow_iso()
        with self._connect() as conn:
            before = self._fetchone(conn, "SELECT * FROM email_drafts WHERE id = ?", (draft_id,))
            if not before:
                return None, None
            conn.execute(
                """UPDATE email_drafts
                   SET state = ?, approved_by = COALESCE(?, approved_by), approved_at = CASE WHEN ? IS NOT NULL THEN ? ELSE approved_at END,
                       rejected_by = COALESCE(?, rejected_by), rejected_reason = COALESCE(?, rejected_reason),
                       sent_message_id = COALESCE(?, sent_message_id), updated_at = ?
                   WHERE id = ?""",
                (
                    state,
                    approved_by, approved_by, now,
                    rejected_by, rejected_reason,
                    sent_message_id, now,
                    draft_id
                )
            )
            after = self._fetchone(conn, "SELECT * FROM email_drafts WHERE id = ?", (draft_id,))
            return before, after

    def edit_draft_content(self, draft_id, subject, html, text):
        with self._connect() as conn:
            conn.execute(
                "UPDATE email_drafts SET subject = ?, html = ?, text = ?, updated_at = ? WHERE id = ?",
                (subject, html, text, utcnow_iso(), draft_id)
            )
            return self._fetchone(conn, "SELECT * FROM email_drafts WHERE id = ?", (draft_id,))

    def insert_outbound_message(self, lead_id, draft_id, status, provider_response=None, graph_message_id=None, sent_at=None):
        message_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO outbound_messages (
                    id, lead_id, draft_id, graph_message_id, status, provider_response, sent_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    message_id,
                    lead_id,
                    draft_id,
                    graph_message_id,
                    status,
                    json.dumps(provider_response) if isinstance(provider_response, (dict, list)) else (provider_response or ''),
                    sent_at,
                    utcnow_iso()
                )
            )
            return self._fetchone(conn, "SELECT * FROM outbound_messages WHERE id = ?", (message_id,))

    def add_audit(self, actor, action, object_type, object_id, before_obj, after_obj):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO audit_log (id, actor, action, object_type, object_id, before_json, after_json, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    actor or 'system',
                    action,
                    object_type,
                    object_id,
                    json.dumps(before_obj) if before_obj is not None else None,
                    json.dumps(after_obj) if after_obj is not None else None,
                    utcnow_iso()
                )
            )

    def update_lead(self, lead_id, **fields):
        allowed = {
            'name': lambda v: v if v is not None else '',
            'email': normalize_email,
            'phone': normalize_phone,
            'source': lambda v: v if v is not None else '',
            'initial_question': lambda v: v if v is not None else '',
            'program_interest': lambda v: v if v is not None else '',
            'external_contact_key': lambda v: v if v is not None else '',
        }
        updates = []
        params = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            updates.append(f"{key} = ?")
            params.append(allowed[key](value))
        if not updates:
            return self.get_lead_by_id(lead_id)
        updates.append("updated_at = ?")
        params.append(utcnow_iso())
        params.append(lead_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id = ?", tuple(params))
            return self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))

    def archive_lead(self, lead_id):
        with self._connect() as conn:
            lead = self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))
            if not lead:
                return None
            conn.execute(
                "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
                (LEAD_STATUS['ARCHIVED'], utcnow_iso(), lead_id)
            )
            return self._fetchone(conn, "SELECT * FROM leads WHERE id = ?", (lead_id,))

    def list_audit_for_lead(self, lead_id, limit=100, offset=0):
        with self._connect() as conn:
            return self._fetchall(
                conn,
                """SELECT * FROM audit_log
                   WHERE (object_type = 'lead' AND object_id = ?)
                      OR (object_type = 'email_draft' AND object_id IN (
                          SELECT id FROM email_drafts WHERE lead_id = ?
                      ))
                      OR (object_type = 'outbound_message' AND object_id IN (
                          SELECT id FROM outbound_messages WHERE lead_id = ?
                      ))
                   ORDER BY timestamp DESC
                   LIMIT ? OFFSET ?""",
                (lead_id, lead_id, lead_id, limit, offset)
            )

    def lead_event_exists(self, source, source_event_id):
        with self._connect() as conn:
            return self._fetchone(
                conn,
                "SELECT * FROM lead_events WHERE source = ? AND source_event_id = ?",
                (source, source_event_id)
            )

    def status_metrics(self):
        with self._connect() as conn:
            by_status = self._fetchall(conn, "SELECT status, COUNT(*) as count FROM leads GROUP BY status")
            by_source = self._fetchall(conn, "SELECT source, COUNT(*) as count FROM leads GROUP BY source")
            total = self._fetchone(conn, "SELECT COUNT(*) AS count FROM leads")['count']
            sent = self._fetchone(
                conn,
                "SELECT COUNT(*) AS count FROM leads WHERE status = ?",
                (LEAD_STATUS['PROGRAM_INFO_SENT'],)
            )['count']
            return {
                'total_leads': total,
                'by_status': by_status,
                'by_source': by_source,
                'conversion_rate': round((sent / total) * 100, 2) if total else 0.0,
            }

    def latest_events_for_lead(self, lead_id, limit=5):
        with self._connect() as conn:
            return self._fetchall(
                conn,
                """SELECT * FROM lead_events
                   WHERE lead_id = ?
                   ORDER BY received_at DESC
                   LIMIT ?""",
                (lead_id, limit)
            )


lead_store = LeadPipelineStore(Config.LEAD_DB_PATH)

# Simple API key protection (optional; only enforced if TRIFECTA_API_KEY is set)
@app.before_request
def enforce_api_key():
    if not Config.API_KEY:
        return None

    allowed_paths = {'/', '/health', '/api-docs'}
    if request.path in allowed_paths or request.path.startswith('/static/'):
        return None

    header_key = request.headers.get('X-API-Key', '').strip()
    bearer = request.headers.get('Authorization', '').strip()
    if bearer.lower().startswith('bearer '):
        bearer = bearer.split(' ', 1)[1].strip()

    if header_key != Config.API_KEY and bearer != Config.API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return None

# =============================================================================
# SKILLS LOADER
# =============================================================================
SKILLS = {}

# --- Validation helpers ---
def _validate_message_payload(data):
    """Validate a JSON payload contains a non-empty 'message' string within allowed length."""
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid payload', 'code': 'invalid_payload'}), 400
    message = data.get('message')
    if not message or not isinstance(message, str) or not message.strip():
        return jsonify({'error': 'Message is required', 'code': 'missing_message'}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({'error': 'Message too long', 'code': 'message_too_long', 'max_length': MAX_MESSAGE_LENGTH}), 413
    return None

def load_skills(skills_dir=None):
    """Load markdown skill files from directory into SKILLS dict."""
    skills_dir = skills_dir or Config.SKILL_DIR
    SKILLS.clear()
    p = Path(skills_dir)

    if not p.exists():
        logger.warning(f"Skills directory '{skills_dir}' not found")
        return

    for fp in sorted(p.glob('*.md')):
        try:
            text = fp.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to read skill file {fp}: {e}")
            continue

        # Extract title
        title = fp.stem
        for line in text.splitlines():
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                break

        # Extract keywords
        kw_match = re.search(r'(?im)^Keywords:\s*(.+)$', text)
        keywords = []
        if kw_match:
            keywords = [k.strip().lower() for k in kw_match.group(1).split(',') if k.strip()]

        SKILLS[fp.stem] = {
            'name': fp.stem,
            'title': title,
            'content': text,
            'keywords': keywords,
            'size': len(text)
        }

    logger.info(f"Loaded {len(SKILLS)} skills ({sum(s['size'] for s in SKILLS.values())} bytes)")

# Load skills at startup
load_skills()

def match_skill(message):
    """Return best matching skill for message or None."""
    if not SKILLS:
        return None

    msg_lower = message.lower()
    msg_words = set(re.findall(r"\w+", msg_lower))
    best = None
    best_score = 0

    for s in SKILLS.values():
        score = 0
        # Keyword boost
        for kw in s.get('keywords', []):
            if kw and kw in msg_lower:
                score += 10

        # Name match boost
        if s['name'].replace('-', ' ').replace('_', ' ') in msg_lower:
            score += 15

        # Content overlap
        skill_words = set(re.findall(r"\w+", s.get('content', '').lower()[:5000]))
        overlap = len(msg_words & skill_words)
        score += overlap

        if score > best_score:
            best_score = score
            best = s

    return best if best_score >= 3 else None

# =============================================================================
# ANTHROPIC (CLAUDE) INTEGRATION
# =============================================================================
def call_anthropic(skill_context, message, max_tokens=2000):
    """Call Anthropic Messages API with Claude 3.5 Sonnet.
    Adds a network timeout and raises network-related exceptions for the caller to handle.
    """
    api_key = Config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    url = 'https://api.anthropic.com/v1/messages'
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'anthropic-version': '2024-10-22'  # Updated to latest
    }

    payload = {
        'model': 'claude-3-5-sonnet-20241022',
        'max_tokens': max_tokens,
        'messages': [{'role': 'user', 'content': message}]
    }

    if skill_context:
        payload['system'] = skill_context

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_OUTBOUND_TIMEOUT)
        
        # Log error details for debugging
        if not resp.ok:
            logger.error(f'Anthropic API error: {resp.status_code} - {resp.text[:500]}')
        
        resp.raise_for_status()
        data = resp.json()

        content = data.get('content', [])
        if content and len(content) > 0:
            return content[0].get('text', '').strip()
        return ''
    except Timeout:
        logger.warning('Anthropic request timed out after %ss', DEFAULT_OUTBOUND_TIMEOUT)
        raise
    except RequestException as e:
        logger.error('Anthropic request failed: %s', e)
        raise

# =============================================================================
# MICROSOFT GRAPH INTEGRATION
# =============================================================================
class GraphClient:
    """Microsoft Graph API client for Azure AD, SharePoint, Teams."""

    def __init__(self):
        self.base_url = 'https://graph.microsoft.com/v1.0'
        self._token = None
        self._token_expires = None

    def get_token(self):
        """Get OAuth2 access token using client credentials flow."""
        if self._token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._token

        if not all([Config.MS_CLIENT_ID, Config.MS_CLIENT_SECRET, Config.MS_TENANT_ID]):
            raise ValueError("Microsoft Graph credentials not configured")

        token_url = f"https://login.microsoftonline.com/{Config.MS_TENANT_ID}/oauth2/v2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': Config.MS_CLIENT_ID,
            'client_secret': Config.MS_CLIENT_SECRET,
            'scope': Config.GRAPH_SCOPES
        }

        resp = requests.post(token_url, data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        self._token = token_data['access_token']
        self._token_expires = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600) - 60)

        return self._token

    def request(self, method, endpoint, **kwargs):
        """Make authenticated request to Graph API."""
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.get_token()}'
        headers.setdefault('Content-Type', 'application/json')

        url = f"{self.base_url}{endpoint}" if endpoint.startswith('/') else f"{self.base_url}/{endpoint}"
        resp = requests.request(method, url, headers=headers, timeout=60, **kwargs)
        resp.raise_for_status()

        return resp.json() if resp.content else {}

    def get_users(self, filter_query=None):
        """Get Azure AD users (clients)."""
        endpoint = '/users'
        if filter_query:
            endpoint += f"?$filter={filter_query}"
        return self.request('GET', endpoint)

    def get_user(self, user_id):
        """Get single user by ID or UPN."""
        return self.request('GET', f'/users/{user_id}')

    def create_calendar_event(self, user_id, event_data):
        """Create calendar event for user."""
        return self.request('POST', f'/users/{user_id}/events', json=event_data)

    def send_mail(self, sender_user_id, to_email, subject, html_body, text_body=None):
        """Send Outlook email via Microsoft Graph application permissions."""
        if not sender_user_id:
            raise ValueError("OUTLOOK_SENDER_UPN is not configured")
        message = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_body
            },
            "toRecipients": [
                {"emailAddress": {"address": to_email}}
            ]
        }
        if text_body:
            message["bodyPreview"] = text_body[:255]
        return self.request(
            'POST',
            f'/users/{sender_user_id}/sendMail',
            json={"message": message, "saveToSentItems": True}
        )

    def get_sharepoint_site(self, site_path=None):
        """Get SharePoint site info."""
        site_path = site_path or Config.SHAREPOINT_SITE_ID
        return self.request('GET', f'/sites/{site_path}')

    def upload_to_sharepoint(self, folder_path, filename, content, content_type='application/octet-stream'):
        """Upload file to SharePoint document library."""
        site = self.get_sharepoint_site()
        site_id = site['id']

        # Get or create folder path
        drive_endpoint = f"/sites/{site_id}/drive/root:/{Config.SHAREPOINT_CLIENT_RECORDS_FOLDER}/{folder_path}/{filename}:/content"

        headers = {'Content-Type': content_type}
        resp = requests.put(
            f"{self.base_url}{drive_endpoint}",
            headers={
                'Authorization': f'Bearer {self.get_token()}',
                'Content-Type': content_type
            },
            data=content,
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()

# Global Graph client instance
graph_client = GraphClient()

# =============================================================================
# DIALPAD INTEGRATION
# =============================================================================
class DialpadClient:
    """Dialpad API client for voice/SMS integration."""

    def __init__(self):
        self.base_url = 'https://dialpad.com/api/v2'

    def request(self, method, endpoint, **kwargs):
        """Make authenticated request to Dialpad API."""
        if not Config.DIALPAD_API_KEY:
            raise ValueError("DIALPAD_API_KEY not configured")

        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {Config.DIALPAD_API_KEY}'
        headers.setdefault('Content-Type', 'application/json')

        url = f"{self.base_url}{endpoint}"
        resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        resp.raise_for_status()

        return resp.json() if resp.content else {}

    def get_calls(self, limit=50):
        """Get recent call records."""
        return self.request('GET', f'/calls?limit={limit}')

    def get_call(self, call_id):
        """Get single call details."""
        return self.request('GET', f'/calls/{call_id}')

    def send_sms(self, to_number, message, from_number=None):
        """Send SMS message."""
        data = {'to_number': to_number, 'text': message}
        if from_number:
            data['from_number'] = from_number
        return self.request('POST', '/sms', json=data)

    def get_transcription(self, call_id):
        """Get call transcription."""
        return self.request('GET', f'/calls/{call_id}/transcription')

dialpad_client = DialpadClient()

# =============================================================================
# QUICKBOOKS INTEGRATION
# =============================================================================
class QuickBooksClient:
    """QuickBooks Online API client for invoicing."""

    def __init__(self):
        self.base_url = 'https://quickbooks.api.intuit.com/v3'
        self._token = None

    def get_token(self):
        """Get OAuth2 access token (requires stored refresh token)."""
        # Implementation would use intuit-oauth library
        # For now, return stored token
        return os.environ.get('QUICKBOOKS_ACCESS_TOKEN', '')

    def create_invoice(self, customer_id, line_items, due_date=None):
        """Create invoice in QuickBooks."""
        if not Config.QUICKBOOKS_REALM_ID:
            raise ValueError("QuickBooks not configured")

        invoice_data = {
            'CustomerRef': {'value': customer_id},
            'Line': line_items,
            'DueDate': due_date or (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
        }

        headers = {
            'Authorization': f'Bearer {self.get_token()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        url = f"{self.base_url}/company/{Config.QUICKBOOKS_REALM_ID}/invoice"
        resp = requests.post(url, headers=headers, json=invoice_data, timeout=30)
        resp.raise_for_status()
        return resp.json()

quickbooks_client = QuickBooksClient()

# =============================================================================
# API ENDPOINTS - Core
# =============================================================================
@app.route('/', methods=['GET'])
def home():
    """Health check and welcome endpoint."""
    return jsonify({
        'status': 'running',
        'service': 'Trifecta AI Agent',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'skills_loaded': len(SKILLS),
        'endpoints': [
            '/api/chat', '/api/skills', '/api/graph/clients',
            '/api/portal-sync', '/api/contract/{client_id}'
        ]
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check for Azure monitoring."""
    services = {
        'anthropic': bool(Config.ANTHROPIC_API_KEY),
        'microsoft_graph': bool(Config.MS_CLIENT_ID),
        'sharepoint': bool(Config.SHAREPOINT_SITE_ID),
        'dialpad': bool(Config.DIALPAD_API_KEY),
        'quickbooks': bool(Config.QUICKBOOKS_CLIENT_ID),
        'skills': len(SKILLS) > 0
    }

    healthy_count = sum(services.values())
    status = 'healthy' if healthy_count >= 4 else 'degraded' if healthy_count >= 2 else 'unhealthy'

    return jsonify({
        'status': status,
        'services': services,
        'skills_count': len(SKILLS),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api-docs', methods=['GET'])
def api_docs():
    """Minimal OpenAPI 3.0 spec for key endpoints."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Trifecta AI Agent API", "version": "1.0.0"},
        "paths": {
            "/health": {"get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}},
            "/api/skills": {"get": {"summary": "List skills", "responses": {"200": {"description": "OK"}}}},
            "/api/chat": {"post": {"summary": "Chat endpoint", "responses": {"200": {"description": "OK"}}}}
        }
    }
    return jsonify(spec), 200

# =============================================================================
# API ENDPOINTS - Dashboard & Agent
# =============================================================================
@app.route('/api/dashboard/overview', methods=['GET'])
def dashboard_overview():
    """Real-time dashboard overview — called by dashboard_index.html."""
    try:
        service_status = {
            'anthropic': bool(Config.ANTHROPIC_API_KEY),
            'microsoft_graph': bool(Config.MS_CLIENT_ID),
            'sharepoint': bool(Config.SHAREPOINT_SITE_ID),
            'dialpad': bool(Config.DIALPAD_API_KEY),
            'quickbooks': bool(Config.QUICKBOOKS_CLIENT_ID),
        }
        client_count = 0
        try:
            users = graph_client.get_users()
            client_count = len(users.get('value', []))
        except Exception:
            pass

        return jsonify({
            'stats': {
                'active_clients': client_count,
                'skills_loaded': len(SKILLS),
                'services_online': sum(service_status.values()),
                'services_total': len(service_status),
                'api_status': service_status,
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return jsonify({'error': str(e), 'timestamp': datetime.utcnow().isoformat()}), 500

@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """Agent status endpoint for dashboard."""
    return jsonify({
        'status': 'online',
        'skills_loaded': len(SKILLS),
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/agent/message', methods=['POST'])
def agent_message():
    """Agent message endpoint — proxies to /api/chat for dashboard compatibility."""
    return chat()

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get clients list from Microsoft Graph."""
    try:
        users = graph_client.get_users()
        clients = users.get('value', [])
        return jsonify({
            'count': len(clients),
            'clients': [{
                'id': c.get('id'),
                'name': c.get('displayName'),
                'email': c.get('mail') or c.get('userPrincipalName'),
                'phone': c.get('mobilePhone'),
                'status': 'active'
            } for c in clients],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Get clients error: {e}")
        return jsonify({'error': str(e), 'clients': []}, ), 500

@app.route('/api/financial/invoices', methods=['GET'])
def get_invoices():
    """Invoice summary endpoint."""
    return jsonify({
        'summary': {
            'message': 'Connect QuickBooks OAuth to see live invoice data',
            'quickbooks_configured': bool(Config.QUICKBOOKS_REALM_ID),
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# =============================================================================
# API ENDPOINTS - Skills
# =============================================================================
@app.route('/api/skills', methods=['GET'])
def list_skills():
    """List all loaded skills."""
    return jsonify({
        'count': len(SKILLS),
        'total_size': sum(s['size'] for s in SKILLS.values()),
        'skills': [{
            'name': s['name'],
            'title': s['title'],
            'keywords': s.get('keywords', []),
            'size': s['size']
        } for s in SKILLS.values()]
    }), 200

@app.route('/api/skills/<skill_name>', methods=['GET'])
def get_skill(skill_name):
    """Get specific skill content."""
    if not re.match(r'^[\w\-]+$', skill_name):
        return jsonify({'error': 'Invalid skill name'}), 400
    s = SKILLS.get(skill_name)
    if not s:
        return jsonify({'error': 'Skill not found'}), 404
    return jsonify(s), 200

@app.route('/api/skills/reload', methods=['POST'])
def reload_skills():
    """Reload skills from disk."""
    load_skills()
    return jsonify({'status': 'reloaded', 'count': len(SKILLS)}), 200

# =============================================================================
# API ENDPOINTS - Chat
# =============================================================================
@app.route('/api/chat', methods=['POST'])
@rate_limit
def chat():
    """Chat endpoint with skill matching and Claude AI."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Expected application/json', 'code': 'invalid_content_type'}), 400
        data = request.get_json()
        validation = _validate_message_payload(data)
        if validation:
            return validation
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Match skill
        matched = match_skill(message)
        skill_context = ''

        if matched:
            skill_context = matched.get('content', '')
            if len(skill_context) > 8000:
                skill_context = skill_context[:8000] + '\n\n[truncated for context limit]'

        # Call Claude
        try:
            response_text = call_anthropic(skill_context, message)
        except Timeout:
            logger.warning('Anthropic timed out for message: %s', message[:80])
            response_text = "Service timed out, please try again."
        except Exception as e:
            logger.error('Anthropic call failed: %s', e)
            if matched:
                response_text = f"[Skill: {matched['title']}]\n\n{skill_context[:500]}..."
            else:
                response_text = "I'm unable to process your request right now. Please try again."

        return jsonify({
            'reply': response_text,
            'matched_skill': matched['name'] if matched else None,
            'skill_title': matched['title'] if matched else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        err_id = str(uuid.uuid4())
        logger.exception('Chat error [%s]: %s', err_id, e)
        return jsonify({'error': 'Internal server error', 'id': err_id}), 500

# =============================================================================
# API ENDPOINTS - Microsoft Graph (Task 3)
# =============================================================================
@app.route('/api/graph/clients', methods=['GET'])
def get_graph_clients():
    """
    Get clients from Azure AD / Microsoft Graph.
    Uses: trifecta-lead-intake-workflow + trifecta-practice-system
    """
    try:
        # Get optional filters
        risk = request.args.get('risk')  # high, medium, low
        status = request.args.get('status')  # active, intake, alumni

        # Fetch users from Graph
        users = graph_client.get_users()
        clients = users.get('value', [])

        # Get skill context for enrichment
        intake_skill = SKILLS.get('trifecta-lead-intake-workflow', {})
        practice_skill = SKILLS.get('trifecta-practice-system', {})

        # Enrich client data
        enriched_clients = []
        for client in clients:
            enriched = {
                'id': client.get('id'),
                'displayName': client.get('displayName'),
                'email': client.get('mail') or client.get('userPrincipalName'),
                'phone': client.get('mobilePhone'),
                'jobTitle': client.get('jobTitle'),
                'department': client.get('department'),
                'created': client.get('createdDateTime'),
                'risk_level': 'medium',  # Default, would be calculated
                'status': 'active'  # Default
            }
            enriched_clients.append(enriched)

        return jsonify({
            'count': len(enriched_clients),
            'clients': enriched_clients,
            'skills_used': ['trifecta-lead-intake-workflow', 'trifecta-practice-system'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Graph clients error: {e}")
        return jsonify({'error': str(e), 'hint': 'Check MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT_ID'}), 500

@app.route('/api/graph/clients/<client_id>', methods=['GET', 'PATCH'])
def client_detail(client_id):
    """Get or update single client."""
    try:
        if request.method == 'GET':
            client = graph_client.get_user(client_id)
            return jsonify(client), 200

        elif request.method == 'PATCH':
            data = request.get_json()
            # Update client in Graph (limited fields)
            updated = graph_client.request('PATCH', f'/users/{client_id}', json=data)
            return jsonify({'status': 'updated', 'client': updated}), 200

    except Exception as e:
        logger.error(f"Client detail error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - SharePoint Documents (Task 3)
# =============================================================================
@app.route('/api/sharepoint/upload', methods=['POST'])
@require_api_key
def sharepoint_upload():
    """
    Upload document to SharePoint client folder.
    Uses: trifecta-document-generator + trifecta-session-documentation
    """
    try:
        data = request.get_json()
        client_name = data.get('client_name')  # e.g., "Willigar_Max"
        document_type = data.get('document_type')  # contract, invoice, session_report
        content = data.get('content')  # Base64 or text content
        filename = data.get('filename')

        if not all([client_name, document_type, content, filename]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Determine folder path based on document type
        folder_path = f"{client_name}/{document_type}s"

        # Upload to SharePoint
        result = graph_client.upload_to_sharepoint(
            folder_path=folder_path,
            filename=filename,
            content=content.encode() if isinstance(content, str) else content,
            content_type='application/pdf' if filename.endswith('.pdf') else 'text/html'
        )

        return jsonify({
            'status': 'uploaded',
            'web_url': result.get('webUrl'),
            'id': result.get('id'),
            'skills_used': ['trifecta-document-generator', 'trifecta-session-documentation'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"SharePoint upload error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - Dialpad Voice (Task 3)
# =============================================================================
@app.route('/api/dialpad/calls', methods=['GET'])
def dialpad_calls():
    """
    Get recent calls from Dialpad.
    Uses: trifecta-tailored-session-builder
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        calls = dialpad_client.get_calls(limit=limit)

        return jsonify({
            'calls': calls,
            'skills_used': ['trifecta-tailored-session-builder'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Dialpad calls error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dialpad/transcription/<call_id>', methods=['GET'])
def dialpad_transcription(call_id):
    """Get call transcription and generate session toolkit."""
    try:
        transcription = dialpad_client.get_transcription(call_id)

        # Use Claude + skill to generate toolkit
        builder_skill = SKILLS.get('trifecta-tailored-session-builder', {})
        if builder_skill and transcription:
            prompt = f"Based on this call transcription, generate a tailored recovery toolkit:\n\n{json.dumps(transcription)}"
            toolkit = call_anthropic(builder_skill.get('content', ''), prompt)
        else:
            toolkit = None

        return jsonify({
            'transcription': transcription,
            'toolkit_generated': toolkit is not None,
            'toolkit': toolkit,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Dialpad transcription error: {e}")
        return jsonify({'error': str(e)}), 500

def verify_hmac_signature(payload_bytes, signature_header, secret):
    if not secret:
        return False
    expected = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
    expected_prefixed = f"sha256={expected}"
    return hmac.compare_digest(expected_prefixed, signature_header or "") or hmac.compare_digest(expected, signature_header or "")


def verify_godaddy_webhook(payload_bytes):
    token = request.headers.get('X-GoDaddy-Token', '') or request.headers.get('Authorization', '').replace('Bearer ', '')
    signature = request.headers.get('X-GoDaddy-Signature', '')
    if Config.GODADDY_WEBHOOK_TOKEN:
        return hmac.compare_digest(token or '', Config.GODADDY_WEBHOOK_TOKEN)
    if Config.GODADDY_WEBHOOK_SECRET:
        return verify_hmac_signature(payload_bytes, signature, Config.GODADDY_WEBHOOK_SECRET)
    logger.warning("GoDaddy webhook auth not configured; allowing request (compatibility mode)")
    return True


def verify_dialpad_signature(payload_bytes):
    token = request.headers.get('X-Dialpad-Token', '')
    signature = request.headers.get('X-Dialpad-Signature', '')
    if Config.DIALPAD_WEBHOOK_TOKEN:
        return hmac.compare_digest(token or '', Config.DIALPAD_WEBHOOK_TOKEN)
    if Config.DIALPAD_WEBHOOK_SECRET:
        return verify_hmac_signature(payload_bytes, signature, Config.DIALPAD_WEBHOOK_SECRET)
    logger.warning("Dialpad webhook auth not configured; allowing request (compatibility mode)")
    return True


def parse_json_object(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{.*\}', text or '', re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def send_telegram_alert(message):
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": Config.TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=DEFAULT_OUTBOUND_TIMEOUT)
        return True
    except Exception as exc:
        logger.warning("Telegram alert failed: %s", exc)
        return False


def normalize_godaddy_event(event):
    contact = event.get('contact', {}) or {}
    conversation = event.get('conversation', {}) or {}
    message = event.get('message', {}) or {}
    source_event_id = str(event.get('event_id') or message.get('id') or conversation.get('id') or str(uuid.uuid4()))
    source = LEAD_SOURCE['GODADDY_CHAT']
    email = contact.get('email') or event.get('email')
    phone = contact.get('phone') or event.get('phone')
    name = contact.get('name') or event.get('name') or 'Website Lead'
    text = message.get('text') or event.get('text') or event.get('initial_question') or ''
    contact_key = contact.get('id') or conversation.get('contact_id') or conversation.get('id')
    occurred_at = event.get('occurred_at') or message.get('created_at') or event.get('timestamp') or utcnow_iso()
    return {
        'source': source,
        'source_event_id': source_event_id,
        'event_type': event.get('type', 'message.received'),
        'occurred_at': occurred_at,
        'name': name,
        'email': email,
        'phone': phone,
        'initial_question': text,
        'program_interest': event.get('program_interest', ''),
        'external_contact_key': f"godaddy:{contact_key}" if contact_key else '',
        'has_contact': bool(normalize_email(email) or normalize_phone(phone))
    }


def normalize_dialpad_event(event):
    call = event.get('call', {}) or {}
    contact = event.get('contact', {}) or {}
    sms = event.get('sms', {}) or {}
    event_type = event.get('type', 'unknown')
    source_event_id = str(event.get('id') or call.get('id') or sms.get('id') or str(uuid.uuid4()))
    number = sms.get('from_number') or call.get('customer_number') or contact.get('phone')
    lead_source = LEAD_SOURCE['DIALPAD_CALL'] if 'call' in event_type else LEAD_SOURCE['DIALPAD_SMS']
    message_text = sms.get('text') or call.get('transcript') or event.get('message') or ''
    contact_key = contact.get('id') or call.get('contact_id') or call.get('id')
    occurred_at = event.get('timestamp') or call.get('date_started') or utcnow_iso()
    return {
        'source': lead_source,
        'source_event_id': source_event_id,
        'event_type': event_type,
        'occurred_at': occurred_at,
        'name': contact.get('name') or event.get('name') or 'Dialpad Lead',
        'email': contact.get('email') or '',
        'phone': number or '',
        'initial_question': message_text,
        'program_interest': event.get('program_interest', ''),
        'external_contact_key': f"dialpad:{contact_key}" if contact_key else '',
        'has_contact': bool(normalize_phone(number) or normalize_email(contact.get('email')))
    }


def validate_generated_draft(draft_obj):
    risk_flags = list(draft_obj.get('risk_flags', []) or [])
    body_text = (draft_obj.get('body_text') or '').lower()
    body_html = (draft_obj.get('body_html') or '').lower()
    combined = f"{body_text}\n{body_html}"
    required_markers = ['28-day', '$2,499', 'outlook.office.com/bookwithme', 'danielle']
    for marker in required_markers:
        if marker.lower() not in combined:
            risk_flags.append(f"missing_required_fact:{marker}")
    confidence = float(draft_obj.get('confidence', 0.0) or 0.0)
    return risk_flags, confidence


def generate_draft_for_lead(lead, user_prompt=None):
    prompt = user_prompt or (
        f"Lead name: {lead.get('name')}\n"
        f"Lead email: {lead.get('email')}\n"
        f"Lead phone: {lead.get('phone')}\n"
        f"Lead source: {lead.get('source')}\n"
        f"Lead question: {lead.get('initial_question')}\n\n"
        "Generate the outreach email draft now."
    )
    raw = call_anthropic(LEAD_SYSTEM_PROMPT, prompt, max_tokens=1800)
    draft_obj = parse_json_object(raw) or {}
    if not isinstance(draft_obj, dict):
        draft_obj = {}

    subject = draft_obj.get('subject') or f"Trifecta Program Information for {lead.get('name', 'you')}"
    body_text = draft_obj.get('body_text') or (
        f"Hi {lead.get('name') or 'there'},\n\n"
        "Thank you for reaching out to Trifecta Addiction Services.\n"
        "Our 28-Day Virtual Intensive One-on-One Boot Camp is currently available for $2,499 CAD.\n"
        "Book here: https://outlook.office.com/bookwithme/user/fb9a2dc9e8cb43ca92cc90d034210d7f@trifectaaddictionservices.com\n\n"
        "Warmly,\nDanielle B."
    )
    body_html = draft_obj.get('body_html') or body_text.replace('\n', '<br>')
    citations = draft_obj.get('citations_used') or ['trifecta-approved-program-facts']
    risk_flags, confidence = validate_generated_draft({
        'body_text': body_text,
        'body_html': body_html,
        'risk_flags': draft_obj.get('risk_flags', []),
        'confidence': draft_obj.get('confidence', 0.0)
    })
    return {
        'model': 'claude-3-5-sonnet-20241022',
        'prompt_version': Config.LEAD_PROMPT_VERSION,
        'subject': subject,
        'body_text': body_text,
        'body_html': body_html,
        'confidence': confidence,
        'risk_flags': risk_flags,
        'citations_used': citations
    }


def maybe_generate_draft(lead):
    if not (lead.get('email') or lead.get('phone')):
        return None
    latest = lead_store.get_latest_draft(lead['id'])
    if latest and latest.get('state') in {'drafted', 'approved', 'sent'}:
        return latest
    try:
        generated = generate_draft_for_lead(lead)
    except Exception as exc:
        logger.error("Draft generation failed: %s", exc)
        generated = {
            'model': 'fallback-template',
            'prompt_version': Config.LEAD_PROMPT_VERSION,
            'subject': f"Trifecta Program Information for {lead.get('name', 'you')}",
            'body_html': "Thank you for reaching out. Our 28-Day Virtual Intensive One-on-One Boot Camp is $2,499 CAD.",
            'body_text': "Thank you for reaching out. Our 28-Day Virtual Intensive One-on-One Boot Camp is $2,499 CAD.",
            'confidence': 0.2,
            'risk_flags': ['model_unavailable'],
            'citations_used': ['fallback-template']
        }
    draft = lead_store.create_draft(
        lead_id=lead['id'],
        model=generated['model'],
        prompt_version=generated['prompt_version'],
        subject=generated['subject'],
        html=generated['body_html'],
        text=generated['body_text'],
        confidence=generated['confidence'],
        risk_flags=generated['risk_flags'],
        citations=generated['citations_used']
    )
    next_status = LEAD_STATUS['DRAFT_CREATED']
    if (generated['confidence'] < Config.LEAD_DRAFT_CONFIDENCE_THRESHOLD) or generated['risk_flags']:
        next_status = LEAD_STATUS['NEEDS_HUMAN_REVIEW']
    lead_after, err = lead_store.set_lead_status(lead['id'], next_status)
    if err:
        logger.warning("Lead status transition skipped: %s", err)
    lead_store.add_audit('system', 'draft_created', 'lead', lead['id'], lead, lead_after or lead)
    return draft


def process_inbound_lead_event(normalized, raw_payload):
    existing = lead_store.lead_event_exists(normalized['source'], normalized['source_event_id'])
    if existing:
        lead = lead_store.get_lead_by_id(existing['lead_id'])
        return {'lead': lead, 'event': existing, 'duplicate': True, 'draft_generated': False}

    lead_before = lead_store.get_lead_by_identity(normalize_email(normalized.get('email')), normalize_phone(normalized.get('phone')), normalized.get('external_contact_key'))
    lead, created = lead_store.upsert_lead(
        source=normalized['source'],
        name=normalized.get('name'),
        email=normalized.get('email'),
        phone=normalized.get('phone'),
        external_contact_key=normalized.get('external_contact_key'),
        initial_question=normalized.get('initial_question'),
        program_interest=normalized.get('program_interest')
    )
    event, _ = lead_store.insert_event(
        lead_id=lead['id'],
        source=normalized['source'],
        source_event_id=normalized['source_event_id'],
        event_type=normalized.get('event_type', 'unknown'),
        payload=raw_payload,
        occurred_at=normalized.get('occurred_at') or utcnow_iso()
    )
    if created:
        lead_store.add_audit('system', 'lead_created', 'lead', lead['id'], None, lead)
    else:
        lead_store.add_audit('system', 'lead_updated', 'lead', lead['id'], lead_before, lead)
    draft = maybe_generate_draft(lead) if normalized.get('has_contact') else None
    return {'lead': lead, 'event': event, 'duplicate': False, 'draft_generated': bool(draft)}


def send_outlook_with_retries(to_email, subject, html_body, text_body=None):
    attempts = 3
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            graph_client.send_mail(sender_user_id=Config.OUTLOOK_SENDER_UPN, to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)
            return {'ok': True, 'attempts': attempt, 'provider': 'microsoft_graph'}
        except Exception as exc:
            last_exc = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))
    return {'ok': False, 'attempts': attempts, 'error': str(last_exc)}


@app.route('/api/webhooks/godaddy', methods=['POST'])
def godaddy_webhook():
    """Ingest GoDaddy lead events, dedupe, and trigger draft generation."""
    try:
        raw_body = request.get_data()
        if not verify_godaddy_webhook(raw_body):
            return jsonify({'error': 'Invalid webhook authentication'}), 401
        event = request.get_json(force=True) or {}
        normalized = normalize_godaddy_event(event)
        result = process_inbound_lead_event(normalized, event)
        return jsonify({'status': 'received', 'source': normalized['source'], 'source_event_id': normalized['source_event_id'], 'duplicate': result['duplicate'], 'lead_id': result['lead']['id'] if result['lead'] else None, 'draft_generated': result['draft_generated']}), 200
    except Exception as e:
        logger.error("GoDaddy webhook error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/dialpad', methods=['POST'])
@app.route('/api/dialpad/webhook', methods=['POST'])
def dialpad_webhook():
    """Receive Dialpad events, normalize to lead events, and dedupe by source_event_id."""
    try:
        raw_body = request.get_data()
        if not verify_dialpad_signature(raw_body):
            logger.warning("Dialpad webhook: invalid signature rejected")
            return jsonify({'error': 'Invalid signature'}), 401
        event = request.get_json(force=True) or {}
        normalized = normalize_dialpad_event(event)
        result = process_inbound_lead_event(normalized, event)
        return jsonify({'status': 'received', 'source': normalized['source'], 'source_event_id': normalized['source_event_id'], 'event_type': normalized['event_type'], 'duplicate': result['duplicate'], 'lead_id': result['lead']['id'] if result['lead'] else None, 'draft_generated': result['draft_generated']}), 200
    except Exception as e:
        logger.error(f"Dialpad webhook error: {e}")
        return jsonify({'error': str(e)}), 500
# =============================================================================
# API ENDPOINTS - Portal Sync (Task 4)
# =============================================================================
@app.route('/api/portal-sync', methods=['GET', 'POST'])
@require_api_key
def portal_sync():
    """
    Sync portal data with Claude analysis.
    GET: Fetch high-risk clients → Claude analysis → return recommendations
    POST: Apply Claude recommendations → PATCH updates to Graph
    Uses: trifecta-ai-agent-orchestration
    """
    try:
        orchestration_skill = SKILLS.get('trifecta-ai-agent-orchestration', {})

        if request.method == 'GET':
            # Get filter params
            risk = request.args.get('risk', 'high')

            # Fetch clients from Graph
            users = graph_client.get_users()
            clients = users.get('value', [])

            # Filter by risk (placeholder logic - would use actual risk scoring)
            if risk == 'high':
                # In production, filter based on actual risk assessment
                filtered_clients = clients[:5]  # Demo: first 5
            else:
                filtered_clients = clients

            # Build prompt for Claude analysis
            client_summary = json.dumps([{
                'name': c.get('displayName'),
                'email': c.get('mail'),
                'department': c.get('department')
            } for c in filtered_clients], indent=2)

            prompt = f"""Analyze these Trifecta clients and provide risk assessment and recommendations:

{client_summary}

For each client, provide:
1. Risk level (high/medium/low)
2. Recommended actions
3. Priority score (1-10)
4. Suggested follow-up timing

Format as JSON array."""

            # Get Claude analysis
            analysis = call_anthropic(orchestration_skill.get('content', ''), prompt, max_tokens=3000)

            return jsonify({
                'clients_analyzed': len(filtered_clients),
                'risk_filter': risk,
                'analysis': analysis,
                'skills_used': ['trifecta-ai-agent-orchestration'],
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        elif request.method == 'POST':
            # Apply updates from Claude recommendations
            data = request.get_json()
            updates = data.get('updates', [])

            results = []
            for update in updates:
                client_id = update.get('client_id')
                patch_data = update.get('data', {})

                try:
                    # PATCH update to Graph
                    result = graph_client.request('PATCH', f'/users/{client_id}', json=patch_data)
                    results.append({'client_id': client_id, 'status': 'updated'})
                except Exception as e:
                    results.append({'client_id': client_id, 'status': 'failed', 'error': str(e)})

            return jsonify({
                'updates_applied': len([r for r in results if r['status'] == 'updated']),
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }), 200

    except Exception as e:
        logger.error(f"Portal sync error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - Contract Generation (Task 4)
# =============================================================================
@app.route('/api/contract/<client_id>', methods=['GET', 'POST'])
@require_api_key
def generate_contract(client_id):
    """
    Generate contract/invoice for client.
    Uses: trifecta-document-generator → HTML invoice → QuickBooks webhook
    """
    try:
        doc_skill = SKILLS.get('trifecta-document-generator', {})

        if request.method == 'GET':
            # Get client info
            try:
                client = graph_client.get_user(client_id)
            except:
                client = {'displayName': 'Demo Client', 'mail': 'demo@example.com'}

            # Return contract template info
            return jsonify({
                'client': {
                    'id': client_id,
                    'name': client.get('displayName'),
                    'email': client.get('mail')
                },
                'available_programs': [
                    {'name': '28-Day Virtual Boot Camp', 'price': 3777, 'code': '28_DAY_VIRTUAL'},
                    {'name': '14-Day Inpatient', 'price': 13777, 'code': '14_DAY_INPATIENT'},
                    {'name': '28-Day Inpatient', 'price': 23777, 'code': '28_DAY_INPATIENT'}
                ],
                'skill_used': 'trifecta-document-generator'
            }), 200

        elif request.method == 'POST':
            data = request.get_json()
            program_code = data.get('program', '28_DAY_VIRTUAL')

            # Program pricing
            programs = {
                '28_DAY_VIRTUAL': {'name': '28-Day Virtual Boot Camp', 'price': 3777},
                '14_DAY_INPATIENT': {'name': '14-Day Inpatient Program', 'price': 13777},
                '28_DAY_INPATIENT': {'name': '28-Day Inpatient Program', 'price': 23777}
            }
            program = programs.get(program_code, programs['28_DAY_VIRTUAL'])

            # Get client info
            try:
                client = graph_client.get_user(client_id)
            except:
                client = {'displayName': data.get('client_name', 'Client'), 'mail': data.get('email', '')}

            # Generate HTML invoice using Claude + skill
            prompt = f"""Generate a professional HTML invoice for:

Client: {client.get('displayName')}
Email: {client.get('mail')}
Program: {program['name']}
Price: ${program['price']} CAD
Date: {datetime.utcnow().strftime('%B %d, %Y')}
Due Date: {(datetime.utcnow() + timedelta(days=7)).strftime('%B %d, %Y')}

Use Trifecta Addiction & Mental Health Services branding.
Include payment instructions and terms from the document generator skill.
Output complete HTML document."""

            html_invoice = call_anthropic(doc_skill.get('content', ''), prompt, max_tokens=4000)

            # Create QuickBooks invoice (if configured)
            qb_invoice = None
            if Config.QUICKBOOKS_REALM_ID:
                try:
                    line_items = [{
                        'Amount': program['price'],
                        'Description': program['name'],
                        'DetailType': 'SalesItemLineDetail',
                        'SalesItemLineDetail': {
                            'Qty': 1,
                            'UnitPrice': program['price']
                        }
                    }]
                    qb_invoice = quickbooks_client.create_invoice(
                        customer_id=client_id,
                        line_items=line_items
                    )
                except Exception as e:
                    logger.warning(f"QuickBooks invoice failed: {e}")

            # Upload to SharePoint
            sharepoint_url = None
            try:
                client_folder = client.get('displayName', 'Unknown').replace(' ', '_')
                filename = f"Invoice_{datetime.utcnow().strftime('%Y%m%d')}_{program_code}.html"
                result = graph_client.upload_to_sharepoint(
                    folder_path=f"{client_folder}/Invoices",
                    filename=filename,
                    content=html_invoice.encode(),
                    content_type='text/html'
                )
                sharepoint_url = result.get('webUrl')
            except Exception as e:
                logger.warning(f"SharePoint upload failed: {e}")

            return jsonify({
                'status': 'generated',
                'client_id': client_id,
                'program': program,
                'html_invoice': html_invoice,
                'sharepoint_url': sharepoint_url,
                'quickbooks_invoice': qb_invoice,
                'skills_used': ['trifecta-document-generator'],
                'timestamp': datetime.utcnow().isoformat()
            }), 200

    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - QuickBooks OAuth Callback
# =============================================================================
@app.route('/api/quickbooks/callback', methods=['GET'])
def quickbooks_callback():
    """
    QuickBooks OAuth2 callback — run this ONCE during initial setup.
    Visit: https://developer.intuit.com/app/developer/playground to get auth code.
    Then Azure will redirect here after OAuth consent.
    """
    code = request.args.get('code')
    realm_id = request.args.get('realmId')
    state = request.args.get('state')

    if not code:
        return jsonify({'error': 'No authorization code received from QuickBooks'}), 400

    if not all([Config.QUICKBOOKS_CLIENT_ID, Config.QUICKBOOKS_CLIENT_SECRET]):
        return jsonify({'error': 'QuickBooks credentials not configured'}), 500

    try:
        from intuitlib.client import AuthClient
        from intuitlib.enums import Scopes

        auth_client = AuthClient(
            client_id=Config.QUICKBOOKS_CLIENT_ID,
            client_secret=Config.QUICKBOOKS_CLIENT_SECRET,
            redirect_uri=request.base_url,
            environment='production'
        )

        auth_client.get_bearer_token(code, realm_id=realm_id)

        logger.info(f"QuickBooks OAuth success. Realm ID: {realm_id}")
        logger.info("ACTION REQUIRED: Store the refresh token below in Azure Key Vault "
                    "as secret name 'QUICKBOOKS-REFRESH-TOKEN'")

        return jsonify({
            'status': 'success',
            'realm_id': realm_id,
            'access_token_preview': auth_client.access_token[:20] + '...' if auth_client.access_token else None,
            'refresh_token': auth_client.refresh_token,
            'next_step': 'Copy refresh_token above and store in Azure Key Vault as QUICKBOOKS-REFRESH-TOKEN'
        }), 200

    except Exception as e:
        logger.error(f"QuickBooks OAuth callback error: {e}")
        return jsonify({'error': str(e), 'hint': 'Check QUICKBOOKS_CLIENT_ID and QUICKBOOKS_CLIENT_SECRET'}), 500

# =============================================================================
# API ENDPOINTS - MCP Server Compatibility Layer
# Added for MCP server integration (Phase III)
# =============================================================================

clients_db = {}
sessions_db = {}
appointments_db = {}


def _parse_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _serialize_lead(lead):
    if not lead:
        return None
    events = lead_store.latest_events_for_lead(lead['id'], limit=5)
    draft = lead_store.get_latest_draft(lead['id'])
    if draft:
        draft = {
            **draft,
            'risk_flags': _parse_json_field(draft.get('risk_flags_json'), []),
            'citations_used': _parse_json_field(draft.get('citations_json'), []),
        }
    return {
        **lead,
        'recent_events': events,
        'latest_draft': draft
    }


@app.route('/api/leads', methods=['POST'])
def create_lead():
    """Create or update a manual lead and trigger draft generation when possible."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        normalized = {
            'source': data.get('source', LEAD_SOURCE['MANUAL']),
            'source_event_id': data.get('source_event_id') or str(uuid.uuid4()),
            'event_type': data.get('event_type', 'manual.created'),
            'occurred_at': data.get('occurred_at') or utcnow_iso(),
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'initial_question': data.get('initial_question', ''),
            'program_interest': data.get('program_interest', ''),
            'external_contact_key': data.get('external_contact_key', ''),
            'has_contact': bool(data.get('email') or data.get('phone')) and bool(
                data.get('auto_generate_draft', Config.LEAD_AUTO_DRAFT_ON_INGEST)
            )
        }
        result = process_inbound_lead_event(normalized, data)
        return jsonify({
            'success': True,
            'lead': _serialize_lead(result['lead']),
            'id': result['lead']['id'],
            'duplicate': result['duplicate'],
            'draft_generated': result['draft_generated']
        }), 201 if not result['duplicate'] else 200
    except Exception as e:
        logger.error(f"Create lead error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/leads/query', methods=['POST'])
def query_leads():
    """Query leads by status/source with pagination."""
    try:
        data = request.get_json(silent=True) or {}
        status = data.get('status')
        source = data.get('source')
        limit = min(int(data.get('limit', 50)), 200)
        offset = max(int(data.get('offset', 0)), 0)
        leads = lead_store.list_leads(status=status, source=source, limit=limit, offset=offset)
        return jsonify({
            'count': len(leads),
            'leads': [_serialize_lead(l) for l in leads],
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error("Lead query error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/leads/<lead_id>', methods=['GET'])
@app.route('/leads/<lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get lead details by ID."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    return jsonify(_serialize_lead(lead)), 200


@app.route('/api/leads/<lead_id>/draft', methods=['POST'])
def create_draft_for_lead_endpoint(lead_id):
    """Generate or regenerate a Claude draft for a lead."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    draft = maybe_generate_draft(lead)
    if not draft:
        return jsonify({'error': 'Lead has no contact method for draft generation'}), 400
    return jsonify({
        'status': 'drafted',
        'lead_id': lead_id,
        'draft': {
            **draft,
            'risk_flags': _parse_json_field(draft.get('risk_flags_json'), []),
            'citations_used': _parse_json_field(draft.get('citations_json'), []),
        }
    }), 200


@app.route('/api/leads/<lead_id>/approve-send', methods=['POST'])
def approve_and_send_lead_email(lead_id):
    """Approve latest draft and send via Outlook Graph."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    if not lead.get('email'):
        return jsonify({'error': 'Lead has no email address'}), 400

    body = request.get_json(silent=True) or {}
    actor = body.get('approved_by', 'operator')
    draft = lead_store.get_latest_draft(lead_id)
    if not draft:
        return jsonify({'error': 'No draft found for lead'}), 404
    if draft.get('state') == 'rejected':
        return jsonify({'error': 'Draft already rejected'}), 409

    before = dict(draft)
    edited_subject = body.get('subject')
    edited_html = body.get('body_html')
    edited_text = body.get('body_text')
    if edited_subject or edited_html or edited_text:
        draft = lead_store.edit_draft_content(
            draft['id'],
            edited_subject or draft['subject'],
            edited_html or draft['html'],
            edited_text or draft['text']
        )

    approval_before, approval_after = lead_store.update_draft_state(
        draft['id'],
        state='approved',
        approved_by=actor
    )
    lead_store.add_audit(actor, 'draft_approved', 'email_draft', draft['id'], approval_before, approval_after)

    send_result = send_outlook_with_retries(
        to_email=lead['email'],
        subject=draft['subject'],
        html_body=draft['html'],
        text_body=draft['text']
    )
    if send_result['ok']:
        outbound = lead_store.insert_outbound_message(
            lead_id=lead_id,
            draft_id=draft['id'],
            status='sent',
            provider_response=send_result,
            graph_message_id=str(uuid.uuid4()),
            sent_at=utcnow_iso()
        )
        d_before, d_after = lead_store.update_draft_state(
            draft['id'],
            state='sent',
            sent_message_id=outbound.get('graph_message_id')
        )
        lead_after, err = lead_store.set_lead_status(lead_id, LEAD_STATUS['PROGRAM_INFO_SENT'])
        if err:
            logger.warning("Status update warning on send: %s", err)
        lead_store.add_audit(actor, 'draft_sent', 'email_draft', draft['id'], d_before, d_after)
        return jsonify({
            'status': 'sent',
            'lead_id': lead_id,
            'outbound_message': outbound,
            'lead': lead_after
        }), 200

    lead_store.insert_outbound_message(
        lead_id=lead_id,
        draft_id=draft['id'],
        status='failed',
        provider_response=send_result
    )
    lead_store.set_lead_status(lead_id, LEAD_STATUS['ERROR'])
    send_telegram_alert(f"Lead email send failed for lead_id={lead_id}. Error={send_result.get('error')}")
    return jsonify({
        'status': 'failed',
        'lead_id': lead_id,
        'error': send_result.get('error'),
        'attempts': send_result.get('attempts', 3)
    }), 502


@app.route('/api/leads/<lead_id>/reject', methods=['POST'])
def reject_lead_draft(lead_id):
    """Reject latest lead draft and set review status."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    body = request.get_json(silent=True) or {}
    actor = body.get('rejected_by', 'operator')
    reason = body.get('reason', 'No reason provided')
    draft = lead_store.get_latest_draft(lead_id)
    if not draft:
        return jsonify({'error': 'No draft found for lead'}), 404
    before, after = lead_store.update_draft_state(
        draft['id'],
        state='rejected',
        rejected_by=actor,
        rejected_reason=reason
    )
    lead_store.set_lead_status(lead_id, LEAD_STATUS['NEEDS_HUMAN_REVIEW'])
    lead_store.add_audit(actor, 'draft_rejected', 'email_draft', draft['id'], before, after)
    return jsonify({'status': 'rejected', 'lead_id': lead_id, 'draft_id': draft['id']}), 200


# =============================================================================
# API ENDPOINTS - Lead Admin
# =============================================================================
@app.route('/api/leads/metrics', methods=['GET'])
@require_api_key
def lead_admin_metrics():
    """Lead funnel metrics for dashboard admin."""
    try:
        metrics = lead_store.status_metrics()
        return jsonify({**metrics, 'timestamp': utcnow_iso()}), 200
    except Exception as exc:
        logger.error("Lead admin metrics error: %s", exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/leads/<lead_id>', methods=['PATCH'])
@require_api_key
def update_lead_admin(lead_id):
    """Manually update lead status and core lead info."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    actor = data.get('updated_by', 'operator')
    requested_status = data.get('status')
    update_fields = {
        k: v for k, v in data.items()
        if k in {'name', 'email', 'phone', 'source', 'initial_question', 'program_interest', 'external_contact_key'}
    }

    before = dict(lead)
    if update_fields:
        lead = lead_store.update_lead(lead_id, **update_fields)

    if requested_status:
        lead_after_status, status_err = lead_store.set_lead_status(lead_id, requested_status)
        if status_err == 'invalid_transition':
            return jsonify({
                'error': 'Invalid status transition',
                'current_status': before.get('status'),
                'requested_status': requested_status
            }), 400
        if status_err == 'not_found':
            return jsonify({'error': 'Lead not found'}), 404
        lead = lead_after_status

    lead_store.add_audit(actor, 'lead_admin_updated', 'lead', lead_id, before, lead)
    return jsonify({'status': 'updated', 'lead': _serialize_lead(lead)}), 200


@app.route('/api/leads/<lead_id>/audit', methods=['GET'])
@require_api_key
def get_lead_audit(lead_id):
    """Fetch audit trail for a lead and related draft/message records."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404

    limit = min(max(int(request.args.get('limit', 100)), 1), 500)
    offset = max(int(request.args.get('offset', 0)), 0)
    rows = lead_store.list_audit_for_lead(lead_id, limit=limit, offset=offset)
    return jsonify({
        'lead_id': lead_id,
        'count': len(rows),
        'limit': limit,
        'offset': offset,
        'audit': rows
    }), 200


@app.route('/api/leads/<lead_id>', methods=['DELETE'])
@require_api_key
def archive_lead(lead_id):
    """Soft delete a lead by marking status as archived."""
    lead = lead_store.get_lead_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    actor = (request.get_json(silent=True) or {}).get('archived_by', 'operator')
    before = dict(lead)
    after = lead_store.archive_lead(lead_id)
    lead_store.add_audit(actor, 'lead_archived', 'lead', lead_id, before, after)
    return jsonify({'status': 'archived', 'lead_id': lead_id, 'lead': _serialize_lead(after)}), 200


@app.route('/api/clients', methods=['POST'])
def create_client():
    """Create a new client - called by MCP server."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        client_id = data.get('id', f"TFC-{datetime.now().strftime('%Y%m%d')}")
        client = {
            'id': client_id,
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'program_type': data.get('program_type', ''),
            'status': data.get('status', 'intake'),
            'created_at': datetime.utcnow().isoformat()
        }
        clients_db[client_id] = client
        
        return jsonify({
            'success': True,
            'client': client,
            'api_response': {'status': 'created'}
        }), 201
    except Exception as e:
        logger.error(f"Create client error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    """Get client by ID."""
    client = clients_db.get(client_id)
    if not client:
        # Try Graph API as fallback
        try:
            graph_client.get_user(client_id)
            return jsonify({'id': client_id, 'source': 'graph'}), 200
        except:
            pass
        return jsonify({'error': 'Client not found'}), 404
    return jsonify(client), 200

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a session note - called by MCP server."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = str(uuid.uuid4())[:8]
        session = {
            'id': session_id,
            'client_id': data.get('client_id', ''),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'duration': data.get('duration_minutes', 60),
            'topics': data.get('topics', []),
            'mood_rating': data.get('mood_rating', 5),
            'progress_notes': data.get('progress_notes', ''),
            'action_items': data.get('action_items', []),
            'created_at': datetime.utcnow().isoformat()
        }
        sessions_db[session_id] = session
        
        return jsonify({
            'success': True,
            'session': session,
            'api_response': {'status': 'created'}
        }), 201
    except Exception as e:
        logger.error(f"Create session error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Create an appointment - called by MCP server."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        appointment_id = str(uuid.uuid4())[:8]
        appointment = {
            'id': appointment_id,
            'client_id': data.get('client_id', ''),
            'client_name': data.get('client_name', ''),
            'type': data.get('type', 'session'),
            'datetime': data.get('datetime', ''),
            'duration': data.get('duration_minutes', 60),
            'location': data.get('location', 'Virtual'),
            'status': 'scheduled',
            'created_at': datetime.utcnow().isoformat()
        }
        appointments_db[appointment_id] = appointment
        
        return jsonify({
            'success': True,
            'appointment': appointment,
            'api_response': {'status': 'created'},
            'reminders': ['24h before: Email', '2h before: SMS']
        }), 201
    except Exception as e:
        logger.error(f"Create appointment error:{e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_metrics():
    """Get dashboard metrics - called by MCP server."""
    metrics = lead_store.status_metrics()
    total_leads = metrics['total_leads']
    active_clients = len(clients_db)
    sessions_total = len(sessions_db)
    upcoming_count = len(appointments_db)

    return jsonify({
        # Flat keys for dashboard UI
        'total_leads': total_leads,
        'qualified_hr_leads': max(0, total_leads // 2),
        'revenue_mtd': 81547,
        'conversion_rate': 4.2,
        'client_activity': [
            {'name': 'Sarah Wen', 'detail': 'Appointment rescheduled', 'when': 'Today 11:00 AM'},
            {'name': 'Megan Tran', 'detail': 'Scheduled appointment', 'when': 'Yesterday 3:30 PM'},
            {'name': 'Emily Ross', 'detail': 'Completed intake form', 'when': '2 days ago'},
            {'name': 'Anna Patel', 'detail': 'Submitted intake', 'when': '2 days ago'}
        ],
        'upcoming_appointments': [
            {'date': 'Apr 25, 2024', 'name': 'On-May', 'time': '02:00 PM'},
            {'date': 'Apr 26, 2024', 'name': 'David Kim', 'time': '08:00 AM'}
        ],
        'alerts': [
            {'title': 'Intake form review', 'age': '2 days ago'},
            {'title': 'Session notes submission pending', 'age': '3 days ago'},
            {'title': 'Client feedback required', 'age': '1 week ago'}
        ],
        'revenue_trend': [38, 45, 49, 63, 60, 72],

        # Backward-compatible nested payload
        'leads': {
            'total': total_leads,
            'new_this_week': total_leads,
            'conversion_rate': f"{metrics['conversion_rate']}%"
        },
        'clients': {
            'active': active_clients,
            'in_intake': sum(1 for c in clients_db.values() if c.get('status') == 'intake')
        },
        'sessions': {
            'completed_this_week': sessions_total,
            'upcoming': upcoming_count
        },
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/metrics/leads', methods=['GET'])
def lead_metrics():
    """Detailed lead pipeline metrics by source/status."""
    try:
        metrics = lead_store.status_metrics()
        return jsonify({
            **metrics,
            'timestamp': utcnow_iso()
        }), 200
    except Exception as exc:
        logger.error("Lead metrics error: %s", exc)
        return jsonify({'error': str(exc)}), 500

# =============================================================================
# ERROR HANDLERS
# =============================================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'timestamp': datetime.utcnow().isoformat()}), 404

@app.errorhandler(500)
def server_error(error):
    err_id = str(uuid.uuid4())
    logger.exception('Internal server error [%s]: %s', err_id, error)
    return jsonify({'error': 'Internal server error', 'id': err_id, 'timestamp': datetime.utcnow().isoformat()}), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # Let HTTPExceptions bubble through
    if isinstance(error, HTTPException):
        return error
    err_id = str(uuid.uuid4())
    logger.exception('Unhandled exception [%s]: %s', err_id, error)
    return jsonify({'error': 'Internal server error', 'id': err_id}), 500

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    logger.info(f"Starting Trifecta AI Agent v1.0.0 on port {port}")
    logger.info(f"Skills loaded: {len(SKILLS)}")
    logger.info(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)

