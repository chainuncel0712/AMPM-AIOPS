"""
Organ Registry v2 — 器官註冊、版本、健康、依賴管理
=====================================================
"""

import threading
from typing import Any, Callable, Dict, List, Optional

from skeleton.registry import Registry


class OrganRegistry:
    """
    Organ Registry v2 with multi-organ registration, versioning,
    health status, dependency management, and lazy loading.
    """

    def __init__(self):
        self._registry = Registry()
        self._lock = threading.RLock()
        self._organs: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._versions: Dict[str, int] = {}
        self._dependencies: Dict[str, List[str]] = {}

    def add(self, organ, name: str = None) -> Any:
        result = self._registry.add(organ)
        key = name or organ.__class__.__name__
        with self._lock:
            self._organs[key] = result
            self._versions[key] = self._versions.get(key, 0) + 1
        return result

    def register_factory(self, name: str, factory: Callable[[], Any], depends_on: List[str] = None) -> None:
        """註冊懶載入器官 — 首次 get() 時才實例化"""
        with self._lock:
            self._factories[name] = factory
            if depends_on:
                self._dependencies[name] = depends_on

    def remove(self, name: str) -> bool:
        with self._lock:
            if name in self._organs:
                del self._organs[name]
                self._versions[name] = self._versions.get(name, 0) + 1
                return True
            self._factories.pop(name, None)
        return False

    def get(self, name: str) -> Any:
        with self._lock:
            organ = self._organs.get(name)
            if organ is not None:
                return organ
            factory = self._factories.get(name)
            if factory is not None:
                instance = factory()
                self._organs[name] = instance
                self._versions[name] = self._versions.get(name, 0) + 1
                del self._factories[name]
                return instance
        return None

    def all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._organs)

    def count(self) -> int:
        with self._lock:
            return len(self._organs)

    def get_version(self, name: str) -> int:
        return self._versions.get(name, 0)

    def declare_dependency(self, organ_name: str, depends_on: List[str]):
        with self._lock:
            self._dependencies[organ_name] = depends_on

    def get_dependencies(self, name: str) -> List[str]:
        return self._dependencies.get(name, [])

    def get_dependents(self, name: str) -> List[str]:
        with self._lock:
            return [k for k, v in self._dependencies.items() if name in v]

    def health_check(self) -> List[Dict]:
        results = []
        for name, organ in self.all().items():
            status = "alive"
            error = ""
            try:
                if hasattr(organ, "is_alive") and callable(organ.is_alive):
                    if not organ.is_alive():
                        status = "dead"
            except Exception as e:
                status = "error"
                error = str(e)[:100]

            dep_status = []
            for dep in self.get_dependencies(name):
                dep_organ = self._organs.get(dep)
                if dep_organ is None:
                    dep_status.append({"name": dep, "status": "missing"})
                elif hasattr(dep_organ, "is_alive") and not dep_organ.is_alive():
                    dep_status.append({"name": dep, "status": "dead"})
                else:
                    dep_status.append({"name": dep, "status": "alive"})

            results.append({
                "name": name,
                "status": status,
                "error": error,
                "type": organ.__class__.__name__,
                "version": self.get_version(name),
                "dependencies": dep_status,
            })
        return results

    def get_stats(self) -> Dict:
        with self._lock:
            alive = dead = error = 0
            for h in self.health_check():
                if h["status"] == "alive":
                    alive += 1
                elif h["status"] == "dead":
                    dead += 1
                else:
                    error += 1
            return {
                "total": len(self._organs),
                "alive": alive,
                "dead": dead,
                "error": error,
                "versions": dict(self._versions),
                "dependencies": dict(self._dependencies),
            }
