from typing import Any, Dict

_ports: Dict[str, Any] = {}


def register_port(name: str, implementation: Any) -> None:
    _ports[name] = implementation


def get_port(name: str) -> Any:
    if name not in _ports:
        from app.shared.fakes import get_fake_port
        fake = get_fake_port(name)
        _ports[name] = fake
        return fake
    return _ports[name]


def clear_registry() -> None:
    """Clears registry (useful for unit test resets)."""
    _ports.clear()

