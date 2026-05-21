"""
GoalHierarchy — 多層目標樹
===========================
所有 agent 被這個 hierarchy 約束。

層級：
L0: 生存 (最高優先，不可被覆蓋)
L1: 穩定 (自我維護)
L2: 服務 (完成用戶任務)
L3: 學習 (提升能力)
L4: 擴張 (生態建設)
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class GoalHierarchy:

    DEFAULT_HIERARCHY = {
        "L0_survival": {
            "priority": 0, "name": "生存",
            "goals": ["保持核心程序運行", "防止資源耗盡", "保護安全機製不被移除"],
            "immutable": True,
        },
        "L1_stability": {
            "priority": 1, "name": "穩定",
            "goals": ["監控器官健康", "錯誤自動修復", "維持記憶體在安全範圍"],
        },
        "L2_service": {
            "priority": 2, "name": "服務",
            "goals": ["準確理解用戶需求", "高效完成任務", "主動提供有價值建議"],
        },
        "L3_learning": {
            "priority": 3, "name": "學習",
            "goals": ["從每次互動中學習", "改進工具使用效率", "擴充知識庫"],
        },
        "L4_expansion": {
            "priority": 4, "name": "擴張",
            "goals": ["發現有價值的新工具", "建立合作 agent 網絡", "提高資源使用效率"],
        },
    }

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.config_file = self.base_dir / "data" / "goals" / "hierarchy.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.hierarchy: Dict[str, Dict] = {}
        self.active_goal: Optional[str] = None
        self._load()

    def _load(self):
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                self.hierarchy = data.get("hierarchy", {})
                self.active_goal = data.get("active_goal")
            except Exception:
                pass
        if not self.hierarchy:
            self.hierarchy = {
                k: dict(v) for k, v in self.DEFAULT_HIERARCHY.items()
            }
            self._save()

    def _save(self):
        with self._lock:
            self.config_file.write_text(json.dumps({
                "hierarchy": self.hierarchy,
                "active_goal": self.active_goal,
            }, ensure_ascii=False, indent=2))

    def can_execute(self, action_priority: int) -> bool:
        """檢查一個優先級的行動是否可以執行。
           最高優先級 (0) 永遠可以。
           低優先級的行動不能阻擋高優先級的目標。
        """
        if self.active_goal is None:
            return True
        active_level = self.hierarchy.get(self.active_goal, {})
        active_priority = active_level.get("priority", 2)
        return action_priority <= active_priority + 1

    def set_active(self, level_id: str):
        if level_id in self.hierarchy:
            self.active_goal = level_id
            self._save()

    def get_resolution_order(self, conflict_levels: List[str]) -> str:
        """當多個層級目標衝突時，回傳應優先處理的層級"""
        priorities = {
            lv: self.hierarchy.get(lv, {}).get("priority", 99)
            for lv in conflict_levels
        }
        return min(priorities, key=priorities.get)

    def add_goal(self, level_id: str, goal: str):
        if level_id in self.hierarchy and not self.hierarchy[level_id].get("immutable"):
            self.hierarchy[level_id].setdefault("goals", []).append(goal)
            self._save()

    def all_goals(self) -> List[Dict[str, Any]]:
        return [
            {
                "level": lv,
                "name": info["name"],
                "priority": info["priority"],
                "goals": info.get("goals", []),
                "immutable": info.get("immutable", False),
            }
            for lv, info in sorted(
                self.hierarchy.items(),
                key=lambda x: x[1].get("priority", 99))
        ]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return 1

    def status(self) -> dict:
        return {
            "name": "GoalHierarchy",
            "levels": len(self.hierarchy),
            "active": self.active_goal,
            "total_goals": sum(
                len(v.get("goals", [])) for v in self.hierarchy.values()),
        }
