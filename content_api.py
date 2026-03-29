"""
Content Drafts API Blueprint
Handles CRUD + platform posting for Trifecta's content pipeline.
Platforms: linkedin, instagram, facebook, google, wordpress
"""

import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import requests

logger = logging.getLogger(__name__)

_default_db_dir = os.path.join(os.path.dirname(__file__), '..', 'trifecta-ai-agent')
CONTENT_DB_PATH = os.environ.get(
    'CONTENT_DB_PATH',
    os.path.join(_default_db_dir, 'content_drafts.db')
)

content_bp = Blueprint('content', __name__, url_prefix='/api/content')

# ── DB helpers ────────────────────────────────────────────────

def _get_db():
    db_path = CONTENT_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_table(conn)
    return conn

def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_drafts (
            id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            platform TEXT NOT NULL DEFAULT 'linkedin',
            topic TEXT,
            title TEXT,
            body TEXT NOT NULL DEFAULT '',
            hashtags TEXT,
            image_url TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            approved_at TEXT,
            posted_at TEXT,
            post_url TEXT,
            notes TEXT
        )
    """)
    conn.commit()

def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)

# ── Routes ────────────────────────────────────────────────────

@content_bp.route('', methods=['GET'])
def list_drafts():
    """List all content drafts with optional filters."""
    platform = request.args.get('platform')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 200))
    offset = int(request.args.get('offset', 0))

    conditions = []
    params = []
    if platform:
        conditions.append("platform = ?")
        params.append(platform)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    try:
        conn = _get_db()
        rows = conn.execute(
            f"SELECT * FROM content_drafts {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM content_drafts {where}", params).fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'drafts': [_row_to_dict(r) for r in rows], 'total': total})
    except Exception as e:
        logger.error(f"Content list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('', methods=['POST'])
def create_draft():
    """Create a new content draft."""
    data = request.get_json(force=True)
    required = ['platform', 'body']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

    draft_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    try:
        conn = _get_db()
        conn.execute("""
            INSERT INTO content_drafts
                (id, created_at, updated_at, platform, topic, title, body, hashtags, image_url, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?)
        """, (
            draft_id, now, now,
            data['platform'],
            data.get('topic'),
            data.get('title'),
            data['body'],
            data.get('hashtags'),
            data.get('image_url'),
            data.get('notes'),
        ))
        conn.commit()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        conn.close()
        return jsonify({'success': True, 'draft': _row_to_dict(row)}), 201
    except Exception as e:
        logger.error(f"Content create error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('/<draft_id>', methods=['GET'])
def get_draft(draft_id):
    try:
        conn = _get_db()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'error': 'Draft not found'}), 404
        return jsonify({'success': True, 'draft': _row_to_dict(row)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('/<draft_id>', methods=['PUT', 'PATCH'])
def update_draft(draft_id):
    data = request.get_json(force=True)
    allowed = ['platform', 'topic', 'title', 'body', 'hashtags', 'image_url', 'notes', 'status']
    sets = []
    params = []
    for field in allowed:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])
    if not sets:
        return jsonify({'success': False, 'error': 'No fields to update'}), 400
    sets.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(draft_id)
    try:
        conn = _get_db()
        conn.execute(f"UPDATE content_drafts SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'error': 'Draft not found'}), 404
        return jsonify({'success': True, 'draft': _row_to_dict(row)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('/<draft_id>/approve', methods=['POST'])
def approve_draft(draft_id):
    """Mark draft as approved. Does NOT auto-post."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn = _get_db()
        conn.execute(
            "UPDATE content_drafts SET status = 'approved', approved_at = ?, updated_at = ? WHERE id = ?",
            (now, now, draft_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'error': 'Draft not found'}), 404
        return jsonify({'success': True, 'draft': _row_to_dict(row), 'message': 'Draft approved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('/<draft_id>/post', methods=['POST'])
def post_draft(draft_id):
    """
    Post approved content to the platform.
    Currently uses webhook/API calls where credentials are configured;
    falls back to 'queued' status when credentials are not available.
    """
    try:
        conn = _get_db()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Draft not found'}), 404

        draft = _row_to_dict(row)

        if draft['status'] == 'posted':
            conn.close()
            return jsonify({'success': False, 'error': 'Draft already posted'}), 400

        platform = draft['platform']
        result = _post_to_platform(platform, draft)

        now = datetime.now(timezone.utc).isoformat()
        if result.get('success'):
            conn.execute(
                "UPDATE content_drafts SET status = 'posted', posted_at = ?, post_url = ?, updated_at = ? WHERE id = ?",
                (now, result.get('url'), now, draft_id)
            )
        else:
            # Mark as queued so Danielle knows it needs manual posting
            conn.execute(
                "UPDATE content_drafts SET status = 'queued', notes = ?, updated_at = ? WHERE id = ?",
                (f"Auto-post failed: {result.get('error', 'unknown')} — post manually", now, draft_id)
            )
        conn.commit()
        row = conn.execute("SELECT * FROM content_drafts WHERE id = ?", (draft_id,)).fetchone()
        conn.close()
        return jsonify({'success': result.get('success', False), 'draft': _row_to_dict(row), 'result': result})

    except Exception as e:
        logger.error(f"Content post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@content_bp.route('/stats', methods=['GET'])
def stats():
    try:
        conn = _get_db()
        total = conn.execute("SELECT COUNT(*) FROM content_drafts").fetchone()[0]
        by_status = conn.execute(
            "SELECT status, COUNT(*) as count FROM content_drafts GROUP BY status"
        ).fetchall()
        by_platform = conn.execute(
            "SELECT platform, COUNT(*) as count FROM content_drafts GROUP BY platform"
        ).fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'total': total,
            'by_status': [dict(r) for r in by_status],
            'by_platform': [dict(r) for r in by_platform],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Platform posting ──────────────────────────────────────────

def _post_to_platform(platform: str, draft: dict) -> dict:
    """
    Attempt to post to the given platform.
    Returns {'success': bool, 'url': str|None, 'error': str|None}
    """
    try:
        if platform == 'linkedin':
            return _post_linkedin(draft)
        elif platform == 'wordpress':
            return _post_wordpress(draft)
        elif platform in ('facebook', 'instagram'):
            return _post_meta(platform, draft)
        elif platform == 'google':
            return _post_google_business(draft)
        else:
            return {'success': False, 'error': f'Unknown platform: {platform}'}
    except Exception as e:
        logger.error(f"Platform post error ({platform}): {e}")
        return {'success': False, 'error': str(e)}


def _post_linkedin(draft: dict) -> dict:
    access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    person_urn = os.environ.get('LINKEDIN_PERSON_URN')  # e.g. urn:li:person:XXXXX

    if not access_token or not person_urn:
        return {'success': False, 'error': 'LinkedIn credentials not configured (set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN)'}

    body = draft.get('body', '')
    hashtags = draft.get('hashtags', '')
    if hashtags:
        body = f"{body}\n\n{hashtags}"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": body},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=15
    )
    if resp.status_code in (200, 201):
        post_id = resp.headers.get('x-restli-id', '')
        return {'success': True, 'url': f"https://www.linkedin.com/feed/update/{post_id}"}
    return {'success': False, 'error': f"LinkedIn API error {resp.status_code}: {resp.text[:200]}"}


def _post_wordpress(draft: dict) -> dict:
    wp_url = os.environ.get('WORDPRESS_URL', 'https://trifectaaddictionservices.com')
    wp_user = os.environ.get('WORDPRESS_USER')
    wp_password = os.environ.get('WORDPRESS_APP_PASSWORD')

    if not wp_user or not wp_password:
        return {'success': False, 'error': 'WordPress credentials not configured (set WORDPRESS_USER and WORDPRESS_APP_PASSWORD)'}

    body = draft.get('body', '')
    title = draft.get('title') or draft.get('topic') or 'New Post'

    resp = requests.post(
        f"{wp_url}/wp-json/wp/v2/posts",
        auth=(wp_user, wp_password),
        json={
            "title": title,
            "content": body,
            "status": "draft",  # Always draft first — Danielle publishes from WP
            "categories": [],
        },
        timeout=20
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        return {'success': True, 'url': data.get('link', wp_url)}
    return {'success': False, 'error': f"WordPress API error {resp.status_code}: {resp.text[:200]}"}


def _post_meta(platform: str, draft: dict) -> dict:
    """Facebook or Instagram via Meta Graph API."""
    page_id = os.environ.get('META_PAGE_ID')
    access_token = os.environ.get('META_ACCESS_TOKEN')

    if not page_id or not access_token:
        return {'success': False, 'error': f'{platform.capitalize()} Meta credentials not configured (set META_PAGE_ID and META_ACCESS_TOKEN)'}

    body = draft.get('body', '')
    hashtags = draft.get('hashtags', '')
    message = f"{body}\n\n{hashtags}" if hashtags else body

    if platform == 'facebook':
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/feed",
            params={"access_token": access_token},
            json={"message": message},
            timeout=15
        )
        if resp.status_code == 200:
            post_id = resp.json().get('id', '')
            return {'success': True, 'url': f"https://www.facebook.com/{post_id}"}
        return {'success': False, 'error': f"Facebook API error {resp.status_code}: {resp.text[:200]}"}

    else:  # instagram
        ig_id = os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID', page_id)
        # Step 1: create container
        container_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_id}/media",
            params={"access_token": access_token},
            json={"caption": message, "media_type": "IMAGE" if draft.get('image_url') else None},
            timeout=15
        )
        if container_resp.status_code != 200:
            return {'success': False, 'error': f"Instagram container error: {container_resp.text[:200]}"}
        container_id = container_resp.json().get('id')
        # Step 2: publish
        pub_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_id}/media_publish",
            params={"access_token": access_token},
            json={"creation_id": container_id},
            timeout=15
        )
        if pub_resp.status_code == 200:
            return {'success': True, 'url': 'https://www.instagram.com/trifectarecovery/'}
        return {'success': False, 'error': f"Instagram publish error: {pub_resp.text[:200]}"}


def _post_google_business(draft: dict) -> dict:
    """Post to Google Business Profile via GBP API."""
    # TODO: Implement Google Business Profile API posting
    # Requires Google OAuth2 credentials and account/location IDs
    account_id = os.environ.get('GOOGLE_BUSINESS_ACCOUNT_ID')
    location_id = os.environ.get('GOOGLE_BUSINESS_LOCATION_ID')
    access_token = os.environ.get('GOOGLE_BUSINESS_ACCESS_TOKEN')

    if not account_id or not location_id or not access_token:
        return {'success': False, 'error': 'Google Business credentials not configured (set GOOGLE_BUSINESS_ACCOUNT_ID, GOOGLE_BUSINESS_LOCATION_ID, GOOGLE_BUSINESS_ACCESS_TOKEN)'}

    body = draft.get('body', '')
    resp = requests.post(
        f"https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations/{location_id}/localPosts",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={
            "languageCode": "en-US",
            "summary": body[:1500],  # GBP limit
            "callToAction": {
                "actionType": "LEARN_MORE",
                "url": "https://trifectaaddictionservices.com"
            },
            "topicType": "STANDARD"
        },
        timeout=15
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        return {'success': True, 'url': data.get('searchUrl', 'https://trifectaaddictionservices.com')}
    return {'success': False, 'error': f"Google Business API error {resp.status_code}: {resp.text[:200]}"}
