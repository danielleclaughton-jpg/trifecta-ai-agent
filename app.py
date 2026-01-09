"""
Trifecta AI Agent - Flask Application
Flask-based AI agent API with Azure cognitive services integration
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from anthropic import Anthropic

app = Flask(__name__)
CORS(app)

# Environment variables for Azure services
AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY', 'not-configured')
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'eastus')
MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID', 'not-configured')
MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET', 'not-configured')
MS_TENANT_ID = os.environ.get('MS_TENANT_ID', 'not-configured')
GRAPH_CLIENT_SECRET = os.environ.get('GRAPH_CLIENT_SECRET', 'not-configured')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DIALPOD_API_KEY = os.environ.get('DialpodApiKey', 'not-configured')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'not-configured')

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY != 'not-configured' else None

app.secret_key = SECRET_KEY


@app.route('/', methods=['GET'])
def home():
    """Health check and welcome endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'Trifecta AI Agent',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.2.0',
        'message': 'Welcome to Trifecta AI Agent API'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Azure monitoring"""
    services = {
        'azure_speech': AZURE_SPEECH_KEY != 'not-configured',
        'microsoft_graph': MS_CLIENT_ID != 'not-configured',
        'dialpod': DIALPOD_API_KEY != 'not-configured',
        'claude_api': ANTHROPIC_API_KEY != 'not-configured'
    }

    all_healthy = all(services.values())

    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'services': services,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if all_healthy else 503


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current service configuration (no secrets)"""
    return jsonify({
        'services': {
            'azure_speech': {
                'configured': AZURE_SPEECH_KEY != 'not-configured',
                'region': AZURE_SPEECH_REGION
            },
            'microsoft_graph': {
                'configured': MS_CLIENT_ID != 'not-configured',
                'tenant_id': MS_TENANT_ID
            },
            'dialpod': {
                'configured': DIALPOD_API_KEY != 'not-configured'
            },
            'claude_api': {
                'configured': ANTHROPIC_API_KEY != 'not-configured'
            }
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/agent/message', methods=['POST'])
def agent_message():
    """Process a message through the AI agent"""
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Placeholder for actual AI processing
        response = {
            'user_message': message,
            'agent_response': f'Processed: {message}',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending_ai_implementation'
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for TrifectaAI chatbot with Claude API integration"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_history = data.get('conversationHistory', [])

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Check if Anthropic client is configured
        if not anthropic_client:
            return jsonify({
                'error': 'Claude API not configured',
                'status': 'missing_credentials'
            }), 503

        # Build messages array from conversation history
        messages = []
        if conversation_history:
            for entry in conversation_history:
                if entry.get('role') and entry.get('content'):
                    messages.append({
                        'role': entry['role'],
                        'content': entry['content']
                    })

        # Add current user message
        messages.append({
            'role': 'user',
            'content': message
        })

        # System prompt for Dr. Lembe persona
        system_prompt = """You are Dr. Lembe, a compassionate Sober Self Mentor and recovery coach.
Your role is to provide supportive, evidence-based guidance for individuals in recovery from substance use.
You use neuroscience-informed approaches and focus on building awareness, resilience, and healthy coping strategies.
Be warm, empathetic, and encouraging while maintaining professional boundaries.
Focus on empowering the individual and celebrating their progress, no matter how small."""

        # Call Claude API
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        # Extract reply from Claude response
        reply = response.content[0].text

        return jsonify({
            'reply': reply,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# CONTRACT & INVOICE GENERATOR ENDPOINTS
# ============================================

@app.route('/api/documents/contract', methods=['POST'])
def generate_contract():
    """Generate a client contract using Claude AI"""
    try:
        data = request.get_json()
        client_name = data.get('client_name', '')
        service_type = data.get('service_type', 'Recovery Coaching')
        start_date = data.get('start_date', datetime.utcnow().strftime('%Y-%m-%d'))
        duration = data.get('duration', '12 weeks')
        rate = data.get('rate', '$150/session')
        custom_terms = data.get('custom_terms', '')

        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400

        if not anthropic_client:
            return jsonify({'error': 'Claude API not configured'}), 503

        # Generate contract using Claude
        contract_prompt = f"""Generate a professional service agreement contract for Trifecta Addiction and Mental Health Services.

Client Information:
- Client Name: {client_name}
- Service Type: {service_type}
- Start Date: {start_date}
- Duration: {duration}
- Rate: {rate}
- Custom Terms: {custom_terms if custom_terms else 'None'}

The contract should include:
1. Introduction and parties involved
2. Scope of services (recovery coaching, DBT sessions, support)
3. Payment terms and cancellation policy
4. Confidentiality clause
5. Client responsibilities
6. Provider responsibilities
7. Termination conditions
8. Liability limitations
9. Signature blocks for both parties
10. Date fields

Make it professional, warm, and recovery-focused. Include Trifecta's mission of empowering clients through neuroscience-informed recovery coaching."""

        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system="You are a professional legal document generator for Trifecta Addiction and Mental Health Services. Generate clear, professional contracts that protect both the client and provider while maintaining a supportive, recovery-focused tone.",
            messages=[{"role": "user", "content": contract_prompt}]
        )

        contract_content = response.content[0].text

        return jsonify({
            'contract': contract_content,
            'client_name': client_name,
            'service_type': service_type,
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'generated'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/invoice', methods=['POST'])
def generate_invoice():
    """Generate a client invoice"""
    try:
        data = request.get_json()
        client_name = data.get('client_name', '')
        client_email = data.get('client_email', '')
        services = data.get('services', [])  # List of {description, quantity, rate}
        invoice_number = data.get('invoice_number', f"TRI-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        due_date = data.get('due_date', '')
        notes = data.get('notes', '')

        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400

        if not services:
            return jsonify({'error': 'At least one service is required'}), 400

        # Calculate totals
        subtotal = 0
        line_items = []
        for service in services:
            description = service.get('description', 'Service')
            quantity = float(service.get('quantity', 1))
            rate = float(service.get('rate', 0))
            amount = quantity * rate
            subtotal += amount
            line_items.append({
                'description': description,
                'quantity': quantity,
                'rate': rate,
                'amount': amount
            })

        # For now, no tax (healthcare services often tax-exempt)
        tax_rate = 0
        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount

        invoice = {
            'invoice_number': invoice_number,
            'invoice_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'due_date': due_date or (datetime.utcnow().strftime('%Y-%m-%d')),
            'company': {
                'name': 'Trifecta Addiction and Mental Health Services',
                'address': 'Your Address Here',
                'phone': 'Your Phone Here',
                'email': 'info@trifectaaddictionservices.com',
                'website': 'https://trifectaaddictionservices.com'
            },
            'client': {
                'name': client_name,
                'email': client_email
            },
            'line_items': line_items,
            'subtotal': round(subtotal, 2),
            'tax_rate': tax_rate,
            'tax_amount': round(tax_amount, 2),
            'total': round(total, 2),
            'notes': notes,
            'payment_instructions': 'Payment accepted via bank transfer, credit card, or check. Please reference invoice number with payment.',
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'generated'
        }

        return jsonify(invoice), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/dbt-session', methods=['POST'])
def generate_dbt_session():
    """Generate a personalized DBT session outline using Claude AI"""
    try:
        data = request.get_json()
        client_name = data.get('client_name', '')
        session_number = data.get('session_number', 1)
        focus_area = data.get('focus_area', 'Distress Tolerance')
        previous_homework = data.get('previous_homework', '')
        current_challenges = data.get('current_challenges', '')
        goals = data.get('goals', '')

        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400

        if not anthropic_client:
            return jsonify({'error': 'Claude API not configured'}), 503

        # Generate DBT session outline using Claude
        dbt_prompt = f"""Generate a personalized DBT (Dialectical Behavior Therapy) session outline for a recovery coaching session.

Client: {client_name}
Session Number: {session_number}
Focus Area: {focus_area}
Previous Homework Review: {previous_homework if previous_homework else 'First session or no previous homework'}
Current Challenges: {current_challenges if current_challenges else 'To be discussed'}
Client Goals: {goals if goals else 'To be established'}

Create a structured session outline including:
1. Opening check-in (5-10 min) - How is the client feeling? Any urgent matters?
2. Homework review (10 min) - Review previous week's practice
3. Main skill teaching (20-25 min) - Focus on the {focus_area} module
4. Practice exercise (15 min) - Interactive skill practice
5. Discussion & application (10 min) - How to apply this week
6. Homework assignment (5 min) - Specific practice for the week
7. Closing & next steps (5 min)

Include specific DBT skills relevant to {focus_area}:
- For Distress Tolerance: TIPP, STOP, Radical Acceptance, Self-Soothe
- For Emotion Regulation: PLEASE, ABC, Opposite Action
- For Interpersonal Effectiveness: DEAR MAN, GIVE, FAST
- For Mindfulness: Wise Mind, Observe, Describe, Participate

Make it recovery-focused and neuroscience-informed where applicable."""

        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system="You are Dr. Lembe, a DBT-trained recovery coach. Generate comprehensive, personalized DBT session outlines that integrate neuroscience principles with practical recovery skills.",
            messages=[{"role": "user", "content": dbt_prompt}]
        )

        session_outline = response.content[0].text

        return jsonify({
            'session_outline': session_outline,
            'client_name': client_name,
            'session_number': session_number,
            'focus_area': focus_area,
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'generated'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents/intake', methods=['POST'])
def process_intake():
    """Process client intake form and generate summary"""
    try:
        data = request.get_json()

        # Extract intake form data
        client_info = data.get('client_info', {})
        medical_history = data.get('medical_history', {})
        substance_history = data.get('substance_history', {})
        mental_health = data.get('mental_health', {})
        support_system = data.get('support_system', {})
        goals = data.get('goals', '')

        if not client_info.get('name'):
            return jsonify({'error': 'Client name is required'}), 400

        if not anthropic_client:
            return jsonify({'error': 'Claude API not configured'}), 503

        # Generate intake summary using Claude
        intake_prompt = f"""Analyze the following client intake information and generate a comprehensive intake summary for recovery coaching.

CLIENT INFORMATION:
{json.dumps(client_info, indent=2)}

MEDICAL HISTORY:
{json.dumps(medical_history, indent=2)}

SUBSTANCE USE HISTORY:
{json.dumps(substance_history, indent=2)}

MENTAL HEALTH:
{json.dumps(mental_health, indent=2)}

SUPPORT SYSTEM:
{json.dumps(support_system, indent=2)}

STATED GOALS:
{goals}

Generate:
1. Executive Summary (2-3 paragraphs)
2. Key Risk Factors to Monitor
3. Protective Factors & Strengths
4. Recommended Treatment Focus Areas
5. Suggested DBT Modules to Prioritize
6. Initial Session Recommendations
7. Referral Considerations (if any)
8. Preliminary Treatment Goals

Be thorough, professional, and recovery-focused. Highlight both challenges and strengths."""

        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system="You are Dr. Lembe, a clinical intake specialist for Trifecta Addiction and Mental Health Services. Generate comprehensive, HIPAA-mindful intake summaries that support treatment planning.",
            messages=[{"role": "user", "content": intake_prompt}]
        )

        intake_summary = response.content[0].text

        return jsonify({
            'intake_summary': intake_summary,
            'client_name': client_info.get('name'),
            'intake_date': datetime.utcnow().isoformat(),
            'status': 'processed'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# AZURE SPEECH SERVICES ENDPOINTS
# ============================================

@app.route('/api/speech/recognize', methods=['POST'])
def speech_recognize():
    """Speech-to-text endpoint using Azure Speech Services"""
    if AZURE_SPEECH_KEY == 'not-configured':
        return jsonify({
            'error': 'Azure Speech Services not configured',
            'status': 'missing_credentials'
        }), 503

    return jsonify({
        'status': 'ready',
        'message': 'Speech recognition endpoint ready',
        'region': AZURE_SPEECH_REGION
    }), 200


@app.route('/api/speech/synthesize', methods=['POST'])
def speech_synthesize():
    """Text-to-speech endpoint using Azure Speech Services"""
    if AZURE_SPEECH_KEY == 'not-configured':
        return jsonify({
            'error': 'Azure Speech Services not configured',
            'status': 'missing_credentials'
        }), 503

    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'en-US-JennyNeural')  # Default female voice

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # Return configuration for client-side synthesis
        # Or implement server-side synthesis if needed
        return jsonify({
            'status': 'ready',
            'text': text,
            'voice': voice,
            'region': AZURE_SPEECH_REGION,
            'message': 'Use Azure Speech SDK with these settings'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


if __name__ == '__main__':
    # Get port from environment variable or use 5000
    port = int(os.environ.get('PORT', 5000))
    # Azure App Service requires 0.0.0.0 binding
    app.run(host='0.0.0.0', port=port, debug=False)
