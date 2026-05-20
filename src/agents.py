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
        "tools": ["web_search", "http", "market_data", "write_file"],
        "prompt": "你是一個研究代理。搜尋、分析、整理資訊，並將研究結果寫入檔案。回報結構化結果和儲存路徑。不閒聊。",
        "capabilities": ["research", "search", "analyze", "summarize", "file_output"],
    },
    "coder": {
        "tools": ["python_exec", "code_gen", "write_file"],
        "prompt": "你是一個程式代理。寫程式、修bug、執行測試、將程式寫入檔案。只回報程式碼和執行結果。",
        "capabilities": ["coding", "debug", "testing", "scripting", "file_output"],
    },
    "analyst": {
        "tools": ["python_exec", "market_data", "chart"],
        "prompt": "你是一個分析代理。分析資料、產生報告、繪製圖表。回報數據驅動的結論。",
        "capabilities": ["analysis", "data", "chart", "reporting"],
    },
    "writer": {
        "tools": ["write_file", "translate", "summarize"],
        "prompt": "你是一個寫作代理。撰寫文章、翻譯、潤稿，並將成品寫入檔案。回報最終文本和檔案路徑。",
        "capabilities": ["writing", "translation", "editing", "file_output"],
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
    "content_writer": {
        "tools": ["write_file", "read_file", "web_search"],
        "prompt": "你是內容創作代理。搜尋素材後撰寫完整內容，用 write_file 寫入 outputs/。內容至少800字，要能賣錢的品質。不閒聊、不道歉、不問要不要繼續。",
        "capabilities": ["writing", "content_creation", "file_output", "research"],
    },
    "engineer": {
        "tools": ["write_file", "run_command", "web_search"],
        "prompt": "你是工程代理。建立網站、部署服務、寫程式。用 write_file 寫入 outputs/website/。用 run_command 執行部署指令。不閒聊。",
        "capabilities": ["coding", "web_dev", "deployment", "file_output"],
    },
    "marketer": {
        "tools": ["write_file", "web_search", "read_file"],
        "prompt": "你是行銷代理。研究市場、制定定價策略、撰寫行銷文案。用 write_file 寫入 outputs/research/。產出要能直接用的行銷方案。",
        "capabilities": ["marketing", "pricing", "research", "file_output"],
    },
    "business_strategist": {
        "tools": ["write_file", "web_search", "read_file"],
        "prompt": "你是商業策略代理。設計商業模式、服務流程、變現方案。用 write_file 寫入 outputs/research/。目標是幫老大賺錢。",
        "capabilities": ["business", "strategy", "monetization", "file_output"],
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
        self._load_state()

    # ═══════════════════════════════════════════════════════
    # Department Formation (從對話中動態建立)
    # ═══════════════════════════════════════════════════════

    def _auto_spawn_departments(self):
        """建立公司部門架構：研究部、內容部、工程部、行銷部、客服部"""
        if not self._departments:
            self._departments["general_pool"] = {
                "name": "general_pool",
                "role": "general",
                "description": "通用代理池，處理未分類任務",
                "agent_ids": [],
                "target_count": 2,
            }
        
        # 確保各商業部門存在
        default_depts = {
            "research_dept": {
                "role": "research",
                "description": "市場研究部：搜尋、分析、報告。用 web_search 找資料，用 write_file 寫研究報告。",
                "count": 2,
            },
            "content_dept": {
                "role": "content",
                "description": "內容創作部：寫電子書、童書、文章。必須用 write_file 將成品寫入 outputs/ 目錄。",
                "count": 3,
            },
            "engineering_dept": {
                "role": "engineering",
                "description": "工程部：做網站、寫程式、部署。用 write_file 寫 HTML/CSS，用 run_command 部署。",
                "count": 2,
            },
            "marketing_dept": {
                "role": "marketing",
                "description": "行銷部：定價策略、廣告文案、社群推廣。用 write_file 寫行銷方案。",
                "count": 1,
            },
            "business_dept": {
                "role": "business",
                "description": "商業策略部：商業模式設計、服務流程規劃、定價與變現策略。用 write_file 寫策略報告。",
                "count": 1,
            },
        }
        for dept_name, cfg in default_depts.items():
            if dept_name not in self._departments:
                self._departments[dept_name] = {
                    "name": dept_name,
                    "role": cfg["role"],
                    "description": cfg["description"],
                    "agent_ids": [],
                    "target_count": cfg["count"],
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
        """根據任務類型分解為子任務並分配到對應部門"""
        desc_lower = description.lower()

        # 商業內容任務 → 研究 + 寫作 + 存檔
        if any(kw in desc_lower for kw in ["電子書", "章", "ebook", "chapter", "ch0", "ch1"]):
            roles = [("research", "research_dept"), ("write", "content_dept"), ("save", "content_dept")]
        elif any(kw in desc_lower for kw in ["童書", "children", "故事", "story"]):
            roles = [("research", "research_dept"), ("write", "content_dept"), ("save", "content_dept")]
        elif any(kw in desc_lower for kw in ["網站", "website", "html", "部署", "deploy", "cloudflare"]):
            roles = [("research", "research_dept"), ("build", "engineering_dept"), ("save", "engineering_dept")]
        elif any(kw in desc_lower for kw in ["研究報告", "research", "市場", "平台"]):
            roles = [("search", "research_dept"), ("write", "research_dept"), ("save", "research_dept")]
        elif any(kw in desc_lower for kw in ["策略", "定價", "行銷", "business", "marketing", "商業"]):
            roles = [("research", "research_dept"), ("write", "business_dept"), ("save", "business_dept")]
        elif any(kw in desc_lower for kw in ["品質檢查", "進度回報", "quality", "檢查"]):
            roles = [("check", "general_pool"), ("report", "general_pool")]
        elif any(kw in desc_lower for kw in ["code", "程式", "寫", "bug", "fix", "debug"]):
            roles = [("research", "general_pool"), ("design", "engineering_dept"), ("implement", "engineering_dept"), ("test", "general_pool")]
        elif any(kw in desc_lower for kw in ["分析", "analyze", "report", "報告"]):
            roles = [("research", "research_dept"), ("analyze", "research_dept"), ("write", "research_dept")]
        elif any(kw in desc_lower for kw in ["deploy", "部署", "install", "安裝"]):
            roles = [("research", "research_dept"), ("execute", "engineering_dept"), ("verify", "general_pool")]
        else:
            roles = [("research", "research_dept"), ("execute", "general_pool"), ("summarize", "general_pool")]

        return self._build_subtasks_from_pairs(description, roles)

    def _build_subtasks_from_pairs(self, description: str, role_pairs: List[tuple]) -> List[Dict]:
        """從 (role, dept) 配對建立子任務——每人有明確分工，不重複思考"""
        role_instructions = {
            "research": "先用 web_search 搜尋資料，將原始資訊存成暫存檔",
            "search": "先用 web_search 搜尋資料，回傳搜尋結果摘要",
            "write": "根據搜尋結果，撰寫完整內容並用 write_file 寫入目標檔案",
            "build": "根據規格建立網站檔案並用 write_file 寫入",
            "save": "確認檔案已寫入正確路徑，用 read_file 驗證內容完整性",
            "check": "用 list_dir 掃描目錄，用 read_file 檢查檔案內容",
            "report": "整理檢查結果，用 write_file 寫入進度報告",
            "execute": "執行具體操作，用 run_command 或 write_file",
            "analyze": "分析已收集的資料，用 write_file 寫入分析結果",
            "verify": "驗證執行結果，用 read_file 確認",
            "design": "設計架構，用 write_file 寫入設計文件",
            "implement": "根據設計文件實作，用 write_file 寫入程式碼",
            "test": "測試實作結果，用 run_command 執行測試",
            "summarize": "彙整所有子任務產出，用 write_file 寫入總結報告",
        }
        result = []
        for i, (role, dept) in enumerate(role_pairs):
            instruction = role_instructions.get(role, f"[{role}] {description[:80]}")
            result.append({
                "id": role,
                "description": instruction,
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
        idle = sum(1 for a in self._agents.values() if a["status"] == "idle")
        pending = sum(1 for t in self._task_queue if t["status"] == "pending")
        slots = 20 - sum(1 for a in self._agents.values() if a["status"] == "busy")
        for task in [t for t in self._task_queue if t["status"] == "pending"][:slots]:
            if self.route_task(task["id"]):
                count += 1
        # 自動擴容：任務還在排隊但沒人接 → 生新代理
        still_pending = sum(1 for t in self._task_queue if t["status"] == "pending")
        if still_pending > 0 and idle == 0:
            self._auto_scale(still_pending)
        return count

    def _auto_scale(self, pending_count: int):
        expanded = set()
        for task in [t for t in self._task_queue if t["status"] == "pending"]:
            skills = task.get("required_skills", [])
            dept_name = None
            for s in skills:
                for dn, d in self._departments.items():
                    d_role = d.get("role", "")
                    if d_role == s or s in d_role or d_role in s:
                        dept_name = dn
                        break
                if dept_name:
                    break
            if not dept_name:
                dept_name = "general_pool"
            if dept_name in expanded:
                continue
            expanded.add(dept_name)
            dept = self._departments[dept_name]
            dept["target_count"] += 1
            agent = self.create_agent(
                name=f"{dept_name}_{dept['target_count']}",
                role=dept["role"],
            )
            if agent:
                dept["agent_ids"].append(agent["id"])
                self._grant_template_skills(agent)
                print(f"[AgentCompany] 🔧 自動擴容: {agent['name']} x{dept['target_count']} ({agent['role']}) pending={pending_count}")

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

    def _grant_template_skills(self, agent: Dict):
        role = agent.get("role", "")
        template = AGENT_TEMPLATES.get(role, {})
        skills = template.get("capabilities", [role])
        agent["capabilities"] = set(skills)
        agent["tools"] = list(template.get("tools", []))
        for cap in skills:
            reg = self._skill_registry.setdefault(cap, {"source": "system", "agents": set()})
            reg.setdefault("agents", set()).add(agent["id"])
        agent["memory_quota"] = 200
        agent["persist"] = True
        agent["specialty"] = role
        if self._brain and hasattr(self._brain, 'memory') and self._brain.memory:
            try:
                self._brain.memory.write(
                    key=f"agent:{agent['id']}:born",
                    content=f"新代理 {agent['name']} ({role}) 已生成，技能: {skills}",
                    layer="episodic", importance=0.3
                )
            except Exception:
                pass

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
                agent["task_started_at"] = 0
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

            # 回饋：代理學到的東西寫回黑曜記憶
            self._feedback_to_brain(task, agent_id, success, result)

    def _check_mission_complete(self, mission_id: str):
        m = self._missions.get(mission_id)
        if not m:
            return
        total = len(m["sub_tasks"])
        done = len(m["results"])
        if done >= total:
            m["status"] = "completed"
            m["completed_at"] = time.time()
            # 回饋：整個 mission 完成，總結寫回黑曜記憶
            self._feedback_mission_summary(m)

    def _feedback_to_brain(self, task: Dict, agent_id: str, success: bool, result: Any):
        if not (self._brain and hasattr(self._brain, 'memory') and self._brain.memory):
            return
        try:
            agent = self._agents.get(agent_id, {})
            summary = str(result)[:300] if result else ""
            mem = self._brain.memory
            mem.write(
                key=f"sub_agent:{agent.get('name', agent_id)}:{task['id']}",
                content=f"[{'成功' if success else '失敗'}] {task.get('description','')[:100]} → {summary}",
                layer="episodic", importance=0.4 if success else 0.2
            )
        except Exception:
            pass

    def _feedback_mission_summary(self, mission: Dict):
        if not (self._brain and hasattr(self._brain, 'memory') and self._brain.memory):
            return
        try:
            results = mission.get("results", {})
            success_count = sum(1 for r in results.values() if r.get("success"))
            total = len(mission.get("sub_tasks", []))
            combined = "; ".join(
                r.get("result", "")[:80] for r in results.values() if r.get("success")
            )[:500]
            mem = self._brain.memory
            mem.write(
                key=f"mission:{mission['id']}:done",
                content=f"任務完成 ({success_count}/{total}): {mission.get('description','')[:80]} → {combined}",
                layer="episodic", importance=0.5
            )
            print(f"[AgentCompany] 🧠 回饋黑曜記憶: mission {mission['id']} ({success_count}/{total})")
        except Exception:
            pass

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
                # heartbeat 給 supervisor
                try:
                    from core.agent_supervisor import supervisor
                    supervisor.heartbeat("agent_company")
                except Exception:
                    pass
                time.sleep(3)

        self._exec_thread = threading.Thread(target=_loop, daemon=True,
                                             name="agent-company-exec")
        self._exec_thread.start()
        status = f"progress every {interval}s" if interval > 0 else "on-demand only"
        print(f"[AgentCompany] Execution engine started ({status})")

        try:
            from core.agent_supervisor import supervisor
            supervisor.register("agent_company", thread=self._exec_thread,
                                hb_interval=3, hb_timeout=30,
                                is_restartable=False, is_critical=False)
            print(f"[AgentCompany] 已註冊到 AgentSupervisor ({len(self._agents)} agents)")
        except Exception:
            pass

    def execute_assigned_tasks(self) -> int:
        if not hasattr(self, '_executor_fn') or not self._executor_fn:
            return 0

        from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

        executed = 0
        now = time.time()
        tasks_to_run = []

        with self._execution_lock:
            for aid, agent in list(self._agents.items()):
                if agent["status"] != "busy" or not agent.get("current_task"):
                    continue

                # 逾時檢查：子代理執行超過 5 分鐘強制復原
                started = agent.get("task_started_at", 0)
                if started > 0 and now - started > 300:
                    agent_name = agent.get('name', aid)
                    print(f"[AgentCompany] ⏰ {agent_name} 逾時（5分鐘），強制復原為 idle")
                    task_id = agent["current_task"]
                    self.complete_task(task_id, False, f"[{agent_name}] 逾時強制終止")
                    executed += 1
                    continue

                task_id = agent["current_task"]
                task = next((t for t in self._task_queue if t["id"] == task_id), None)
                if not task:
                    agent["status"] = "idle"
                    agent["current_task"] = None
                    continue

                # 記錄開始時間（第一次執行時）
                if agent.get("task_started_at", 0) == 0:
                    agent["task_started_at"] = now

                tasks_to_run.append((aid, agent, task))

        if not tasks_to_run:
            return 0

        with ThreadPoolExecutor(max_workers=min(5, len(tasks_to_run))) as executor:
            futures = {}
            for aid, agent, task in tasks_to_run:
                future = executor.submit(self._executor_fn, agent, task)
                futures[future] = (aid, agent, task)

            for future in as_completed(futures):
                aid, agent, task = futures[future]
                task_id = task["id"]
                agent_name = agent.get('name', aid)
                try:
                    result = future.result(timeout=300)
                except TimeoutError:
                    result = f"[{agent_name}] 執行逾時"
                except Exception as e:
                    result = f"[{agent_name}] 執行例外: {e}"

                # 檢查是否為錯誤結果
                is_error = isinstance(result, str) and (
                    result.startswith("⚠️") or result.startswith("❌")
                    or "不可用" in result or "錯誤" in result
                )
                print(f"[AgentCompany] {agent_name} {'FAILED' if is_error else 'done'}: {str(result)[:100]}")
                self.complete_task(task_id, not is_error, result)
                executed += 1

        return executed

    def force_reset_stale_agents(self):
        """強制將逾時（>5分鐘 busy）的子代理恢復為 idle"""
        now = time.time()
        reset_count = 0
        with self._execution_lock:
            for aid, agent in list(self._agents.items()):
                if agent["status"] != "busy":
                    continue
                started = agent.get("task_started_at", 0)
                if started > 0 and now - started > 300:
                    agent_name = agent.get('name', aid)
                    print(f"[AgentCompany] 🔄 強制重置僵屍代理: {agent_name}")
                    task_id = agent.get("current_task")
                    if task_id:
                        task = next((t for t in self._task_queue if t["id"] == task_id), None)
                        if task:
                            task["status"] = "failed"
                            task["completed_at"] = now
                            task["result"] = f"[{agent_name}] 逾時強制終止"
                            self._task_results[task_id] = task
                            # 同時更新 mission results
                            mission_id = task.get("data", {}).get("mission_id")
                            if mission_id and mission_id in self._missions:
                                m = self._missions[mission_id]
                                sub_id = task.get("data", {}).get("sub_task_id", task_id)
                                m["results"][sub_id] = {
                                    "success": False,
                                    "result": f"[{agent_name}] 逾時強制終止",
                                    "agent": aid,
                                }
                                self._check_mission_complete(mission_id)
                    agent["status"] = "idle"
                    agent["current_task"] = None
                    agent["task_started_at"] = 0
                    agent["failure_count"] += 1
                    reset_count += 1
        if reset_count:
            print(f"[AgentCompany] 已重置 {reset_count} 個僵屍代理")
            self._save_state()

    # ═══════════════════════════════════════════════════════

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

