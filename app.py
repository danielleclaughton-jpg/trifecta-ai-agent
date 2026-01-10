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
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import requests
from functools import wraps
from requests.exceptions import Timeout, RequestException
from werkzeug.exceptions import HTTPException

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
load_dotenv()

# =============================================================================
# APP INITIALIZATION
# =============================================================================
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configurable defaults
DEFAULT_OUTBOUND_TIMEOUT = int(os.environ.get('DEFAULT_OUTBOUND_TIMEOUT', '15'))  # seconds
MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', '2000'))

# Request ID middleware
@app.before_request
def attach_request_id():
    g.request_id = str(uuid.uuid4())

@app.after_request
def add_request_id_header(response):
    response.headers['X-Request-Id'] = getattr(g, 'request_id', '')
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

    # QuickBooks
    QUICKBOOKS_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
    QUICKBOOKS_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
    QUICKBOOKS_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')

    # Anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

    # App
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SKILL_DIR = os.environ.get('SKILL_DIR', 'Assets/skills')

app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

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
        'anthropic-version': '2023-06-01'
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
    }), 200 if status == 'healthy' else 503

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

@app.route('/api/dialpad/webhook', methods=['POST'])
def dialpad_webhook():
    """Receive Dialpad webhooks for call events."""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Dialpad-Signature')
        # TODO: Verify signature with DIALPAD_WEBHOOK_SECRET

        event = request.get_json()
        event_type = event.get('type')

        logger.info(f"Dialpad webhook received: {event_type}")

        # Handle different event types
        if event_type == 'call.ended':
            call_id = event.get('call', {}).get('id')
            # Trigger session documentation workflow
            # This would queue a job to process the call

        return jsonify({'status': 'received'}), 200

    except Exception as e:
        logger.error(f"Dialpad webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - Portal Sync (Task 4)
# =============================================================================
@app.route('/api/portal-sync', methods=['GET', 'POST'])
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
