"""
ObjectiveRouter — 目標路由器
=============================
根據當前情境，決定該啟動哪個目標層級，
並將任務路由到正確的 agent。
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ObjectiveRouter:

    SITUATION_MAP = {
        "error_cascade": "L0_survival",
        "resource_critical": "L0_survival",
        "organ_failure": "L1_stability",
        "high_error_rate": "L1_stability",
        "user_request": "L2_service",
        "new_question": "L2_service",
        "learning_opportunity": "L3_learning",
        "discovery": "L3_learning",
        "expansion_opportunity": "L4_expansion",
        "new_tool_available": "L4_expansion",
    }

    def __init__(self, goal_hierarchy=None, mission_engine=None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.routes_file = self.base_dir / "data" / "goals" / "routes.json"
        self.routes_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.goal_hierarchy = goal_hierarchy
        self.mission_engine = mission_engine
        self.routing_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.routes_file.exists():
            try:
                self.routing_log = json.loads(self.routes_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.routes_file.write_text(
                json.dumps(self.routing_log[-2000:], ensure_ascii=False, indent=2))

    def resolve_objective(self, situation: str,
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Given a situation, determine which goal level should be activated.
        Returns {level, priority, recommended_agents, reasoning}.
        """
        context = context or {}
        level = self.SITUATION_MAP.get(
            situation, self._infer_level(situation, context))

        # Adjust based on urgency
        if context.get("urgency") == "critical":
            if level not in ("L0_survival", "L1_stability"):
                level = "L1_stability"

        agent_map = {
            "L0_survival": ["core_protector", "self_repair"],
            "L1_stability": ["health_monitor", "circuit_controller"],
            "L2_service": ["default_agent", "task_router"],
            "L3_learning": ["auto_learner", "researcher"],
            "L4_expansion": ["scout", "tool_evaluator"],
        }

        result = {
            "situation": situation,
            "level": level,
            "priority": 0 if level == "L0_survival" else (
                1 if level == "L1_stability" else 2),
            "recommended_agents": agent_map.get(level, ["default_agent"]),
            "reasoning": f"matched: {situation} -> {level}",
        }

        self.routing_log.append({
            "situation": situation,
            "level": level,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

        if self.goal_hierarchy:
            self.goal_hierarchy.set_active(level)

        return result

    def _infer_level(self, situation: str, context: Dict) -> str:
        s = situation.lower()
        if any(kw in s for kw in ["error", "crash", "fail", "dead", "critical"]):
            return "L0_survival"
        if any(kw in s for kw in ["slow", "degrade", "lag", "memory", "high"]):
            return "L1_stability"
        if any(kw in s for kw in ["learn", "study", "understand", "analyze"]):
            return "L3_learning"
        if any(kw in s for kw in ["expand", "grow", "new tool", "opportunity"]):
            return "L4_expansion"
        return "L2_service"

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return 1

    def status(self) -> dict:
        return {
            "name": "ObjectiveRouter",
            "total_routes": len(self.routing_log),
            "recent_levels": {
                level: sum(1 for r in self.routing_log[-100:] if r.get("level") == level)
                for level in set(r.get("level", "?") for r in self.routing_log[-100:])
            },
        }
