from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = {}
    actor_id: Optional[str] = None


SubscriptIQEvent = DomainEvent

# Event subscriber registry
_subscribers: Dict[str, List[Callable[[Any], None]]] = {}


def subscribe(event_name: str, handler: Callable[[Any], None]) -> None:
    """Subscribes an async or sync handler to a specific event."""
    if event_name not in _subscribers:
        _subscribers[event_name] = []
    _subscribers[event_name].append(handler)


def publish(event_or_name: Union[DomainEvent, str], payload: Optional[Dict[str, Any]] = None, actor_id: Optional[str] = None) -> DomainEvent:
    """Publishes an event to subscribers supporting both DomainEvent instance and (event_name, payload) arguments."""
    if isinstance(event_or_name, DomainEvent):
        evt = event_or_name
    elif isinstance(event_or_name, str):
        evt = DomainEvent(
            event_name=event_or_name,
            payload=payload or {},
            actor_id=actor_id
        )
    else:
        evt = event_or_name

    handlers = _subscribers.get(evt.event_name, []) + _subscribers.get("*", [])
    for handler in handlers:
        try:
            handler(evt)
        except Exception as e:
            print(f"[EVENT HANDLER ERROR] {evt.event_name}: {e}")
    return evt

