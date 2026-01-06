"""
Trifecta AI Agent - Flask Application
Flask-based AI agent API with Azure cognitive services integration
"""

import os
import json
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Environment variables for Azure services
AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY', 'not-configured')
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'not-configured')
MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID', 'not-configured')
MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET', 'not-configured')
MS_TENANT_ID = os.environ.get('MS_TENANT_ID', 'not-configured')
GRAPH_CLIENT_SECRET = os.environ.get('GRAPH_CLIENT_SECRET', 'not-configured')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DIALPOD_API_KEY = os.environ.get('DialpodApiKey', 'not-configured')

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
          'dialpod': DIALPOD_API_KEY != 'not-configured'
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
