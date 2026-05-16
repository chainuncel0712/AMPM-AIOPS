"""
AgentReliability — Agent 可靠性追蹤
------------------------------------
追蹤每個 agent 的歷史表現：
- 任務完成率
- 平均品質分數
- 超時頻率
- 資源消耗效率
"""
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentReliability:

    def __init__(self, trust_engine: Optional[Any] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "trust" / "agent_reliability.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.trust = trust_engine
        self.agents: Dict[str, Dict] = {}
        self.task_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                self.agents = data.get("agents", {})
                self.task_log = data.get("log", [])
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {"agents": self.agents, "log": self.task_log[-5000:]}
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _init_agent(self, agent_id: str, agent_type: str = "general"):
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "total_tasks": 0,
                "completed": 0,
                "failed": 0,
                "timeout_count": 0,
                "total_duration_ms": 0,
                "quality_scores": [],
                "avg_quality": 0.0,
                "reliability": 0.5,
                "last_active": None,
                "cost_efficiency": 0.0,
                "total_cost_usd": 0.0,
            }

    def record_task(self, agent_id: str, task_id: str, success: bool,
                    duration_ms: float, quality_score: float = 0.7,
                    cost_usd: float = 0.0, agent_type: str = "general",
                    timeout: bool = False):
        with self._lock:
            self._init_agent(agent_id, agent_type)
            a = self.agents[agent_id]

            a["total_tasks"] += 1
            if success:
                a["completed"] += 1
            else:
                a["failed"] += 1

            if timeout:
                a["timeout_count"] += 1

            a["total_duration_ms"] += duration_ms
            a["quality_scores"].append(quality_score)
            if len(a["quality_scores"]) > 100:
                a["quality_scores"] = a["quality_scores"][-100:]

            a["avg_quality"] = round(
                sum(a["quality_scores"]) / len(a["quality_scores"]), 4)

            a["total_cost_usd"] = round(a["total_cost_usd"] + cost_usd, 6)
            a["last_active"] = datetime.now().isoformat()

            total = a["total_tasks"]
            completion_rate = a["completed"] / total if total > 0 else 0
            timeout_penalty = a["timeout_count"] / max(1, total) * 0.2

            if a["total_cost_usd"] > 0:
                a["cost_efficiency"] = round(
                    a["completed"] / a["total_cost_usd"], 2)
            else:
                a["cost_efficiency"] = a["completed"]

            a["reliability"] = round(
                max(0.0, min(1.0,
                    completion_rate * 0.5 +
                    a["avg_quality"] * 0.3 +
                    min(a["cost_efficiency"] / 100, 1.0) * 0.1 -
                    timeout_penalty
                )), 4)

        if self.trust:
            self.trust.record(f"agent_{agent_id}", success, tags=["agent_task"])

        self.task_log.append({
            "agent_id": agent_id,
            "task_id": task_id,
            "success": success,
            "quality": quality_score,
            "duration_ms": duration_ms,
            "cost_usd": cost_usd,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_reliability(self, agent_id: str) -> Dict[str, Any]:
        with self._lock:
            a = self.agents.get(agent_id)
            if not a:
                return {"reliability": 0.5, "reason": "unknown_agent"}
            return {
                "agent_id": agent_id,
                "type": a["type"],
                "reliability": a["reliability"],
                "completion_rate": round(
                    a["completed"] / max(1, a["total_tasks"]), 4),
                "avg_quality": a["avg_quality"],
                "total_tasks": a["total_tasks"],
                "cost_efficiency": a["cost_efficiency"],
                "total_cost": a["total_cost_usd"],
            }

    def best_agents(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            ranked = sorted(self.agents.items(),
                            key=lambda x: -x[1]["reliability"])
            return [self.get_reliability(k) for k, _ in ranked[:top_n]]

    def worst_agents(self, top_n: int = 5) -> List[Dict]:
        with self._lock:
            ranked = sorted(self.agents.items(),
                            key=lambda x: x[1]["reliability"])
            return [self.get_reliability(k) for k, _ in ranked[:top_n]]

    def status(self) -> dict:
        with self._lock:
            return {
                "name": "AgentReliability",
                "total_agents": len(self.agents),
                "avg_reliability": round(
                    sum(a["reliability"] for a in self.agents.values()) /
                    max(1, len(self.agents)), 4),
                "total_tasks_tracked": len(self.task_log),
                "worst_agents": self.worst_agents(3),
            }
