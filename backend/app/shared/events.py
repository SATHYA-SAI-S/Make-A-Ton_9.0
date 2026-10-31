"""
Shared Events across SubscriptIQ.
Event names are strictly standardized as per Document 00 Section 6.2.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

class SubscriptIQEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]
    actor_id: Optional[str] = None

_EVENT_SUBSCRIBERS: Dict[str, List[Any]] = {}

def subscribe(event_name: str, handler: Any) -> None:
    """Subscribes an async or sync handler to a specific event."""
    if event_name not in _EVENT_SUBSCRIBERS:
        _EVENT_SUBSCRIBERS[event_name] = []
    _EVENT_SUBSCRIBERS[event_name].append(handler)

def publish(event_name: str, payload: Dict[str, Any], actor_id: Optional[str] = None) -> SubscriptIQEvent:
    """Publishes an event to subscribers and logs it."""
    evt = SubscriptIQEvent(
        event_name=event_name,
        payload=payload,
        actor_id=actor_id
    )
    # Invoke local subscribers
    handlers = _EVENT_SUBSCRIBERS.get(event_name, []) + _EVENT_SUBSCRIBERS.get("*", [])
    for handler in handlers:
        try:
            handler(evt)
        except Exception as e:
            print(f"[EVENT HANDLER ERROR] {event_name}: {e}")
    return evt
