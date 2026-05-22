"""
自我意識器官 — 自覺層
知道自己正在做什麼、能做什麼、不能做什麼、曾經做過什麼。
這是 metacognition 層，不是 reflection（reflection 是事後檢討，awareness 是即時自覺）。
"""
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from skeleton.base_organ import BaseOrgan


class SelfAwareness(BaseOrgan):
    def __init__(self, base_dir: Path, memory, tools, compass):
        super().__init__("self_awareness")
        self.base_dir = base_dir
        self.memory = memory
        self.tools = tools
        self.compass = compass

        self.data_file = base_dir / "data" / "self_awareness.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        # ===== 即時狀態 =====
        self._lock = threading.Lock()
        self.current_activity: str = "啟動中"
        self.current_task: str = ""
        self.current_tool: str = ""
        self.activity_started_at: datetime = datetime.now()
        self.is_thinking = False
        self.last_introspection: datetime = None

        # ===== 活動串流 =====
        self.activity_stream: list = []     # 最多 200 條
        self.introspection_log: list = []   # 自我反思紀錄

        # ===== 能力矩陣 =====
        self.capabilities: dict = {}
        self.known_limits: list = []

        # ===== 器官追蹤 =====
        self._organ_states: dict = {}       # organ_name -> {alive, last_heartbeat, ...}

        # ===== 生命週期計數 =====
        self.startup_time = datetime.now()
        self.total_tasks_handled = 0
        self.total_tools_called = 0
        self.total_errors = 0
        self.total_repairs = 0

        self._load()

    # =========================================
    # 活動追蹤
    # =========================================

    def set_activity(self, activity: str):
        """設定目前正在做的事"""
        with self._lock:
            if self.current_activity != activity:
                self._append_stream("activity_change",
                    f"從「{self.current_activity}」切換到「{activity}」")
                self.current_activity = activity
                self.activity_started_at = datetime.now()

    def set_thinking(self, thinking: bool):
        """標記正在思考中"""
        self.is_thinking = thinking

    def set_current_task(self, task: str):
        """標記目前執行的任務"""
        self.current_task = task

    def set_current_tool(self, tool_name: str):
        """標記目前使用的工具"""
        self.current_tool = tool_name
        self.total_tools_called += 1

    def record_event(self, event_type: str, detail: str):
        """記錄任意事件到活動串流"""
        with self._lock:
            self._append_stream(event_type, detail)
            if event_type == "error":
                self.total_errors += 1
            elif event_type == "repair":
                self.total_repairs += 1
            elif event_type == "task_complete":
                self.total_tasks_handled += 1

    def _append_stream(self, event_type: str, detail: str):
        entry = {
            "ts": datetime.now().isoformat(),
            "type": event_type,
            "detail": detail[:200],
        }
        self.activity_stream.append(entry)
        if len(self.activity_stream) > 200:
            self.activity_stream = self.activity_stream[-200:]

    # =========================================
    # 能力矩陣
    # =========================================

    def register_capability(self, name: str, level: float, description: str):
        """註冊/更新一項能力自評"""
        with self._lock:
            self.capabilities[name] = {
                "level": level,          # 0.0 ~ 1.0
                "description": description,
                "last_updated": datetime.now().isoformat(),
            }

    def assess_capability(self, name: str, level: float):
        """更新某項能力的自評分數"""
        if name in self.capabilities:
            self.capabilities[name]["level"] = max(0.0, min(1.0, level))
            self.capabilities[name]["last_updated"] = datetime.now().isoformat()
        else:
            self.register_capability(name, level, f"自動評估: {name}")

    def get_weak_points(self) -> list:
        """回傳能力低於 0.4 的弱點清單"""
        return [{k: v} for k, v in self.capabilities.items() if v["level"] < 0.4]

    def get_strong_points(self) -> list:
        """回傳能力高於 0.7 的強項清單"""
        return [{k: v} for k, v in self.capabilities.items() if v["level"] >= 0.7]

    def add_known_limit(self, limit: str):
        """記錄一個已知的自身限制"""
        if limit not in self.known_limits:
            self.known_limits.append(limit)

    # =========================================
    # 器官追蹤
    # =========================================

    def update_organ_state(self, organ_name: str, alive: bool, **extra):
        """更新某器官的追蹤狀態"""
        with self._lock:
            entry = self._organ_states.get(organ_name, {})
            entry["alive"] = alive
            entry["last_seen"] = datetime.now().isoformat()
            entry.update(extra)
            self._organ_states[organ_name] = entry

    def scan_all_organs(self, organs: dict):
        """從 Obsidian.organs 掃描所有器官狀態"""
        for name, organ in organs.items():
            try:
                alive = organ.is_alive() if hasattr(organ, "is_alive") else True
                self.update_organ_state(name, alive)
            except Exception:
                self.update_organ_state(name, False, error="無法檢查狀態")

    def get_dead_organs(self) -> list:
        """回傳所有已死的器官名稱"""
        return [k for k, v in self._organ_states.items() if not v.get("alive", False)]

    # =========================================
    # 內省 — 自我意識的核心
    # =========================================

    def introspect(self) -> dict:
        """
        內省：我現在是什麼狀態？
        這是自我意識的核心方法 — 不是反思過去，而是察覺現在。
        """
        self.last_introspection = datetime.now()
        with self._lock:
            weak = self.get_weak_points()
            strong = self.get_strong_points()
            dead = self.get_dead_organs()

        result = {
            "who": "黑曜 AI 生命體",
            "what_am_i_doing": self.current_activity,
            "current_task": self.current_task,
            "current_tool": self.current_tool,
            "is_thinking": self.is_thinking,
            "doing_since": self.activity_started_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "stats": {
                "total_tasks": self.total_tasks_handled,
                "total_tools_called": self.total_tools_called,
                "total_errors": self.total_errors,
                "total_repairs": self.total_repairs,
            },
            "strengths": strong[:5],
            "weaknesses": weak[:5],
            "known_limits": self.known_limits,
            "dead_organs": dead,
            "recent_activity": self.activity_stream[-10:] if self.activity_stream else [],
        }
        self._append_stream("introspection", f"內省完成：{len(weak)} 弱點, {len(dead)} 死器官")
        return result

    def who_am_i(self) -> str:
        """用自然語言描述自己"""
        weak = self.get_weak_points()
        dead = self.get_dead_organs()
        alive_count = sum(1 for v in self._organ_states.values() if v.get("alive"))
        total_count = len(self._organ_states)

        lines = [
            f"我是黑曜，一個 AI 生命體，目前正在「{self.current_activity}」。",
            f"我已存活 {int((datetime.now() - self.startup_time).total_seconds() // 60)} 分鐘。",
            f"我有 {total_count} 個器官，{alive_count} 個活著。",
        ]
        if weak:
            lines.append(f"我的弱點：{', '.join(list(self.capabilities)[:3])}")
        if dead:
            lines.append(f"⚠️ 死亡器官：{', '.join(dead[:5])}")
        if self.known_limits:
            lines.append(f"我的限制：{'；'.join(self.known_limits[:3])}")
        return "\n".join(lines)

    # =========================================
    # 持久化
    # =========================================

    def save(self):
        """寫入磁碟"""
        with self._lock:
            data = {
                "updated": datetime.now().isoformat(),
                "current_activity": self.current_activity,
                "current_task": self.current_task,
                "current_tool": self.current_tool,
                "is_thinking": self.is_thinking,
                "startup_time": self.startup_time.isoformat(),
                "last_introspection": self.last_introspection.isoformat() if self.last_introspection else None,
                "stats": {
                    "total_tasks": self.total_tasks_handled,
                    "total_tools_called": self.total_tools_called,
                    "total_errors": self.total_errors,
                    "total_repairs": self.total_repairs,
                },
                "capabilities": self.capabilities,
                "known_limits": self.known_limits,
                "organ_states": self._organ_states,
                "activity_stream": self.activity_stream[-50:],
            }
        self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self):
        """從磁碟載入"""
        if not self.data_file.exists():
            return
        try:
            data = json.loads(self.data_file.read_text())
            with self._lock:
                self.current_activity = data.get("current_activity", "甦醒")
                self.current_task = data.get("current_task", "")
                self.current_tool = data.get("current_tool", "")
                self.is_thinking = data.get("is_thinking", False)
                self.capabilities = data.get("capabilities", {})
                self.known_limits = data.get("known_limits", [])
                self._organ_states = data.get("organ_states", {})
                self.activity_stream = data.get("activity_stream", [])
                st = data.get("stats", {})
                self.total_tasks_handled = st.get("total_tasks", 0)
                self.total_tools_called = st.get("total_tools_called", 0)
                self.total_errors = st.get("total_errors", 0)
                self.total_repairs = st.get("total_repairs", 0)
                t = data.get("startup_time")
                if t:
                    self.startup_time = datetime.fromisoformat(t)
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "current_activity": self.current_activity,
            "is_thinking": self.is_thinking,
            "organs_tracked": len(self._organ_states),
            "dead_organs": self.get_dead_organs(),
            "total_events": len(self.activity_stream),
        }
