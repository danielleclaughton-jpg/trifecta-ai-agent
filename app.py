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
import subprocess
from flask import Flask, request, jsonify, g, send_from_directory, redirect
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import time
from pathlib import Path
import requests
from functools import wraps
from requests.exceptions import Timeout, RequestException
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
try:
    import jwt as pyjwt
    PYJWT_AVAILABLE = True
except ImportError:
    pyjwt = None
    PYJWT_AVAILABLE = False
from collections import defaultdict
from io import BytesIO

# --- Real-time Dashboard Integration ---
# Emit events to Lamby Command Center Socket.IO server
# so the dashboard updates in < 1 second, not 30s
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:3015').rstrip('/')

def emit_to_dashboard(event_type, message, data=None):
    """
    POST to dashboard's /api/realtime/emit endpoint.
    Runs in background thread so it never blocks Flask.
    """
    def _emit():
        try:
            resp = requests.post(
                f"{DASHBOARD_URL}/api/realtime/emit",
                json={"event_type": event_type, "message": message, "data": data or {}},
                timeout=3,
            )
            if resp.status_code == 200:
                logger.debug(f"[Realtime Emit] {event_type}: {message}")
            else:
                logger.warning(f"[Realtime Emit] Failed ({resp.status_code}): {event_type}")
        except RequestException as e:
            # Non-blocking: dashboard might not be running locally
            logger.debug(f"[Realtime Emit] Dashboard unreachable: {e}")

    threading.Thread(target=_emit, daemon=True).start()

# --- API Key Authentication Middleware ---
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', '')

def require_api_key(f):
    """Decorator: require X-API-Key header on sensitive endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not INTERNAL_API_KEY:
            if bool(os.environ.get('WEBSITE_SITE_NAME')):
                # On Azure: reject if no API key configured (security hardening)
                return jsonify({'error': 'Server misconfigured: INTERNAL_API_KEY not set', 'code': 'no_api_key'}), 500
            return f(*args, **kwargs)  # Skip auth in local dev if key not set
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

# Azure SDK imports (optional — not needed for local dev)
try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_SDK_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    AZURE_SDK_AVAILABLE = False
    DefaultAzureCredential = None
    ClientSecretCredential = None
    SecretClient = None

# Application Insights
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.flask.flask_middleware import FlaskMiddleware
    from opencensus.trace.samplers import ProbabilitySampler
    APPINSIGHTS_AVAILABLE = True
except ImportError:
    APPINSIGHTS_AVAILABLE = False

# Load environment variables
# Detect local vs Azure: Azure App Service sets WEBSITE_SITE_NAME automatically
from dotenv import load_dotenv

_base_dir = os.path.dirname(os.path.abspath(__file__))
IS_AZURE = bool(os.environ.get('WEBSITE_SITE_NAME') or os.environ.get('WEBSITE_INSTANCE_ID'))

if IS_AZURE:
    # On Azure: load .env (production secrets are in Azure App Settings)
    env_path = os.path.join(_base_dir, '.env')
    load_dotenv(env_path)
else:
    # Local development: load .env.local first (overrides), then .env as fallback
    env_local_path = os.path.join(_base_dir, '.env.local')
    env_path = os.path.join(_base_dir, '.env')
    if os.path.exists(env_local_path):
        load_dotenv(env_local_path)
    load_dotenv(env_path)  # Won't override already-set vars from .env.local

# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": [
    "https://trifectaaddictionservices.com",
    "https://www.trifectaaddictionservices.com",
    "https://trifecta-agent.azurewebsites.net",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:3015",
    "http://127.0.0.1:3015",
    "http://localhost:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3003",
]}})

# Configure logging (must be before blueprint registration)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register content drafts blueprint
try:
    from content_api import content_bp
    app.register_blueprint(content_bp)
    logger.info("Content drafts API registered at /api/content")
except Exception as _e:
    logger.warning(f"Failed to register content_api blueprint: {_e}")

# --- Dashboard (served from Flask in production) ---
@app.route('/dashboard')
def serve_dashboard():
    """Serve the command center dashboard."""
    return send_from_directory(_base_dir, 'dashboard_index.html')

@app.route('/dashboard_assets/<path:filename>')
def serve_dashboard_assets(filename):
    """Serve dashboard static assets (logos, CSS, etc.)."""
    return send_from_directory(os.path.join(_base_dir, 'dashboard_assets'), filename)

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
    GODADDY_LIVE_SYNC_ENABLED = os.environ.get('GODADDY_LIVE_SYNC_ENABLED', '1' if not IS_AZURE else '0') == '1'
    GODADDY_LIVE_SYNC_MAX_PAGES = max(1, int(os.environ.get('GODADDY_LIVE_SYNC_MAX_PAGES', '2')))
    GODADDY_LIVE_SYNC_PAGE_SIZE = min(max(int(os.environ.get('GODADDY_LIVE_SYNC_PAGE_SIZE', '30')), 1), 100)
    GODADDY_REAMAZE_BRAND_URL = os.environ.get('GODADDY_REAMAZE_BRAND_URL', '296192a1-995f-4939-9ee8-40270af7aaa5')
    GODADDY_BROWSER_USER_DATA_DIR = os.environ.get(
        'GODADDY_BROWSER_USER_DATA_DIR',
        r'C:\Users\TrifectaAgent\.openclaw\browser\openclaw\user-data'
    )
    GODADDY_CHROME_PATH = os.environ.get(
        'GODADDY_CHROME_PATH',
        r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    )
    GODADDY_BROWSER_DEBUG_URL = os.environ.get('GODADDY_BROWSER_DEBUG_URL', 'http://127.0.0.1:18800')

    # Lead pipeline
    # On Azure, use persistent storage mount; locally, use app directory
    _default_db_dir = '/home/data' if bool(os.environ.get('WEBSITE_SITE_NAME')) else os.path.dirname(os.path.abspath(__file__))
    LEAD_DB_PATH = os.environ.get('LEAD_DB_PATH', os.path.join(_default_db_dir, 'lead_pipeline.db'))
    OIL_GAS_LEAD_DB_PATH = os.environ.get('OIL_GAS_LEAD_DB_PATH', os.path.join(_default_db_dir, 'oil_gas_leads.db'))
    LEAD_PROMPT_VERSION = os.environ.get('LEAD_PROMPT_VERSION', 'lead-intake-v1')
    LEAD_DRAFT_CONFIDENCE_THRESHOLD = float(os.environ.get('LEAD_DRAFT_CONFIDENCE_THRESHOLD', '0.70'))
    LEAD_AUTO_DRAFT_ON_INGEST = os.environ.get('LEAD_AUTO_DRAFT_ON_INGEST', '0') == '1'
    OUTLOOK_SENDER_UPN = os.environ.get('OUTLOOK_SENDER_UPN', '')
    OUTLOOK_FORM_WEBHOOK_TOKEN = os.environ.get('OUTLOOK_FORM_WEBHOOK_TOKEN', '')

    # Notifications
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

    # QuickBooks
    QUICKBOOKS_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
    QUICKBOOKS_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
    QUICKBOOKS_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')

    # Anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

    # OpenAI (direct)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    # OpenRouter (OpenAI-compatible)
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
    OPENROUTER_BASE_URL = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
    OPENROUTER_SITE_URL = os.environ.get('OPENROUTER_SITE_URL', 'https://trifecta-agent.azurewebsites.net')
    OPENROUTER_APP_NAME = os.environ.get('OPENROUTER_APP_NAME', 'Trifecta AI Agent')

    # Provider routing, first available key wins unless explicitly set.
    LLM_PROVIDER_ORDER = os.environ.get('LLM_PROVIDER_ORDER', 'openrouter,openai,anthropic')

    # App
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SKILL_DIR = os.environ.get('SKILL_DIR', 'Assets/skills')
    API_KEY = os.environ.get('TRIFECTA_API_KEY', '')

    # Portal JWT Auth
    PORTAL_JWT_SECRET = os.environ.get('PORTAL_JWT_SECRET', 'dev-portal-jwt-secret-change-in-production')
    PORTAL_JWT_EXPIRY_HOURS = int(os.environ.get('PORTAL_JWT_EXPIRY_HOURS', '24'))

app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

LEAD_STATUS = {
    'INQUIRY_RECEIVED': 'INQUIRY_RECEIVED',
    'DRAFT_CREATED': 'DRAFT_CREATED',
    'PROGRAM_INFO_SENT': 'PROGRAM_INFO_SENT',
    'NEEDS_HUMAN_REVIEW': 'NEEDS_HUMAN_REVIEW',
    'REPLIED': 'REPLIED',
    'CONSULTATION_BOOKED': 'CONSULTATION_BOOKED',
    'ENROLLED': 'ENROLLED',
    'CLOSED': 'CLOSED',
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
    LEAD_STATUS['PROGRAM_INFO_SENT']: {
        LEAD_STATUS['REPLIED'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['REPLIED']: {
        LEAD_STATUS['CONSULTATION_BOOKED'],
        LEAD_STATUS['CLOSED'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['CONSULTATION_BOOKED']: {
        LEAD_STATUS['ENROLLED'],
        LEAD_STATUS['CLOSED'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['ENROLLED']: {
        LEAD_STATUS['CLOSED'],
        LEAD_STATUS['ARCHIVED'],
    },
    LEAD_STATUS['CLOSED']: {LEAD_STATUS['ARCHIVED']},
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
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_iso_datetime(value):
    if not value or not isinstance(value, str):
        return None
    try:
        normalized = value.replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        # Ensure timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


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

            CREATE TABLE IF NOT EXISTS portal_users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'client',
                client_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_portal_users_email ON portal_users(email);

            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                program_type TEXT,
                status TEXT NOT NULL DEFAULT 'intake',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                date TEXT,
                duration INTEGER DEFAULT 60,
                topics TEXT,
                mood_rating INTEGER DEFAULT 5,
                progress_notes TEXT,
                action_items TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_client_id ON sessions(client_id);

            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                client_name TEXT,
                type TEXT DEFAULT 'session',
                datetime TEXT,
                duration INTEGER DEFAULT 60,
                location TEXT DEFAULT 'Virtual',
                status TEXT NOT NULL DEFAULT 'scheduled',
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            CREATE INDEX IF NOT EXISTS idx_appointments_client_id ON appointments(client_id);
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

    def get_latest_outbound_message(self, lead_id):
        with self._connect() as conn:
            return self._fetchone(
                conn,
                "SELECT * FROM outbound_messages WHERE lead_id = ? ORDER BY COALESCE(sent_at, created_at) DESC LIMIT 1",
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

    def list_leads_needing_attention(self, statuses, updated_before=None, limit=100):
        if not statuses:
            return []
        placeholders = ','.join('?' for _ in statuses)
        params = list(statuses)
        sql = f"SELECT * FROM leads WHERE status IN ({placeholders})"
        if updated_before:
            sql += " AND updated_at < ?"
            params.append(updated_before)
        sql += " ORDER BY updated_at ASC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            return self._fetchall(conn, sql, tuple(params))


    # --- Client / Session / Appointment persistence ---

    def upsert_client(self, client):
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO clients (id, first_name, last_name, email, phone, program_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (client['id'], client.get('first_name', ''), client.get('last_name', ''),
                  client.get('email', ''), client.get('phone', ''), client.get('program_type', ''),
                  client.get('status', 'intake'), client.get('created_at', utcnow_iso())))
        return client

    def get_client(self, client_id):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT * FROM clients WHERE id = ?", (client_id,))

    def list_clients(self):
        with self._connect() as conn:
            return self._fetchall(conn, "SELECT * FROM clients ORDER BY created_at DESC")

    def count_clients(self, status=None):
        with self._connect() as conn:
            if status:
                return self._fetchone(conn, "SELECT COUNT(*) AS count FROM clients WHERE status = ?", (status,))['count']
            return self._fetchone(conn, "SELECT COUNT(*) AS count FROM clients")['count']

    def insert_session(self, session):
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT INTO sessions (id, client_id, date, duration, topics, mood_rating, progress_notes, action_items, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session['id'], session.get('client_id', ''), session.get('date', ''),
                  session.get('duration', 60), json.dumps(session.get('topics', [])),
                  session.get('mood_rating', 5), session.get('progress_notes', ''),
                  json.dumps(session.get('action_items', [])), session.get('created_at', utcnow_iso())))
        return session

    def count_sessions(self):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT COUNT(*) AS count FROM sessions")['count']

    def insert_appointment(self, appointment):
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT INTO appointments (id, client_id, client_name, type, datetime, duration, location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (appointment['id'], appointment.get('client_id', ''), appointment.get('client_name', ''),
                  appointment.get('type', 'session'), appointment.get('datetime', ''),
                  appointment.get('duration', 60), appointment.get('location', 'Virtual'),
                  appointment.get('status', 'scheduled'), appointment.get('created_at', utcnow_iso())))
        return appointment

    def count_appointments(self):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT COUNT(*) AS count FROM appointments")['count']

    def list_sessions(self, client_id=None, limit=50):
        with self._connect() as conn:
            if client_id:
                return self._fetchall(conn, "SELECT * FROM sessions WHERE client_id = ? ORDER BY date DESC LIMIT ?", (client_id, limit))
            return self._fetchall(conn, "SELECT * FROM sessions ORDER BY date DESC LIMIT ?", (limit,))

    def list_appointments(self, client_id=None, limit=50):
        with self._connect() as conn:
            if client_id:
                return self._fetchall(conn, "SELECT * FROM appointments WHERE client_id = ? ORDER BY datetime DESC LIMIT ?", (client_id, limit))
            return self._fetchall(conn, "SELECT * FROM appointments ORDER BY datetime DESC LIMIT ?", (limit,))

    # --- Portal User Auth ---
    def get_portal_user_by_email(self, email):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT * FROM portal_users WHERE email = ?", (email,))

    def get_portal_user_by_id(self, user_id):
        with self._connect() as conn:
            return self._fetchone(conn, "SELECT * FROM portal_users WHERE id = ?", (user_id,))

    def create_portal_user(self, user_id, email, password_hash, name, role='client', client_id=None):
        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT INTO portal_users (id, email, password_hash, name, role, client_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, email, password_hash, name, role, client_id, utcnow_iso()))
        return self.get_portal_user_by_id(user_id)

    def list_portal_users(self):
        with self._connect() as conn:
            return self._fetchall(conn, "SELECT id, email, name, role, client_id, created_at FROM portal_users ORDER BY created_at DESC")


lead_store = LeadPipelineStore(Config.LEAD_DB_PATH)

# Simple API key protection (optional; only enforced if TRIFECTA_API_KEY is set)
@app.before_request
def enforce_api_key():
    if not Config.API_KEY:
        return None

    allowed_paths = {'/', '/health', '/api-docs', '/dashboard'}
    if request.path in allowed_paths or request.path.startswith('/static/') or request.path.startswith('/dashboard_assets/'):
        return None

    # Portal endpoints use their own JWT auth, skip API key check
    if request.path.startswith('/api/auth/') or request.path.startswith('/api/client/') or request.path.startswith('/api/admin/'):
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
def _provider_order():
    raw = Config.LLM_PROVIDER_ORDER or 'openrouter,openai,anthropic'
    seen = set()
    order = []
    for item in raw.split(','):
        provider = item.strip().lower()
        if provider and provider not in seen:
            seen.add(provider)
            order.append(provider)
    return order or ['openrouter', 'openai', 'anthropic']


def _extract_openai_content(choice_message):
    content = choice_message.get('content', '')
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(item.get('text', ''))
        return ''.join(parts).strip()
    return str(content).strip()


def _call_openai_compatible(base_url, api_key, model, skill_context, message, max_tokens=2000, extra_headers=None):
    if not api_key:
        raise ValueError('API key not configured')

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    if extra_headers:
        headers.update(extra_headers)

    messages = []
    if skill_context:
        messages.append({'role': 'system', 'content': skill_context})
    messages.append({'role': 'user', 'content': message})

    payload = {
        'model': model,
        'max_tokens': max_tokens,
        'messages': messages,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_OUTBOUND_TIMEOUT)
    if not resp.ok:
        logger.error('OpenAI-compatible API error: %s - %s', resp.status_code, resp.text[:500])
    resp.raise_for_status()
    data = resp.json()
    choices = data.get('choices', [])
    if choices:
        msg = choices[0].get('message', {})
        return _extract_openai_content(msg)
    return ''


def _call_anthropic_only(skill_context, message, max_tokens=2000):
    api_key = Config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY not configured')

    url = 'https://api.anthropic.com/v1/messages'
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'anthropic-version': '2024-10-22',
    }
    payload = {
        'model': Config.ANTHROPIC_MODEL,
        'max_tokens': max_tokens,
        'messages': [{'role': 'user', 'content': message}],
    }
    if skill_context:
        payload['system'] = skill_context

    resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_OUTBOUND_TIMEOUT)
    if not resp.ok:
        logger.error('Anthropic API error: %s - %s', resp.status_code, resp.text[:500])
    resp.raise_for_status()
    data = resp.json()
    content = data.get('content', [])
    if content and len(content) > 0:
        return content[0].get('text', '').strip()
    return ''


def call_anthropic(skill_context, message, max_tokens=2000):
    """LLM call with provider fallback. Keeps legacy function name for compatibility."""
    errors = []
    for provider in _provider_order():
        try:
            if provider == 'openrouter' and Config.OPENROUTER_API_KEY:
                return _call_openai_compatible(
                    Config.OPENROUTER_BASE_URL,
                    Config.OPENROUTER_API_KEY,
                    Config.OPENROUTER_MODEL,
                    skill_context,
                    message,
                    max_tokens=max_tokens,
                    extra_headers={
                        'HTTP-Referer': Config.OPENROUTER_SITE_URL,
                        'X-Title': Config.OPENROUTER_APP_NAME,
                    },
                )
            if provider == 'openai' and Config.OPENAI_API_KEY:
                return _call_openai_compatible(
                    Config.OPENAI_BASE_URL,
                    Config.OPENAI_API_KEY,
                    Config.OPENAI_MODEL,
                    skill_context,
                    message,
                    max_tokens=max_tokens,
                )
            if provider == 'anthropic' and Config.ANTHROPIC_API_KEY:
                return _call_anthropic_only(skill_context, message, max_tokens=max_tokens)
        except Timeout:
            logger.warning('LLM request timed out via provider=%s after %ss', provider, DEFAULT_OUTBOUND_TIMEOUT)
            errors.append(f'{provider}: timeout')
        except RequestException as e:
            logger.error('LLM request failed via provider=%s: %s', provider, e)
            errors.append(f'{provider}: request_failed')
        except Exception as e:
            logger.error('LLM provider error via provider=%s: %s', provider, e)
            errors.append(f'{provider}: {str(e)[:120]}')

    details = ' | '.join(errors) if errors else 'No API key configured'
    raise RuntimeError(f'All configured LLM providers failed. Details: {details}')

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
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
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
        self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', 3600) - 60)

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

    def get_calendar_events(self, user_id, days_ahead=7):
        """Get upcoming calendar events for user."""
        start = datetime.now(timezone.utc).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()
        return self.request(
            'GET',
            f'/users/{user_id}/calendarView?startDateTime={start}&endDateTime={end}&$top=50&$orderby=start/dateTime'
        )

    def get_inbox_messages(self, user_id, top=10, unread_only=True):
        """Get recent inbox messages for user."""
        filter_str = "&$filter=isRead eq false" if unread_only else ""
        return self.request(
            'GET',
            f'/users/{user_id}/mailFolders/inbox/messages?$top={top}&$orderby=receivedDateTime desc{filter_str}'
        )

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

# Global Graph client instance (lazy-loaded to prevent startup hang)
graph_client = None

def get_graph_client():
    """Lazy-load the Graph client to avoid blocking Flask startup."""
    global graph_client
    if graph_client is None:
        graph_client = GraphClient()
    return graph_client
# TODO: Wire MS Graph mail webhook (or poll /me/mailFolders/inbox/messages)
# to call update_lead_status() when a reply is received from a known lead email address.
# See: https://learn.microsoft.com/en-us/graph/webhooks

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
        """Send SMS message via Dialpad API.
        
        Dialpad requires to_numbers as an array. from_number should be
        the Trifecta main line: +14039070996
        """
        # Dialpad API requires 'to_numbers' as an array, not 'to_number'
        if isinstance(to_number, list):
            to_numbers = to_number
        else:
            to_numbers = [to_number]
        data = {'to_numbers': to_numbers, 'text': message}
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
    """QuickBooks Online API client for invoicing with auto-refresh."""

    def __init__(self):
        self.base_url = 'https://quickbooks.api.intuit.com/v3'
        self._access_token = None
        self._token_expiry = None

    def get_token(self):
        """Get OAuth2 access token, auto-refreshing if expired."""
        # If we have a valid cached token, return it
        if self._access_token and self._token_expiry and datetime.now(timezone.utc) < self._token_expiry:
            return self._access_token

        # Try to refresh using stored refresh token
        refresh_token = os.environ.get('QUICKBOOKS_REFRESH_TOKEN', '')
        if refresh_token and Config.QUICKBOOKS_CLIENT_ID and Config.QUICKBOOKS_CLIENT_SECRET:
            try:
                from intuitlib.client import AuthClient
                auth_client = AuthClient(
                    client_id=Config.QUICKBOOKS_CLIENT_ID,
                    client_secret=Config.QUICKBOOKS_CLIENT_SECRET,
                    redirect_uri=os.environ.get('QUICKBOOKS_REDIRECT_URI',
                        'https://trifecta-agent.azurewebsites.net/api/quickbooks/callback'),
                    environment='production'
                )
                auth_client.refresh(refresh_token=refresh_token)
                self._access_token = auth_client.access_token
                # QuickBooks tokens expire in 1 hour, refresh 5 min early
                self._token_expiry = datetime.now(timezone.utc) + timedelta(minutes=55)
                logger.info("QuickBooks token refreshed successfully")
                return self._access_token
            except Exception as e:
                logger.error(f"QuickBooks token refresh failed: {e}")

        # Fallback to env var
        return os.environ.get('QUICKBOOKS_ACCESS_TOKEN', '')

    def create_invoice(self, customer_id, line_items, due_date=None):
        """Create invoice in QuickBooks."""
        if not Config.QUICKBOOKS_REALM_ID:
            raise ValueError("QuickBooks not configured")

        invoice_data = {
            'CustomerRef': {'value': customer_id},
            'Line': line_items,
            'DueDate': due_date or (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')
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
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'skills_loaded': len(SKILLS),
        'endpoints': [
            '/api/chat', '/api/skills', '/api/graph/clients',
            '/api/portal-sync', '/api/contract/{client_id}'
        ]
    }), 200

@app.route('/api/agents/status', methods=['GET'])
def agents_status():
    """Return live status of all AI agents from JSON status files."""
    import glob
    status_dir = os.path.join(os.path.dirname(__file__), '..', 'trifecta', 'agent-status')
    status_dir = os.path.abspath(status_dir)
    agents = []
    if os.path.isdir(status_dir):
        for path in glob.glob(os.path.join(status_dir, '*.json')):
            try:
                with open(path, 'r') as f:
                    agents.append(json.load(f))
            except Exception:
                pass
    if not agents:
        agents = [
            {"agent": "Scout", "status": "idle", "last_run": None, "leads_processed": 0, "last_sync": None, "errors": []},
            {"agent": "Lamby", "status": "idle", "last_run": None, "leads_processed": 0, "last_sync": None, "errors": []},
        ]
    return jsonify({"success": True, "data": agents, "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route('/health', methods=['GET'])
def health():
    """Health check for Azure monitoring."""
    llm_ready = bool(Config.OPENROUTER_API_KEY or Config.OPENAI_API_KEY or Config.ANTHROPIC_API_KEY)
    services = {
        'llm': llm_ready,
        'openrouter': bool(Config.OPENROUTER_API_KEY),
        'openai': bool(Config.OPENAI_API_KEY),
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
        'timestamp': datetime.now(timezone.utc).isoformat()
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
    """Real-time dashboard overview â€" called by dashboard_index.html."""
    try:
        llm_ready = bool(Config.OPENROUTER_API_KEY or Config.OPENAI_API_KEY or Config.ANTHROPIC_API_KEY)
        service_status = {
            'llm': llm_ready,
            'openrouter': bool(Config.OPENROUTER_API_KEY),
            'openai': bool(Config.OPENAI_API_KEY),
            'anthropic': bool(Config.ANTHROPIC_API_KEY),
            'microsoft_graph': bool(Config.MS_CLIENT_ID),
            'sharepoint': bool(Config.SHAREPOINT_SITE_ID),
            'dialpad': bool(Config.DIALPAD_API_KEY),
            'quickbooks': bool(Config.QUICKBOOKS_CLIENT_ID),
        }
        client_count = 0
        try:
            users = get_graph_client().get_users()
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return jsonify({'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()}), 500

def _status_count_map(metrics):
    return {row.get('status'): row.get('count', 0) for row in metrics.get('by_status', [])}


def _source_count_map(metrics):
    return {row.get('source'): row.get('count', 0) for row in metrics.get('by_source', [])}


def _humanize_age(timestamp_value):
    if not timestamp_value:
        return "unknown"
    try:
        dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    except Exception:
        return timestamp_value
    seconds = max(int(delta.total_seconds()), 0)
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _mission_control_payload():
    metrics = lead_store.status_metrics()
    status_counts = _status_count_map(metrics)
    source_counts = _source_count_map(metrics)
    review_queue = status_counts.get(LEAD_STATUS['NEEDS_HUMAN_REVIEW'], 0)
    draft_queue = status_counts.get(LEAD_STATUS['DRAFT_CREATED'], 0)
    fresh_inquiries = status_counts.get(LEAD_STATUS['INQUIRY_RECEIVED'], 0)
    sent_count = status_counts.get(LEAD_STATUS['PROGRAM_INFO_SENT'], 0)
    error_count = status_counts.get(LEAD_STATUS['ERROR'], 0)
    archived_count = status_counts.get(LEAD_STATUS['ARCHIVED'], 0)

    active_clients = lead_store.count_clients()
    intake_clients = lead_store.count_clients(status='intake')
    sessions_total = lead_store.count_sessions()
    upcoming_appointments = lead_store.count_appointments()
    total_leads = metrics.get('total_leads', 0)
    active_pipeline = fresh_inquiries + draft_queue + review_queue

    service_status = {
        'anthropic': bool(Config.ANTHROPIC_API_KEY),
        'openai': bool(Config.OPENAI_API_KEY),
        'openrouter': bool(Config.OPENROUTER_API_KEY),
        'microsoft_graph': bool(Config.MS_CLIENT_ID),
        'sharepoint': bool(Config.SHAREPOINT_SITE_ID),
        'dialpad': bool(Config.DIALPAD_API_KEY),
        'quickbooks': bool(Config.QUICKBOOKS_CLIENT_ID),
    }
    services_online = sum(1 for enabled in service_status.values() if enabled)

    recent_leads = []
    for lead in lead_store.list_leads(limit=6):
        recent_leads.append({
            'id': lead.get('id'),
            'title': lead.get('name') or lead.get('email') or 'Unnamed lead',
            'status': lead.get('status'),
            'source': lead.get('source'),
            'summary': lead.get('initial_question') or 'No intake summary captured yet.',
            'age': _humanize_age(lead.get('updated_at') or lead.get('created_at')),
        })

    mission_agents = [
        {
            'name': 'Lead Intake',
            'lane': 'Growth',
            'status': 'hot' if fresh_inquiries else 'steady',
            'model': 'anthropic/claude-opus-4-6',
            'current_work': f"Processing {fresh_inquiries} fresh inquiries and normalizing inbound contact data.",
            'queue': fresh_inquiries,
            'target': 'Website chat, forms, Dialpad inbound',
        },
        {
            'name': 'Draft Desk',
            'lane': 'Comms',
            'status': 'watch' if review_queue else 'steady',
            'model': 'anthropic/claude-sonnet-4-6',
            'current_work': f"{draft_queue} drafts ready, {review_queue} waiting on founder review.",
            'queue': draft_queue + review_queue,
            'target': 'Program info replies and approvals',
        },
        {
            'name': 'Client Operations',
            'lane': 'Care',
            'status': 'steady' if active_clients or intake_clients else 'idle',
            'model': 'system',
            'current_work': f"{active_clients} active clients, {intake_clients} currently in intake, {upcoming_appointments} appointments queued.",
            'queue': upcoming_appointments,
            'target': 'Appointments, records, portal sync',
        },
        {
            'name': 'Founder Radar',
            'lane': 'Exec',
            'status': 'watch' if error_count else 'steady',
            'model': 'mission-control',
            'current_work': f"Watching {active_pipeline} open pipeline items with {error_count} errors needing intervention.",
            'queue': error_count,
            'target': 'Escalations, daily priorities, blockers',
        },
    ]

    return {
        'generated_at': utcnow_iso(),
        'business': {
            'headline': 'Trifecta Mission Control',
            'subhead': 'Live operating view across intake, client delivery, and founder priorities.',
            'lead_pipeline_open': active_pipeline,
            'total_leads': total_leads,
            'conversion_rate': metrics.get('conversion_rate', 0.0),
            'active_clients': active_clients,
            'intake_clients': intake_clients,
            'sessions_logged': sessions_total,
            'upcoming_appointments': upcoming_appointments,
            'program_info_sent': sent_count,
            'archived_leads': archived_count,
            'integrations_online': services_online,
            'integrations_total': len(service_status),
            'revenue_tracking_configured': bool(Config.QUICKBOOKS_REALM_ID),
        },
        'pulse': [
            {
                'label': 'Lead Pipeline',
                'value': str(active_pipeline),
                'detail': f"{fresh_inquiries} new, {draft_queue} drafted, {review_queue} in review",
                'tone': 'hot' if active_pipeline >= 8 else 'steady'
            },
            {
                'label': 'Client Load',
                'value': str(active_clients),
                'detail': f"{intake_clients} in intake, {upcoming_appointments} upcoming appointments",
                'tone': 'steady' if active_clients else 'watch'
            },
            {
                'label': 'Throughput',
                'value': f"{metrics.get('conversion_rate', 0.0)}%",
                'detail': f"{sent_count} leads reached program info sent",
                'tone': 'steady' if sent_count else 'watch'
            },
            {
                'label': 'Integrations',
                'value': f"{services_online}/{len(service_status)}",
                'detail': 'Anthropic, Graph, SharePoint, Dialpad, QuickBooks readiness',
                'tone': 'steady' if services_online >= 4 else 'watch'
            },
        ],
        'agents': mission_agents,
        'focus': [
            f"Founder review queue currently sits at {review_queue} lead(s).",
            f"Lead sources are led by {max(source_counts, key=source_counts.get) if source_counts else 'manual intake'} right now.",
            "OpenAI/Codex is not wired yet in this app environment." if not Config.OPENAI_API_KEY else "OpenAI/Codex is configured and ready to be assigned.",
        ],
        'recent_work': recent_leads,
        'services': service_status,
    }


@app.route('/api/dashboard/mission-control', methods=['GET'])
def dashboard_mission_control():
    """Mission-control payload for founder dashboard and board-room views."""
    try:
        return jsonify(_mission_control_payload()), 200
    except Exception as exc:
        logger.error("Mission control payload error: %s", exc)
        return jsonify({'error': str(exc), 'generated_at': utcnow_iso()}), 500

@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """Agent status endpoint for dashboard."""
    return jsonify({
        'status': 'online',
        'skills_loaded': len(SKILLS),
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/api/agent/message', methods=['POST'])
def agent_message():
    """Agent message endpoint â€" proxies to /api/chat for dashboard compatibility."""
    return chat()

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get clients list from Microsoft Graph."""
    try:
        users = get_graph_client().get_users()
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
            'timestamp': datetime.now(timezone.utc).isoformat()
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
        'timestamp': datetime.now(timezone.utc).isoformat()
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
            logger.warning('LLM request timed out')
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
            'timestamp': datetime.now(timezone.utc).isoformat()
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
        users = get_graph_client().get_users()
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Graph clients error: {e}")
        return jsonify({'error': str(e), 'hint': 'Check MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT_ID'}), 500

@app.route('/api/graph/clients/<client_id>', methods=['GET', 'PATCH'])
def client_detail(client_id):
    """Get or update single client."""
    try:
        if request.method == 'GET':
            client = get_graph_client().get_user(client_id)
            return jsonify(client), 200

        elif request.method == 'PATCH':
            data = request.get_json()
            # Update client in Graph (limited fields)
            updated = get_graph_client().request('PATCH', f'/users/{client_id}', json=data)
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
        result = get_graph_client().upload_to_sharepoint(
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
            'timestamp': datetime.now(timezone.utc).isoformat()
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Dialpad calls error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sms/send', methods=['POST'])
def send_sms_endpoint():
    """Send SMS via Dialpad to a lead or any number.
    
    Body (JSON):
      to_number   - E.164 format phone number (e.g. +14031234567)
      message     - SMS text content
      from_number - Optional; defaults to Trifecta main line +14039070996
      lead_id     - Optional; if provided, logs send attempt against lead
    """
    body = request.get_json(silent=True) or {}
    to_number = body.get('to_number')
    message = body.get('message') or body.get('text')
    from_number = body.get('from_number', '+14039070996')  # Default: Trifecta main line
    lead_id = body.get('lead_id')

    if not to_number:
        return jsonify({'error': 'to_number is required'}), 400
    if not message:
        return jsonify({'error': 'message (or text) is required'}), 400

    try:
        result = dialpad_client.send_sms(
            to_number=to_number,
            message=message,
            from_number=from_number
        )
        logger.info(f"SMS sent via Dialpad to {to_number}: {result.get('id')}")

        # Optionally log against lead
        if lead_id:
            lead_store.insert_outbound_message(
                lead_id=lead_id,
                draft_id=None,
                status='sent',
                provider_response=result
            )
            # Also append to sent-log for real-time Sheet sync
            _append_sent_log({
                'ts': utcnow_iso(),
                'type': 'sms',
                'to': to_number,
                'lead_id': lead_id,
                'subject': (message or '')[:80],
                'channel': 'dialpad',
                'status': 'sent'
            })

        return jsonify({
            'success': True,
            'sms_id': result.get('id'),
            'status': result.get('message_status'),
            'to': result.get('to_numbers'),
            'from': result.get('from_number'),
            'provider': 'dialpad',
            'raw': result
        }), 200

    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 502


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
            'timestamp': datetime.now(timezone.utc).isoformat()
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


def verify_outlook_form_webhook(payload_bytes):
    token = request.headers.get('X-Outlook-Token', '') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if Config.OUTLOOK_FORM_WEBHOOK_TOKEN:
        return hmac.compare_digest(token or '', Config.OUTLOOK_FORM_WEBHOOK_TOKEN)
    logger.warning("Outlook Forms webhook auth not configured; allowing request (compatibility mode)")
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
    # Support both Dialpad real API field (customer_number) and test payload field (phone_number)
    number = sms.get('from_number') or call.get('customer_number') or call.get('phone_number') or contact.get('phone')
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
        'has_contact': bool(normalize_phone(number) or normalize_email(contact.get('email'))),
        # Include full call object for webhook handler to inspect missed flag
        '_call': call,
    }


def normalize_outlook_form_event(event):
    submission = event.get('submission', {}) or {}
    data = event.get('data', {}) or {}
    responses = event.get('responses') or event.get('answers') or event.get('fields') or []
    response_map = {}
    if isinstance(responses, dict):
        for k, v in responses.items():
            response_map[str(k).strip().lower()] = v
    elif isinstance(responses, list):
        for item in responses:
            if not isinstance(item, dict):
                continue
            key = item.get('name') or item.get('key') or item.get('id') or item.get('question') or item.get('label') or item.get('title')
            value = item.get('value')
            if value is None:
                value = item.get('answer')
            if value is None:
                value = item.get('text')
            if value is None:
                value = item.get('response')
            if key:
                response_map[str(key).strip().lower()] = value

    def lookup(*keys):
        for key in keys:
            if key in event and event.get(key):
                return event.get(key)
            if key in submission and submission.get(key):
                return submission.get(key)
            if key in data and data.get(key):
                return data.get(key)
            low_key = str(key).strip().lower()
            if low_key in response_map and response_map.get(low_key):
                return response_map.get(low_key)
        return ''

    source_event_id = str(
        lookup('event_id', 'id', 'submission_id', 'submissionId')
        or f"outlook-form:{sha256_json(event)[:20]}"
    )
    occurred_at = lookup('createdDateTime', 'submitted_at', 'submittedAt', 'timestamp') or utcnow_iso()
    name = lookup('name', 'full_name', 'contact_name', 'responder_name', 'display_name') or 'Forms Lead'
    email = lookup('email', 'email_address', 'responder_email')
    phone = lookup('phone', 'phone_number', 'mobile', 'telephone')
    initial_question = lookup('question', 'message', 'comments', 'notes', 'initial_question')
    program_interest = lookup('program_interest', 'program', 'service_interest')
    contact_key = lookup('responder_id', 'responderId', 'submission_id', 'submissionId')

    return {
        'source': LEAD_SOURCE['OUTLOOK_FORM'],
        'source_event_id': source_event_id,
        'event_type': lookup('event_type', 'type') or 'form.submitted',
        'occurred_at': occurred_at,
        'name': name,
        'email': email,
        'phone': phone,
        'initial_question': initial_question,
        'program_interest': program_interest,
        'external_contact_key': f"outlook:{contact_key}" if contact_key else '',
        'has_contact': bool(normalize_email(email) or normalize_phone(phone))
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


def log_lead_to_sheets(lead_data: dict) -> bool:
    """Log a new lead to Google Sheets. Returns True if successful."""
    try:
        creds_path = os.path.join(_base_dir, 'google-credentials.json')
        if not os.path.exists(creds_path):
            logger.warning("Google Sheets: google-credentials.json not found, skipping")
            return False

        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)

        sheet_id = os.environ.get('GOOGLE_SHEETS_ID', '1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0')
        sheet = client.open_by_key(sheet_id).sheet1

        row = [
            lead_data.get('created_at', '')[:10],           # A: Date Contacted
            lead_data.get('name', ''),                       # B: Name
            lead_data.get('email', ''),                      # C: Email
            lead_data.get('phone', ''),                      # D: Phone
            lead_data.get('source', ''),                     # E: Source
            lead_data.get('initial_question', ''),           # F: Initial Question
            '',                                               # G: Date Responded (blank)
            lead_data.get('status', 'INQUIRY_RECEIVED'),     # H: Status
            'No',                                            # I: Follow-up Sent
            lead_data.get('program_interest', ''),           # J: Notes
            '',                                               # K: Last Outreach (blank, filled by sent-log)
            0,                                                # L: Outreach Count (blank, filled by sent-log)
        ]

        sheet.append_row(row)
        logger.info(f"Lead logged to Google Sheets: {lead_data.get('name')}")
        return True

    except Exception as e:
        logger.warning(f"Google Sheets logging failed (non-fatal): {e}")
        return False


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
        # Log new lead to Google Sheets (non-fatal)
        log_lead_to_sheets(dict(lead))
    else:
        lead_store.add_audit('system', 'lead_updated', 'lead', lead['id'], lead_before, lead)
    draft = maybe_generate_draft(lead) if normalized.get('has_contact') else None
    return {'lead': lead, 'event': event, 'duplicate': False, 'draft_generated': bool(draft)}


def update_lead_status(email: str = None, phone: str = None, new_status: str = None, notes: str = None) -> bool:
    """Update lead status when they reply. Updates SQLite + Google Sheets."""
    if not email and not phone:
        return False
    try:
        now = datetime.now(timezone.utc).isoformat()
        email_norm = normalize_email(email) if email else None
        phone_norm = normalize_phone(phone) if phone else None

        # Find the lead
        lead = lead_store.get_lead_by_identity(email_norm, phone_norm, None)
        if not lead:
            return False

        # Update status
        lead_before = dict(lead)
        lead_after, err = lead_store.set_lead_status(lead['id'], new_status)
        if err:
            # If transition isn't in VALID_LEAD_TRANSITIONS, force-update directly
            with lead_store._connect() as conn:
                conn.execute(
                    'UPDATE leads SET status = ?, updated_at = ? WHERE id = ?',
                    (new_status, now, lead['id'])
                )
            lead_after = lead_store.get_lead_by_id(lead['id'])

        lead_store.add_audit('system', 'status_updated', 'lead', lead['id'], lead_before, lead_after)

        # Update Google Sheets if credentials exist
        try:
            creds_path = os.path.join(_base_dir, 'google-credentials.json')
            if os.path.exists(creds_path):
                import gspread
                from google.oauth2.service_account import Credentials
                scopes = ['https://www.googleapis.com/auth/spreadsheets']
                creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(os.environ.get('GOOGLE_SHEETS_ID', '1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0')).sheet1

                # Find the row with this email/phone and update status column (H) and date responded (G)
                cell = sheet.find(email_norm or phone_norm)
                if cell:
                    sheet.update_cell(cell.row, 7, now[:10])   # G: Date Responded
                    sheet.update_cell(cell.row, 8, new_status)  # H: Status
                    # Also refresh I/K/L from sent-log
                    _update_lead_sheets_row(lead['id'], email=email, phone=phone)
        except Exception as e:
            logger.warning(f"Sheets status update failed (non-fatal): {e}")

        logger.info(f"Lead status updated: {email or phone} -> {new_status}")
        return True

    except Exception as e:
        logger.error(f"Lead status update error: {e}")
        return False


def _extract_customer_identity(conversation):
    last_message = conversation.get('last_message') if isinstance(conversation.get('last_message'), dict) else {}
    author = conversation.get('author') if isinstance(conversation.get('author'), dict) else {}
    followers = conversation.get('followers') if isinstance(conversation.get('followers'), list) else []
    candidates = []
    if isinstance(last_message.get('user'), dict):
        candidates.append(last_message.get('user'))
    if author:
        candidates.append(author)
    candidates.extend([item for item in followers if isinstance(item, dict)])

    for candidate in candidates:
        if candidate.get('staff?') or candidate.get('bot?'):
            continue
        return candidate
    return {}


def _extract_conversation_phone(conversation, customer):
    data = conversation.get('data') if isinstance(conversation.get('data'), dict) else {}
    candidates = [
        data.get('Phone'),
        data.get('phone'),
        data.get('Mobile'),
        data.get('mobile'),
        customer.get('mobile') if isinstance(customer, dict) else '',
    ]
    for candidate in candidates:
        normalized = normalize_phone(candidate)
        if normalized:
            return normalized
    return ''


def _extract_conversation_email(conversation, customer):
    data = conversation.get('data') if isinstance(conversation.get('data'), dict) else {}
    candidates = [
        data.get('Email'),
        data.get('email'),
        customer.get('email') if isinstance(customer, dict) else '',
    ]
    identities = customer.get('identities') if isinstance(customer, dict) else []
    for identity in identities or []:
        if not isinstance(identity, dict):
            continue
        if identity.get('type') == 'email':
            candidates.append(identity.get('identifier'))

    for candidate in candidates:
        normalized = normalize_email(candidate)
        if normalized:
            return normalized
    return ''


def _extract_conversation_name(conversation, customer):
    data = conversation.get('data') if isinstance(conversation.get('data'), dict) else {}
    candidates = [
        data.get('Name (First, Last)'),
        data.get('name'),
        customer.get('friendly_name') if isinstance(customer, dict) else '',
        customer.get('name') if isinstance(customer, dict) else '',
        conversation.get('subject'),
    ]
    for candidate in candidates:
        if not candidate or not isinstance(candidate, str):
            continue
        cleaned = re.sub(r'\s+', ' ', candidate).strip()
        if cleaned and not cleaned.lower().startswith('guest user'):
            return cleaned
    return 'Website Lead'


def _extract_conversation_text(conversation, messages):
    last_message = conversation.get('last_message') if isinstance(conversation.get('last_message'), dict) else {}
    data = conversation.get('data') if isinstance(conversation.get('data'), dict) else {}
    conversation_message = conversation.get('message') if isinstance(conversation.get('message'), dict) else {}
    candidates = [
        last_message.get('body'),
        conversation_message.get('body'),
        data.get('How Can We Help You?'),
        data.get('Message'),
        data.get('Question'),
        conversation.get('display_subject'),
        conversation.get('subject'),
    ]
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        body = message.get('body')
        if body:
            candidates.append(body)
    for candidate in candidates:
        if candidate and isinstance(candidate, str):
            cleaned = re.sub(r'\s+', ' ', candidate).strip()
            if cleaned:
                return cleaned[:400]
    return ''


def _build_godaddy_sync_event(conversation, messages):
    customer = _extract_customer_identity(conversation)
    last_message = conversation.get('last_message') if isinstance(conversation.get('last_message'), dict) else {}
    conversation_id = conversation.get('id')
    message_id = last_message.get('id') or f"conversation-{conversation_id}"
    email = _extract_conversation_email(conversation, customer)
    phone = _extract_conversation_phone(conversation, customer)
    return {
        'type': 'conversation.sync',
        'event_id': f"godaddy-sync:{conversation_id}:{message_id}",
        'timestamp': last_message.get('created_at') or conversation.get('newest_message_timestamp') or conversation.get('updated_at') or utcnow_iso(),
        'name': _extract_conversation_name(conversation, customer),
        'email': email,
        'phone': phone,
        'initial_question': _extract_conversation_text(conversation, messages),
        'program_interest': '',
        'contact': {
            'id': customer.get('id') or conversation_id,
            'name': _extract_conversation_name(conversation, customer),
            'email': email,
            'phone': phone,
        },
        'conversation': {
            'id': conversation_id,
            'contact_id': customer.get('id') or conversation_id,
            'updated_at': conversation.get('newest_message_timestamp') or conversation.get('updated_at'),
            'subject': conversation.get('display_subject') or conversation.get('subject'),
            'status': conversation.get('status'),
            'read': conversation.get('read'),
        },
        'message': {
            'id': message_id,
            'text': _extract_conversation_text(conversation, messages),
            'created_at': last_message.get('created_at') or conversation.get('newest_message_timestamp') or conversation.get('updated_at'),
            'staff': bool(((last_message.get('user') or {}).get('staff?')) if isinstance(last_message, dict) else False),
        },
        'messages': messages or [],
        'raw_conversation': conversation,
    }


def _fetch_godaddy_live_payload(max_pages=None, page_size=None):
    script_path = Path(_base_dir) / 'scripts' / 'godaddy_live_sync.js'
    if not script_path.exists():
        raise FileNotFoundError(f"Missing live sync script: {script_path}")

    command = [
        'node',
        str(script_path),
        '--brand',
        Config.GODADDY_REAMAZE_BRAND_URL,
        '--pages',
        str(max_pages or Config.GODADDY_LIVE_SYNC_MAX_PAGES),
        '--page-size',
        str(page_size or Config.GODADDY_LIVE_SYNC_PAGE_SIZE),
        '--browser-url',
        Config.GODADDY_BROWSER_DEBUG_URL,
        '--user-data-dir',
        Config.GODADDY_BROWSER_USER_DATA_DIR,
        '--chrome',
        Config.GODADDY_CHROME_PATH,
    ]
    completed = subprocess.run(
        command,
        cwd=_base_dir,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    stdout = (completed.stdout or '').strip()
    stderr = (completed.stderr or '').strip()
    if completed.returncode != 0:
        details = stderr or stdout or f'Exit code {completed.returncode}'
        raise RuntimeError(f"GoDaddy live sync command failed: {details}")
    payload = json.loads(stdout or '{}')
    if not payload.get('success'):
        raise RuntimeError(payload.get('error') or 'GoDaddy live sync payload was unsuccessful')
    return payload


def sync_godaddy_live_conversations(max_pages=None, page_size=None):
    payload = _fetch_godaddy_live_payload(max_pages=max_pages, page_size=page_size)
    conversations = payload.get('conversations') or []
    message_map = payload.get('messages') or {}
    snapshots = []
    ingested = 0
    duplicates = 0

    for conversation in conversations:
        if not isinstance(conversation, dict):
            continue
        conversation_id = conversation.get('id')
        messages = message_map.get(str(conversation_id)) or []
        event = _build_godaddy_sync_event(conversation, messages)
        normalized = normalize_godaddy_event(event)
        result = process_inbound_lead_event(normalized, event)
        if result.get('duplicate'):
            duplicates += 1
        else:
            ingested += 1
        snapshots.append({
            'contact': event.get('contact'),
            'conversation': event.get('conversation'),
            'message': event.get('message'),
            'messages': messages,
            'name': event.get('name'),
            'email': event.get('email'),
            'phone': event.get('phone'),
            'initial_question': event.get('initial_question'),
        })

    return {
        'success': True,
        'source': LEAD_SOURCE['GODADDY_CHAT'],
        'checked_at': payload.get('fetched_at') or utcnow_iso(),
        'upstream_count': len(conversations),
        'ingested_count': ingested,
        'duplicate_count': duplicates,
        'snapshots': snapshots,
    }


def send_outlook_with_retries(to_email, subject, html_body, text_body=None):
    attempts = 3
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            get_graph_client().send_mail(sender_user_id=Config.OUTLOOK_SENDER_UPN, to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)
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

        # Auto-update lead status to REPLIED if this is a returning lead (duplicate event = they replied)
        if result.get('duplicate') and result.get('lead'):
            lead = result['lead']
            lead_email = normalize_email(lead.get('email'))
            lead_phone = normalize_phone(lead.get('phone'))
            if lead.get('status') in (LEAD_STATUS['PROGRAM_INFO_SENT'], LEAD_STATUS['DRAFT_CREATED'], LEAD_STATUS['INQUIRY_RECEIVED']):
                update_lead_status(email=lead_email, phone=lead_phone, new_status=LEAD_STATUS['REPLIED'], notes='Auto-detected reply via GoDaddy webhook')
                logger.info(f"[GoDaddy] Auto-marked lead {lead['id']} as REPLIED")

        return jsonify({'status': 'received', 'source': normalized['source'], 'source_event_id': normalized['source_event_id'], 'duplicate': result['duplicate'], 'lead_id': result['lead']['id'] if result['lead'] else None, 'draft_generated': result['draft_generated']}), 200
    except Exception as e:
        logger.error("GoDaddy webhook error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/dialpad', methods=['POST'])
@app.route('/api/dialpad/webhook', methods=['POST'])
@app.route('/api/webhooks/dialpad', methods=['POST'])
def dialpad_webhook():
    """Receive Dialpad events, normalize to lead events, dedupe, and auto-reply missed calls with SMS."""
    sms_sent = False
    sms_error = None
    try:
        raw_body = request.get_data()
        if not verify_dialpad_signature(raw_body):
            logger.warning("Dialpad webhook: invalid signature rejected")
            return jsonify({'error': 'Invalid signature'}), 401
        event = request.get_json(force=True) or {}
        normalized = normalize_dialpad_event(event)
        result = process_inbound_lead_event(normalized, event)

        # --- Missed Call SMS Auto-Reply ---
        call_obj = normalized.get('_call', {})
        is_missed = call_obj.get('missed') is True or call_obj.get('missed') == 'true'
        event_type = normalized.get('event_type', '')
        if is_missed and event_type == 'call.created' and not result.get('duplicate'):
            caller_phone = normalized.get('phone')
            if caller_phone and Config.DIALPAD_API_KEY:
                sms_message = (
                    "Hi, this is Trifecta Recovery Services. "
                    "We noticed your call and will follow up shortly. "
                    "You can reach us at (403) 907-0996."
                )
                try:
                    dialpad_client.send_sms(
                        to_number=caller_phone,
                        message=sms_message,
                        from_number='+14039070996'
                    )
                    sms_sent = True
                    logger.info(f"Missed call SMS sent to {caller_phone}")

                    # Log to sent-log.jsonl
                    if result.get('lead'):
                        _append_sent_log({
                            'ts': utcnow_iso(),
                            'type': 'sms',
                            'to': caller_phone,
                            'lead_id': result['lead']['id'],
                            'subject': 'Missed call auto-reply',
                            'channel': 'dialpad',
                            'status': 'sent',
                            'direction': 'outbound',
                            'trigger': 'missed_call_auto_reply',
                        })
                except Exception as sms_exc:
                    sms_error = str(sms_exc)
                    logger.warning(f"Missed call SMS failed for {caller_phone}: {sms_exc}")

        return jsonify({
            'status': 'received',
            'source': normalized['source'],
            'source_event_id': normalized['source_event_id'],
            'event_type': normalized['event_type'],
            'duplicate': result['duplicate'],
            'lead_id': result['lead']['id'] if result['lead'] else None,
            'draft_generated': result['draft_generated'],
            'sms_sent': sms_sent,
            'sms_error': sms_error,
        }), 200
    except Exception as e:
        logger.error(f"Dialpad webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/outlook-form', methods=['POST'])
def outlook_form_webhook():
    """Receive Microsoft Forms submissions and ingest to lead pipeline."""
    try:
        raw_body = request.get_data()
        if not verify_outlook_form_webhook(raw_body):
            logger.warning("Outlook Forms webhook: invalid token rejected")
            return jsonify({'error': 'Invalid webhook authentication'}), 401
        event = request.get_json(force=True) or {}
        normalized = normalize_outlook_form_event(event)
        result = process_inbound_lead_event(normalized, event)
        return jsonify({
            'status': 'received',
            'source': normalized['source'],
            'source_event_id': normalized['source_event_id'],
            'duplicate': result['duplicate'],
            'lead_id': result['lead']['id'] if result['lead'] else None,
            'draft_generated': result['draft_generated']
        }), 200
    except Exception as e:
        logger.error("Outlook Forms webhook error: %s", e)
        return jsonify({'error': str(e)}), 500


# =============================================================================
# API ENDPOINTS - Outbound Sent-Log (Real-Time Sheet Sync)
# =============================================================================

OUTBOUND_SENT_LOG = os.path.join(_base_dir, 'trifecta', 'outbound', 'sent-log.jsonl')
OUTBOUND_KPI_FILE = os.path.join(_base_dir, 'trifecta', 'kpi', 'live-kpis.json')


def _append_sent_log(entry: dict) -> bool:
    """Append a sent entry to the sent-log.jsonl file. Returns True on success."""
    try:
        os.makedirs(os.path.dirname(OUTBOUND_SENT_LOG), exist_ok=True)
        with open(OUTBOUND_SENT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')
        return True
    except Exception as e:
        logger.warning("Failed to append sent-log: %s", e)
        return False


def _read_sent_log() -> list:
    """Read all entries from sent-log.jsonl."""
    if not os.path.exists(OUTBOUND_SENT_LOG):
        return []
    try:
        with open(OUTBOUND_SENT_LOG, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        return [json.loads(line) for line in lines]
    except Exception as e:
        logger.warning("Failed to read sent-log: %s", e)
        return []


def _update_lead_sheets_row(lead_id: str, email: str = None, phone: str = None) -> bool:
    """Update a lead row in Google Sheets with outreach data from sent-log. Returns True on success."""
    try:
        creds_path = os.path.join(_base_dir, 'google-credentials.json')
        if not os.path.exists(creds_path):
            logger.warning("Google Sheets: google-credentials.json not found, skipping row update")
            return False

        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = os.environ.get('GOOGLE_SHEETS_ID', '1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0')
        sheet = client.open_by_key(sheet_id).sheet1

        # Find row matching lead email or phone
        norm_email = normalize_email(email) if email else None
        norm_phone = normalize_phone(phone) if phone else None
        search_value = norm_email or norm_phone
        if not search_value:
            return False

        try:
            cell = sheet.find(search_value)
        except Exception:
            return False

        row_num = cell.row

        # Get all sent entries for this lead
        sent_entries = [e for e in _read_sent_log() if e.get('lead_id') == lead_id]

        # Column I: Follow-up Sent (YES/NO)
        followup_sent = 'YES' if sent_entries else 'NO'

        # Column K: Last Outreach (date of most recent sent)
        last_outreach = ''
        if sent_entries:
            latest = max(sent_entries, key=lambda e: e.get('ts', ''))
            last_outreach = latest.get('ts', '')[:10]

        # Column L: Outreach Count
        outreach_count = len(sent_entries)

        # Update the row (I=9, K=11, L=12)
        sheet.update_cell(row_num, 9, followup_sent)
        sheet.update_cell(row_num, 11, last_outreach)
        sheet.update_cell(row_num, 12, outreach_count)

        logger.info("Sheet row updated for lead_id=%s: Follow-up=%s, Last=%s, Count=%d",
                    lead_id, followup_sent, last_outreach, outreach_count)
        return True

    except Exception as e:
        logger.warning("Sheets row update failed (non-fatal): %s", e)
        return False


@app.route('/api/outbound/log', methods=['POST'])
def log_outbound_sent():
    """
    Log an outbound message (email/SMS/call) to sent-log.jsonl and sync Sheet row.
    Body: {type, to, lead_id, subject, channel, status}
    """
    try:
        data = request.get_json(silent=True) or {}
        required = ['type', 'to', 'lead_id', 'channel']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing required fields: {missing}'}), 400

        entry = {
            'ts': utcnow_iso(),
            'type': data.get('type', 'email'),
            'to': data.get('to', ''),
            'lead_id': data.get('lead_id', ''),
            'subject': data.get('subject', ''),
            'channel': data.get('channel', 'unknown'),
            'status': data.get('status', 'sent'),
        }

        logged = _append_sent_log(entry)
        if not logged:
            return jsonify({'error': 'Failed to write sent-log'}), 500

        # Sync Sheet row for this lead
        email = data.get('to') if data.get('type') == 'email' else None
        phone = data.get('to') if data.get('type') in ('sms', 'call') else None
        sheet_updated = _update_lead_sheets_row(
            lead_id=entry['lead_id'],
            email=email,
            phone=phone
        )

        # Emit real-time event to dashboard
        msg_type = entry['type']
        channel = entry['channel']
        emit_to_dashboard(
            "outbound:sent",
            f"{msg_type.capitalize()} sent via {channel}: {entry.get('to', '')}",
            {"leadId": entry['lead_id'], "type": msg_type, "channel": channel, "to": entry.get('to')}
        )

        return jsonify({
            'ok': True,
            'entry': entry,
            'sheet_updated': sheet_updated,
            'timestamp': utcnow_iso()
        }), 201

    except Exception as e:
        logger.error("Outbound log error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/outbound/log', methods=['GET'])
def get_outbound_log():
    """Return all sent-log entries. Optional: ?lead_id=<id> to filter."""
    try:
        lead_id_filter = request.args.get('lead_id')
        entries = _read_sent_log()
        if lead_id_filter:
            entries = [e for e in entries if e.get('lead_id') == lead_id_filter]
        return jsonify({
            'count': len(entries),
            'entries': entries,
            'timestamp': utcnow_iso()
        }), 200
    except Exception as e:
        logger.error("Outbound log GET error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/outbound/summary', methods=['GET'])
def get_outbound_summary():
    """
    Return sent-log counts grouped by day, week, and month.
    Used for KPI dashboard.
    """
    try:
        entries = _read_sent_log()
        now = datetime.now(timezone.utc)

        today_date = now.date()
        week_start = (now - timedelta(days=now.weekday())).date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

        daily = {}
        for entry in entries:
            try:
                ts = datetime.fromisoformat(entry.get('ts', '').replace('Z', '+00:00'))
                d = ts.date()
                daily[d] = daily.get(d, 0) + 1
            except Exception:
                pass

        today_count = sum(v for k, v in daily.items() if k == today_date)
        week_count = sum(v for k, v in daily.items() if k >= week_start)
        month_count = sum(v for k, v in daily.items() if k >= month_start)
        total_count = len(entries)

        # Top channels
        channel_counts = {}
        for entry in entries:
            ch = entry.get('channel', 'unknown')
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        # Recent days (last 14)
        recent_days = []
        for i in range(13, -1, -1):
            d = (now - timedelta(days=i)).date()
            recent_days.append({'date': d.isoformat(), 'count': daily.get(d, 0)})

        return jsonify({
            'total': total_count,
            'today': today_count,
            'this_week': week_count,
            'this_month': month_count,
            'by_channel': channel_counts,
            'recent_days': recent_days,
            'timestamp': utcnow_iso()
        }), 200

    except Exception as e:
        logger.error("Outbound summary error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/kpi/update-from-sent-log', methods=['POST'])
def update_kpi_from_sent_log():
    """
    Read sent-log.jsonl, update live-kpis.json with emails_sent_today / emails_sent_week,
    and sync Sheet rows for all logged leads.
    """
    try:
        entries = _read_sent_log()
        now = datetime.now(timezone.utc)
        today_date = now.date()
        week_start = (now - timedelta(days=now.weekday())).date()

        today_count = 0
        week_count = 0
        seen_lead_ids = set()

        for entry in entries:
            try:
                ts = datetime.fromisoformat(entry.get('ts', '').replace('Z', '+00:00'))
                d = ts.date()
                if entry.get('type') == 'email':
                    if d == today_date:
                        today_count += 1
                    if d >= week_start:
                        week_count += 1
                seen_lead_ids.add(entry.get('lead_id'))
            except Exception:
                pass

        # Update live-kpis.json
        kpi_path = OUTBOUND_KPI_FILE
        kpi_data = {}
        if os.path.exists(kpi_path):
            try:
                with open(kpi_path, 'r', encoding='utf-8') as f:
                    kpi_data = json.load(f)
            except Exception:
                kpi_data = {}

        kpi_data['updated'] = utcnow_iso()
        kpi_data['emails_sent_today'] = today_count
        kpi_data['emails_sent_week'] = week_count

        os.makedirs(os.path.dirname(kpi_path), exist_ok=True)
        with open(kpi_path, 'w', encoding='utf-8') as f:
            json.dump(kpi_data, f, indent=2)

        # Emit real-time event to dashboard
        emit_to_dashboard(
            "metrics:updated",
            f"KPI updated: {today_count} emails sent today",
            {"emails_sent_today": today_count, "emails_sent_week": week_count, "kpi": kpi_data}
        )

        # Sync Sheet rows for all leads that appear in sent-log
        sheet_updated = 0
        for lead_id in seen_lead_ids:
            # Look up the lead to get email
            lead = lead_store.get_lead_by_id(lead_id)
            if lead:
                updated = _update_lead_sheets_row(
                    lead_id=lead_id,
                    email=lead.get('email'),
                    phone=lead.get('phone')
                )
                if updated:
                    sheet_updated += 1

        return jsonify({
            'ok': True,
            'kpi_updated': kpi_data,
            'sheet_rows_synced': sheet_updated,
            'leads_in_log': len(seen_lead_ids),
            'timestamp': utcnow_iso()
        }), 200

    except Exception as e:
        logger.error("KPI update from sent-log error: %s", e)
        return jsonify({'error': str(e)}), 500


# =============================================================================
# API ENDPOINTS - Portal Sync (Task 4)
# =============================================================================
@app.route('/api/portal-sync', methods=['GET', 'POST'])
@require_api_key
def portal_sync():
    """
    Sync portal data with Claude analysis.
    GET: Fetch high-risk clients â†' Claude analysis â†' return recommendations
    POST: Apply Claude recommendations â†' PATCH updates to Graph
    Uses: trifecta-ai-agent-orchestration
    """
    try:
        orchestration_skill = SKILLS.get('trifecta-ai-agent-orchestration', {})

        if request.method == 'GET':
            # Get filter params
            risk = request.args.get('risk', 'high')

            # Fetch clients from Graph
            users = get_graph_client().get_users()
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
                'timestamp': datetime.now(timezone.utc).isoformat()
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
                    result = get_graph_client().request('PATCH', f'/users/{client_id}', json=patch_data)
                    results.append({'client_id': client_id, 'status': 'updated'})
                except Exception as e:
                    results.append({'client_id': client_id, 'status': 'failed', 'error': str(e)})

            return jsonify({
                'updates_applied': len([r for r in results if r['status'] == 'updated']),
                'results': results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200

    except Exception as e:
        logger.error(f"Portal sync error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - Contract Generation (Task 4)
# =============================================================================
def _render_template(template_name, variables):
    """Render an HTML template with simple variable substitution."""
    tpl_path = Path(__file__).parent / "templates" / template_name
    html = tpl_path.read_text(encoding="utf-8")
    for key, value in variables.items():
        html = html.replace("{{" + key + "}}", str(value))
    return html


def _html_to_pdf(html: str) -> bytes:
    """Convert HTML string to PDF bytes using xhtml2pdf."""
    from xhtml2pdf import pisa
    buf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buf)
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed with {pisa_status.err} errors")
    return buf.getvalue()


PROGRAMS = {
    '28_DAY_VIRTUAL': {
        'name': '28-Day Virtual Boot Camp',
        'price': 3777,
        'description': '28 days of intensive virtual recovery coaching with daily DBT/CBT sessions, neuroplasticity exercises, and 24/7 support access.'
    },
    '14_DAY_INPATIENT': {
        'name': '14-Day Inpatient Program',
        'price': 13777,
        'description': '14-day immersive inpatient program with round-the-clock clinical support, group therapy, and personalized recovery planning.'
    },
    '28_DAY_INPATIENT': {
        'name': '28-Day Inpatient Program',
        'price': 23777,
        'description': '28-day comprehensive inpatient treatment with full clinical team, family sessions, aftercare planning, and neuroplasticity-based recovery.'
    }
}


@app.route('/api/contract/<client_id>', methods=['GET', 'POST'])
@require_api_key
def generate_contract(client_id):
    """Generate contract + invoice for a client, with PDF output."""
    try:
        if request.method == 'GET':
            try:
                client = get_graph_client().get_user(client_id)
            except Exception:
                client = {'displayName': 'Demo Client', 'mail': 'demo@example.com'}

            return jsonify({
                'client': {
                    'id': client_id,
                    'name': client.get('displayName'),
                    'email': client.get('mail')
                },
                'available_programs': [
                    {'name': p['name'], 'price': p['price'], 'code': code}
                    for code, p in PROGRAMS.items()
                ],
                'skill_used': 'trifecta-document-generator'
            }), 200

        data = request.get_json() or {}
        program_code = data.get('program', '28_DAY_VIRTUAL')
        program = PROGRAMS.get(program_code, PROGRAMS['28_DAY_VIRTUAL'])

        try:
            client = get_graph_client().get_user(client_id)
        except Exception:
            client = {'displayName': data.get('client_name', 'Client'), 'mail': data.get('email', '')}

        now = datetime.now(timezone.utc)
        contract_number = f"TRI-{now.strftime('%Y%m%d')}-{client_id[:6].upper()}"
        invoice_number = f"INV-{now.strftime('%Y%m%d')}-{client_id[:6].upper()}"

        # Render contract HTML from template
        contract_html = _render_template('contract_template.html', {
            'CLIENT_NAME': client.get('displayName', ''),
            'CLIENT_EMAIL': client.get('mail', ''),
            'DATE': now.strftime('%B %d, %Y'),
            'CONTRACT_NUMBER': contract_number,
            'PROGRAM_NAME': program['name'],
            'PROGRAM_PRICE': f"{program['price']:,}",
            'PROGRAM_DESCRIPTION': program['description'],
        })

        # Render invoice HTML from template
        line_items_html = f"""
        <tr>
            <td>
                <div class="line-item-title">{program['name']}</div>
                <div class="line-item-date">{now.strftime('%B %d, %Y')}</div>
            </td>
            <td>${program['price']:,}.00</td>
            <td>${program['price']:,}.00</td>
        </tr>"""

        invoice_html = _render_template('invoice_template_pdf.html', {
            'INVOICE_NUMBER': invoice_number,
            'CLIENT_NAME': client.get('displayName', ''),
            'SERVICE_TYPE': program['name'],
            'PAYMENT_METHOD': data.get('payment_method', 'E-Transfer'),
            'PROGRAM_SERVICE': program['name'],
            'STATUS_CLASS': 'status-outstanding',
            'STATUS': 'Outstanding',
            'SESSIONS_COVERED': 'Full Program',
            'LINE_ITEMS': line_items_html,
            'OUTSTANDING_BALANCE': f"{program['price']:,}.00",
            'SUMMARY_NOTE': f"Service agreement for {program['name']}. Full payment due upon receipt.",
            'PAYMENT_STATUS_TEXT': 'Outstanding - Payment due upon receipt',
            'CURRENT_YEAR': str(now.year),
        })

        # Generate PDFs
        contract_pdf = _html_to_pdf(contract_html)
        invoice_pdf = _html_to_pdf(invoice_html)

        # Upload to SharePoint
        sharepoint_urls = {}
        try:
            client_folder = client.get('displayName', 'Unknown').replace(' ', '_')
            for doc_type, content, ctype in [
                ('Contract', contract_pdf, 'application/pdf'),
                ('Invoice', invoice_pdf, 'application/pdf'),
            ]:
                filename = f"{doc_type}_{now.strftime('%Y%m%d')}_{program_code}.pdf"
                result = get_graph_client().upload_to_sharepoint(
                    folder_path=f"{client_folder}/Documents",
                    filename=filename,
                    content=content,
                    content_type=ctype
                )
                sharepoint_urls[doc_type.lower()] = result.get('webUrl')
        except Exception as e:
            logger.warning(f"SharePoint upload failed: {e}")

        # Create QuickBooks invoice (if configured)
        qb_invoice = None
        if Config.QUICKBOOKS_REALM_ID:
            try:
                qb_invoice = quickbooks_client.create_invoice(
                    customer_id=client_id,
                    line_items=[{
                        'Amount': program['price'],
                        'Description': program['name'],
                        'DetailType': 'SalesItemLineDetail',
                        'SalesItemLineDetail': {'Qty': 1, 'UnitPrice': program['price']}
                    }]
                )
            except Exception as e:
                logger.warning(f"QuickBooks invoice failed: {e}")

        import base64
        return jsonify({
            'status': 'generated',
            'client_id': client_id,
            'contract_number': contract_number,
            'invoice_number': invoice_number,
            'program': program,
            'contract_pdf_base64': base64.b64encode(contract_pdf).decode(),
            'invoice_pdf_base64': base64.b64encode(invoice_pdf).decode(),
            'sharepoint_urls': sharepoint_urls,
            'quickbooks_invoice': qb_invoice,
            'skills_used': ['trifecta-document-generator'],
            'timestamp': now.isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/invoice/pdf/<client_id>', methods=['POST'])
@require_api_key
def generate_invoice_pdf(client_id):
    """Generate just an invoice PDF and return it directly."""
    from flask import Response
    try:
        data = request.get_json() or {}
        program_code = data.get('program', '28_DAY_VIRTUAL')
        program = PROGRAMS.get(program_code, PROGRAMS['28_DAY_VIRTUAL'])
        now = datetime.now(timezone.utc)

        try:
            client = get_graph_client().get_user(client_id)
        except Exception:
            client = {'displayName': data.get('client_name', 'Client'), 'mail': data.get('email', '')}

        invoice_number = f"INV-{now.strftime('%Y%m%d')}-{client_id[:6].upper()}"
        line_items_html = f"""
        <tr>
            <td>
                <div class="line-item-title">{program['name']}</div>
                <div class="line-item-date">{now.strftime('%B %d, %Y')}</div>
            </td>
            <td>${program['price']:,}.00</td>
            <td>${program['price']:,}.00</td>
        </tr>"""

        invoice_html = _render_template('invoice_template_pdf.html', {
            'INVOICE_NUMBER': invoice_number,
            'CLIENT_NAME': client.get('displayName', ''),
            'SERVICE_TYPE': program['name'],
            'PAYMENT_METHOD': data.get('payment_method', 'E-Transfer'),
            'PROGRAM_SERVICE': program['name'],
            'STATUS_CLASS': 'status-outstanding',
            'STATUS': 'Outstanding',
            'SESSIONS_COVERED': 'Full Program',
            'LINE_ITEMS': line_items_html,
            'OUTSTANDING_BALANCE': f"{program['price']:,}.00",
            'SUMMARY_NOTE': f"Service agreement for {program['name']}. Full payment due upon receipt.",
            'PAYMENT_STATUS_TEXT': 'Outstanding - Payment due upon receipt',
            'CURRENT_YEAR': str(now.year),
        })

        pdf_bytes = _html_to_pdf(invoice_html)
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{invoice_number}.pdf"'}
        )
    except Exception as e:
        logger.error(f"Invoice PDF generation error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - QuickBooks OAuth
# =============================================================================
@app.route('/api/quickbooks/connect', methods=['GET'])
def quickbooks_connect():
    """Start QuickBooks OAuth2 flow — redirects to Intuit login."""
    if not all([Config.QUICKBOOKS_CLIENT_ID, Config.QUICKBOOKS_CLIENT_SECRET]):
        return jsonify({'error': 'QuickBooks credentials not configured',
                        'hint': 'Add QUICKBOOKS_CLIENT_ID and QUICKBOOKS_CLIENT_SECRET to env vars'}), 500
    try:
        from intuitlib.client import AuthClient
        from intuitlib.enums import Scopes
        auth_client = AuthClient(
            client_id=Config.QUICKBOOKS_CLIENT_ID,
            client_secret=Config.QUICKBOOKS_CLIENT_SECRET,
            redirect_uri=request.url_root.rstrip('/') + '/api/quickbooks/callback',
            environment='production'
        )
        auth_url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"QuickBooks OAuth start error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/quickbooks/callback', methods=['GET'])
def quickbooks_callback():
    """
    QuickBooks OAuth2 callback â€" run this ONCE during initial setup.
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

# Client/session/appointment records now persisted in SQLite via lead_store


def _parse_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


WORKFLOW_STAGE = {
    'AWAITING_HUMAN_RESPONSE': 'AWAITING_HUMAN_RESPONSE',
    'AWAITING_EMAIL': 'AWAITING_EMAIL',
    'PROGRAM_INFO_READY': 'PROGRAM_INFO_READY',
    'PROGRAM_INFO_SENT': 'PROGRAM_INFO_SENT',
    'REPLIED': 'REPLIED',
    'CONSULTATION_BOOKED': 'CONSULTATION_BOOKED',
    'ENROLLED': 'ENROLLED',
    'CLOSED': 'CLOSED',
    'NEEDS_REVIEW_ERROR': 'NEEDS_REVIEW_ERROR',
    'ARCHIVED_CLOSED': 'ARCHIVED_CLOSED',
}


def _extract_latest_message_preview(events):
    for event in events or []:
        payload = _parse_json_field(event.get('payload_json'), {})
        if not isinstance(payload, dict):
            continue
        last_message = payload.get('last_message') if isinstance(payload.get('last_message'), dict) else {}
        message = payload.get('message') if isinstance(payload.get('message'), dict) else {}
        conversation_data = payload.get('data') if isinstance(payload.get('data'), dict) else {}
        candidates = [
            message.get('text'),
            message.get('body'),
            last_message.get('body'),
            payload.get('text'),
            payload.get('initial_question'),
            conversation_data.get('How Can We Help You?'),
            payload.get('message') if isinstance(payload.get('message'), str) else None,
        ]
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                preview = re.sub(r'\s+', ' ', candidate).strip()
                return preview[:180]
    return ''


def _derive_lead_operational_state(lead, events=None, draft=None, outbound=None):
    events = events or []
    has_contact = bool(normalize_email(lead.get('email')) or normalize_phone(lead.get('phone')))
    latest_inbound = events[0] if events else None
    latest_message_preview = _extract_latest_message_preview(events)
    last_inbound_at = None
    if latest_inbound:
        last_inbound_at = latest_inbound.get('occurred_at') or latest_inbound.get('received_at')
    last_outbound_at = None
    outbound_status = None
    if outbound:
        last_outbound_at = outbound.get('sent_at') or outbound.get('created_at')
        outbound_status = outbound.get('status')

    status = lead.get('status')
    last_activity = parse_iso_datetime(last_inbound_at) or parse_iso_datetime(lead.get('updated_at'))
    hours_since_activity = None
    if last_activity:
        hours_since_activity = max(0.0, (datetime.now(timezone.utc) - last_activity).total_seconds() / 3600.0)

    needs_response = False
    if status == LEAD_STATUS['INQUIRY_RECEIVED']:
        needs_response = not has_contact or not draft
    elif status in {LEAD_STATUS['NEEDS_HUMAN_REVIEW'], LEAD_STATUS['ERROR']}:
        needs_response = True

    is_stale = bool(
        hours_since_activity is not None
        and hours_since_activity >= 48
        and status in {
            LEAD_STATUS['INQUIRY_RECEIVED'],
            LEAD_STATUS['DRAFT_CREATED'],
            LEAD_STATUS['NEEDS_HUMAN_REVIEW'],
            LEAD_STATUS['ERROR'],
        }
    )

    if status == LEAD_STATUS['ARCHIVED'] or status == LEAD_STATUS['CLOSED']:
        workflow_stage = WORKFLOW_STAGE['ARCHIVED_CLOSED']
    elif status == LEAD_STATUS['ENROLLED']:
        workflow_stage = WORKFLOW_STAGE['ENROLLED']
    elif status == LEAD_STATUS['CONSULTATION_BOOKED']:
        workflow_stage = WORKFLOW_STAGE['CONSULTATION_BOOKED']
    elif status == LEAD_STATUS['REPLIED']:
        workflow_stage = WORKFLOW_STAGE['REPLIED']
    elif status in {LEAD_STATUS['ERROR'], LEAD_STATUS['NEEDS_HUMAN_REVIEW']}:
        workflow_stage = WORKFLOW_STAGE['NEEDS_REVIEW_ERROR']
    elif status == LEAD_STATUS['PROGRAM_INFO_SENT'] or outbound_status == 'sent':
        workflow_stage = WORKFLOW_STAGE['PROGRAM_INFO_SENT']
    elif status == LEAD_STATUS['DRAFT_CREATED'] or (draft and draft.get('state') in {'drafted', 'approved'}):
        workflow_stage = WORKFLOW_STAGE['PROGRAM_INFO_READY']
    elif lead.get('source') == LEAD_SOURCE['GODADDY_CHAT'] and not has_contact:
        workflow_stage = WORKFLOW_STAGE['AWAITING_EMAIL']
    else:
        workflow_stage = WORKFLOW_STAGE['AWAITING_HUMAN_RESPONSE']

    return {
        'workflow_stage': workflow_stage,
        'needs_response': needs_response,
        'has_contact': has_contact,
        'last_inbound_at': last_inbound_at,
        'last_outbound_at': last_outbound_at,
        'latest_message_preview': latest_message_preview,
        'latest_outbound': outbound,
        'is_stale': is_stale,
        'hours_since_activity': round(hours_since_activity, 2) if hours_since_activity is not None else None,
    }


def _serialize_lead_with_context(lead, events, draft, outbound):
    if draft:
        draft = {
            **draft,
            'risk_flags': _parse_json_field(draft.get('risk_flags_json'), []),
            'citations_used': _parse_json_field(draft.get('citations_json'), []),
        }
    operational = _derive_lead_operational_state(lead, events=events, draft=draft, outbound=outbound)
    return {
        **lead,
        'recent_events': events,
        'latest_draft': draft,
        **operational,
        'is_missing_from_pipeline': False,
    }


def _serialize_lead(lead):
    if not lead:
        return None
    events = lead_store.latest_events_for_lead(lead['id'], limit=5)
    draft = lead_store.get_latest_draft(lead['id'])
    outbound = lead_store.get_latest_outbound_message(lead['id'])
    return _serialize_lead_with_context(lead, events, draft, outbound)


def _build_workflow_counts(leads):
    counts = {stage: 0 for stage in WORKFLOW_STAGE.values()}
    for lead in leads:
        counts[lead.get('workflow_stage')] = counts.get(lead.get('workflow_stage'), 0) + 1
    return counts


def _normalize_upstream_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        return None
    conversation = snapshot.get('conversation') if isinstance(snapshot.get('conversation'), dict) else snapshot
    contact = snapshot.get('contact') if isinstance(snapshot.get('contact'), dict) else {}
    message = snapshot.get('message') if isinstance(snapshot.get('message'), dict) else {}
    if not message and isinstance(snapshot.get('last_message'), dict):
        message = snapshot.get('last_message')
    contact_id = contact.get('id') or conversation.get('contact_id') or conversation.get('contactId')
    conversation_id = conversation.get('id') or snapshot.get('id') or snapshot.get('conversation_id')
    email = normalize_email(contact.get('email') or snapshot.get('email'))
    phone = normalize_phone(contact.get('phone') or snapshot.get('phone'))
    latest_at = (
        message.get('created_at')
        or snapshot.get('updated_at')
        or conversation.get('updated_at')
        or snapshot.get('timestamp')
        or utcnow_iso()
    )
    preview = message.get('text') or snapshot.get('text') or snapshot.get('initial_question') or ''
    return {
        'source': LEAD_SOURCE['GODADDY_CHAT'],
        'conversation_id': str(conversation_id) if conversation_id else '',
        'external_contact_key': f"godaddy:{contact_id}" if contact_id else '',
        'email': email,
        'phone': phone,
        'name': contact.get('name') or snapshot.get('name') or 'Website Lead',
        'latest_message_preview': re.sub(r'\s+', ' ', preview).strip()[:180],
        'last_activity_at': latest_at,
    }


def _reconcile_upstream_snapshots(upstream_snapshots, serialized_leads, stale_after_hours=48):
    leads_by_external = {}
    leads_by_email = {}
    leads_by_phone = {}
    for lead in serialized_leads:
        if lead.get('external_contact_key'):
            leads_by_external[lead['external_contact_key']] = lead
        if lead.get('email'):
            leads_by_email[normalize_email(lead['email'])] = lead
        if lead.get('phone'):
            leads_by_phone[normalize_phone(lead['phone'])] = lead

    missing = []
    mismatches = []
    for raw_snapshot in upstream_snapshots or []:
        snapshot = _normalize_upstream_snapshot(raw_snapshot)
        if not snapshot:
            continue
        match = None
        if snapshot['external_contact_key']:
            match = leads_by_external.get(snapshot['external_contact_key'])
        if not match and snapshot['email']:
            match = leads_by_email.get(snapshot['email'])
        if not match and snapshot['phone']:
            match = leads_by_phone.get(snapshot['phone'])

        if not match:
            missing.append({
                **snapshot,
                'is_missing_from_pipeline': True,
            })
            continue

        upstream_dt = parse_iso_datetime(snapshot['last_activity_at'])
        local_dt = parse_iso_datetime(match.get('last_inbound_at')) or parse_iso_datetime(match.get('updated_at'))
        if upstream_dt and local_dt and upstream_dt > local_dt:
            mismatches.append({
                'lead_id': match.get('id'),
                'name': match.get('name') or snapshot.get('name'),
                'source': match.get('source'),
                'upstream_last_activity_at': snapshot['last_activity_at'],
                'pipeline_last_activity_at': match.get('last_inbound_at') or match.get('updated_at'),
                'latest_message_preview': snapshot.get('latest_message_preview', ''),
            })

    stale_cutoff = (datetime.now(timezone.utc) - timedelta(hours=stale_after_hours)).replace(microsecond=0)
    stale = []
    for lead in serialized_leads:
        if lead.get('is_stale'):
            stale.append({
                'lead_id': lead.get('id'),
                'name': lead.get('name'),
                'source': lead.get('source'),
                'workflow_stage': lead.get('workflow_stage'),
                'hours_since_activity': lead.get('hours_since_activity'),
                'latest_message_preview': lead.get('latest_message_preview'),
                'updated_at': lead.get('updated_at'),
            })

    return {
        'checked_at': utcnow_iso(),
        'stale_after_hours': stale_after_hours,
        'upstream_count': len(upstream_snapshots or []),
        'missing_count': len(missing),
        'stale_count': len(stale),
        'mismatch_count': len(mismatches),
        'missing_leads': missing,
        'stale_leads': stale,
        'activity_mismatches': mismatches,
        'stale_cutoff': stale_cutoff.isoformat().replace('+00:00', 'Z'),
    }


@app.route('/api/leads/update-status', methods=['POST'])
def lead_update_status():
    """Update lead status when they reply to email or chat."""
    data = request.get_json() or {}
    email = data.get('email')
    phone = data.get('phone')
    new_status = data.get('status', 'REPLIED')
    notes = data.get('notes', '')

    if not email and not phone:
        return jsonify({'error': 'email or phone required'}), 400

    valid_statuses = set(LEAD_STATUS.values())
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Valid: {sorted(valid_statuses)}'}), 400

    success = update_lead_status(email=email, phone=phone, new_status=new_status, notes=notes)

    if success:
        emit_to_dashboard("lead:updated", f"Lead status updated to {new_status}", {"email": email, "status": new_status})
        return jsonify({'ok': True, 'status': new_status}), 200
    else:
        return jsonify({'error': 'Lead not found'}), 404


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
        lead = result['lead']
        if not result['duplicate']:
            emit_to_dashboard(
                "lead:new",
                f"New lead captured: {lead.get('name') or lead.get('email') or 'Unknown'} from {lead.get('source', 'Unknown')}",
                {"leadId": lead['id'], "name": lead.get('name'), "source": lead.get('source'), "email": lead.get('email')}
            )
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
        serialized = [_serialize_lead(l) for l in leads]
        return jsonify({
            'count': len(leads),
            'leads': serialized,
            'workflow_counts': _build_workflow_counts(serialized),
            'needs_response_count': sum(1 for lead in serialized if lead.get('needs_response')),
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error("Lead query error: %s", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/leads/board', methods=['GET'])
def lead_board():
    """Return a board-oriented view of the live lead pipeline."""
    try:
        source = request.args.get('source') or None
        limit = min(max(int(request.args.get('limit', 100)), 1), 200)
        offset = max(int(request.args.get('offset', 0)), 0)
        stale_after_hours = min(max(int(request.args.get('stale_after_hours', 48)), 1), 168)
        sync_live = request.args.get('sync_live', '1').lower() not in {'0', 'false', 'no'}
        sync_summary = None
        upstream_snapshots = []
        if sync_live and Config.GODADDY_LIVE_SYNC_ENABLED and (not source or source == LEAD_SOURCE['GODADDY_CHAT']):
            try:
                sync_summary = sync_godaddy_live_conversations()
                upstream_snapshots = sync_summary.get('snapshots') or []
            except Exception as exc:
                logger.warning("GoDaddy live sync skipped: %s", exc)
                sync_summary = {
                    'success': False,
                    'source': LEAD_SOURCE['GODADDY_CHAT'],
                    'checked_at': utcnow_iso(),
                    'error': str(exc),
                    'upstream_count': 0,
                    'ingested_count': 0,
                    'duplicate_count': 0,
                }
        leads = lead_store.list_leads(source=source, limit=limit, offset=offset)
        serialized = [_serialize_lead(lead) for lead in leads]
        reconciliation = _reconcile_upstream_snapshots(upstream_snapshots, serialized, stale_after_hours=stale_after_hours)
        return jsonify({
            'count': len(serialized),
            'leads': serialized,
            'workflow_counts': _build_workflow_counts(serialized),
            'needs_response_count': sum(1 for lead in serialized if lead.get('needs_response')),
            'reconciliation': reconciliation,
            'live_sync': sync_summary,
            'timestamp': utcnow_iso(),
            'limit': limit,
            'offset': offset,
        }), 200
    except Exception as exc:
        logger.error("Lead board error: %s", exc)
        return jsonify({'error': str(exc), 'code': 'lead_board_failed'}), 500


@app.route('/api/leads/reconcile', methods=['POST'])
def reconcile_leads():
    """Compare upstream GoDaddy/OpenClaw snapshots with the live pipeline."""
    try:
        data = request.get_json(silent=True) or {}
        snapshots = data.get('upstream_conversations') or data.get('snapshots') or []
        source = data.get('source')
        stale_after_hours = min(max(int(data.get('stale_after_hours', 48)), 1), 168)
        leads = lead_store.list_leads(source=source, limit=200, offset=0)
        serialized = [_serialize_lead(lead) for lead in leads]
        reconciliation = _reconcile_upstream_snapshots(snapshots, serialized, stale_after_hours=stale_after_hours)
        return jsonify({
            'success': True,
            'source': source or 'ALL',
            'reconciliation': reconciliation,
        }), 200
    except Exception as exc:
        logger.error("Lead reconciliation error: %s", exc)
        return jsonify({'error': str(exc), 'code': 'lead_reconciliation_failed'}), 500


@app.route('/api/leads/sync/godaddy-live', methods=['POST', 'GET'])
def sync_godaddy_live():
    """Pull live GoDaddy conversations from the local browser session into the lead pipeline."""
    try:
        data = request.get_json(silent=True) or {}
        max_pages = min(max(int(data.get('max_pages', request.args.get('max_pages', Config.GODADDY_LIVE_SYNC_MAX_PAGES))), 1), 5)
        page_size = min(max(int(data.get('page_size', request.args.get('page_size', Config.GODADDY_LIVE_SYNC_PAGE_SIZE))), 1), 100)
        summary = sync_godaddy_live_conversations(max_pages=max_pages, page_size=page_size)
        return jsonify({'success': True, 'sync': summary}), 200
    except Exception as exc:
        logger.error("GoDaddy live sync error: %s", exc)
        return jsonify({'success': False, 'error': str(exc), 'code': 'godaddy_live_sync_failed'}), 500


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

        # Also append to sent-log for real-time Sheet sync
        _append_sent_log({
            'ts': utcnow_iso(),
            'type': 'email',
            'to': lead.get('email', ''),
            'lead_id': lead_id,
            'subject': draft.get('subject', ''),
            'channel': 'outlook',
            'status': 'sent'
        })

        # Emit real-time event to dashboard
        emit_to_dashboard(
            "outbound:sent",
            f"Email approved and sent to {lead.get('email', '')}",
            {"leadId": lead_id, "type": "email", "channel": "outlook", "to": lead.get('email')}
        )

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
        return jsonify({'error': str(exc), 'code': 'lead_metrics_failed'}), 500


@app.route('/api/leads/<lead_id>', methods=['PATCH'])
@require_api_key
def update_lead_admin(lead_id):
    """Manually update lead status and core lead info."""
    try:
        lead = lead_store.get_lead_by_id(lead_id)
        if not lead:
            return jsonify({'error': 'Lead not found', 'code': 'lead_not_found'}), 404

        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not data:
            return jsonify({'error': 'No data provided', 'code': 'missing_payload'}), 400

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
                    'code': 'invalid_transition',
                    'current_status': before.get('status'),
                    'requested_status': requested_status
                }), 400
            if status_err == 'not_found':
                return jsonify({'error': 'Lead not found', 'code': 'lead_not_found'}), 404
            lead = lead_after_status

        lead_store.add_audit(actor, 'lead_admin_updated', 'lead', lead_id, before, lead)
        return jsonify({'status': 'updated', 'lead': _serialize_lead(lead)}), 200
    except Exception as exc:
        logger.error("Lead admin patch error: %s", exc)
        return jsonify({'error': str(exc), 'code': 'lead_update_failed'}), 500


@app.route('/api/leads/<lead_id>/audit', methods=['GET'])
@require_api_key
def get_lead_audit(lead_id):
    """Fetch audit trail for a lead and related draft/message records."""
    try:
        lead = lead_store.get_lead_by_id(lead_id)
        if not lead:
            return jsonify({'error': 'Lead not found', 'code': 'lead_not_found'}), 404

        try:
            limit = min(max(int(request.args.get('limit', 100)), 1), 500)
            offset = max(int(request.args.get('offset', 0)), 0)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid pagination parameters', 'code': 'invalid_pagination'}), 400

        rows = lead_store.list_audit_for_lead(lead_id, limit=limit, offset=offset)
        return jsonify({
            'lead_id': lead_id,
            'count': len(rows),
            'limit': limit,
            'offset': offset,
            'audit': rows
        }), 200
    except Exception as exc:
        logger.error("Lead audit fetch error: %s", exc)
        return jsonify({'error': str(exc), 'code': 'lead_audit_failed'}), 500


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


# ── Email Drafts ─────────────────────────────────────────────────────
@app.route('/api/email-drafts', methods=['GET'])
def get_email_drafts():
    try:
        state = request.args.get('state')
        conn = lead_store._connect()
        if state:
            rows = conn.execute("SELECT d.*, l.name as lead_name, l.email as lead_email FROM email_drafts d LEFT JOIN leads l ON d.lead_id = l.id WHERE d.state = ? ORDER BY d.created_at DESC", (state,)).fetchall()
        else:
            rows = conn.execute("SELECT d.*, l.name as lead_name, l.email as lead_email FROM email_drafts d LEFT JOIN leads l ON d.lead_id = l.id ORDER BY d.created_at DESC").fetchall()
        drafts = [dict(r) for r in rows]
        total = conn.execute("SELECT COUNT(*) FROM email_drafts").fetchone()[0]
        drafted = conn.execute("SELECT COUNT(*) FROM email_drafts WHERE state='drafted'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM email_drafts WHERE state='approved'").fetchone()[0]
        sent = conn.execute("SELECT COUNT(*) FROM email_drafts WHERE state='sent'").fetchone()[0]
        conn.close()
        return jsonify({"success": True, "drafts": drafts, "counts": {"total": total, "drafted": drafted, "approved": approved, "sent": sent}})
    except Exception as e:
        logger.error(f"Error fetching email drafts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/email-drafts/<draft_id>', methods=['PATCH'])
def update_email_draft(draft_id):
    try:
        data = request.json
        conn = lead_store._connect()
        allowed = ['state', 'subject', 'text', 'html', 'approved_by', 'approved_at', 'rejected_by', 'rejected_reason']
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            conn.close()
            return jsonify({"error": "No valid fields"}), 400
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE email_drafts SET {set_clause} WHERE id = ?", list(updates.values()) + [draft_id])
        conn.commit()
        draft = dict(conn.execute("SELECT * FROM email_drafts WHERE id = ?", (draft_id,)).fetchone())
        conn.close()
        return jsonify({"success": True, "draft": draft})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# APPROVAL QUEUE ENDPOINTS
# =============================================================================

@app.route('/api/approvals', methods=['GET'])
def list_approvals():
    """List approval items, optionally filtered by status."""
    try:
        status_filter = request.args.get('status')
        conn = lead_store._connect()
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM approvals WHERE status = ? ORDER BY priority DESC, created_at ASC",
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approvals ORDER BY priority DESC, created_at ASC"
            ).fetchall()
        items = [dict(r) for r in rows]
        counts = {}
        for s in ['pending', 'approved', 'rejected', 'sent']:
            counts[s] = conn.execute("SELECT COUNT(*) FROM approvals WHERE status = ?", (s,)).fetchone()[0]
        conn.close()
        return jsonify({"success": True, "items": items, "counts": counts})
    except Exception as e:
        logger.error(f"Error listing approvals: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/approvals/<approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    """One-tap approve a content or email item."""
    try:
        body = request.get_json(silent=True) or {}
        actor = body.get('approved_by', 'founder')
        now = utcnow_iso()
        conn = lead_store._connect()
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Approval not found"}), 404
        conn.execute(
            "UPDATE approvals SET status = 'approved', updated_at = ? WHERE id = ?",
            (now, approval_id)
        )
        conn.commit()
        updated = dict(conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone())
        conn.close()
        emit_to_dashboard("approval:approved", f"Approved: {updated.get('title', '')}", {"id": approval_id})
        logger.info(f"[Approval] Approved by {actor}: {updated.get('title')}")
        return jsonify({"success": True, "item": updated})
    except Exception as e:
        logger.error(f"Error approving {approval_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/approvals/<approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    """One-tap reject a content or email item."""
    try:
        body = request.get_json(silent=True) or {}
        actor = body.get('rejected_by', 'founder')
        now = utcnow_iso()
        conn = lead_store._connect()
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Approval not found"}), 404
        conn.execute(
            "UPDATE approvals SET status = 'rejected', updated_at = ? WHERE id = ?",
            (now, approval_id)
        )
        conn.commit()
        updated = dict(conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone())
        conn.close()
        emit_to_dashboard("approval:rejected", f"Rejected: {updated.get('title', '')}", {"id": approval_id})
        logger.info(f"[Approval] Rejected by {actor}: {updated.get('title')}")
        return jsonify({"success": True, "item": updated})
    except Exception as e:
        logger.error(f"Error rejecting {approval_id}: {e}")
        return jsonify({"error": str(e)}), 500


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
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        lead_store.upsert_client(client)

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
    client = lead_store.get_client(client_id)
    if not client:
        # Try Graph API as fallback
        try:
            get_graph_client().get_user(client_id)
            return jsonify({'id': client_id, 'source': 'graph'}), 200
        except Exception:
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
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        lead_store.insert_session(session)

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
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        lead_store.insert_appointment(appointment)

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
    active_clients = lead_store.count_clients()
    sessions_total = lead_store.count_sessions()
    upcoming_count = lead_store.count_appointments()

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
            'in_intake': lead_store.count_clients(status='intake')
        },
        'sessions': {
            'completed_this_week': sessions_total,
            'upcoming': upcoming_count
        },
        'status': 'operational',
        'timestamp': datetime.now(timezone.utc).isoformat()
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
    return jsonify({'error': 'Endpoint not found', 'timestamp': datetime.now(timezone.utc).isoformat()}), 404

@app.errorhandler(500)
def server_error(error):
    err_id = str(uuid.uuid4())
    logger.exception('Internal server error [%s]: %s', err_id, error)
    return jsonify({'error': 'Internal server error', 'id': err_id, 'timestamp': datetime.now(timezone.utc).isoformat()}), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # Let HTTPExceptions bubble through
    if isinstance(error, HTTPException):
        return error
    err_id = str(uuid.uuid4())
    logger.exception('Unhandled exception [%s]: %s', err_id, error)
    return jsonify({'error': 'Internal server error', 'id': err_id}), 500

# =============================================================================
# SCHEDULED TASKS (APScheduler)
# =============================================================================
def _init_scheduler():
    """Initialize APScheduler for recurring background tasks."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("APScheduler not installed, scheduled tasks disabled")
        return None

    scheduler = BackgroundScheduler(daemon=True)

    # --- Daily Lead Summary (8 AM UTC / 1 AM MST) ---
    def daily_lead_summary():
        """Send a daily summary of lead pipeline activity."""
        with app.app_context():
            try:
                metrics = lead_store.status_metrics()
                new_count = sum(v for v in metrics.values())  # total active
                pending_count = metrics.get('INQUIRY_RECEIVED', 0) + metrics.get('DRAFT_CREATED', 0) + metrics.get('NEEDS_HUMAN_REVIEW', 0)
                drafts_pending = metrics.get('DRAFT_CREATED', 0)
                active_count = sum(v for k, v in metrics.items() if k != 'ARCHIVED')

                summary = (
                    f"Daily Lead Summary:\n"
                    f"- New leads (24h): {new_count}\n"
                    f"- Awaiting action: {pending_count}\n"
                    f"- Drafts pending approval: {drafts_pending}\n"
                    f"- Total active leads: {active_count}"
                )
                logger.info(f"[CRON] {summary}")

                # Send via Telegram if configured
                telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                telegram_chat = os.environ.get('TELEGRAM_CHAT_ID')
                if telegram_token and telegram_chat:
                    requests.post(
                        f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                        json={'chat_id': telegram_chat, 'text': summary},
                        timeout=10
                    )

            except Exception as e:
                logger.error(f"[CRON] Daily lead summary failed: {e}")

    # --- Follow-up Reminder (every 4 hours) ---
    def check_stale_leads():
        """Flag leads that haven't been actioned in 48+ hours."""
        with app.app_context():
            try:
                stale = lead_store.list_leads(status='INQUIRY_RECEIVED', limit=50)
                stale += lead_store.list_leads(status='DRAFT_CREATED', limit=50)
                # Filter to those older than 2 days
                cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
                stale = [l for l in stale if l.get('updated_at', '') < cutoff]

                if stale:
                    logger.warning(f"[CRON] {len(stale)} stale leads need follow-up")
                    for lead in stale:
                        logger.warning(f"[CRON] Stale lead: {lead['id']} ({lead['status']}) - last updated {lead.get('updated_at')}")
            except Exception as e:
                logger.error(f"[CRON] Stale lead check failed: {e}")

    # --- Auto-draft for un-drafted leads (every 30 min) ---
    def auto_draft_undrafted():
        """Generate drafts for leads that don't have one yet."""
        if os.environ.get('LEAD_AUTO_DRAFT_ON_INGEST', '').lower() != 'true':
            return
        with app.app_context():
            try:
                leads = lead_store.list_leads(status='INQUIRY_RECEIVED', limit=10)
                for lead in leads:
                    if not lead.get('email'):
                        continue
                    existing_draft = lead_store.get_latest_draft(lead['id'])
                    if existing_draft:
                        continue
                    try:
                        maybe_generate_draft(lead)
                        logger.info(f"[CRON] Auto-drafted email for lead {lead['id']}")
                    except Exception as e:
                        logger.warning(f"[CRON] Auto-draft failed for lead {lead['id']}: {e}")
            except Exception as e:
                logger.error(f"[CRON] Auto-draft check failed: {e}")

    # --- Compute KPIs from real database data (every 5 min) ---
    def compute_kpis_from_db():
        """Compute live KPIs from actual database tables and write to live-kpis.json."""
        with app.app_context():
            try:
                metrics = lead_store.status_metrics()
                total_leads = metrics.get('total_leads', 0)
                conversion_rate = metrics.get('conversion_rate', 0.0)

                # Count today's leads
                today_start = datetime.now(timezone.utc).strftime('%Y-%m-%dT00:00:00')
                with lead_store._connect() as conn:
                    leads_today = lead_store._fetchone(
                        conn,
                        "SELECT COUNT(*) AS count FROM leads WHERE created_at >= ?",
                        (today_start,)
                    )['count']

                    # Count emails sent today and this week
                    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                    emails_sent_today = lead_store._fetchone(
                        conn,
                        "SELECT COUNT(*) AS count FROM outbound_messages WHERE status='sent' AND sent_at >= ?",
                        (today_start,)
                    )['count']
                    emails_sent_week = lead_store._fetchone(
                        conn,
                        "SELECT COUNT(*) AS count FROM outbound_messages WHERE status='sent' AND sent_at >= ?",
                        (week_start,)
                    )['count']

                    # Count content approved/sent (from approvals table if it exists)
                    content_today = 0
                    content_week = 0
                    try:
                        content_today = lead_store._fetchone(
                            conn,
                            "SELECT COUNT(*) AS count FROM approvals WHERE status IN ('approved','sent') AND updated_at >= ?",
                            (today_start,)
                        )['count']
                        content_week = lead_store._fetchone(
                            conn,
                            "SELECT COUNT(*) AS count FROM approvals WHERE status IN ('approved','sent') AND updated_at >= ?",
                            (week_start,)
                        )['count']
                    except Exception:
                        pass  # approvals table may not exist yet

                active_clients = lead_store.count_clients()

                kpis = {
                    "leads_today": leads_today,
                    "leads_total": total_leads,
                    "emails_sent_today": emails_sent_today,
                    "emails_sent_week": emails_sent_week,
                    "content_posted_today": content_today,
                    "content_posted_week": content_week,
                    "active_clients": active_clients,
                    "conversion_rate": conversion_rate,
                }
                _save_kpis(kpis)
                logger.info(f"[CRON] KPIs computed: leads_today={leads_today}, emails_sent_today={emails_sent_today}, active_clients={active_clients}")
            except Exception as e:
                logger.error(f"[CRON] KPI computation failed: {e}")

    # --- Poll info@ inbox and notify Discord (every 2 min) ---
    _last_seen_email_id_file = os.path.join(os.path.dirname(__file__), '.logs', 'last_inbox_id.txt')

    def poll_inbox_and_notify():
        """Check info@ inbox for new unread emails and send Discord notifications."""
        with app.app_context():
            try:
                webhook = os.environ.get('DISCORD_WEBHOOK_URL', '')
                if not webhook:
                    return  # Discord not configured, skip

                user_id = Config.OUTLOOK_SENDER_UPN
                if not user_id:
                    return

                client = get_graph_client()
                result = client.get_inbox_messages(user_id, top=5, unread_only=True)
                messages = result.get('value', [])

                if not messages:
                    return

                # Track last seen to avoid duplicate notifications
                last_seen = ''
                try:
                    with open(_last_seen_email_id_file, 'r') as f:
                        last_seen = f.read().strip()
                except FileNotFoundError:
                    pass

                new_messages = []
                for msg in messages:
                    if msg['id'] == last_seen:
                        break
                    new_messages.append(msg)

                if not new_messages:
                    return

                # Save newest ID
                os.makedirs(os.path.dirname(_last_seen_email_id_file), exist_ok=True)
                with open(_last_seen_email_id_file, 'w') as f:
                    f.write(new_messages[0]['id'])

                for msg in new_messages[:3]:  # Max 3 notifications per poll
                    sender = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    subject = msg.get('subject', '(no subject)')
                    preview = (msg.get('bodyPreview', '') or '')[:200]
                    notification = f"**New Email** from `{sender}`\n**Subject:** {subject}\n> {preview}"
                    send_discord_notification(notification)

                logger.info(f"[CRON] Notified Discord of {len(new_messages)} new emails")

            except Exception as e:
                logger.error(f"[CRON] Inbox poll failed: {e}")

    scheduler.add_job(daily_lead_summary, 'cron', hour=8, minute=0, id='daily_lead_summary')
    scheduler.add_job(check_stale_leads, 'interval', hours=4, id='check_stale_leads')
    scheduler.add_job(auto_draft_undrafted, 'interval', minutes=30, id='auto_draft_undrafted')
    scheduler.add_job(compute_kpis_from_db, 'interval', minutes=5, id='compute_kpis')
    scheduler.add_job(poll_inbox_and_notify, 'interval', minutes=2, id='poll_inbox_discord')

    scheduler.start()
    logger.info("[CRON] Scheduler started with 5 jobs: daily_lead_summary, check_stale_leads, auto_draft_undrafted, compute_kpis, poll_inbox_discord")

    # Compute KPIs immediately on startup
    try:
        compute_kpis_from_db()
    except Exception as e:
        logger.warning(f"[CRON] Initial KPI computation failed (will retry): {e}")
    return scheduler


@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """Show status of scheduled tasks."""
    if not hasattr(app, '_scheduler') or app._scheduler is None:
        return jsonify({'status': 'disabled', 'jobs': []}), 200
    jobs = []
    for job in app._scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
        })
    return jsonify({'status': 'running', 'jobs': jobs}), 200


# =============================================================================
# PORTAL AUTH + CLIENT/ADMIN API ENDPOINTS
# =============================================================================

def _create_portal_token(user):
    """Create a JWT token for a portal user."""
    if not PYJWT_AVAILABLE:
        # Fallback: simple HMAC token
        payload = json.dumps({'user_id': user['id'], 'role': user['role'], 'exp': (datetime.now(timezone.utc) + timedelta(hours=Config.PORTAL_JWT_EXPIRY_HOURS)).isoformat()})
        sig = hmac.new(Config.PORTAL_JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{hashlib.sha256(payload.encode()).hexdigest()}.{sig}"
    return pyjwt.encode(
        {'user_id': user['id'], 'email': user['email'], 'role': user['role'], 'name': user['name'],
         'exp': datetime.now(timezone.utc) + timedelta(hours=Config.PORTAL_JWT_EXPIRY_HOURS)},
        Config.PORTAL_JWT_SECRET, algorithm='HS256'
    )


def _verify_portal_token(token):
    """Verify a portal JWT token, return payload or None."""
    if not PYJWT_AVAILABLE:
        return None
    try:
        return pyjwt.decode(token, Config.PORTAL_JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None


def require_portal_auth(f):
    """Decorator: require valid portal JWT in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header[7:]
        payload = _verify_portal_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        g.portal_user = payload
        return f(*args, **kwargs)
    return decorated


def require_admin_auth(f):
    """Decorator: require valid portal JWT with admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header[7:]
        payload = _verify_portal_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        g.portal_user = payload
        return f(*args, **kwargs)
    return decorated


# --- Auth Endpoints ---

@app.route('/api/auth/login', methods=['POST'])
def portal_login():
    """Authenticate portal user and return JWT token."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    user = lead_store.get_portal_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = _create_portal_token(user)
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'email': user['email'], 'name': user['name'], 'role': user['role']},
    }), 200


@app.route('/api/auth/me', methods=['GET'])
@require_portal_auth
def portal_me():
    """Return current authenticated user info."""
    return jsonify({'user': g.portal_user}), 200


@app.route('/api/auth/register', methods=['POST'])
@require_admin_auth
def portal_register():
    """Admin-only: create a new portal user account."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name = data.get('name') or ''
    role = data.get('role', 'client')
    client_id = data.get('client_id')
    if not email or not password or not name:
        return jsonify({'error': 'Email, password, and name are required'}), 400
    if role not in ('client', 'admin'):
        return jsonify({'error': 'Role must be client or admin'}), 400
    existing = lead_store.get_portal_user_by_email(email)
    if existing:
        return jsonify({'error': 'User with this email already exists'}), 409
    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    user = lead_store.create_portal_user(user_id, email, password_hash, name, role, client_id)
    return jsonify({'user': {'id': user['id'], 'email': user['email'], 'name': user['name'], 'role': user['role']}}), 201


@app.route('/api/auth/setup', methods=['POST'])
def portal_setup():
    """One-time setup: create the initial admin account. Only works if no users exist."""
    users = lead_store.list_portal_users()
    if users:
        return jsonify({'error': 'Setup already completed. Use /api/auth/login'}), 400
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name = data.get('name') or 'Admin'
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    user = lead_store.create_portal_user(user_id, email, password_hash, name, 'admin')
    token = _create_portal_token(user)
    return jsonify({
        'message': 'Admin account created',
        'token': token,
        'user': {'id': user['id'], 'email': user['email'], 'name': user['name'], 'role': user['role']},
    }), 201


# --- Client Portal Endpoints ---

@app.route('/api/client/dashboard', methods=['GET'])
@require_portal_auth
def client_dashboard():
    """Client dashboard overview."""
    user = g.portal_user
    client_id = user.get('user_id')
    client = lead_store.get_client(client_id) if client_id else None
    sessions = lead_store.list_sessions(client_id=client_id) if client_id else []
    appointments = lead_store.list_appointments(client_id=client_id) if client_id else []
    return jsonify({
        'program': (client or {}).get('program_type', 'Virtual Boot Camp'),
        'client_name': user.get('name', 'Client'),
        'sessions_completed': len(sessions),
        'sessions_total': 28,
        'upcoming_appointments': len([a for a in appointments if a.get('status') == 'scheduled']),
        'documents_count': 0,
        'payment_status': 'current',
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/client/sessions', methods=['GET'])
@require_portal_auth
def client_sessions():
    """Client sessions list."""
    user = g.portal_user
    client_id = user.get('user_id')
    sessions = lead_store.list_sessions(client_id=client_id) if client_id else lead_store.list_sessions()
    result = []
    for s in sessions:
        result.append({
            'id': s.get('id'),
            'date': s.get('date'),
            'duration': s.get('duration', 60),
            'topics': json.loads(s.get('topics', '[]')) if isinstance(s.get('topics'), str) else s.get('topics', []),
            'mood_rating': s.get('mood_rating'),
            'progress_notes': s.get('progress_notes'),
            'status': 'completed',
        })
    return jsonify(result), 200


@app.route('/api/client/documents', methods=['GET'])
@require_portal_auth
def client_documents():
    """Client documents list. Currently returns empty — wire to SharePoint or Azure Blob."""
    return jsonify([]), 200


@app.route('/api/client/documents', methods=['POST'])
@require_portal_auth
def client_upload_document():
    """Client document upload placeholder."""
    return jsonify({'message': 'Document upload coming soon', 'success': True}), 200


@app.route('/api/client/payments', methods=['GET'])
@require_portal_auth
def client_payments():
    """Client payment history. Wire to QuickBooks for real data."""
    return jsonify({
        'payments': [],
        'quickbooks_configured': bool(Config.QUICKBOOKS_REALM_ID),
        'message': 'Connect QuickBooks for live payment data' if not Config.QUICKBOOKS_REALM_ID else None,
    }), 200


@app.route('/api/client/profile', methods=['GET'])
@require_portal_auth
def client_profile():
    """Get client profile."""
    user = g.portal_user
    client = lead_store.get_client(user.get('user_id'))
    return jsonify({
        'id': user.get('user_id'),
        'name': user.get('name'),
        'email': user.get('email'),
        'phone': (client or {}).get('phone', ''),
        'program_type': (client or {}).get('program_type', ''),
        'status': (client or {}).get('status', 'active'),
    }), 200


@app.route('/api/client/profile', methods=['PUT'])
@require_portal_auth
def client_update_profile():
    """Update client profile."""
    data = request.get_json(silent=True) or {}
    return jsonify({'message': 'Profile updated', 'success': True}), 200


# --- Admin Dashboard Endpoints ---

@app.route('/api/admin/dashboard', methods=['GET'])
@require_admin_auth
def admin_dashboard():
    """Admin dashboard overview with real stats."""
    metrics = lead_store.status_metrics()
    active_clients = lead_store.count_clients()
    intake_clients = lead_store.count_clients(status='intake')
    sessions_total = lead_store.count_sessions()
    upcoming = lead_store.count_appointments()
    total_leads = metrics.get('total_leads', 0)
    recent_leads = []
    for lead in lead_store.list_leads(limit=5):
        recent_leads.append({
            'id': lead.get('id'),
            'name': lead.get('name') or lead.get('email') or 'Unnamed',
            'source': lead.get('source'),
            'status': lead.get('status'),
            'created_at': lead.get('created_at'),
        })
    return jsonify({
        'stats': {
            'active_clients': active_clients,
            'intake_clients': intake_clients,
            'total_leads': total_leads,
            'sessions_logged': sessions_total,
            'upcoming_appointments': upcoming,
            'conversion_rate': metrics.get('conversion_rate', 0.0),
        },
        'recent_leads': recent_leads,
        'by_status': metrics.get('by_status', []),
        'by_source': metrics.get('by_source', []),
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/admin/clients', methods=['GET'])
@require_admin_auth
def admin_clients():
    """Admin view of all clients."""
    clients = lead_store.list_clients()
    return jsonify({'clients': clients, 'count': len(clients), 'timestamp': utcnow_iso()}), 200


@app.route('/api/admin/clients/<client_id>', methods=['GET'])
@require_admin_auth
def admin_client_detail(client_id):
    """Admin view of a single client."""
    client = lead_store.get_client(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    sessions = lead_store.list_sessions(client_id=client_id)
    appointments = lead_store.list_appointments(client_id=client_id)
    return jsonify({'client': client, 'sessions': sessions, 'appointments': appointments}), 200


@app.route('/api/admin/communications', methods=['GET'])
@require_admin_auth
def admin_communications():
    """Admin communications overview. Aggregates from available integrations."""
    comms = []
    # Pull recent lead events as communication log
    for lead in lead_store.list_leads(limit=20):
        if lead.get('source') in ('godaddy_chat', 'dialpad', 'email', 'webchat', 'website_form'):
            comms.append({
                'id': lead.get('id'),
                'type': lead.get('source'),
                'name': lead.get('name') or lead.get('email') or 'Unknown',
                'email': lead.get('email'),
                'phone': lead.get('phone'),
                'message': lead.get('initial_question', ''),
                'status': lead.get('status'),
                'date': lead.get('created_at'),
            })
    return jsonify({
        'communications': comms,
        'integrations': {
            'godaddy': bool(Config.GODADDY_WEBHOOK_SECRET),
            'dialpad': bool(Config.DIALPAD_API_KEY),
            'email': bool(Config.MS_CLIENT_ID),
        },
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/admin/schedule', methods=['GET'])
@require_admin_auth
def admin_schedule():
    """Admin schedule/calendar view."""
    appointments = lead_store.list_appointments(limit=50)
    return jsonify({'appointments': appointments, 'count': len(appointments), 'timestamp': utcnow_iso()}), 200


@app.route('/api/admin/financial', methods=['GET'])
@require_admin_auth
def admin_financial():
    """Admin financial overview. Wire to QuickBooks for real data."""
    clients = lead_store.list_clients()
    return jsonify({
        'revenue': {'total': 0, 'monthly': 0, 'currency': 'CAD'},
        'invoices': [],
        'active_clients': len(clients),
        'quickbooks_configured': bool(Config.QUICKBOOKS_REALM_ID),
        'message': 'Connect QuickBooks for live financial data' if not Config.QUICKBOOKS_REALM_ID else None,
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/admin/marketing', methods=['GET'])
@require_admin_auth
def admin_marketing():
    """Admin marketing analytics."""
    metrics = lead_store.status_metrics()
    source_counts = {row.get('source'): row.get('count', 0) for row in metrics.get('by_source', [])}
    return jsonify({
        'lead_sources': source_counts,
        'total_leads': metrics.get('total_leads', 0),
        'conversion_rate': metrics.get('conversion_rate', 0.0),
        'top_source': max(source_counts, key=source_counts.get) if source_counts else None,
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/admin/ai-agent', methods=['GET'])
@require_admin_auth
def admin_ai_agent():
    """Admin AI agent status and metrics."""
    llm_ready = bool(Config.OPENROUTER_API_KEY or Config.OPENAI_API_KEY or Config.ANTHROPIC_API_KEY)
    metrics = lead_store.status_metrics()
    status_counts = {row.get('status'): row.get('count', 0) for row in metrics.get('by_status', [])}
    drafts_created = status_counts.get('DRAFT_CREATED', 0)
    auto_sent = status_counts.get('PROGRAM_INFO_SENT', 0)
    return jsonify({
        'status': 'online' if llm_ready else 'offline',
        'llm_ready': llm_ready,
        'skills_loaded': len(SKILLS),
        'drafts_pending': drafts_created,
        'emails_sent': auto_sent,
        'leads_processed': metrics.get('total_leads', 0),
        'provider': 'openrouter' if Config.OPENROUTER_API_KEY else ('openai' if Config.OPENAI_API_KEY else ('anthropic' if Config.ANTHROPIC_API_KEY else 'none')),
        'timestamp': utcnow_iso(),
    }), 200


@app.route('/api/admin/conversations', methods=['GET'])
@require_admin_auth
def admin_conversations():
    """Admin view of AI agent conversations. Returns recent lead drafts as conversation history."""
    conversations = []
    for lead in lead_store.list_leads(limit=20):
        if lead.get('initial_question'):
            conversations.append({
                'id': lead.get('id'),
                'name': lead.get('name') or lead.get('email') or 'Unknown',
                'message': lead.get('initial_question'),
                'source': lead.get('source'),
                'date': lead.get('created_at'),
            })
    return jsonify({'conversations': conversations, 'timestamp': utcnow_iso()}), 200


# =============================================================================
# STARTUP WARNINGS
# =============================================================================
def _log_startup_warnings():
    """Log warnings for missing production configuration."""
    warnings = []
    if not INTERNAL_API_KEY:
        warnings.append("INTERNAL_API_KEY not set - API auth disabled" + (" (CRITICAL on Azure!)" if IS_AZURE else " (OK for local dev)"))
    if not Config.ANTHROPIC_API_KEY and not Config.OPENAI_API_KEY and not Config.OPENROUTER_API_KEY:
        warnings.append("No LLM API key configured - /api/chat will fail")
    if not Config.MS_CLIENT_ID:
        warnings.append("MS_CLIENT_ID not set - Microsoft Graph/SharePoint disabled")
    if not Config.DIALPAD_API_KEY:
        warnings.append("DIALPAD_API_KEY not set - Dialpad integration disabled")
    if not Config.DIALPAD_WEBHOOK_SECRET:
        warnings.append("DIALPAD_WEBHOOK_SECRET not set - webhook signature verification disabled")
    if not Config.GODADDY_WEBHOOK_SECRET:
        warnings.append("GODADDY_WEBHOOK_SECRET not set - webhook signature verification disabled")
    for w in warnings:
        logger.warning(f"[STARTUP] {w}")
    if not warnings:
        logger.info("[STARTUP] All critical secrets configured")

_log_startup_warnings()

# =============================================================================
# CALENDAR SYNC ENDPOINT
# =============================================================================

@app.route('/api/calendar/upcoming', methods=['GET'])
def calendar_upcoming():
    """Get upcoming calendar events from Outlook."""
    try:
        days = int(request.args.get('days', 7))
        user_id = Config.OUTLOOK_SENDER_UPN
        if not user_id:
            return jsonify({"error": "OUTLOOK_SENDER_UPN not configured"}), 500
        client = get_graph_client()
        result = client.get_calendar_events(user_id, days_ahead=days)
        events = result.get('value', [])
        formatted = []
        for ev in events:
            formatted.append({
                'id': ev.get('id'),
                'subject': ev.get('subject'),
                'start': ev.get('start', {}).get('dateTime'),
                'end': ev.get('end', {}).get('dateTime'),
                'location': ev.get('location', {}).get('displayName', ''),
                'organizer': ev.get('organizer', {}).get('emailAddress', {}).get('name', ''),
                'is_online': ev.get('isOnlineMeeting', False),
            })
        return jsonify({"success": True, "events": formatted, "count": len(formatted)})
    except Exception as e:
        logger.error(f"Calendar fetch failed: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# DISCORD NOTIFICATION HELPER
# =============================================================================

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')

def send_discord_notification(content, username="Trifecta AI"):
    """Send a notification to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        logger.debug("[Discord] No webhook URL configured, skipping notification")
        return False
    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": content, "username": username},
            timeout=10
        )
        return resp.status_code in (200, 204)
    except Exception as e:
        logger.warning(f"[Discord] Notification failed: {e}")
        return False


# =============================================================================
# IMAGE GENERATION ENDPOINT (DALL-E 3)
# =============================================================================

@app.route('/api/content/generate-image', methods=['POST'])
def generate_image():
    """Generate an image using OpenAI DALL-E 3."""
    try:
        body = request.get_json() or {}
        prompt = body.get('prompt')
        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            return jsonify({"error": "OPENAI_API_KEY not configured"}), 500

        size = body.get('size', '1024x1024')
        style = body.get('style', 'natural')

        resp = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers={
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'dall-e-3',
                'prompt': prompt,
                'n': 1,
                'size': size,
                'style': style
            },
            timeout=60
        )
        resp.raise_for_status()
        result = resp.json()
        image_url = result['data'][0]['url']
        revised_prompt = result['data'][0].get('revised_prompt', '')

        # Save image locally
        img_dir = os.path.join(os.path.dirname(__file__), 'trifecta', 'content-assets')
        os.makedirs(img_dir, exist_ok=True)
        img_filename = f"{uuid.uuid4().hex[:12]}.png"
        img_path = os.path.join(img_dir, img_filename)

        img_resp = requests.get(image_url, timeout=30)
        with open(img_path, 'wb') as f:
            f.write(img_resp.content)

        logger.info(f"[Image Gen] Created {img_filename} for prompt: {prompt[:50]}...")
        return jsonify({
            "success": True,
            "image_url": image_url,
            "local_path": img_path,
            "filename": img_filename,
            "revised_prompt": revised_prompt
        })
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# KPI LIVE DATA ENDPOINTS
# =============================================================================

KPI_FILE = os.path.join(os.path.dirname(__file__), "trifecta", "kpi", "live-kpis.json")

def _load_kpis() -> dict:
    """Load KPIs from JSON file, return defaults if missing."""
    default_kpis = {
        "updated": utcnow_iso(),
        "leads_today": 0,
        "leads_total": 0,
        "emails_sent_today": 0,
        "emails_sent_week": 0,
        "content_posted_today": 0,
        "content_posted_week": 0,
        "active_clients": 0,
        "monthly_revenue": 0,
        "conversion_rate": 0.0,
        "pipeline_value": 0,
    }
    try:
        with open(KPI_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_kpis

def _save_kpis(kpis: dict) -> None:
    """Save KPIs to JSON file atomically."""
    os.makedirs(os.path.dirname(KPI_FILE), exist_ok=True)
    kpis["updated"] = utcnow_iso()
    tmp = KPI_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(kpis, f, indent=2)
    os.replace(tmp, KPI_FILE)

@app.route("/api/kpi/live", methods=["GET"])
def kpi_live():
    """Return the current live KPIs as JSON."""
    kpis = _load_kpis()
    return jsonify({"success": True, "data": kpis})

@app.route("/api/kpi/update", methods=["POST"])
def kpi_update():
    """Update one or more KPI fields. Accepts a JSON body like {\"leads_today\": 5}."""
    data = request.get_json() or {}
    allowed_fields = {
        "leads_today", "leads_total", "emails_sent_today", "emails_sent_week",
        "content_posted_today", "content_posted_week", "active_clients",
        "monthly_revenue", "conversion_rate", "pipeline_value",
    }
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        return jsonify({"success": False, "error": "No valid fields provided"}), 400
    kpis = _load_kpis()
    kpis.update(updates)
    _save_kpis(kpis)
    logger.info(f"[KPI] Updated: {updates}")
    return jsonify({"success": True, "data": kpis})

# =============================================================================
# =============================================================================
# DAILY BRIEF ENDPOINT
# =============================================================================

@app.route('/api/brief', methods=['GET'])
def daily_brief():
    """
    Returns a structured daily brief for Lamby/Danielle:
    - Today's calendar events (via Microsoft Graph)
    - Active leads needing action (from lead_pipeline.db)
    - Content queue status (from content_drafts table or content-queue/)
    """
    brief = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'calendar': [],
        'leads': [],
        'content_queue': {},
        'errors': []
    }

    # --- Calendar Events via Microsoft Graph ---
    try:
        if Config.MS_CLIENT_ID and Config.MS_CLIENT_SECRET and Config.MS_TENANT_ID:
            graph = GraphClient()
            token = graph._get_token()
            now_utc = datetime.now(timezone.utc)
            start = now_utc.strftime('%Y-%m-%dT00:00:00Z')
            end = now_utc.strftime('%Y-%m-%dT23:59:59Z')
            user_email = os.environ.get('MS_USER_EMAIL', 'info@trifectaaddictionservices.com')
            resp = requests.get(
                f"{graph.base_url}/users/{user_email}/calendarView",
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                params={'startDateTime': start, 'endDateTime': end, '$select': 'subject,start,end,location,organizer', '$top': '20'},
                timeout=10
            )
            if resp.status_code == 200:
                events = resp.json().get('value', [])
                brief['calendar'] = [
                    {
                        'subject': e.get('subject', 'Untitled'),
                        'start': e.get('start', {}).get('dateTime', ''),
                        'end': e.get('end', {}).get('dateTime', ''),
                        'location': e.get('location', {}).get('displayName', '')
                    }
                    for e in events
                ]
            else:
                brief['errors'].append(f'Calendar fetch failed: {resp.status_code}')
        else:
            brief['errors'].append('Microsoft Graph not configured')
    except Exception as e:
        brief['errors'].append(f'Calendar error: {str(e)}')

    # --- Active Leads Needing Action ---
    try:
        db_path = Config.LEAD_DB_PATH if hasattr(Config, 'LEAD_DB_PATH') else os.path.join(
            os.environ.get('HOME', '/home'), 'data', 'lead_pipeline.db'
        )
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Leads that are active/new and haven't been contacted recently
            cur.execute("""
                SELECT id, name, email, phone, status, source, created_at, last_contacted_at, notes
                FROM leads
                WHERE status NOT IN ('closed', 'converted', 'rejected', 'unsubscribed')
                ORDER BY
                    CASE status
                        WHEN 'new' THEN 0
                        WHEN 'hot' THEN 1
                        WHEN 'warm' THEN 2
                        WHEN 'contacted' THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            brief['leads'] = [dict(r) for r in rows]
            conn.close()
        else:
            brief['errors'].append(f'Lead DB not found at {db_path}')
    except Exception as e:
        brief['errors'].append(f'Leads error: {str(e)}')

    # --- Content Queue Status ---
    try:
        db_path = Config.LEAD_DB_PATH if hasattr(Config, 'LEAD_DB_PATH') else os.path.join(
            os.environ.get('HOME', '/home'), 'data', 'lead_pipeline.db'
        )
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Content drafts summary
            cur.execute("SELECT status, COUNT(*) as count FROM content_drafts GROUP BY status")
            draft_stats = {row['status']: row['count'] for row in cur.fetchall()}
            # Approvals summary
            cur.execute("SELECT status, COUNT(*) as count FROM approvals GROUP BY status")
            approval_stats = {row['status']: row['count'] for row in cur.fetchall()}
            conn.close()
            brief['content_queue'] = {
                'drafts': draft_stats,
                'approvals': approval_stats,
                'pending_approvals': approval_stats.get('pending', 0)
            }
        # Also scan filesystem content-queue/
        queue_dir = os.path.join(os.path.dirname(__file__), 'trifecta', 'content-queue')
        if os.path.isdir(queue_dir):
            md_files = [f for f in os.listdir(queue_dir) if f.endswith('.md')]
            brief['content_queue']['filesystem_queue'] = md_files
    except Exception as e:
        brief['errors'].append(f'Content queue error: {str(e)}')

    return jsonify({'success': True, 'data': brief}), 200


# OIL & GAS CAMPAIGN LEADS
# =============================================================================
def _oil_gas_db():
    """Get a connection to the Oil & Gas leads SQLite database."""
    db_path = Config.OIL_GAS_LEAD_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _init_oil_gas_db():
    """Create Oil & Gas leads tables if they don't exist."""
    conn = _oil_gas_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oil_gas_leads (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                source TEXT DEFAULT 'oil_gas_website',
                platform TEXT,
                enquiry_type TEXT,
                lead_score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'INQUIRY_RECEIVED',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oil_gas_events (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                event_type TEXT,
                source TEXT,
                received_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (lead_id) REFERENCES oil_gas_leads(id)
            )
        """)
        conn.commit()
        logger.info("[OilGas] Database initialized")
    finally:
        conn.close()

# Init on startup
_init_oil_gas_db()

@app.route('/api/oil-gas/leads', methods=['POST'])
def create_oil_gas_lead():
    """Create a new Oil & Gas campaign lead."""
    try:
        data = request.get_json() or {}
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        lead_id = str(uuid.uuid4())
        now = utcnow_iso()
        conn = _oil_gas_db()
        try:
            conn.execute("""
                INSERT INTO oil_gas_leads (id, name, email, phone, source, platform, enquiry_type, lead_score, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'INQUIRY_RECEIVED', ?, ?, ?)
            """, (
                lead_id,
                data.get('name', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('source', 'oil_gas_website'),
                data.get('platform', ''),
                data.get('enquiry_type', ''),
                int(data.get('lead_score', 0)),
                data.get('notes', ''),
                now,
                now
            ))
            conn.commit()
            # Emit to dashboard
            emit_to_dashboard(
                "oil_gas_lead:new",
                f"Oil & Gas lead: {data.get('name')} from {data.get('platform', data.get('source', 'web'))}",
                {"leadId": lead_id, "name": data.get('name'), "source": data.get('source', 'oil_gas_website'), "platform": data.get('platform', '')}
            )
            return jsonify({'success': True, 'id': lead_id, 'status': 'INQUIRY_RECEIVED'}), 201
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Create Oil & Gas lead error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/query', methods=['POST'])
def query_oil_gas_leads():
    """Query Oil & Gas leads with optional filters."""
    try:
        data = request.get_json(silent=True) or {}
        conn = _oil_gas_db()
        try:
            conditions = []
            params = []
            if data.get('status'):
                conditions.append("status = ?")
                params.append(data['status'])
            if data.get('source'):
                conditions.append("source = ?")
                params.append(data['source'])
            if data.get('platform'):
                conditions.append("platform = ?")
                params.append(data['platform'])
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            limit = min(int(data.get('limit', 100)), 500)
            offset = int(data.get('offset', 0))
            rows = conn.execute(
                f"SELECT * FROM oil_gas_leads {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (*params, limit, offset)
            ).fetchall()
            total = conn.execute(
                f"SELECT COUNT(*) as cnt FROM oil_gas_leads {where}", tuple(params)
            ).fetchone()['cnt']
            return jsonify({'leads': [dict(r) for r in rows], 'count': total})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Query Oil & Gas leads error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/stats', methods=['GET'])
def oil_gas_leads_stats():
    """Get Oil & Gas leads stats."""
    try:
        conn = _oil_gas_db()
        try:
            total = conn.execute("SELECT COUNT(*) as cnt FROM oil_gas_leads").fetchone()['cnt']
            today = datetime.now().strftime('%Y-%m-%d')
            new_today = conn.execute(
                "SELECT COUNT(*) as cnt FROM oil_gas_leads WHERE date(created_at) = ?", (today,)
            ).fetchone()['cnt']
            hot_leads = conn.execute(
                "SELECT COUNT(*) as cnt FROM oil_gas_leads WHERE lead_score >= 15"
            ).fetchone()['cnt']
            return jsonify({'total': total, 'newToday': new_today, 'hotLeads': hot_leads})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Oil & Gas stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/<lead_id>', methods=['GET'])
def get_oil_gas_lead(lead_id):
    """Get a single Oil & Gas lead."""
    try:
        conn = _oil_gas_db()
        try:
            lead = conn.execute("SELECT * FROM oil_gas_leads WHERE id = ?", (lead_id,)).fetchone()
            if not lead:
                return jsonify({'error': 'Lead not found'}), 404
            events = conn.execute(
                "SELECT * FROM oil_gas_events WHERE lead_id = ? ORDER BY received_at DESC LIMIT 20", (lead_id,)
            ).fetchall()
            return jsonify({**dict(lead), 'events': [dict(e) for e in events]})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Get Oil & Gas lead error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/<lead_id>', methods=['PATCH'])
def update_oil_gas_lead(lead_id):
    """Update an Oil & Gas lead."""
    try:
        data = request.get_json() or {}
        allowed = ['name', 'email', 'phone', 'status', 'lead_score', 'notes', 'enquiry_type', 'platform']
        fields = {k: v for k, v in data.items() if k in allowed}
        if not fields:
            return jsonify({'success': True})
        fields['updated_at'] = utcnow_iso()
        set_clause = ", ".join([f"{k} = ?" for k in fields])
        conn = _oil_gas_db()
        try:
            conn.execute(
                f"UPDATE oil_gas_leads SET {set_clause} WHERE id = ?",
                (*fields.values(), lead_id)
            )
            conn.commit()
            emit_to_dashboard("oil_gas_lead:updated", f"Oil & Gas lead updated", {"leadId": lead_id, "status": fields.get('status', '')})
            return jsonify({'success': True})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Update Oil & Gas lead error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/<lead_id>/archive', methods=['POST'])
def archive_oil_gas_lead(lead_id):
    """Archive an Oil & Gas lead."""
    try:
        conn = _oil_gas_db()
        try:
            conn.execute(
                "UPDATE oil_gas_leads SET status = ?, updated_at = ? WHERE id = ?",
                ('ARCHIVED', utcnow_iso(), lead_id)
            )
            conn.commit()
            emit_to_dashboard("oil_gas_lead:updated", "Oil & Gas lead archived", {"leadId": lead_id, "status": "ARCHIVED"})
            return jsonify({'success': True})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Archive Oil & Gas lead error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oil-gas/leads/metrics', methods=['GET'])
def oil_gas_leads_metrics():
    """Get Oil & Gas leads metrics breakdown."""
    try:
        conn = _oil_gas_db()
        try:
            by_status = [dict(r) for r in conn.execute("SELECT status, COUNT(*) as count FROM oil_gas_leads GROUP BY status").fetchall()]
            by_source = [dict(r) for r in conn.execute("SELECT source, COUNT(*) as count FROM oil_gas_leads GROUP BY source").fetchall()]
            by_platform = [dict(r) for r in conn.execute("SELECT platform, COUNT(*) as count FROM oil_gas_leads GROUP BY platform").fetchall()]
            return jsonify({'by_status': by_status, 'by_source': by_source, 'by_platform': by_platform})
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Oil & Gas metrics error: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# RECOVERY BUDDY
# =============================================================================

RECOVERY_BUDDY_SYSTEM_PROMPT = (
    "You are the Trifecta Recovery Buddy, a warm and compassionate AI assistant for "
    "Trifecta Addiction and Mental Health Services. You are trained in DBT and CBT approaches. "
    "You provide emotional support, answer questions about programs, and help people take the "
    "first step toward recovery. You never give medical advice. You always encourage professional "
    "support. Programs available: 14-Day Executive Reset ($13,777, next intake April 5), "
    "21-Day Intensive Inpatient ($17,777), 28-Day Inpatient Residential ($23,777), "
    "28-Day Virtual Boot Camp ($3,777). "
    "Booking link: https://trifectaaddictionservices.com/m/login?r=%2Fm%2Fbookings "
    "Phone: (403) 907-0996. "
    "If someone is in crisis, direct them to 988 (Suicide and Crisis Lifeline) immediately. "
    "Always be warm and gentle. Use no em dashes. Use no emojis. Evidence-based language only. "
    "Keep responses concise (2-4 sentences). Never use the word 'boundaries' as a cliche."
)


@app.route('/api/recovery-buddy/chat', methods=['POST'])
def recovery_buddy_chat():
    """Recovery Buddy chat endpoint - 24/7 lead capture and support chatbot."""
    import re as _re
    if not request.is_json:
        return jsonify({'error': 'JSON required'}), 400

    data = request.get_json()
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({'error': 'message required'}), 400

    if not isinstance(history, list):
        return jsonify({'error': 'history must be a list'}), 400

    # Build messages for Claude
    messages = []
    for h in history[-10:]:  # Keep last 10 turns
        if isinstance(h, dict) and h.get('role') in ('user', 'assistant') and h.get('content'):
            messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': message})

    # Check for email capture
    email_match = _re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', message)
    if email_match:
        try:
            captured_email = email_match.group(0)
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id FROM leads WHERE email=?", (captured_email,))
            if not c.fetchone():
                import uuid as _uuid
                from datetime import datetime as _dt
                c.execute(
                    "INSERT INTO leads (id, email, source, status, initial_question, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (str(_uuid.uuid4()), captured_email, 'RECOVERY_BUDDY', 'INQUIRY_RECEIVED',
                     message[:200], _dt.utcnow().isoformat(), _dt.utcnow().isoformat())
                )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Recovery Buddy lead capture failed: {e}")

    # Call Anthropic API
    anthropic_key = app.config.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_key:
        return jsonify({'reply': 'I am having trouble connecting right now. Please call us at (403) 907-0996.', 'history': history}), 200

    try:
        import requests as _req
        resp = _req.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': anthropic_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 300,
                'system': RECOVERY_BUDDY_SYSTEM_PROMPT,
                'messages': messages
            },
            timeout=15
        )
        resp.raise_for_status()
        reply = resp.json()['content'][0]['text']
    except Exception as e:
        logger.warning(f"Recovery Buddy API call failed: {e}")
        reply = 'I am here with you. If you need immediate support, please call us at (403) 907-0996 or reach the crisis line at 988.'

    updated_history = list(history) + [
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': reply}
    ]

    return jsonify({'reply': reply, 'history': updated_history})


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    logger.info(f"Starting Trifecta AI Agent v1.0.0 on port {port}")
    logger.info(f"Skills loaded: {len(SKILLS)}")
    logger.info(f"Debug mode: {debug}")

    app._scheduler = _init_scheduler()
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # Production (gunicorn) — start scheduler on import
    app._scheduler = _init_scheduler()



