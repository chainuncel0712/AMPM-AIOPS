"""
ProactiveExecutor — 主動執行器
讓黑曜從被動等待變成主動自治 AI：
1. 定期掃描任務佇列，自動執行 pending 任務
2. 偵測系統異常，自動建立並執行修復任務
3. 透過 Telegram 回報進度
"""
import threading
import time
import json
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_ACTIVE_EXECUTORS: Dict[str, "ProactiveExecutor"] = {}


class ProactiveExecutor:
    """
    主動執行器 — 背景 daemon 執行緒
    """

    def __init__(self, obsidian: Any):
        self.obsidian = obsidian
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._last_scan_time = 0
        self._current_task_id: Optional[str] = None
        self._current_mission_id: Optional[str] = None
        self._pending_missions: Dict[str, str] = {}  # task_id -> mission_id

        # 全域單例註冊（供 supervisor 心跳用）
        _ACTIVE_EXECUTORS["proactive_executor"] = self

    @property
    def planner(self):
        """取得 PlannerOrgan (TaskSchedulerOrgan)"""
        return (
            self.obsidian.organs.get("plannerorgan")
            or self.obsidian.organs.get("taskschedulerorgan")
        )

    @property
    def agents(self):
        """取得 AgentTaskRouter"""
        return (
            self.obsidian.organs.get("agent_company")
            or getattr(self.obsidian, "agents", None)
        )

    def is_alive(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {
            "name": "ProactiveExecutor",
            "alive": self.is_alive(),
            "current_task": self._current_task_id,
            "current_mission": self._current_mission_id,
            "pending_missions": len(self._pending_missions),
            "last_scan": datetime.fromtimestamp(self._last_scan_time).isoformat() if self._last_scan_time else None,
        }

    # ── 啟動 / 停止 ──────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="proactive-executor"
        )
        self._thread.start()
        print("[ProactiveExecutor] ✅ 主動執行器已啟動")

        # 註冊到 supervisor
        try:
            from core.agent_supervisor import supervisor
            supervisor.register(
                "proactive_executor",
                thread=self._thread,
                hb_interval=30,
                hb_timeout=120,
                is_restartable=False,
                is_critical=True,
            )
        except Exception:
            pass

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    # ── 主要迴圈 ────────────────────────────────────────────

    def _loop(self):
        print("[ProactiveExecutor] 🔄 主動工作迴圈啟動")
        while self._running:
            try:
                self._last_scan_time = time.time()

                # 1. 檢查並執行 pending 任務
                self._execute_pending_tasks()

                # 2. 檢查目前 mission 的完成狀態
                self._check_mission_completions()

                # 3. 主動偵測系統問題並建立修復任務
                self._scan_for_problems()

                # 心跳
                try:
                    from core.agent_supervisor import supervisor
                    supervisor.heartbeat("proactive_executor")
                except Exception:
                    pass

            except Exception as e:
                print(f"[ProactiveExecutor] 迴圈錯誤: {e}")
                traceback.print_exc()

            time.sleep(30)

    # ── 1. 執行 pending 任務 ─────────────────────────────────

    def _execute_pending_tasks(self):
        planner = self.planner
        agents = self.agents

        if not planner or not agents:
            return

        # 如果 agent_company 正在忙，等一下
        stats = agents.get_global_stats() if hasattr(agents, "get_global_stats") else {}
        busy_agents = stats.get("agents_busy", 0)
        if busy_agents > 10:
            return  # 代理太忙，不塞新任務

        # 取得所有 pending 任務
        pending = [
            t for t in planner.tasks.values()
            if t.get("status") == "pending"
            and t.get("id") not in self._pending_missions
        ]
        if not pending:
            return

        # 按優先級排序（數字越小越優先）
        pending.sort(key=lambda t: (t["priority"], t["created_at"]))

        # 一次拿一個最高優先級任務
        task = pending[0]

        # 標記為 in_progress
        task["status"] = "in_progress"
        task["updated_at"] = datetime.now().isoformat()
        planner._save_to_disk()

        # 建立任務描述
        desc = f"{task['title']}"
        if task.get("description"):
            desc += f"：{task['description'][:200]}"

        print(f"[ProactiveExecutor] 🚀 自動執行: {task['id']} - {task['title']} (優先級={task['priority']})")

        try:
            mission_id = agents.launch_mission(desc)
            if mission_id:
                self._pending_missions[task["id"]] = mission_id
                self._current_task_id = task["id"]
                self._current_mission_id = mission_id
                self._notify_user(
                    f"🚀 黑曜自主啟動任務\n"
                    f"📋 {task['title']}\n"
                    f"🆔 {task['id']}\n"
                    f"🔢 優先級: {'🔥' * (6 - task['priority'])}"
                )
                print(f"[ProactiveExecutor] → mission {mission_id}")
            else:
                # 任務啟動失敗，恢復 pending
                planner.update_task_status(task["id"], "pending")
        except Exception as e:
            print(f"[ProactiveExecutor] 啟動 mission 失敗: {e}")
            planner.update_task_status(task["id"], "pending")

    # ── 2. 檢查 mission 完成狀態 ──────────────────────────────

    def _check_mission_completions(self):
        agents = self.agents
        planner = self.planner

        if not agents or not planner:
            return

        completed_ids = []
        for task_id, mission_id in list(self._pending_missions.items()):
            mission = agents.get_mission(mission_id) if hasattr(agents, "get_mission") else None

            if not mission:
                continue

            status = mission.get("status", "")

            if status == "completed":
                # 完成！
                results = mission.get("results", {})
                success_count = sum(1 for r in results.values() if r.get("success"))
                total = len(mission.get("sub_tasks", []))

                planner.complete_task(task_id)
                completed_ids.append(task_id)

                task = planner.tasks.get(task_id, {})
                self._notify_user(
                    f"✅ 黑曜完成任務\n"
                    f"📋 {task.get('title', task_id)}\n"
                    f"🆔 {task_id}\n"
                    f"📊 子任務: {success_count}/{total} 成功"
                )
                print(f"[ProactiveExecutor] ✅ 任務完成: {task_id} ({success_count}/{total})")

                self._current_task_id = None
                self._current_mission_id = None

            elif status == "failed":
                planner.update_task_status(task_id, "pending")
                completed_ids.append(task_id)
                print(f"[ProactiveExecutor] ❌ 任務失敗: {task_id}")

                self._current_task_id = None
                self._current_mission_id = None

        for tid in completed_ids:
            self._pending_missions.pop(tid, None)

    # ── 3. 主動找問題 ───────────────────────────────────────

    def _scan_for_problems(self):
        """主動掃描系統，發現問題自動建立任務並執行"""
        planner = self.planner
        if not planner:
            return

        problems = []

        # 3a. 檢查記憶是否過多需要壓縮
        try:
            mem = getattr(self.obsidian, "memory", None)
            if mem:
                count = len(getattr(mem, "_texts", [])) if hasattr(mem, "_texts") else 0
                if count > 500:
                    problems.append({
                        "title": "記憶壓縮",
                        "description": f"記憶已達 {count} 條（超過 500 條閾值），需要壓縮以維持效能",
                        "priority": 3,
                    })
        except Exception:
            pass

        # 3b. 檢查 organ 是否有 dead/zombie 狀態
        try:
            for name, organ in self.obsidian.organs.items():
                if hasattr(organ, "is_alive") and not organ.is_alive():
                    problems.append({
                        "title": f"器官修復: {name}",
                        "description": f"器官 {name} 已死亡，需要修復或重啟",
                        "priority": 1,
                    })
        except Exception:
            pass

        # 3c. 檢查進化循環是否太久沒執行
        try:
            ec = getattr(self.obsidian, "evolution_cycle", None) or self.obsidian.organs.get("evolution_cycle")
            if ec and hasattr(ec, "status"):
                st = ec.status()
                cycles = st.get("cycles", 0)
        except Exception:
            pass

        # 3d. 檢查是否有長期 pending 的任務（超過 24 小時）
        try:
            now = datetime.now()
            for task in planner.tasks.values():
                if task.get("status") == "pending":
                    created = datetime.fromisoformat(task["created_at"])
                    hours_pending = (now - created).total_seconds() / 3600
                    if hours_pending > 24:
                        problems.append({
                            "title": f"逾期任務警報",
                            "description": f"任務 {task['id']}「{task['title']}」已 pending {hours_pending:.0f} 小時，需要關注",
                            "priority": 2,
                        })
        except Exception:
            pass

        # 如果有發現問題，加入任務佇列
        for problem in problems:
            # 避免重複建立同名任務
            existing = [
                t for t in planner.tasks.values()
                if t.get("title") == problem["title"] and t.get("status") == "pending"
            ]
            if existing:
                continue

            planner.add_task(
                title=problem["title"],
                description=problem["description"],
                priority=problem["priority"],
            )
            print(f"[ProactiveExecutor] 🔍 發現問題，建立任務: {problem['title']}")

    # ── Telegram 通知 ────────────────────────────────────────

    def _notify_user(self, message: str):
        """透過 Telegram 發送通知給使用者"""
        token = getattr(self.obsidian, "telegram_token", None)
        chat_id = getattr(self.obsidian, "telegram_chat_id", None)

        if not token or not chat_id:
            return

        try:
            import urllib.request
            import urllib.parse

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": message[:4000],
                "parse_mode": "Markdown",
            }).encode()

            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
