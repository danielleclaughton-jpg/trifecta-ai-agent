import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set dummy env vars before importing app
os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key')
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('SKILL_DIR', 'Assets/skills')
os.environ.setdefault('INTERNAL_API_KEY', '')

from app import app, load_skills, match_skill, SKILLS


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestHealthEndpoints:
    def test_root_returns_running(self, client):
        r = client.get('/')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['status'] == 'running'

    def test_health_endpoint_exists(self, client):
        r = client.get('/health')
        assert r.status_code in [200, 503]
        data = json.loads(r.data)
        assert 'status' in data
        assert 'services' in data


class TestSkillsEndpoints:
    def test_skills_loaded(self, client):
        r = client.get('/api/skills')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'count' in data
        assert data['count'] >= 0

    def test_skill_not_found_returns_404(self, client):
        r = client.get('/api/skills/nonexistent-skill-xyz')
        assert r.status_code == 404

    def test_invalid_skill_name_rejected(self, client):
        r = client.get('/api/skills/../etc/passwd')
        assert r.status_code in [400, 404]


class TestChatEndpoint:
    def test_chat_requires_json(self, client):
        r = client.post('/api/chat', data='not json',
                        content_type='text/plain')
        assert r.status_code == 400

    def test_chat_requires_message_field(self, client):
        r = client.post('/api/chat',
                        data=json.dumps({}),
                        content_type='application/json')
        assert r.status_code == 400

    def test_chat_rejects_empty_message(self, client):
        r = client.post('/api/chat',
                        data=json.dumps({'message': '   '}),
                        content_type='application/json')
        assert r.status_code == 400

    def test_chat_rejects_oversized_message(self, client):
        r = client.post('/api/chat',
                        data=json.dumps({'message': 'x' * 3000}),
                        content_type='application/json')
        assert r.status_code == 413


class TestSkillMatching:
    def test_skill_loading(self):
        load_skills()
        # Skills may or may not be present depending on environment
        assert isinstance(SKILLS, dict)

    def test_match_skill_returns_none_on_empty(self):
        result = match_skill('xyzzy frobinator nonsense 12345')
        assert result is None


class TestDashboardEndpoints:
    def test_dashboard_overview_exists(self, client):
        r = client.get('/api/dashboard/overview')
        assert r.status_code in [200, 500]
        data = json.loads(r.data)
        assert 'timestamp' in data

    def test_agent_status_returns_online(self, client):
        r = client.get('/api/agent/status')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['status'] == 'online'


class TestRateLimiting:
    def test_rate_limit_allows_normal_traffic(self, client):
        for _ in range(5):
            r = client.post('/api/chat',
                            data=json.dumps({'message': 'test'}),
                            content_type='application/json')
            # 400 is fine (no Anthropic key in test), 429 is not
            assert r.status_code != 429


class TestSecurity:
    def test_404_returns_json(self, client):
        r = client.get('/nonexistent-endpoint-xyz')
        assert r.status_code == 404
        data = json.loads(r.data)
        assert 'error' in data

    def test_request_id_header_present(self, client):
        r = client.get('/')
        assert 'X-Request-Id' in r.headers
