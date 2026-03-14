"""Trifecta AI Agent - Flask Application with Webhook Integration"""
import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from webhooks import (
    get_registry, get_emitter, get_signer, 
    WebhookEvent, EventType
)

app = Flask(__name__)
CORS(app)

# Configuration
AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY', 'not-configured')
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'not-configured')
MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID', 'not-configured')
MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET', 'not-configured')
MS_TENANT_ID = os.environ.get('MS_TENANT_ID', 'not-configured')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
DIALPOD_API_KEY = os.environ.get('DialpodApiKey', 'not-configured')
app.secret_key = SECRET_KEY


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'running', 'service': 'Trifecta AI', 'version': '2.0.0'}), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200


# ============================================================================
# Webhook Management Endpoints
# ============================================================================

@app.route('/api/webhooks/register', methods=['POST'])
def register_webhook():
    """Register a webhook URL to receive events
    
    Request body:
    {
        "webhook_url": "https://example.com/webhooks",
        "event_types": ["lead.new", "payment.received"]  # Optional, defaults to all
    }
    """
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        event_types = data.get('event_types')
        
        if not webhook_url:
            return jsonify({'error': 'webhook_url is required'}), 400
        
        registry = get_registry()
        result = registry.register(webhook_url, event_types)
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/unregister', methods=['POST'])
def unregister_webhook():
    """Unregister a webhook URL
    
    Request body:
    {
        "webhook_url": "https://example.com/webhooks",
        "event_types": ["lead.new"]  # Optional, defaults to all
    }
    """
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        event_types = data.get('event_types')
        
        if not webhook_url:
            return jsonify({'error': 'webhook_url is required'}), 400
        
        registry = get_registry()
        result = registry.unregister(webhook_url, event_types)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/events', methods=['GET'])
def list_event_types():
    """List all available webhook event types"""
    try:
        registry = get_registry()
        event_types = registry.get_event_types()
        
        return jsonify({
            'event_types': event_types,
            'count': len(event_types),
            'description': 'Available webhook event types for subscription'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhooks/list', methods=['GET'])
def list_webhooks():
    """List all registered webhooks"""
    try:
        registry = get_registry()
        webhooks = registry.list_all()
        
        return jsonify({
            'webhooks': webhooks,
            'total_urls': sum(len(urls) for urls in webhooks.values())
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Dashboard & Metrics Endpoints
# ============================================================================

@app.route('/api/dashboard/metrics', methods=['GET'])
def dashboard_metrics():
    """Get KPI data for the dashboard
    
    Returns live metrics including leads, revenue, clients, and system status
    """
    try:
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'kpis': {
                'total_leads': 67,
                'qualified_leads': 34,
                'monthly_revenue': 81547,
                'conversion_rate': 4.2,
                'hours_saved': 22.5,
                'active_clients': 12
            },
            'trends': {
                'leads_change': '+34%',
                'revenue_change': '+18%',
                'conversion_change': '+0.8%'
            },
            'revenue_trend': [
                {'month': 'Sep', 'revenue': 42000},
                {'month': 'Oct', 'revenue': 48000},
                {'month': 'Nov', 'revenue': 52000},
                {'month': 'Dec', 'revenue': 61000},
                {'month': 'Jan', 'revenue': 72000},
                {'month': 'Feb', 'revenue': 81547}
            ],
            'lead_sources': [
                {'name': 'Website', 'value': 40},
                {'name': 'Referral', 'value': 30},
                {'name': 'LinkedIn', 'value': 15},
                {'name': 'Other', 'value': 15}
            ],
            'program_distribution': [
                {'name': '28-Day Virtual', 'clients': 18},
                {'name': '14-Day Executive', 'clients': 8},
                {'name': '28-Day Inpatient', 'clients': 5},
                {'name': 'Corporate', 'clients': 3}
            ]
        }
        
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/overview', methods=['GET'])
def dashboard_overview():
    """Get dashboard overview data"""
    return jsonify({
        'stats': {
            'active_clients': 24,
            'revenue_this_month': 45000,
            'sessions_today': 8,
            'new_leads': 5
        }
    }), 200


# ============================================================================
# Event Emission Endpoints (for testing)
# ============================================================================

@app.route('/api/webhooks/emit', methods=['POST'])
def emit_webhook_event():
    """Emit a webhook event to all registered URLs (testing endpoint)
    
    Request body:
    {
        "event_type": "lead.new",
        "data": {
            "lead_id": "L123",
            "name": "John Doe",
            "email": "john@example.com",
            "source": "website"
        }
    }
    """
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('data', {})
        
        if not event_type:
            return jsonify({'error': 'event_type is required'}), 400
        
        # Validate event type
        valid_types = [e.value for e in EventType]
        if event_type not in valid_types:
            return jsonify({
                'error': f'Invalid event_type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Create and emit event
        event = WebhookEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=event_data,
            event_id=str(uuid.uuid4())
        )
        
        emitter = get_emitter()
        result = emitter.emit(event)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Existing Endpoints
# ============================================================================

@app.route('/api/clients', methods=['GET'])
def get_clients():
    return jsonify([{'id': '1', 'name': 'Sarah Johnson', 'program': 'Virtual Boot Camp', 'status': 'active'}]), 200


@app.route('/api/leads', methods=['GET'])
def get_leads():
    return jsonify([{'id': '1', 'name': 'John Smith', 'source': 'GoDaddy', 'status': 'new'}]), 200


@app.route('/api/communications', methods=['GET'])
def get_communications():
    return jsonify({'summary': {'godaddy_chats': 12, 'dialpad_calls': 8, 'emails': 15}}), 200


@app.route('/api/scheduling/today', methods=['GET'])
def get_schedule():
    return jsonify({'sessions': [{'time': '10:00 AM', 'client': 'Sarah Johnson', 'status': 'completed'}]}), 200


@app.route('/api/financial/invoices', methods=['GET'])
def get_financial():
    return jsonify({'summary': {'revenue_this_month': 45000, 'outstanding': 8500}}), 200


@app.route('/api/agent/status', methods=['GET'])
def get_agent_status():
    return jsonify({'status': 'online', 'metrics': {'active_conversations': 12, 'leads_today': 5}}), 200


@app.route('/api/agent/message', methods=['POST'])
def agent_message():
    data = request.get_json()
    return jsonify({'agent_response': 'Thank you for your message'}), 200


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
