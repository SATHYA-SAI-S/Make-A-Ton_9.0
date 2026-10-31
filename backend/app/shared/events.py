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


def publish(event_or_name: Union[DomainEvent, str, None] = None, payload: Optional[Dict[str, Any]] = None, actor_id: Optional[str] = None, event_name: Optional[str] = None, **kwargs) -> DomainEvent:
    """Publishes an event to subscribers supporting both DomainEvent instance and (event_name, payload) arguments."""
    target = event_name or event_or_name
    if isinstance(target, DomainEvent):
        evt = target
    elif isinstance(target, str):
        evt = DomainEvent(
            event_name=target,
            payload=payload or {},
            actor_id=actor_id
        )
    else:
        evt = target

    handlers = _subscribers.get(evt.event_name, []) + _subscribers.get("*", [])
    for handler in handlers:
        try:
            handler(evt)
        except Exception as e:
            print(f"[EVENT HANDLER ERROR] {evt.event_name}: {e}")
    return evt

