"""
審計層 — 所有行為的完整可追蹤記錄
=====================================
統一封裝 EventLog + AuditLayer，提供：
- event_log() — 通用事件記錄
- tool_usage_log() — 工具使用記錄
- repair_log() — 修復記錄
- evolution_log() — 演化記錄
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class AuditLogger:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir

    def event_log(self, source: str, action: str, input_data: Any = None,
                  output: Any = None, parent_id: str = "",
                  duration_ms: float = 0.0) -> str:
        """通用事件記錄，回傳 action_id"""
        try:
            from governance.event_log import EventLog
            EventLog().record(
                source=source,
                action=action,
                input_data=input_data,
                output=output,
                parent_id=parent_id or None,
                duration_ms=duration_ms,
            )
            import hashlib
            return hashlib.sha256(f"{source}{action}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        except Exception as e:
            return f""

    def tool_usage_log(self, tool_name: str, agent: str, args: Dict = None,
                       result: str = "", success: bool = True,
                       duration_ms: float = 0.0) -> str:
        """工具使用記錄"""
        return self.event_log(
            source=f"tool:{agent}",
            action=f"tool_use:{tool_name}",
            input_data=args or {},
            output={"success": success, "result": str(result)[:200]},
            duration_ms=duration_ms,
        )

    def repair_log(self, repair_type: str, trigger: str = "",
                   params: Dict = None, result: Dict = None) -> str:
        """修復記錄"""
        return self.event_log(
            source="repair_orchestrator",
            action=f"repair:{repair_type}",
            input_data={"trigger": trigger, "params": params or {}},
            output=result or {},
        )

    def evolution_log(self, change_type: str, description: str,
                      version: int = 0, reasoning: str = "") -> str:
        """演化記錄"""
        return self.event_log(
            source="evolution",
            action=f"evolve:{change_type}",
            input_data={"description": description[:200], "reasoning": reasoning[:200]},
            output={"version": version},
        )

    def get_recent(self, source: str = None, limit: int = 20) -> List[Dict]:
        """取得最近的審計記錄"""
        try:
            from governance.event_log import EventLog
            if source:
                return EventLog().get_by_source(source, limit)
            all_events = []
            for s in ["decision", "tool", "memory", "repair_orchestrator",
                       "evolution", "gatekeeper"]:
                all_events.extend(EventLog().get_by_source(s, limit // 6 + 1))
            return all_events[:limit]
        except Exception:
            return []

    def query(self, action_id: str) -> Dict:
        """查詢單一事件的完整審計軌跡"""
        try:
            from governance.audit import auditor
            return auditor.trace(action_id) or {}
        except Exception:
            return {}
