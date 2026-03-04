"""Webhook Management and Event Emitter for Trifecta AI Agent"""
import os
import json
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Event Types
class EventType(Enum):
    """Supported webhook event types"""
    LEAD_NEW = "lead.new"
    LEAD_QUALIFIED = "lead.qualified"
    CLIENT_INTAKE = "client.intake"
    CLIENT_ACTIVITY = "client.activity"
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    PAYMENT_RECEIVED = "payment.received"
    SESSION_COMPLETED = "session.completed"
    ALERT_NEW = "alert.new"
    METRICS_UPDATED = "metrics.updated"


@dataclass
class WebhookEvent:
    """Webhook event payload structure"""
    event_type: str
    timestamp: str
    data: Dict[str, Any]
    event_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class WebhookRegistry:
    """In-memory webhook URL registry"""
    
    def __init__(self):
        self.webhooks: Dict[str, List[str]] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Load webhook URLs from environment variables"""
        webhook_url = os.environ.get('WEBHOOK_URL')
        if webhook_url:
            self.register(webhook_url)
    
    def register(self, webhook_url: str, event_types: Optional[List[str]] = None) -> Dict:
        """Register a webhook URL for specific event types"""
        if event_types is None:
            event_types = [e.value for e in EventType]
        
        for event_type in event_types:
            if event_type not in self.webhooks:
                self.webhooks[event_type] = []
            if webhook_url not in self.webhooks[event_type]:
                self.webhooks[event_type].append(webhook_url)
        
        return {
            "status": "registered",
            "webhook_url": webhook_url,
            "event_types": event_types
        }
    
    def unregister(self, webhook_url: str, event_types: Optional[List[str]] = None) -> Dict:
        """Unregister a webhook URL"""
        if event_types is None:
            event_types = [e.value for e in EventType]
        
        for event_type in event_types:
            if event_type in self.webhooks and webhook_url in self.webhooks[event_type]:
                self.webhooks[event_type].remove(webhook_url)
        
        return {
            "status": "unregistered",
            "webhook_url": webhook_url,
            "event_types": event_types
        }
    
    def get_webhooks_for_event(self, event_type: str) -> List[str]:
        """Get all registered webhooks for a specific event type"""
        return self.webhooks.get(event_type, [])
    
    def list_all(self) -> Dict:
        """List all registered webhooks"""
        return self.webhooks
    
    def get_event_types(self) -> List[str]:
        """Get all available event types"""
        return [e.value for e in EventType]


class WebhookSigner:
    """HMAC-SHA256 signature generation and verification"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.environ.get('WEBHOOK_SECRET', 'dev-secret-key')
    
    def sign(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for payload"""
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify(self, payload: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        expected_signature = self.sign(payload)
        return hmac.compare_digest(expected_signature, signature)


class WebhookEmitter:
    """Emit webhook events to registered URLs"""
    
    def __init__(self, registry: WebhookRegistry, signer: WebhookSigner):
        self.registry = registry
        self.signer = signer
        self.timeout = 10  # seconds
    
    def emit(self, event: WebhookEvent) -> Dict[str, Any]:
        """Emit a webhook event to all registered URLs"""
        webhooks = self.registry.get_webhooks_for_event(event.event_type)
        
        if not webhooks:
            return {
                "status": "no_webhooks",
                "event_type": event.event_type,
                "delivered": 0
            }
        
        payload = json.dumps(event.to_dict())
        signature = self.signer.sign(payload)
        
        results = []
        for webhook_url in webhooks:
            try:
                response = requests.post(
                    webhook_url,
                    json=event.to_dict(),
                    headers={
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": event.event_type,
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout
                )
                results.append({
                    "url": webhook_url,
                    "status": response.status_code,
                    "success": response.status_code < 400
                })
            except requests.RequestException as e:
                results.append({
                    "url": webhook_url,
                    "status": "error",
                    "error": str(e),
                    "success": False
                })
        
        return {
            "status": "emitted",
            "event_type": event.event_type,
            "delivered": sum(1 for r in results if r.get("success")),
            "total": len(results),
            "results": results
        }


# Global instances
_registry: Optional[WebhookRegistry] = None
_signer: Optional[WebhookSigner] = None
_emitter: Optional[WebhookEmitter] = None


def get_registry() -> WebhookRegistry:
    """Get or create webhook registry"""
    global _registry
    if _registry is None:
        _registry = WebhookRegistry()
    return _registry


def get_signer() -> WebhookSigner:
    """Get or create webhook signer"""
    global _signer
    if _signer is None:
        _signer = WebhookSigner()
    return _signer


def get_emitter() -> WebhookEmitter:
    """Get or create webhook emitter"""
    global _emitter
    if _emitter is None:
        _emitter = WebhookEmitter(get_registry(), get_signer())
    return _emitter
