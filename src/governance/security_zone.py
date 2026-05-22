"""
Security Zone — 三層硬切強制器
================================
強制模組只能在所屬層級執行：
- Decision：只能 think / plan / route
- Execution：只能 run_tool / execute
- Memory：只能 read / write

違反時的行為（依等級）：
- LOG  = 記錄但不擋（現階段相容模式）
- WARN = 記錄 + 警告
- BLOCK = 直接拋異常
"""
import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

from governance.event_log import event_log


class SecurityZone:
    """
    Zone 定義：
      decision  → brain, meta_cognition, agents (planning only)
      execution → executor, tools, sub_agent_tools
      memory    → memory, memory_vector
    """
    ZONES = {
        "decision": {"allowed_modules": ["brain", "meta_cognition", "cortex", "thalamus", "hypothalamus"]},
        "execution": {"allowed_modules": ["executor", "tools", "sub_agent_tools", "proactive_executor"]},
        "memory": {"allowed_modules": ["memory", "memory_vector", "civilization_memory"]},
    }

    # 哪些 action 跨區違規
    CROSS_ZONE_ACTIONS = {
        "decision": ["run_tool", "execute_command", "write_file", "modify_code", "modify_config"],
        "execution": ["make_decision", "modify_routing", "modify_plan"],
        "memory": ["trigger_action", "influence_routing", "modify_decision_logic"],
    }

    _lock = threading.Lock()
    _violation_count = 0
    _mode = os.getenv("AMPM_SECURITY_MODE", "LOG")  # LOG | WARN | BLOCK

    def __init__(self):
        self._mode = os.getenv("AMPM_SECURITY_MODE", "LOG")

    @classmethod
    def check(cls, module_name: str, action: str) -> bool:
        """
        檢查 module_name 是否有權執行 action。
        回傳 False = 違規（但依 mode 決定是否擋）。
        """
        # 找出 module 所屬 zone
        module_zone = None
        for zone, config in cls.ZONES.items():
            if any(m in module_name for m in config["allowed_modules"]):
                module_zone = zone
                break

        if not module_zone:
            return True  # 未知模組，放行（但會記錄）

        # 檢查 action 是否跨區
        for zone, forbidden_actions in cls.CROSS_ZONE_ACTIONS.items():
            if zone != module_zone and action in forbidden_actions:
                with cls._lock:
                    cls._violation_count += 1

                msg = f"🔒 [SecurityZone] {module_name} ({module_zone}) 跨區執行 {action}（屬於 {zone} 層）"

                if cls._mode == "BLOCK":
                    from governance.gatekeeper import GatekeeperViolation
                    raise GatekeeperViolation(msg)
                elif cls._mode == "WARN":
                    print(f"⚠️ {msg}")
                else:
                    print(f"📝 {msg}")

                # 記錄到 event log
                event_log.record(
                    source="security_zone",
                    action="cross_zone_violation",
                    input_data={"module": module_name, "action": action, "zone": module_zone},
                    decision=f"mode={cls._mode}",
                )
                return False

        return True

    @classmethod
    def violation_count(cls) -> int:
        with cls._lock:
            return cls._violation_count

    @classmethod
    def set_mode(cls, mode: str):
        if mode in ("LOG", "WARN", "BLOCK"):
            cls._mode = mode
            print(f"🔒 [SecurityZone] 模式切換為 {mode}")


# 快捷函數
def check_permission(module: str, action: str) -> bool:
    """供其他模組在執行關鍵動作前呼叫。"""
    SecurityZone.check(module, action)
    # 同時檢查 permissions.json
    try:
        from governance.gatekeeper import gatekeeper
        return gatekeeper.check_module_permission(module, action)
    except Exception:
        return True
