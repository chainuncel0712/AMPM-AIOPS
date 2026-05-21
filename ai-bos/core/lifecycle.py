"""
Lifecycle 生命週期管理
=========================
"""
from datetime import datetime
from typing import Any, Dict, List


class Lifecycle:
    """器官生命週期管理員"""

    def __init__(self):
        self._registry: Dict[str, Any] = {}
        self._events: List[Dict] = []

    def register(self, name: str, organ: Any) -> Any:
        self._registry[name] = organ
        self._log("register", name)
        return organ

    def unregister(self, name: str):
        self._registry.pop(name, None)
        self._log("unregister", name)

    def get(self, name: str) -> Any:
        return self._registry.get(name)

    def all(self) -> Dict[str, Any]:
        return dict(self._registry)

    def health_check(self) -> List[Dict]:
        results = []
        for name, organ in self._registry.items():
            status = "alive"
            try:
                if hasattr(organ, "is_alive") and not organ.is_alive():
                    status = "dead"
            except Exception:
                status = "error"
            results.append({"name": name, "status": status})
        return results

    def _log(self, action: str, name: str):
        self._events.append({
            "action": action,
            "organ": name,
            "timestamp": datetime.now().isoformat(),
        })
