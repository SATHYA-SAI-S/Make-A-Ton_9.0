from typing import Dict, Any

_ports: Dict[str, Any] = {}

def register_port(name: str, impl: Any) -> None:
    _ports[name] = impl

def get_port(name: str) -> Any:
    if name not in _ports:
        from app.shared.fakes import get_fake_port
        return get_fake_port(name)
    return _ports[name]
