"""
Organ Registry — 器官註冊與生命維護
=====================================
Handles all organ registration and lifecycle.
Extracted from Obsidian.__init__ for modularity.
"""
import threading
from typing import Any, Dict, List

from skeleton.registry import Registry


class OrganRegistry:
    """
    Wraps skeleton/Registry with Obsidian-specific organ lifecycle.
    All organs register here, then sync to self.organs.
    """

    def __init__(self):
        self._registry = Registry()
        self._lock = threading.RLock()
        self._organs: Dict[str, Any] = {}

    def add(self, organ, name: str = None) -> Any:
        result = self._registry.add(organ)
        key = name or organ.__class__.__name__
        with self._lock:
            self._organs[key] = result
        return result

    def get(self, name: str) -> Any:
        return self._organs.get(name)

    def all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._organs)

    def count(self) -> int:
        with self._lock:
            return len(self._organs)

    def health_check(self) -> List[Dict]:
        results = []
        for name, organ in self.all().items():
            status = "alive"
            try:
                if hasattr(organ, "is_alive") and callable(organ.is_alive):
                    if not organ.is_alive():
                        status = "dead"
            except Exception:
                status = "error"
            results.append({"name": name, "status": status, "type": organ.__class__.__name__})
        return results
