"""
Stable Mode — 生產鎖定模式
=============================
啟用後強制：
  - 禁止 self-modify（code / prompt / config）
  - 禁止 dynamic routing change
  - 禁止 plugin auto-load
  - 禁止 memory schema change

Toggle：透過 env AMPM_STABLE_MODE=1 或 runtime API。
"""
import os
import threading
from datetime import datetime
from typing import Dict, List


class StableModeViolation(Exception):
    pass


class StableMode:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._active = False
                    cls._instance._activated_at: str = ""
                    cls._instance._denied: List[str] = []
                    cls._instance._protections = {
                        "self_modify": True,
                        "dynamic_routing": True,
                        "plugin_autoload": True,
                        "memory_schema_change": True,
                        "dynamic_permission_change": True,
                    }
        return cls._instance

    def activate(self):
        with self._lock:
            self._active = True
            self._activated_at = datetime.now().isoformat()
            print(f"🔒 [StableMode] ✅ 生產鎖定已啟用")
            from governance.event_log import event_log
            event_log.record(
                source="stable_mode", action="activated",
                input_data={"protections": list(self._protections.keys())},
                decision="STABLE_MODE_ON",
                rollback_point=True,
            )

    def deactivate(self):
        with self._lock:
            self._active = False
            print(f"🔒 [StableMode] ⚠️ 生產鎖定已解除")
            from governance.event_log import event_log
            event_log.record(
                source="stable_mode", action="deactivated",
                decision="STABLE_MODE_OFF",
            )

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    def check(self, operation: str) -> bool:
        """
        檢查 operation 是否被生產鎖定禁止。
        若禁止且鎖定中，記錄違規並拋異常 / 回傳 False。
        """
        if not self._active:
            return True

        mapping = {
            "modify_code": "self_modify",
            "modify_prompt": "self_modify",
            "modify_config": "self_modify",
            "modify_routing": "dynamic_routing",
            "auto_load_plugin": "plugin_autoload",
            "modify_memory_schema": "memory_schema_change",
            "change_permissions": "dynamic_permission_change",
        }

        protection = mapping.get(operation)
        if protection and self._protections.get(protection, True):
            with self._lock:
                self._denied.append(operation)
            msg = f"🔒 [StableMode] 生產鎖定中，禁止操作: {operation}（違反 {protection}）"
            print(f"❌ {msg}")

            from governance.event_log import event_log
            event_log.record(
                source="stable_mode",
                action=f"denied:{operation}",
                input_data={"operation": operation, "protection": protection},
                decision="STABLE_MODE_BLOCKED",
            )

            if os.getenv("AMPM_STABLE_MODE", "0") == "2":  # 嚴格模式
                raise StableModeViolation(msg)
            return False

        return True

    def status(self) -> Dict:
        with self._lock:
            return {
                "active": self._active,
                "activated_at": self._activated_at,
                "protections": dict(self._protections),
                "denied_count": len(self._denied),
                "recent_denied": self._denied[-10:] if self._denied else [],
            }


# Auto-activate from env
_stable = StableMode()
if os.getenv("AMPM_STABLE_MODE", "0") in ("1", "2"):
    _stable.activate()

stable = _stable
