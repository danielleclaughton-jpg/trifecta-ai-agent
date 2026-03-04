# Webhook Integration Guide

## Overview

The Trifecta AI Agent now includes comprehensive webhook support for real-time event notifications. This enables the backend to push events to registered frontend applications (like lamby-command-center) whenever important business events occur.

## Event Types

The following event types are supported:

| Event Type | Description |
|-----------|-------------|
| `lead.new` | New lead submitted |
| `lead.qualified` | Lead qualified for program |
| `client.intake` | Client intake form completed |
| `client.activity` | Client activity update |
| `appointment.scheduled` | Appointment scheduled |
| `payment.received` | Payment received |
| `session.completed` | Therapy session completed |
| `alert.new` | New system alert |
| `metrics.updated` | Dashboard metrics updated |

## API Endpoints

### Register a Webhook

**Endpoint:** `POST /api/webhooks/register`

Register a webhook URL to receive events.

**Request:**
```json
{
  "webhook_url": "https://lamby.example.com/api/webhooks/receiver",
  "event_types": ["lead.new", "payment.received"]
}
```

**Response:**
```json
{
  "status": "registered",
  "webhook_url": "https://lamby.example.com/api/webhooks/receiver",
  "event_types": ["lead.new", "payment.received"]
}
```

### Unregister a Webhook

**Endpoint:** `POST /api/webhooks/unregister`

Unregister a webhook URL.

**Request:**
```json
{
  "webhook_url": "https://lamby.example.com/api/webhooks/receiver",
  "event_types": ["lead.new"]
}
```

### List Available Event Types

**Endpoint:** `GET /api/webhooks/events`

Get all available webhook event types.

**Response:**
```json
{
  "event_types": [
    "lead.new",
    "lead.qualified",
    "client.intake",
    "client.activity",
    "appointment.scheduled",
    "payment.received",
    "session.completed",
    "alert.new",
    "metrics.updated"
  ],
  "count": 9,
  "description": "Available webhook event types for subscription"
}
```

### List Registered Webhooks

**Endpoint:** `GET /api/webhooks/list`

Get all currently registered webhooks.

**Response:**
```json
{
  "webhooks": {
    "lead.new": ["https://lamby.example.com/api/webhooks/receiver"],
    "payment.received": ["https://lamby.example.com/api/webhooks/receiver"]
  },
  "total_urls": 2
}
```

### Get Dashboard Metrics

**Endpoint:** `GET /api/dashboard/metrics`

Get KPI data for the dashboard.

**Response:**
```json
{
  "timestamp": "2026-02-19T10:30:00.000000",
  "kpis": {
    "total_leads": 67,
    "qualified_leads": 34,
    "monthly_revenue": 81547,
    "conversion_rate": 4.2,
    "hours_saved": 22.5,
    "active_clients": 12
  },
  "trends": {
    "leads_change": "+34%",
    "revenue_change": "+18%",
    "conversion_change": "+0.8%"
  },
  "revenue_trend": [...],
  "lead_sources": [...],
  "program_distribution": [...]
}
```

### Emit a Webhook Event (Testing)

**Endpoint:** `POST /api/webhooks/emit`

Emit a webhook event to all registered URLs (for testing).

**Request:**
```json
{
  "event_type": "lead.new",
  "data": {
    "lead_id": "L123",
    "name": "John Doe",
    "email": "john@example.com",
    "source": "website"
  }
}
```

**Response:**
```json
{
  "status": "emitted",
  "event_type": "lead.new",
  "delivered": 1,
  "total": 1,
  "results": [
    {
      "url": "https://lamby.example.com/api/webhooks/receiver",
      "status": 200,
      "success": true
    }
  ]
}
```

## Webhook Payload Format

All webhook events are sent as POST requests with the following structure:

```json
{
  "event_type": "lead.new",
  "timestamp": "2026-02-19T10:30:00.000000",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "lead_id": "L123",
    "name": "John Doe",
    "email": "john@example.com",
    "source": "website"
  }
}
```

## Security: HMAC-SHA256 Signatures

All webhook payloads are signed with HMAC-SHA256 to ensure authenticity and integrity.

### Signature Verification

Each webhook request includes the following headers:

- `X-Webhook-Signature`: HMAC-SHA256 signature of the JSON payload
- `X-Webhook-Event`: The event type (e.g., "lead.new")
- `Content-Type`: "application/json"

### Verifying Signatures

To verify a webhook signature:

1. Get the raw JSON payload from the request body
2. Get the signature from the `X-Webhook-Signature` header
3. Compute HMAC-SHA256 of the payload using your secret key
4. Compare with the signature using constant-time comparison

**Python Example:**
```python
import hmac
import hashlib
import json

def verify_webhook(payload_str, signature, secret_key):
    expected_signature = hmac.new(
        secret_key.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

# Usage
payload = json.dumps(request.json)
signature = request.headers.get('X-Webhook-Signature')
secret = 'your-webhook-secret'

if verify_webhook(payload, signature, secret):
    print("Webhook verified!")
else:
    print("Webhook verification failed!")
```

**Node.js Example:**
```javascript
const crypto = require('crypto');

function verifyWebhook(payloadStr, signature, secretKey) {
  const expectedSignature = crypto
    .createHmac('sha256', secretKey)
    .update(payloadStr)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signature)
  );
}

// Usage
const payload = JSON.stringify(req.body);
const signature = req.headers['x-webhook-signature'];
const secret = 'your-webhook-secret';

if (verifyWebhook(payload, signature, secret)) {
  console.log('Webhook verified!');
} else {
  console.log('Webhook verification failed!');
}
```

## Configuration

### Environment Variables

Set the following environment variables to configure webhooks:

```bash
# Webhook secret key for HMAC-SHA256 signatures
WEBHOOK_SECRET=your-secret-key-here

# Optional: Pre-register a webhook URL on startup
WEBHOOK_URL=https://lamby.example.com/api/webhooks/receiver
```

## Integration with lamby-command-center

The lamby-command-center frontend is configured to:

1. Register its webhook receiver endpoint with the backend
2. Receive webhook events in real-time
3. Use Socket.IO to push events to the React frontend
4. Display live data with "LIVE" badges
5. Show toast notifications for incoming events

See the lamby-command-center documentation for frontend integration details.

## Best Practices

1. **Idempotency**: Implement idempotent event handlers in case of duplicate deliveries
2. **Retry Logic**: Implement exponential backoff for failed webhook deliveries
3. **Timeout Handling**: Set appropriate timeouts for webhook requests (default: 10 seconds)
4. **Logging**: Log all webhook events for debugging and auditing
5. **Security**: Always verify HMAC signatures before processing webhooks
6. **Rate Limiting**: Implement rate limiting if receiving high volumes of events

## Troubleshooting

### Webhooks Not Being Delivered

1. Check that the webhook URL is registered: `GET /api/webhooks/list`
2. Verify the webhook URL is accessible from the backend server
3. Check firewall/network rules
4. Review server logs for connection errors

### Signature Verification Failing

1. Ensure you're using the correct secret key
2. Verify you're using the raw JSON payload (not parsed)
3. Check that you're using constant-time comparison
4. Ensure the signature header is being read correctly

### High Latency

1. Increase the timeout value if needed
2. Implement async webhook delivery
3. Use a message queue (e.g., Redis, RabbitMQ) for better throughput
