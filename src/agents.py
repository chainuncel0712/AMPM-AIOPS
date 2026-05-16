"""Agent Task Router v1 — Multi-Agent Coordination + Shared Memory + Skill Registry"""
import json
import sys
import time
import threading
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

sys.path.insert(0, str(Path(__file__).parent))
from skeleton.base_organ import BaseOrgan


class AgentTaskRouter(BaseOrgan):
    """Multi-agent task distribution, skill registry, shared memory graph"""

    def __init__(self, brain=None):
        super().__init__("agent_router")
        self._brain = brain
        self._agents: Dict[str, Dict] = {}
        self._task_queue: List[Dict] = []
        self._task_results: Dict[str, Dict] = {}
        self._skill_registry: Dict[str, Dict] = {}
        self._shared_memory: Dict[str, Dict] = {}
        self._execution_lock = threading.Lock()
        self._agent_counter = 0
        self._max_concurrent_tasks = 10

    # ── Agent Management ──────────────────────────────────

    def register_agent(self, name: str, capabilities: List[str] = None, memory_quota: int = 100) -> str:
        """Register a new agent with its capabilities"""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        agent = {
            "id": agent_id,
            "name": name,
            "capabilities": set(capabilities or []),
            "status": "idle",
            "current_task": None,
            "task_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "skills_contributed": 0,
            "memory_quota": memory_quota,
            "memory_used": 0,
            "registered_at": time.time(),
            "last_active": time.time(),
        }
        self._agents[agent_id] = agent
        # inherit brain skills
        if capabilities:
            for cap in capabilities:
                self._skill_registry.setdefault(cap, {"source": "system", "agents": set()}).setdefault("agents", set()).add(agent_id)
        return agent_id

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, Dict]:
        return {aid: {"name": a["name"], "status": a["status"], "tasks": a["task_count"], "skills": list(a["capabilities"])} for aid, a in self._agents.items()}

    # ── Task Routing ──────────────────────────────────────

    def submit_task(self, description: str, required_skills: List[str] = None, priority: int = 0, data: Dict = None) -> str:
        """Submit a task to be routed to the best agent"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "description": description,
            "required_skills": required_skills or [],
            "priority": priority,
            "data": data or {},
            "status": "pending",
            "assigned_agent": None,
            "created_at": time.time(),
            "completed_at": None,
            "result": None,
        }
        self._task_queue.append(task)
        self._task_queue.sort(key=lambda t: (-t["priority"], t["created_at"]))
        return task_id

    def route_task(self, task_id: str) -> Optional[str]:
        """Find the best agent for a task and assign it"""
        task = next((t for t in self._task_queue if t["id"] == task_id), None)
        if not task:
            return None

        best_agent = self._find_best_agent(task["required_skills"])
        if best_agent:
            task["assigned_agent"] = best_agent
            task["status"] = "assigned"
            self._agents[best_agent]["current_task"] = task_id
            self._agents[best_agent]["status"] = "busy"
            self._agents[best_agent]["last_active"] = time.time()
            return best_agent
        return None

    def route_all_pending(self) -> int:
        """Route all pending tasks to available agents"""
        count = 0
        active = sum(1 for a in self._agents.values() if a["status"] == "busy")
        available_slots = self._max_concurrent_tasks - active

        for task in [t for t in self._task_queue if t["status"] == "pending"][:available_slots]:
            agent_id = self.route_task(task["id"])
            if agent_id:
                count += 1
        return count

    def _find_best_agent(self, required_skills: List[str]) -> Optional[str]:
        """Find the agent with the best skill match (idle priority)"""
        best = None
        best_score = -1
        for aid, agent in self._agents.items():
            if agent["status"] != "idle":
                continue
            if not required_skills:
                score = 0
            else:
                matching = len(set(required_skills) & agent["capabilities"])
                score = matching / len(required_skills) if required_skills else 1
            if score > best_score:
                best_score = score
                best = aid
        return best

    # ── Task Completion ───────────────────────────────────

    def complete_task(self, task_id: str, success: bool, result: Any = None):
        """Mark a task as completed and update agent stats"""
        with self._execution_lock:
            task = next((t for t in self._task_queue if t["id"] == task_id), None)
            if not task:
                return
            task["status"] = "completed" if success else "failed"
            task["completed_at"] = time.time()
            task["result"] = result
            self._task_results[task_id] = task

            agent_id = task.get("assigned_agent")
            if agent_id and agent_id in self._agents:
                agent = self._agents[agent_id]
                agent["status"] = "idle"
                agent["current_task"] = None
                agent["task_count"] += 1
                if success:
                    agent["success_count"] += 1
                else:
                    agent["failure_count"] += 1

    # ── Skill Registry ────────────────────────────────────

    def register_skill(self, name: str, description: str, source_agent: str = "system", skill_type: str = "tool", code: Any = None):
        """Register a new skill learned by an agent"""
        skill = {
            "name": name,
            "description": description,
            "type": skill_type,
            "source": source_agent,
            "registered_at": time.time(),
            "usage_count": 0,
            "success_rate": 1.0,
            "code": code,
            "contributors": {source_agent},
        }
        if name in self._skill_registry:
            self._skill_registry[name].setdefault("contributors", set()).add(source_agent)
            self._skill_registry[name]["usage_count"] = self._skill_registry[name].get("usage_count", 0) + 1
        else:
            self._skill_registry[name] = skill

        if source_agent != "system" and source_agent in self._agents:
            self._agents[source_agent]["capabilities"].add(name)
            self._agents[source_agent]["skills_contributed"] += 1

        # Feed back to brain tool registry if available
        if self._brain and hasattr(self._brain, "tools"):
            try:
                self._brain.tools.learn_tool(name=name, description=description, category=f"agent:{source_agent}", code=code or {})
            except Exception:
                pass

        return skill

    def get_skill(self, name: str) -> Optional[Dict]:
        return self._skill_registry.get(name)

    def list_skills(self, source_agent: str = None) -> Dict[str, Dict]:
        if source_agent:
            return {k: v for k, v in self._skill_registry.items() if source_agent in v.get("contributors", set())}
        return dict(self._skill_registry)

    def search_skills(self, query: str) -> List[Dict]:
        results = []
        for name, skill in self._skill_registry.items():
            if query.lower() in name.lower() or query.lower() in skill.get("description", "").lower():
                results.append({"name": name, "description": skill["description"], "type": skill["type"]})
        return results

    # ── Shared Memory ─────────────────────────────────────

    def write_memory(self, key: str, value: Any, agent_id: str = "system", ttl: int = 3600):
        """Write to shared memory space"""
        entry = {"value": value, "agent_id": agent_id, "timestamp": time.time(), "ttl": ttl, "access_count": 0}
        self._shared_memory[key] = entry

        # track agent memory usage
        if agent_id in self._agents:
            self._agents[agent_id]["memory_used"] = len([v for v in self._shared_memory.values() if v["agent_id"] == agent_id])

    def read_memory(self, key: str) -> Any:
        """Read from shared memory (auto-expire)"""
        entry = self._shared_memory.get(key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > entry["ttl"]:
            del self._shared_memory[key]
            return None
        entry["access_count"] += 1
        return entry["value"]

    def query_memory(self, prefix: str = "", agent_id: str = None) -> Dict[str, Any]:
        """Query shared memory by prefix and/or agent"""
        results = {}
        for key, entry in self._shared_memory.items():
            if prefix and not key.startswith(prefix):
                continue
            if agent_id and entry["agent_id"] != agent_id:
                continue
            if time.time() - entry["timestamp"] < entry["ttl"]:
                results[key] = entry["value"]
        return results

    def broadcast(self, message: Dict, sender_agent: str):
        """Broadcast a message to all agents via shared memory"""
        key = f"broadcast:{int(time.time())}:{sender_agent}"
        self.write_memory(key, message, sender_agent, ttl=300)
        return key

    # ── Agent Stats ───────────────────────────────────────

    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        total = agent["task_count"]
        return {
            "name": agent["name"],
            "status": agent["status"],
            "total_tasks": total,
            "success": agent["success_count"],
            "failure": agent["failure_count"],
            "success_rate": round(agent["success_count"] / max(total, 1) * 100, 1),
            "skills": list(agent["capabilities"]),
            "skills_contributed": agent["skills_contributed"],
            "memory_used": agent["memory_used"],
        }

    def get_global_stats(self) -> Dict:
        tasks = [t for t in self._task_queue if t.get("status") not in ("pending",)]
        tasks_all = list(self._task_results.values())
        return {
            "agents": len(self._agents),
            "agents_idle": sum(1 for a in self._agents.values() if a["status"] == "idle"),
            "agents_busy": sum(1 for a in self._agents.values() if a["status"] == "busy"),
            "tasks_pending": sum(1 for t in self._task_queue if t["status"] == "pending"),
            "tasks_completed": sum(1 for t in tasks_all if t["status"] == "completed"),
            "tasks_failed": sum(1 for t in tasks_all if t["status"] == "failed"),
            "skills_registered": len(self._skill_registry),
            "shared_memory_keys": len(self._shared_memory),
        }

    def get_agent_status(self) -> Dict:
        return {
            "total": len(self._agents),
            "idle": sum(1 for a in self._agents.values() if a["status"] == "idle"),
            "busy": sum(1 for a in self._agents.values() if a["status"] == "busy"),
        }

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            **self.get_global_stats(),
        }


AgentManager = AgentTaskRouter
