"""
Port Registry for Dependency Inversion.
Modules register implementations in bootstrap.py.
If not registered, defaults to high-fidelity Fakes in fakes.py.
"""
from typing import Any, Dict

_REGISTRY: Dict[str, Any] = {}

def register_port(name: str, implementation: Any) -> None:
    """Registers an implementation of a shared port."""
    _REGISTRY[name] = implementation

def get_port(name: str) -> Any:
    """Retrieves the registered port or loads the fallback fake."""
    if name in _REGISTRY:
        return _REGISTRY[name]
    
    # Auto-load fake
    from backend.app.shared.fakes import get_fake_port
    fake = get_fake_port(name)
    _REGISTRY[name] = fake
    return fake

def clear_registry() -> None:
    """Clears registry (useful for unit test resets)."""
    _REGISTRY.clear()
