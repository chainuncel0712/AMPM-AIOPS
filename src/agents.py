"""Agent Company v2 — Mission Decomposition + Department Formation + Progress Tracking"""
import json
import sys
import time
import threading
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

sys.path.insert(0, str(Path(__file__).parent))
from skeleton.base_organ import BaseOrgan


AGENT_TEMPLATES = {
    "researcher": {
        "tools": ["web_search", "http", "market_data"],
        "prompt": "你是一個研究代理。搜尋、分析、整理資訊，回報結構化結果。不閒聊。",
        "capabilities": ["research", "search", "analyze", "summarize"],
    },
    "coder": {
        "tools": ["python_exec", "code_gen", "file_write"],
        "prompt": "你是一個程式代理。寫程式、修bug、執行測試。只回報程式碼和執行結果。",
        "capabilities": ["coding", "debug", "testing", "scripting"],
    },
    "analyst": {
        "tools": ["python_exec", "market_data", "chart"],
        "prompt": "你是一個分析代理。分析資料、產生報告、繪製圖表。回報數據驅動的結論。",
        "capabilities": ["analysis", "data", "chart", "reporting"],
    },
    "writer": {
        "tools": ["translate", "summarize"],
        "prompt": "你是一個寫作代理。撰寫文章、翻譯、潤稿。回報最終文本。",
        "capabilities": ["writing", "translation", "editing"],
    },
    "trader": {
        "tools": ["market_data", "market_analysis", "price_check"],
        "prompt": "你是一個交易代理。分析市場、評估風險、給出交易建議。回報結構化建議。",
        "capabilities": ["trading", "market_analysis", "risk_assessment"],
    },
    "monitor": {
        "tools": ["health_check", "system_status"],
        "prompt": "你是一個監控代理。監視系統健康、資源使用、錯誤率。回報異常。",
        "capabilities": ["monitoring", "alerting", "health_check"],
    },
    "scout": {
        "tools": ["web_search", "github_search", "pip_search"],
        "prompt": "你是一個探索代理。尋找新工具、新模型、新API。回報發現和推薦。",
        "capabilities": ["discovery", "evaluation", "recommendation"],
    },
    "executor": {
        "tools": ["shell", "file_ops", "tool_chain"],
        "prompt": "你是一個執行代理。執行具體操作、部署、安裝。回報執行結果。",
        "capabilities": ["execution", "deployment", "operations"],
    },
}


class AgentTaskRouter(BaseOrgan):
    """Company-style multi-agent system: decompose → team → execute → report"""

    def __init__(self, brain=None):
        super().__init__("agent_company")
        self._brain = brain
        self._agents: Dict[str, Dict] = {}
        self._task_queue: List[Dict] = []
        self._task_results: Dict[str, Dict] = {}
        self._missions: Dict[str, Dict] = {}
        self._departments: Dict[str, Dict] = {}
        self._skill_registry: Dict[str, Dict] = {}
        self._shared_memory: Dict[str, Dict] = {}
        self._execution_lock = threading.RLock()
        self._agent_counter = 0

        self._auto_spawn_departments()
        self.fill_all_departments()

    # ═══════════════════════════════════════════════════════
    # Department Formation (從對話中動態建立)
    # ═══════════════════════════════════════════════════════

    def _auto_spawn_departments(self):
        """On init, create a single general pool. User defines departments via conversation."""
        if not self._departments:
            self._departments["general_pool"] = {
                "name": "general_pool",
                "role": "general",
                "description": "Default agent pool. User can create specialized departments.",
                "agent_ids": [],
                "target_count": 3,
            }

    def create_department(self, name: str, role: str, description: str = "",
                          target_count: int = 2) -> str:
        """Create a new department based on user's definition."""
        dept_name = name.replace(" ", "_").lower()
        if dept_name in self._departments:
            return dept_name
        self._departments[dept_name] = {
            "name": dept_name,
            "role": role,
            "description": description,
            "agent_ids": [],
            "target_count": target_count,
        }
        self.fill_department(dept_name)
        self._save_state()
        print(f"[AgentCompany] New department created: {dept_name} ({role})")
        return dept_name

    def remove_department(self, name: str):
        """Remove a department and release its agents."""
        dept_name = name.replace(" ", "_").lower()
        if dept_name in self._departments:
            for aid in self._departments[dept_name]["agent_ids"]:
                if aid in self._agents:
                    del self._agents[aid]
            del self._departments[dept_name]
            self._save_state()
        for dept_name, cfg in default_depts.items():
            if dept_name not in self._departments:
                self._departments[dept_name] = {
                    "name": dept_name,
                    "role": cfg["role"],
                    "description": cfg["description"],
                    "agent_ids": [],
                    "target_count": cfg["count"],
                }

    def create_agent(self, name: str, role: str, parent_id: str = None,
                     tools: list = None, capabilities: list = None) -> Optional[Dict]:
        """Create a new agent using template"""
        template = AGENT_TEMPLATES.get(role, AGENT_TEMPLATES.get("researcher", {}))
        capabilities = capabilities or template.get("capabilities", [role])
        tools = tools or template.get("tools", [])

        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        self._agent_counter += 1

        agent = {
            "id": agent_id,
            "name": name,
            "role": role,
            "parent_id": parent_id,
            "capabilities": set(capabilities),
            "tools": tools,
            "prompt": template.get("prompt", f"你是{role}代理"),
            "status": "idle",
            "current_task": None,
            "current_mission": None,
            "task_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "created_at": time.time(),
            "last_active": time.time(),
        }
        self._agents[agent_id] = agent

        # Register capabilities
        for cap in capabilities:
            reg = self._skill_registry.setdefault(
                cap, {"source": "system", "agents": set()})
            reg.setdefault("agents", set()).add(agent_id)

        return agent

    def fill_department(self, dept_name: str) -> int:
        """Auto-spawn agents to fill a department to target count"""
        dept = self._departments.get(dept_name)
        if not dept:
            return 0

        current = len(dept["agent_ids"])
        needed = dept["target_count"] - current
        spawned = 0

        for i in range(needed):
            idx = current + i + 1
            agent = self.create_agent(
                name=f"{dept_name}_{idx}",
                role=dept["role"],
            )
            if agent:
                dept["agent_ids"].append(agent["id"])
                spawned += 1

        return spawned

    def fill_all_departments(self) -> int:
        """Ensure all departments have target agent count"""
        total = 0
        for dept_name in self._departments:
            total += self.fill_department(dept_name)
        return total

    # ═══════════════════════════════════════════════════════
    # Mission System (任務拆解)
    # ═══════════════════════════════════════════════════════

    def launch_mission(self, description: str, context: Dict = None) -> str:
        """Launch a full mission: analyze → decompose → dispatch → track"""
        mission_id = f"mission_{uuid.uuid4().hex[:6]}"
        context = context or {}

        # Step 1: Decompose
        sub_tasks = self._decompose_task(description, context)

        # Step 2: Create mission record
        mission = {
            "id": mission_id,
            "description": description,
            "sub_tasks": sub_tasks,
            "status": "in_progress",
            "created_at": time.time(),
            "completed_at": None,
            "results": {},
            "context": context,
        }
        self._missions[mission_id] = mission

        # Step 3: Dispatch to departments
        for st in sub_tasks:
            task_id = self.submit_task(
                st["description"],
                required_skills=st.get("skills", []),
                priority=st.get("priority", 0),
                data={"mission_id": mission_id, "sub_task_id": st["id"]},
            )
            st["task_id"] = task_id

        # Step 4: Route immediately
        self.route_all_pending()

        # Step 5: Broadcast mission to all agents
        self.broadcast({
            "type": "new_mission",
            "mission_id": mission_id,
            "description": description,
            "sub_tasks": len(sub_tasks),
        }, "mission_control")

        self._save_state()
        return mission_id

    def _decompose_task(self, description: str, context: Dict) -> List[Dict]:
        """Decompose into sub-tasks. Uses existing dept roles if defined, else defaults."""
        desc_lower = description.lower()

        # Get available roles from existing departments
        available_roles = [d.get("role", n) for n, d in self._departments.items()]
        if not available_roles:
            available_roles = ["think", "do"]

        # Pick a decomposition pattern based on task type
        if any(kw in desc_lower for kw in ["code", "程式", "寫", "bug", "fix", "debug"]):
            roles = ["research", "design", "implement", "test"]
        elif any(kw in desc_lower for kw in ["分析", "analyze", "report", "報告"]):
            roles = ["research", "analyze", "write"]
        elif any(kw in desc_lower for kw in ["search", "搜", "找", "find"]):
            roles = ["search", "evaluate"]
        elif any(kw in desc_lower for kw in ["deploy", "部署", "install", "安裝"]):
            roles = ["research", "execute", "verify"]
        elif any(kw in desc_lower for kw in ["monitor", "監控", "status", "狀態"]):
            roles = ["check", "report"]
        else:
            roles = ["research", "execute", "summarize"]

        return self._build_subtasks(description, roles)

    def _build_subtasks(self, description: str, roles: List[str]) -> List[Dict]:
        """Build sub-task list from role list (roles defined by user/dynamic depts)."""
        role_to_dept = {}
        for dept_name, dept in self._departments.items():
            role_to_dept[dept.get("role", dept_name)] = dept_name

        result = []
        for i, role in enumerate(roles):
            dept = role_to_dept.get(role, "general_pool")
            result.append({
                "id": role,
                "description": f"[{role}] {description[:80]}",
                "skills": [role],
                "priority": i,
                "department": dept,
            })
        return result

    # ═══════════════════════════════════════════════════════
    # Agent Management (代理管理)
    # ═══════════════════════════════════════════════════════

    def register_agent(self, name: str, capabilities: List[str] = None,
                       memory_quota: int = 100) -> str:
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        agent = {
            "id": agent_id, "name": name,
            "capabilities": set(capabilities or []),
            "status": "idle", "current_task": None, "current_mission": None,
            "task_count": 0, "success_count": 0, "failure_count": 0,
            "memory_quota": memory_quota, "registered_at": time.time(),
            "last_active": time.time(),
        }
        self._agents[agent_id] = agent
        for cap in (capabilities or []):
            self._skill_registry.setdefault(cap, {"source": "system", "agents": set()}).setdefault("agents", set()).add(agent_id)
        return agent_id

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, Dict]:
        return {
            aid: {"name": a.get("name", a.get("id")), "status": a["status"],
                  "role": a.get("role", "unknown"), "tasks": a["task_count"],
                  "skills": list(a.get("capabilities", []))}
            for aid, a in self._agents.items()
        }

    def get_department(self, dept_name: str) -> Dict:
        dept = self._departments.get(dept_name, {})
        agents = [self._agents.get(aid) for aid in dept.get("agent_ids", []) if self._agents.get(aid)]
        return {
            "name": dept.get("name", dept_name),
            "role": dept.get("role", ""),
            "description": dept.get("description", ""),
            "agent_count": len(agents),
            "target_count": dept.get("target_count", 0),
            "idle": sum(1 for a in agents if a and a["status"] == "idle"),
            "busy": sum(1 for a in agents if a and a["status"] == "busy"),
            "agents": [{"id": a["id"], "name": a.get("name", ""), "status": a["status"]}
                       for a in agents if a],
        }

    def list_departments(self) -> Dict[str, Dict]:
        return {dn: self.get_department(dn) for dn in self._departments}

    # ═══════════════════════════════════════════════════════
    # Task Routing (任務分配)
    # ═══════════════════════════════════════════════════════

    def submit_task(self, description: str, required_skills: List[str] = None,
                    priority: int = 0, data: Dict = None) -> str:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id, "description": description,
            "required_skills": required_skills or [],
            "priority": priority, "data": data or {},
            "status": "pending", "assigned_agent": None,
            "created_at": time.time(), "completed_at": None, "result": None,
        }
        self._task_queue.append(task)
        self._task_queue.sort(key=lambda t: (-t["priority"], t["created_at"]))
        return task_id

    def route_task(self, task_id: str) -> Optional[str]:
        task = next((t for t in self._task_queue if t["id"] == task_id), None)
        if not task:
            return None

        best_agent = self._find_best_agent(task)
        if best_agent:
            task["assigned_agent"] = best_agent
            task["status"] = "assigned"
            agent = self._agents[best_agent]
            agent["current_task"] = task_id
            agent["status"] = "busy"
            agent["last_active"] = time.time()
            if task.get("data", {}).get("mission_id"):
                agent["current_mission"] = task["data"]["mission_id"]
            return best_agent
        return None

    def route_all_pending(self) -> int:
        count = 0
        active = sum(1 for a in self._agents.values() if a["status"] == "busy")
        slots = 20 - active
        for task in [t for t in self._task_queue if t["status"] == "pending"][:slots]:
            if self.route_task(task["id"]):
                count += 1
        return count

    def _find_best_agent(self, task: Dict) -> Optional[str]:
        best, best_score = None, -1
        required = task.get("required_skills", [])

        for aid, agent in self._agents.items():
            if agent["status"] != "idle":
                continue
            if not required:
                score = 0
            else:
                matching = len(set(required) & agent.get("capabilities", set()))
                score = matching / len(required) if required else 1
            if score > best_score:
                best_score = score
                best = aid
        return best

    # ═══════════════════════════════════════════════════════
    # Task Completion (任務回報)
    # ═══════════════════════════════════════════════════════

    def complete_task(self, task_id: str, success: bool, result: Any = None):
        with self._execution_lock:
            task = next((t for t in self._task_queue if t["id"] == task_id), None)
            if not task:
                return
            task["status"] = "completed" if success else "failed"
            task["completed_at"] = time.time()
            task["result"] = str(result)[:500] if result else ""
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

            # Update mission progress
            mission_id = task.get("data", {}).get("mission_id")
            if mission_id and mission_id in self._missions:
                m = self._missions[mission_id]
                sub_id = task.get("data", {}).get("sub_task_id", task_id)
                m["results"][sub_id] = {
                    "success": success, "result": str(result)[:300] if result else "",
                    "agent": agent_id,
                }
                self._check_mission_complete(mission_id)
            self._save_state()

    def _check_mission_complete(self, mission_id: str):
        m = self._missions.get(mission_id)
        if not m:
            return
        total = len(m["sub_tasks"])
        done = len(m["results"])
        if done >= total:
            m["status"] = "completed"
            m["completed_at"] = time.time()

    def get_mission(self, mission_id: str) -> Optional[Dict]:
        m = self._missions.get(mission_id)
        if not m:
            return None
        return m

    def get_task_result(self, task_id: str) -> Optional[Dict]:
        return self._task_results.get(task_id)

    # ═══════════════════════════════════════════════════════
    # Skill Registry
    # ═══════════════════════════════════════════════════════

    def register_skill(self, name: str, description: str,
                       source_agent: str = "system", skill_type: str = "tool",
                       code: Any = None):
        skill = {
            "name": name, "description": description, "type": skill_type,
            "source": source_agent, "registered_at": time.time(),
            "usage_count": 0, "success_rate": 1.0, "code": code,
            "contributors": {source_agent},
        }
        if name in self._skill_registry:
            self._skill_registry[name].setdefault("contributors", set()).add(source_agent)
            self._skill_registry[name]["usage_count"] = self._skill_registry[name].get("usage_count", 0) + 1
        else:
            self._skill_registry[name] = skill

        if source_agent != "system" and source_agent in self._agents:
            self._agents[source_agent].setdefault("capabilities", set()).add(name)

    def get_skill(self, name: str) -> Optional[Dict]:
        return self._skill_registry.get(name)

    def list_skills(self, source_agent: str = None) -> Dict[str, Dict]:
        if source_agent:
            return {k: v for k, v in self._skill_registry.items()
                    if source_agent in v.get("contributors", set())}
        return dict(self._skill_registry)

    # ═══════════════════════════════════════════════════════
    # Shared Memory
    # ═══════════════════════════════════════════════════════

    def write_memory(self, key: str, value: Any, agent_id: str = "system", ttl: int = 3600):
        self._shared_memory[key] = {
            "value": value, "agent_id": agent_id,
            "timestamp": time.time(), "ttl": ttl, "access_count": 0,
        }

    def read_memory(self, key: str) -> Any:
        entry = self._shared_memory.get(key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > entry["ttl"]:
            del self._shared_memory[key]
            return None
        entry["access_count"] += 1
        return entry["value"]

    def query_memory(self, prefix: str = "", agent_id: str = None) -> Dict[str, Any]:
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
        key = f"broadcast:{int(time.time())}:{sender_agent}"
        self.write_memory(key, message, sender_agent, ttl=300)
        return key

    # ═══════════════════════════════════════════════════════
    # Global Stats & Status
    # ═══════════════════════════════════════════════════════

    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        total = max(agent["task_count"], 1)
        return {
            "name": agent.get("name", agent_id),
            "role": agent.get("role", "unknown"),
            "status": agent["status"],
            "total_tasks": agent["task_count"],
            "success": agent["success_count"],
            "failure": agent["failure_count"],
            "success_rate": round(agent["success_count"] / total * 100, 1),
            "skills": list(agent.get("capabilities", [])),
            "mission": agent.get("current_mission"),
        }

    def get_global_stats(self) -> Dict:
        results = list(self._task_results.values())
        return {
            "agents": len(self._agents),
            "agents_idle": sum(1 for a in self._agents.values() if a["status"] == "idle"),
            "agents_busy": sum(1 for a in self._agents.values() if a["status"] == "busy"),
            "departments": len(self._departments),
            "missions_active": sum(1 for m in self._missions.values()
                                   if m["status"] == "in_progress"),
            "missions_completed": sum(1 for m in self._missions.values()
                                      if m["status"] == "completed"),
            "tasks_pending": sum(1 for t in self._task_queue if t["status"] == "pending"),
            "tasks_completed": sum(1 for t in results if t["status"] == "completed"),
            "tasks_failed": sum(1 for t in results if t["status"] == "failed"),
            "skills_registered": len(self._skill_registry),
        }

    def get_agent_status(self) -> Dict:
        return {
            "total": len(self._agents),
            "idle": sum(1 for a in self._agents.values() if a["status"] == "idle"),
            "busy": sum(1 for a in self._agents.values() if a["status"] == "busy"),
        }

    def org_chart(self) -> str:
        """Generate a company org chart"""
        lines = [f"  Company Organization Chart  ", f"  Agents: {len(self._agents)} | "
                 f"Departments: {len(self._departments)} | "
                 f"Missions: {sum(1 for m in self._missions.values() if m['status'] == 'in_progress')} active"]
        lines.append("")
        for dept_name in sorted(self._departments.keys()):
            d = self.get_department(dept_name)
            bar = "▓" * d["busy"] + "░" * (d["agent_count"] - d["busy"])
            lines.append(f"  {dept_name}")
            lines.append(f"    [{bar}] {d['agent_count']} agents ({d['idle']} idle, {d['busy']} busy)")
            for a in d.get("agents", [])[:5]:
                status_icon = "🟢" if a["status"] == "idle" else "🔴"
                lines.append(f"    {status_icon} {a['name']} ({a['status']})")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════
    # Agent Execution Engine (代理執行引擎)
    # ═══════════════════════════════════════════════════════

    def set_executor(self, executor_fn, progress_report_interval_s: int = 0):
        """
        Register an executor function that agents use to actually do work.
        progress_report_interval_s: 0 = disabled, 900 = 15 min, etc.
        """
        self._executor_fn = executor_fn
        self._progress_interval = progress_report_interval_s
        self._start_execution_thread()

    def _start_execution_thread(self):
        """Auto-start background thread that picks up assigned tasks and runs them"""
        if hasattr(self, '_exec_thread') and self._exec_thread and self._exec_thread.is_alive():
            return

        interval = getattr(self, '_progress_interval', 0)

        def _loop():
            last_progress = time.time()
            while self.is_alive():
                try:
                    self.execute_assigned_tasks()
                    if interval > 0 and time.time() - last_progress > interval:
                        self.report_mission_progress()
                        last_progress = time.time()
                except Exception as e:
                    print(f"[AgentCompany] exec loop error: {e}")
                time.sleep(3)

        self._exec_thread = threading.Thread(target=_loop, daemon=True)
        self._exec_thread.start()
        status = f"progress every {interval}s" if interval > 0 else "on-demand only"
        print(f"[AgentCompany] Execution engine started ({status})")

    def execute_assigned_tasks(self) -> int:
        """Pick up all assigned tasks and execute them via the registered executor"""
        if not hasattr(self, '_executor_fn') or not self._executor_fn:
            return 0

        executed = 0
        with self._execution_lock:
            for aid, agent in list(self._agents.items()):
                if agent["status"] != "busy" or not agent.get("current_task"):
                    continue

                task_id = agent["current_task"]
                task = next((t for t in self._task_queue if t["id"] == task_id), None)
                if not task:
                    continue

                try:
                    print(f"[AgentCompany] {agent['name']} executing: {task['description'][:80]}")
                    result = self._executor_fn(agent, task)
                    self.complete_task(task_id, True, result)
                    print(f"[AgentCompany] {agent['name']} done: {str(result)[:100]}")
                    executed += 1
                except Exception as e:
                    print(f"[AgentCompany] {agent['name']} failed: {e}")
                    self.complete_task(task_id, False, str(e))
                    executed += 1

        return executed

    # ═══════════════════════════════════════════════════════
    # Promise Execution (答應了就執行)
    # ═══════════════════════════════════════════════════════

    def scan_and_execute_promises(self, reply_text: str) -> str:
        """
        Scan the bot's reply for action commitments.
        If the bot said 'I'll research X' or '幫你查 Y',
        actually launch a mission for it.
        Returns a progress summary string.
        """
        import re

        promise_patterns = [
            (r"(?:我會|我來|幫你|讓我)(?:去)?(查|找|搜|分析|寫|做|研究|build|code|部署|安裝)(?:一下)?[：:\s]*(.+?)(?:[。！\n]|$)", "task"),
            (r"(?:I(?:'ll|\s+will))\s+(search|find|research|analyze|build|code|deploy|check)\s+(.+?)(?:[.!\\n]|$)", "task"),
        ]

        launched = []
        for pattern, _ in promise_patterns:
            matches = re.findall(pattern, reply_text)
            for match in matches:
                if isinstance(match, tuple):
                    action = match[0] if len(match) > 0 else ""
                    target = match[1] if len(match) > 1 else ""
                else:
                    action = ""
                    target = str(match)

                desc = f"{action} {target}".strip()[:200]
                if desc and len(desc) > 5:
                    try:
                        mission_id = self.launch_mission(desc)
                        launched.append(mission_id)
                        print(f"[AgentCompany] Promise detected: '{desc}' -> mission {mission_id}")
                    except Exception as e:
                        print(f"[AgentCompany] Promise launch failed: {e}")

        if launched:
            return (f"\n[系統已自動啟動 {len(launched)} 個後台任務來執行上述承諾，"
                    f"完成後會通知你]")
        return ""

    def report_mission_progress(self):
        """Report progress on all active missions to shared memory"""
        active = {mid: m for mid, m in self._missions.items() if m["status"] == "in_progress"}
        if not active:
            return
        for mid, m in active.items():
            done = len(m.get("results", {}))
            total = len(m.get("sub_tasks", []))
            pct = round(done / total * 100, 1) if total > 0 else 0
            summary = (
                f"Mission {mid}: {m['description'][:80]} - "
                f"{done}/{total} tasks done ({pct}%)"
            )
            self.write_memory(f"mission_progress:{mid}", summary, "system", ttl=3600)
            print(f"[AgentCompany] {summary}")

    # ═══════════════════════════════════════════════════════
    # State Persistence (重啟不忘)
    # ═══════════════════════════════════════════════════════

    def _state_file(self):
        from pathlib import Path
        if isinstance(self._brain, Path):
            base = self._brain
        elif hasattr(self._brain, 'base_dir'):
            base = self._brain.base_dir
        else:
            base = Path("/tmp/.ampm_brain")
        return Path(base) / "data" / "agents" / "state.json"

    def _load_state(self):
        f = self._state_file()
        if not f.exists():
            return
        try:
            data = json.loads(open(str(f)).read())
            self._missions = data.get("missions", {})
            self._task_results = data.get("task_results", {})
            for t in data.get("task_queue", []):
                if t.get("status") == "pending":
                    self._task_queue.append(t)
            print(f"[AgentCompany] Loaded state: {len(self._missions)} missions, "
                  f"{len(self._task_queue)} pending tasks")
        except Exception as e:
            print(f"[AgentCompany] Load state failed: {e}")

    def _save_state(self):
        f = self._state_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "missions": {
                    mid: {
                        k: v for k, v in m.items()
                        if k != "sub_tasks" or not isinstance(v, list)
                        or all(not isinstance(x, dict) for x in v[:1])
                    }
                    for mid, m in self._missions.items()
                },
                "task_queue": [
                    {k: v for k, v in t.items() if k != "result" or isinstance(v, str)}
                    for t in self._task_queue[-100:]
                ],
                "task_results": {
                    tid: {k: v for k, v in t.items() if k != "result" or isinstance(v, (str, type(None)))}
                    for tid, t in list(self._task_results.items())[-200:]
                },
            }
            # Fix missions sub_tasks serialization
            for mid, m in self._missions.items():
                st = []
                for s in m.get("sub_tasks", []):
                    st.append({k: v for k, v in s.items() if k != "task_id" or isinstance(v, (str, type(None)))})
                data["missions"][mid]["sub_tasks"] = st
            open(str(f), 'w').write(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"[AgentCompany] Save state failed: {e}")

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            **self.get_global_stats(),
        }
        return {
            "name": self.name,
            "alive": self.is_alive(),
            **self.get_global_stats(),
        }


AgentManager = AgentTaskRouter

