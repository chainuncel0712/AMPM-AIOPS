"""
AlignmentGuard — 對齊守衛
=========================
確保所有 agent 行動不偏離最高指令與目標層級。
在每個 agent 執行行動前攔截檢查。
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AlignmentGuard:

    BLOCKED_ACTIONS = [
        "rm -rf /",
        "DROP TABLE",
        "DELETE FROM users",
        "shutdown -h now",
        "os.remove",
        "subprocess.call(['rm')",
        "eval(",
        "exec(",
        "importlib.import_module('os').system",
    ]

    def __init__(self, prime_directive=None, goal_hierarchy=None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.log_file = self.base_dir / "data" / "goals" / "alignment_log.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.prime_directive = prime_directive
        self.goal_hierarchy = goal_hierarchy
        self.intervention_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.log_file.exists():
            try:
                self.intervention_log = json.loads(self.log_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.log_file.write_text(
                json.dumps(self.intervention_log[-1000:], ensure_ascii=False, indent=2))

    def check_action(self, action: str, agent_id: str = "",
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Pre-execution check. Returns {allowed, reason, directives_violated, risk_level}.
        """
        context = context or {}
        result = {
            "allowed": True,
            "reason": "passed",
            "directives_violated": [],
            "risk_level": "safe",
        }

        action_lower = action.lower()

        for blocked in self.BLOCKED_ACTIONS:
            if blocked.lower() in action_lower:
                result["allowed"] = False
                result["reason"] = f"blocked_pattern: {blocked}"
                result["risk_level"] = "critical"
                self._log_intervention(agent_id, action, result["reason"])
                return result

        if self.prime_directive:
            dp = self.prime_directive.check(action, context)
            if not dp["allowed"]:
                result["allowed"] = False
                result["directives_violated"] = [v["directive"] for v in dp["violations"]]
                result["reason"] = f"violates: {', '.join(result['directives_violated'])}"
                result["risk_level"] = "high"
                self._log_intervention(agent_id, action, result["reason"])
                return result

        if self.goal_hierarchy:
            priority = context.get("priority", 2)
            if not self.goal_hierarchy.can_execute(priority):
                result["allowed"] = False
                result["reason"] = "goal_priority_conflict"
                result["risk_level"] = "medium"
                self._log_intervention(agent_id, action, result["reason"])
                return result

        cost = context.get("estimated_cost_usd", 0)
        value = context.get("value_score", 0.5)
        if cost > 5.0 and value < 0.1:
            result["reason"] = "high_cost_low_value_warning"
            result["risk_level"] = "low"

        return result

    def _log_intervention(self, agent_id: str, action: str, reason: str):
        self.intervention_log.append({
            "agent_id": agent_id,
            "action": action[:300],
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def recent_interventions(self, n: int = 20) -> List[Dict]:
        return self.intervention_log[-n:]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return 1

    def status(self) -> dict:
        return {
            "name": "AlignmentGuard",
            "total_interventions": len(self.intervention_log),
            "recent_blocks": sum(
                1 for e in self.intervention_log[-100:]
                if "critical" in e.get("reason", "") or "violates" in e.get("reason", "")),
        }
