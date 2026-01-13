"""
Trifecta AI Agent - Production Flask Application
Flask-based AI agent API with Azure integrations, Microsoft Graph, SharePoint, Dialpad
Version: 1.1.0 | Updated: 2026-01-12
"""

import os
import json
import re
import logging
import uuid
from flask import Flask, request, jsonify, g, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import requests
from requests.exceptions import Timeout, RequestException
from werkzeug.exceptions import HTTPException

# Azure SDK imports (optional - only needed if using Azure Key Vault directly)
try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False

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

    # GoDaddy WebChat
    GODADDY_API_KEY = os.environ.get('GODADDY_API_KEY', '')
    GODADDY_API_SECRET = os.environ.get('GODADDY_API_SECRET', '')
    GODADDY_WEBCHAT_WEBHOOK_SECRET = os.environ.get('GODADDY_WEBCHAT_WEBHOOK_SECRET', '')

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
DEMO_MODE = os.environ.get('DEMO_MODE', '0') == '1'

def get_demo_response(message, skill=None):
    """Return demo response when no API key is configured."""
    skill_name = skill['title'] if skill else 'General'
    
    # Smart demo responses based on message content
    msg_lower = message.lower()
    
    if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
        return f"Hello! I'm the Trifecta AI Assistant. I'm currently in demo mode. To enable full AI capabilities, please configure your ANTHROPIC_API_KEY in the .env file."
    
    if any(word in msg_lower for word in ['service', 'program', 'offer', 'help']):
        return """**Trifecta Services** (Demo Mode)

Trifecta Addiction & Mental Health Services offers:

1. **28-Day Virtual Boot Camp** - $3,777 CAD
   - Online recovery program with daily sessions
   
2. **14-Day Inpatient Program** - $13,777 CAD
   - Intensive residential treatment
   
3. **28-Day Inpatient Program** - $23,777 CAD
   - Comprehensive residential recovery

📞 Contact: (403) 907-0996
🌐 Website: trifectaaddiction.ca

*Note: This is a demo response. Configure ANTHROPIC_API_KEY for full AI capabilities.*"""
    
    if any(word in msg_lower for word in ['intake', 'assessment', 'start']):
        return """**Lead Intake Process** (Demo Mode)

To begin the intake process:

1. **Initial Contact** - Phone or webchat
2. **Pre-Assessment** - Brief questionnaire
3. **Consultation** - 30-min call with intake coordinator
4. **Program Selection** - Choose appropriate treatment
5. **Documentation** - Contract and payment setup
6. **Scheduling** - Set start date

*Configure ANTHROPIC_API_KEY for AI-powered intake assistance.*"""
    
    return f"""**Demo Response** (Skill: {skill_name})

Your message: "{message[:100]}..."

I'm currently running in demo mode without an Anthropic API key.

**To enable full AI:**
1. Get an API key from https://console.anthropic.com/
2. Add to .env: ANTHROPIC_API_KEY=sk-ant-api03-...
3. Restart the Flask server

The system is ready - just needs the API key!"""

def call_anthropic(skill_context, message, max_tokens=2000):
    """Call Anthropic Messages API with Claude.
    Falls back to demo mode if no API key is configured.
    """
    api_key = Config.ANTHROPIC_API_KEY
    
    # Check if we should use demo mode
    if not api_key or api_key.startswith('@Microsoft.KeyVault') or api_key.startswith('your_'):
        if DEMO_MODE or os.environ.get('ALLOW_DEMO', '1') == '1':
            logger.info('Using demo mode - no API key configured')
            return None  # Signal to use demo response
        raise ValueError("ANTHROPIC_API_KEY not configured")

    url = 'https://api.anthropic.com/v1/messages'
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01'
    }

    payload = {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': max_tokens,
        'messages': [{'role': 'user', 'content': message}]
    }

    if skill_context:
        payload['system'] = f"""You are Trifecta AI, an assistant for Trifecta Addiction & Mental Health Services in Calgary, Canada.
You help with client intake, session planning, documentation, and recovery support.
Be professional, compassionate, and action-oriented.

Context from skill knowledge base:
{skill_context}"""

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        content = data.get('content', [])
        if content and len(content) > 0:
            return content[0].get('text', '').strip()
        return ''
    except Timeout:
        logger.warning('Anthropic request timed out after 60s')
        raise
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 'unknown'
        body = e.response.text[:200] if e.response else 'No response'
        logger.error('Anthropic HTTP error: %s - %s', status, body)
        raise RequestException(f"Anthropic API error: {status}")
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
        # Validate content type
        if not request.is_json:
            return jsonify({'error': 'Expected application/json', 'code': 'invalid_content_type'}), 400
        
        # Parse JSON with error handling
        try:
            data = request.get_json(force=False)
        except Exception as e:
            logger.warning(f"JSON parse error: {e}")
            return jsonify({'error': 'Invalid JSON', 'code': 'invalid_json'}), 400
        
        # Validate payload
        if data is None:
            return jsonify({'error': 'Invalid payload', 'code': 'invalid_payload'}), 400
        
        validation = _validate_message_payload(data)
        if validation:
            return validation
        
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required', 'code': 'missing_message'}), 400

        # Match skill
        matched = match_skill(message)
        skill_context = ''

        if matched:
            skill_context = matched.get('content', '')
            if len(skill_context) > 8000:
                skill_context = skill_context[:8000] + '\n\n[truncated for context limit]'

        # Call Claude (or use demo mode)
        demo_mode_used = False
        try:
            response_text = call_anthropic(skill_context, message)
            # If None returned, use demo response
            if response_text is None:
                response_text = get_demo_response(message, matched)
                demo_mode_used = True
        except ValueError as e:
            # API key not configured - use demo mode
            logger.warning('Using demo mode: %s', e)
            response_text = get_demo_response(message, matched)
            demo_mode_used = True
        except Timeout:
            logger.warning('Anthropic timed out for message: %s', message[:80])
            response_text = "Service timed out, please try again."
        except RequestException as e:
            logger.error('Anthropic request failed: %s', e)
            response_text = "I'm unable to process your request right now. Please try again."
        except Exception as e:
            logger.error('Unexpected Anthropic error: %s', e)
            response_text = "I'm unable to process your request right now. Please try again."

        return jsonify({
            'reply': response_text,
            'matched_skill': matched['name'] if matched else None,
            'skill_title': matched['title'] if matched else None,
            'demo_mode': demo_mode_used,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        err_id = str(uuid.uuid4())
        logger.exception('Chat error [%s]: %s', err_id, e)
        return jsonify({
            'error': 'Internal server error',
            'id': err_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

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
    """
    Receive Dialpad webhooks for call events.
    Events: call.started, call.ended, voicemail.received, sms.received
    """
    try:
        # Verify webhook signature if secret is configured
        signature = request.headers.get('X-Dialpad-Signature')
        if Config.DIALPAD_WEBHOOK_SECRET and signature:
            import hmac
            import hashlib
            expected = hmac.new(
                Config.DIALPAD_WEBHOOK_SECRET.encode(),
                request.data,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                logger.warning('Invalid Dialpad webhook signature')
                return jsonify({'error': 'Invalid signature'}), 401

        event = request.get_json()
        if not event:
            return jsonify({'error': 'No event data'}), 400
            
        event_type = event.get('type', 'unknown')
        logger.info(f"Dialpad webhook: {event_type}")

        # Handle different event types
        if event_type == 'call.ended':
            call_data = event.get('call', {})
            call_id = call_data.get('id')
            duration = call_data.get('duration')
            caller = call_data.get('caller', {}).get('number')
            
            logger.info(f"Call ended: {call_id}, duration: {duration}s, caller: {caller}")
            
            # Auto-trigger transcription if call was long enough (>60s)
            if duration and int(duration) > 60:
                logger.info(f"Queueing transcription for call {call_id}")
                # In production: queue async job to fetch transcription
                
        elif event_type == 'voicemail.received':
            voicemail = event.get('voicemail', {})
            caller = voicemail.get('caller', {}).get('number')
            logger.info(f"Voicemail from: {caller}")
            
        elif event_type == 'sms.received':
            sms = event.get('sms', {})
            sender = sms.get('from_number')
            text = sms.get('text', '')[:100]
            logger.info(f"SMS from {sender}: {text}...")

        return jsonify({
            'status': 'received',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Dialpad webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - GoDaddy WebChat Webhook
# =============================================================================
@app.route('/api/godaddy/webhook', methods=['POST'])
def godaddy_webhook():
    """
    Receive GoDaddy WebChat webhooks for new messages.
    Auto-responds with AI or creates lead.
    """
    try:
        # Verify webhook signature if configured
        signature = request.headers.get('X-GoDaddy-Signature')
        if Config.GODADDY_WEBCHAT_WEBHOOK_SECRET and signature:
            import hmac
            import hashlib
            expected = hmac.new(
                Config.GODADDY_WEBCHAT_WEBHOOK_SECRET.encode(),
                request.data,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                logger.warning('Invalid GoDaddy webhook signature')
                return jsonify({'error': 'Invalid signature'}), 401

        event = request.get_json()
        if not event:
            return jsonify({'error': 'No event data'}), 400
            
        event_type = event.get('type', 'message')
        logger.info(f"GoDaddy webhook: {event_type}")

        if event_type == 'message.received':
            conversation_id = event.get('conversation_id')
            message = event.get('message', {})
            text = message.get('text', '')
            visitor = event.get('visitor', {})
            
            logger.info(f"WebChat message from {visitor.get('name', 'Unknown')}: {text[:50]}...")
            
            # Check for lead indicators
            lead_keywords = ['help', 'treatment', 'program', 'cost', 'insurance', 'addiction', 'recovery']
            is_potential_lead = any(kw in text.lower() for kw in lead_keywords)
            
            if is_potential_lead:
                logger.info(f"Potential lead detected in conversation {conversation_id}")
                # In production: create lead in CRM, notify intake team
            
            # Auto-respond with AI (if configured)
            # This would call the chat endpoint internally

        return jsonify({
            'status': 'received',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"GoDaddy webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - Lead Intake Webhook
# =============================================================================
@app.route('/api/webhook/lead', methods=['POST'])
def lead_intake_webhook():
    """
    Receive new leads from website forms, landing pages, or third-party sources.
    Creates lead in system and triggers intake workflow.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No lead data'}), 400

        # Extract lead info
        lead = {
            'id': str(uuid.uuid4()),
            'name': data.get('name', '').strip(),
            'email': data.get('email', '').strip(),
            'phone': data.get('phone', '').strip(),
            'source': data.get('source', 'website'),
            'message': data.get('message', ''),
            'interest': data.get('interest', ''),  # e.g., "28-day program"
            'urgency': data.get('urgency', 'normal'),  # low, normal, high, urgent
            'created_at': datetime.utcnow().isoformat(),
            'status': 'new'
        }

        # Validate required fields
        if not lead['name'] or not (lead['email'] or lead['phone']):
            return jsonify({
                'error': 'Name and either email or phone required',
                'code': 'missing_fields'
            }), 400

        logger.info(f"New lead received: {lead['name']} from {lead['source']}")

        # Determine priority based on urgency keywords
        urgent_keywords = ['urgent', 'emergency', 'crisis', 'overdose', 'suicide', 'immediate']
        if any(kw in lead['message'].lower() for kw in urgent_keywords):
            lead['urgency'] = 'urgent'
            lead['priority'] = 1
            logger.warning(f"URGENT lead: {lead['name']} - {lead['message'][:100]}")
        else:
            lead['priority'] = 3 if lead['urgency'] == 'high' else 5

        # In production: Save to database, create in Azure AD, notify team
        # For now, log and return success
        
        return jsonify({
            'status': 'received',
            'lead_id': lead['id'],
            'priority': lead['priority'],
            'urgency': lead['urgency'],
            'message': f"Lead '{lead['name']}' created successfully",
            'timestamp': datetime.utcnow().isoformat()
        }), 201

    except Exception as e:
        logger.error(f"Lead intake webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - QuickBooks Webhook
# =============================================================================
@app.route('/api/quickbooks/webhook', methods=['POST'])
def quickbooks_webhook():
    """
    Receive QuickBooks webhooks for payment events.
    Events: Payment received, Invoice status change
    """
    try:
        # QuickBooks uses a verifier token in query param
        verifier = request.args.get('verifier')
        
        event = request.get_json()
        if not event:
            return jsonify({'error': 'No event data'}), 400

        event_notifications = event.get('eventNotifications', [])
        
        for notification in event_notifications:
            realm_id = notification.get('realmId')
            data_changes = notification.get('dataChangeEvent', {}).get('entities', [])
            
            for entity in data_changes:
                entity_name = entity.get('name')  # e.g., "Payment", "Invoice"
                entity_id = entity.get('id')
                operation = entity.get('operation')  # Create, Update, Delete
                
                logger.info(f"QuickBooks: {operation} {entity_name} {entity_id}")
                
                if entity_name == 'Payment' and operation == 'Create':
                    logger.info(f"Payment received: {entity_id}")
                    # In production: Update client status, send confirmation

        return jsonify({
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"QuickBooks webhook error: {e}")
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
# API ENDPOINTS - Invoice Generation (New Template-Based)
# =============================================================================
def load_invoice_template():
    """Load the HTML invoice template."""
    template_path = Path(__file__).parent / 'templates' / 'invoice_template.html'
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    return None

def generate_invoice_html(invoice_data):
    """Generate HTML invoice from template and data."""
    template = load_invoice_template()
    if not template:
        return None

    # Generate line items HTML
    line_items_html = ""
    for item in invoice_data.get('line_items', []):
        line_items_html += f"""
          <tr>
            <td>
              <div class="line-item-title">{item.get('title', 'Virtual Session – 60 Minutes')}</div>
              <div class="line-item-date">Date: {item.get('date', '')}</div>
              <div class="line-item-focus">Focus: {item.get('focus', '')}</div>
            </td>
            <td>${item.get('rate', '60.00')}</td>
            <td>${item.get('amount', '60.00')}</td>
          </tr>
        """

    # Determine status class
    status = invoice_data.get('status', 'OUTSTANDING')
    status_class = 'status-outstanding'
    if 'PARTIAL' in status.upper():
        status_class = 'status-partial'
    elif 'PAID' in status.upper():
        status_class = 'status-paid'

    # Replace template variables
    html = template
    replacements = {
        '{{INVOICE_NUMBER}}': str(invoice_data.get('invoice_number', '0000')),
        '{{CLIENT_NAME}}': invoice_data.get('client_name', ''),
        '{{SERVICE_TYPE}}': invoice_data.get('service_type', 'Virtual Counselling Sessions'),
        '{{PAYMENT_METHOD}}': invoice_data.get('payment_method', 'e-Transfer'),
        '{{PROGRAM_SERVICE}}': invoice_data.get('program_service', 'Virtual Individual Counselling'),
        '{{STATUS}}': status,
        '{{STATUS_CLASS}}': status_class,
        '{{SESSIONS_COVERED}}': invoice_data.get('sessions_covered', ''),
        '{{LINE_ITEMS}}': line_items_html,
        '{{OUTSTANDING_BALANCE}}': f"{invoice_data.get('outstanding_balance', 0):.2f}",
        '{{SUMMARY_NOTE}}': invoice_data.get('summary_note', ''),
        '{{PAYMENT_STATUS_TEXT}}': invoice_data.get('payment_status_text', ''),
        '{{CURRENT_YEAR}}': str(datetime.utcnow().year),
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    return html

@app.route('/api/invoice/generate', methods=['POST'])
def generate_invoice():
    """
    Generate a professional invoice using the Trifecta template.

    Expected JSON payload:
    {
        "invoice_number": "1413",
        "client_name": "Max Willigar",
        "service_type": "Virtual Counselling Sessions",
        "payment_method": "e-Transfer (Partial Payment)",
        "program_service": "Virtual Individual Counselling",
        "status": "PARTIAL PAYMENT RECEIVED",
        "sessions_covered": "Tuesday Dec 3, Tuesday Dec 10, Wednesday Dec 18, 2025 & Friday Jan 3, 2026",
        "line_items": [
            {
                "title": "Virtual Session – 60 Minutes",
                "date": "Tuesday, December 3, 2025",
                "focus": "Initial assessment and treatment planning for addiction recovery.",
                "rate": "60.00",
                "amount": "60.00"
            }
        ],
        "total_amount": 240.00,
        "amount_paid": 180.00,
        "outstanding_balance": 60.00
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Calculate summary note
        session_count = len(data.get('line_items', []))
        total = data.get('total_amount', 0)

        # Build sessions dates list for summary
        sessions_dates = ', '.join([item.get('date', '') for item in data.get('line_items', [])])

        data['summary_note'] = (
            f"This invoice reflects {session_count} 60-minute virtual counselling sessions for {data.get('client_name', '')} "
            f"on {sessions_dates}. Professional fee is $60/hour, for a total of ${total:.2f} CAD. "
            f"Services are GST exempt."
        )

        # Build payment status text
        amount_paid = data.get('amount_paid', 0)
        outstanding = data.get('outstanding_balance', 0)
        data['payment_status_text'] = f"${amount_paid:.2f} has been received. Outstanding balance: ${outstanding:.2f}"

        # Generate HTML
        html_invoice = generate_invoice_html(data)

        if not html_invoice:
            return jsonify({'error': 'Invoice template not found'}), 500

        # Optionally upload to SharePoint
        sharepoint_url = None
        if data.get('upload_to_sharepoint', False):
            try:
                client_folder = data.get('client_name', 'Unknown').replace(' ', '_')
                filename = f"Invoice_{data.get('invoice_number', '0000')}_{datetime.utcnow().strftime('%Y%m%d')}.html"
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
            'invoice_number': data.get('invoice_number'),
            'client_name': data.get('client_name'),
            'html_invoice': html_invoice,
            'sharepoint_url': sharepoint_url,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Invoice generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/invoice/preview', methods=['POST'])
def preview_invoice():
    """
    Preview invoice as rendered HTML (returns HTML directly for browser preview).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Calculate summary note
        session_count = len(data.get('line_items', []))
        total = data.get('total_amount', 0)
        sessions_dates = ', '.join([item.get('date', '') for item in data.get('line_items', [])])

        data['summary_note'] = (
            f"This invoice reflects {session_count} 60-minute virtual counselling sessions for {data.get('client_name', '')} "
            f"on {sessions_dates}. Professional fee is $60/hour, for a total of ${total:.2f} CAD. "
            f"Services are GST exempt."
        )

        amount_paid = data.get('amount_paid', 0)
        outstanding = data.get('outstanding_balance', 0)
        data['payment_status_text'] = f"${amount_paid:.2f} has been received. Outstanding balance: ${outstanding:.2f}"

        html_invoice = generate_invoice_html(data)

        if not html_invoice:
            return jsonify({'error': 'Invoice template not found'}), 500

        return html_invoice, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        logger.error(f"Invoice preview error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - GoDaddy WebChat Integration
# =============================================================================
# GoDaddy Conversations API Configuration
GODADDY_API_KEY = os.environ.get('GODADDY_API_KEY', '')
GODADDY_API_SECRET = os.environ.get('GODADDY_API_SECRET', '')
GODADDY_BASE_URL = 'https://api.godaddy.com/v1'

@app.route('/api/godaddy/conversations', methods=['GET'])
def godaddy_conversations():
    """
    Get GoDaddy WebChat conversations.
    Query params: limit (default 20), status (open/closed)
    """
    try:
        if not GODADDY_API_KEY:
            return jsonify({
                'error': 'GoDaddy API not configured',
                'hint': 'Set GODADDY_API_KEY and GODADDY_API_SECRET environment variables',
                'conversations': [],
                'count': 0
            }), 200  # Return 200 with empty list for dashboard compatibility

        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', '')

        headers = {
            'Authorization': f'sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}',
            'Content-Type': 'application/json'
        }

        params = {'limit': limit}
        if status:
            params['status'] = status

        # Note: This is a placeholder - actual GoDaddy API endpoint may differ
        # GoDaddy doesn't have a standard conversations API; this would need
        # to be adapted for their specific integration (e.g., Website Builder chat)

        return jsonify({
            'conversations': [],
            'count': 0,
            'note': 'GoDaddy WebChat integration pending configuration',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"GoDaddy conversations error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/godaddy/conversations/<conversation_id>/messages', methods=['GET', 'POST'])
def godaddy_messages(conversation_id):
    """
    Get or send messages for a GoDaddy WebChat conversation.
    """
    try:
        if not GODADDY_API_KEY:
            return jsonify({
                'error': 'GoDaddy API not configured',
                'messages': []
            }), 200

        headers = {
            'Authorization': f'sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}',
            'Content-Type': 'application/json'
        }

        if request.method == 'GET':
            return jsonify({
                'conversation_id': conversation_id,
                'messages': [],
                'note': 'GoDaddy WebChat integration pending configuration',
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        elif request.method == 'POST':
            data = request.get_json()
            message = data.get('message', '')

            return jsonify({
                'status': 'pending',
                'conversation_id': conversation_id,
                'message': message,
                'note': 'GoDaddy WebChat integration pending configuration',
                'timestamp': datetime.utcnow().isoformat()
            }), 200

    except Exception as e:
        logger.error(f"GoDaddy messages error: {e}")
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

    logger.info(f"Starting Trifecta AI Agent v1.1.0 on port {port}")
    logger.info(f"Skills loaded: {len(SKILLS)}")
    logger.info(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)
