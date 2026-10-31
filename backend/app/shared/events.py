from datetime import datetime, timezone
from typing import Dict, Any, Callable, List
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    event_name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = {}

# Event subscriber registry
_subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}

def subscribe(event_name: str, handler: Callable[[DomainEvent], None]):
    if event_name not in _subscribers:
        _subscribers[event_name] = []
    _subscribers[event_name].append(handler)

def publish(event: DomainEvent):
    handlers = _subscribers.get(event.event_name, [])
    for handler in handlers:
        try:
            handler(event)
        except Exception as e:
            print(f"Error handling event {event.event_name}: {e}")
