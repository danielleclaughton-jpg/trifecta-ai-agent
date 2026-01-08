"""Trifecta AI Agent - Flask Application"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY', 'not-configured')
AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'not-configured')
MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID', 'not-configured')
MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET', 'not-configured')
MS_TENANT_ID = os.environ.get('MS_TENANT_ID', 'not-configured')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
DIALPOD_API_KEY = os.environ.get('DialpodApiKey', 'not-configured')
app.secret_key = SECRET_KEY

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'running', 'service': 'Trifecta AI', 'version': '1.0.0'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/api/dashboard/overview', methods=['GET'])
def dashboard_overview():
    return jsonify({'stats': {'active_clients': 24, 'revenue_this_month': 45000, 'sessions_today': 8, 'new_leads': 5}}), 200

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
