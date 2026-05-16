"""
MissionEngine — 任務引擎
=========================
根據目標層級，自動生成、分配、追蹤任務。
每個 agent 的行動必須對應到某個目標層級。
"""
import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MissionEngine:

    def __init__(self, goal_hierarchy=None, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.missions_file = self.base_dir / "data" / "goals" / "missions.json"
        self.missions_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.goal_hierarchy = goal_hierarchy
        self.missions: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if self.missions_file.exists():
            try:
                self.missions = json.loads(self.missions_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.missions_file.write_text(
                json.dumps(self.missions, ensure_ascii=False, indent=2))

    def create(self, title: str, goal_level: str = "L2_service",
               agent_id: str = "default", priority: int = 5,
               deadline_hours: int = 24) -> str:
        mission_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        with self._lock:
            self.missions[mission_id] = {
                "id": mission_id,
                "title": title,
                "goal_level": goal_level,
                "agent_id": agent_id,
                "priority": priority,
                "status": "pending",
                "created_at": now,
                "deadline": (datetime.now().isoformat()),
                "completed_at": None,
                "result": "",
                "attempts": 0,
            }
            self._save()
        return mission_id

    def assign(self, mission_id: str, agent_id: str):
        with self._lock:
            if mission_id in self.missions:
                self.missions[mission_id]["agent_id"] = agent_id
                self._save()

    def complete(self, mission_id: str, result: str = "done", success: bool = True):
        with self._lock:
            if mission_id in self.missions:
                m = self.missions[mission_id]
                m["status"] = "completed" if success else "failed"
                m["result"] = result[:500]
                m["completed_at"] = datetime.now().isoformat()
                self._save()

    def get_pending(self, agent_id: str = None, limit: int = 10) -> List[Dict]:
        with self._lock:
            pending = [
                m for m in self.missions.values()
                if m["status"] == "pending"
                and (agent_id is None or m["agent_id"] == agent_id)
            ]
            pending.sort(key=lambda x: x["priority"])
            return pending[:limit]

    def stats_by_level(self) -> Dict[str, Dict]:
        with self._lock:
            stats: Dict[str, Dict] = {}
            for m in self.missions.values():
                level = m["goal_level"]
                if level not in stats:
                    stats[level] = {"total": 0, "completed": 0, "failed": 0, "pending": 0}
                stats[level]["total"] += 1
                if m["status"] == "completed":
                    stats[level]["completed"] += 1
                elif m["status"] == "failed":
                    stats[level]["failed"] += 1
                else:
                    stats[level]["pending"] += 1
            return stats

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return 2

    def status(self) -> dict:
        return {
            "name": "MissionEngine",
            "total_missions": len(self.missions),
            "pending": sum(1 for m in self.missions.values() if m["status"] == "pending"),
            "by_level": self.stats_by_level(),
        }
