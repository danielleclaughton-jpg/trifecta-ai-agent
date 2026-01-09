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
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'not-configured')
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
          'version': '0.1.0',
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


@app.route('/api/speech/recognize', methods=['POST'])
def speech_recognize():
      """Speech-to-text endpoint using Azure Speech Services"""
    if AZURE_SPEECH_KEY == 'not-configured':
              return jsonify({
                            'error': 'Azure Speech Services not configured',
                            'status': 'missing_credentials'
              }), 503

    return jsonify({
              'status': 'pending_implementation',
              'message': 'Speech recognition endpoint ready'
    }), 200


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
