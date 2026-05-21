"""
TaskSchedulerOrgan — 任務排程器官
優先級任務佇列，支援截止日追蹤、逾期警告與每日摘要。
（註意：任務分解邏輯在 task_planner.py 中）
"""
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

VALID_STATUSES = {"pending", "in_progress", "completed", "cancelled", "blocked"}


class TaskSchedulerOrgan(BrainComponent):
    """
    任務排程器官

    功能：
    1. 優先級任務佇列（1-5，1 為最高優先）
    2. 五種狀態：pending / in_progress / completed / cancelled / blocked
    3. 截止日追蹤與逾期警告
    4. 每日任務摘要（含完成率）
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._counter = 0
        # 硬碟持久化
        self._data_dir = Path(dna.get("data_dir", "data/planner")) if dna else Path("data/planner")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._tasks_file = self._data_dir / "tasks.json"
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            if self._tasks_file.exists():
                data = json.loads(self._tasks_file.read_text())
                self.tasks = data.get("tasks", {})
                self._counter = data.get("counter", 0)
        except Exception:
            pass

    def _save_to_disk(self):
        try:
            self._tasks_file.write_text(json.dumps(
                {"tasks": self.tasks, "counter": self._counter},
                ensure_ascii=False, indent=2))
        except Exception:
            pass

    # ── 公開方法 ──────────────────────────────────────────────

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: int = 3,
        deadline: Optional[str] = None,
    ) -> str:
        """
        新增任務到排程佇列。

        參數：
            title: 任務標題
            description: 任務描述
            priority: 優先級 1-5（1 最高）
            deadline: 截止日 ISO 格式字串（可選）

        回傳：
            確認訊息（含任務 ID）
        """
        if not title.strip():
            return "❌ 任務標題不可為空"
        if priority < 1 or priority > 5:
            return "❌ 優先級必須為 1-5"
        if deadline:
            try:
                datetime.fromisoformat(deadline)
            except (ValueError, TypeError):
                return "❌ 截止日格式錯誤，請使用 ISO 格式 (YYYY-MM-DDTHH:MM:SS)"

        self._counter += 1
        task_id = f"T{self._counter:04d}-{uuid.uuid4().hex[:4]}"
        now = datetime.now()

        self.tasks[task_id] = {
            "id": task_id,
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority,
            "deadline": deadline,
            "status": "pending",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "completed_at": None,
            "overdue_warned": False,
        }

        self._save_to_disk()

        ddl_info = f"\n  截止日: {deadline}" if deadline else ""
        return (
            f"✅ 已新增任務 (ID: {task_id})\n"
            f"  標題: {title}\n"
            f"  優先級: {'🔥' * (6 - priority)} ({priority})\n"
            f"  狀態: pending{ddl_info}"
        )

    def get_next_task(self) -> str:
        """
        取得下一個應執行的任務（最高優先級的待處理任務）。

        回傳：
            任務詳情或無任務提示
        """
        pending = self._get_tasks_by_status("pending")
        if not pending:
            return "📭 目前沒有待處理的任務"

        # 按優先級排序（數字越小越優先），同級則按建立時間
        pending.sort(key=lambda t: (t["priority"], t["created_at"]))

        next_task = pending[0]
        # 標記為進行中
        next_task["status"] = "in_progress"
        next_task["updated_at"] = datetime.now().isoformat()

        return self._format_task(next_task, "▶ 下一個任務")

    def complete_task(self, task_id: str) -> str:
        """
        將指定任務標記為已完成。

        參數：
            task_id: 任務 ID

        回傳：
            完成確認訊息
        """
        task = self.tasks.get(task_id)
        if not task:
            return f"❌ 找不到任務: {task_id}"

        if task["status"] == "completed":
            return f"⚠️ 任務 {task_id} 已是完成狀態"

        now = datetime.now()
        task["status"] = "completed"
        task["completed_at"] = now.isoformat()
        task["updated_at"] = now.isoformat()
        self._save_to_disk()

        created = datetime.fromisoformat(task["created_at"])
        duration = now - created

        return (
            f"✅ 已完成任務 {task_id}: {task['title']}\n"
            f"  耗時: {self._format_duration(duration)}\n"
            f"  優先級: {task['priority']}"
        )

    def update_task_status(self, task_id: str, new_status: str) -> str:
        """
        更新任務狀態。

        參數：
            task_id: 任務 ID
            new_status: 新狀態 (pending/in_progress/cancelled/blocked)

        回傳：
            狀態變更確認
        """
        task = self.tasks.get(task_id)
        if not task:
            return f"❌ 找不到任務: {task_id}"

        if new_status not in VALID_STATUSES:
            return f"❌ 無效狀態: {new_status}，有效狀態: {', '.join(VALID_STATUSES)}"

        if new_status == "completed":
            return self.complete_task(task_id)

        old_status = task["status"]
        task["status"] = new_status
        task["updated_at"] = datetime.now().isoformat()
        self._save_to_disk()

        return (
            f"🔄 任務 {task_id} 狀態變更: {old_status} → {new_status}"
        )

    def list_tasks(self, status: Optional[str] = None) -> str:
        """
        列出任務，可按狀態過濾。

        參數：
            status: 過濾狀態（可選），不指定則回傳全部

        回傳：
            格式化的任務清單
        """
        if status and status not in VALID_STATUSES:
            return f"❌ 無效狀態: {status}，有效狀態: {', '.join(VALID_STATUSES)}"

        tasks = self._get_tasks_by_status(status) if status else list(self.tasks.values())

        if not tasks:
            label = f"「{status}」" if status else ""
            return f"📭 目前沒有{label}任務"

        # 依優先級排序
        tasks.sort(key=lambda t: (t["priority"], t["created_at"]))

        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
            "blocked": "🚫",
        }

        label = f"({status}) " if status else ""
        lines = [f"📋 任務清單 {label}共 {len(tasks)} 項:"]
        for i, task in enumerate(tasks, 1):
            icon = status_icons.get(task["status"], "·")
            overdue = self._check_overdue(task)
            lines.append(
                f"  {i:2d}. {icon} [{task['priority']}] {task['title'][:50]}"
                f" — {task['status']}{' ⚠逾期' if overdue else ''}"
            )
        return "\n".join(lines)

    def get_daily_summary(self) -> str:
        """
        取得今日任務摘要，包含完成率與逾期警告。

        回傳：
            每日摘要
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        all_tasks = list(self.tasks.values())
        created_today = [
            t for t in all_tasks
            if datetime.fromisoformat(t["created_at"]) >= today_start
        ]
        completed_today = [
            t for t in all_tasks
            if t.get("completed_at") and datetime.fromisoformat(t["completed_at"]) >= today_start
        ]
        overdue = [t for t in all_tasks if self._check_overdue(t)]

        total = len(all_tasks)
        completed_total = sum(1 for t in all_tasks if t["status"] == "completed")
        rate = round(completed_total / total * 100, 1) if total > 0 else 0.0

        by_status: Dict[str, int] = {}
        for t in all_tasks:
            s = t["status"]
            by_status[s] = by_status.get(s, 0) + 1

        bar_len = 20
        filled = int(bar_len * rate / 100)
        bar = "▓" * filled + "░" * (bar_len - filled)

        lines = [
            f"📊 每日任務摘要 — {now.strftime('%Y-%m-%d')}",
            f"  ─────────────────────────",
            f"  總任務: {total}",
            f"  完成率: [{bar}] {rate}%",
            f"  今日新增: {len(created_today)}",
            f"  今日完成: {len(completed_today)}",
            f"  ⚠ 逾期: {len(overdue)}",
            f"  狀態分佈: ",
        ]
        for s in ["pending", "in_progress", "completed", "blocked", "cancelled"]:
            count = by_status.get(s, 0)
            if count > 0:
                lines.append(f"    {s}: {count}")

        if overdue:
            lines.append(f"  逾期任務:")
            for t in overdue[:5]:
                lines.append(f"    · [{t['priority']}] {t['title'][:60]} — 截止: {t.get('deadline')}")

        return "\n".join(lines)

    # ── 內部方法 ──────────────────────────────────────────────

    def _get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """依狀態過濾任務。"""
        return [t for t in self.tasks.values() if t.get("status") == status]

    def _check_overdue(self, task: Dict[str, Any]) -> bool:
        """
        檢查任務是否逾期。
        逾期條件：未完成 且 截止日已過。
        """
        if task.get("status") in ("completed", "cancelled"):
            return False
        deadline = task.get("deadline")
        if not deadline:
            return False
        try:
            ddl = datetime.fromisoformat(deadline)
        except (ValueError, TypeError):
            return False
        is_overdue = datetime.now() > ddl
        if is_overdue and not task.get("overdue_warned"):
            task["overdue_warned"] = True
        return is_overdue

    def _format_task(self, task: Dict[str, Any], prefix: str = "") -> str:
        """格式化單一任務顯示。"""
        overdue = " ⚠ 已逾期" if self._check_overdue(task) else ""
        lines = [f"{prefix}: {task['title']}"]
        lines.append(f"  ID: {task['id']}")
        lines.append(f"  優先級: {task['priority']}")
        if task.get("description"):
            lines.append(f"  描述: {task['description'][:120]}")
        if task.get("deadline"):
            lines.append(f"  截止日: {task['deadline']}{overdue}")
        lines.append(f"  狀態: {task['status']}")
        return "\n".join(lines)

    @staticmethod
    def _format_duration(td: timedelta) -> str:
        """格式化時間差為可讀字串。"""
        total_seconds = int(td.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}秒"
        if total_seconds < 3600:
            return f"{total_seconds // 60}分{total_seconds % 60}秒"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours < 24:
            return f"{hours}時{minutes}分"
        days = hours // 24
        hours = hours % 24
        return f"{days}天{hours}時{minutes}分"

    # ── 器官狀態 ──────────────────────────────────────────────

    def status(self) -> dict:
        total = len(self.tasks)
        by_status: Dict[str, int] = {}
        for t in self.tasks.values():
            s = t["status"]
            by_status[s] = by_status.get(s, 0) + 1

        overdue_count = sum(1 for t in self.tasks.values() if self._check_overdue(t))

        return {
            "name": "TaskSchedulerOrgan",
            "alive": True,
            "total_tasks": total,
            "by_status": by_status,
            "overdue": overdue_count,
        }


PlannerOrgan = TaskSchedulerOrgan
