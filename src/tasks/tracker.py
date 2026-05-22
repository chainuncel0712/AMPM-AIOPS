"""
任務追蹤 - 管理待辦事項
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class TaskTracker:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.tasks_file = self.base_dir / "data" / "tasks" / "tasks.json"
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self.tasks = self._load()
    
    def _load(self) -> List[Dict]:
        if self.tasks_file.exists():
            data = json.loads(self.tasks_file.read_text())
            if isinstance(data, list):
                return data
        return []
    
    def _save(self):
        self.tasks_file.write_text(json.dumps(self.tasks, ensure_ascii=False, indent=2))
    
    def add(self, title: str, description: str = "", priority=None) -> str:
        priority_map = {1: "high", 2: "medium", 3: "low"}
        normalized = priority_map.get(priority, priority or "medium")
        task = {
            "id": (max((t["id"] for t in self.tasks), default=0)) + 1,
            "title": title,
            "description": description[:300],
            "priority": normalized,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self._save()
        return f"✅ 已新增任務：{title}"
    
    def complete(self, task_id: int) -> str:
        for task in self.tasks:
            if str(task["id"]) == str(task_id) and task["status"] == "pending":
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                self._save()
                return f"🎉 已完成：{task['title']}"
        return "❌ 任務不存在"
    
    def get_next_action(self) -> Optional[Dict]:
        pending = [t for t in self.tasks if t["status"] == "pending"]
        if not pending:
            return None
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(key=lambda x: priority_order.get(x["priority"], 1))
        return pending[0]
    
    def suggest_next(self) -> str:
        next_task = self.get_next_action()
        if next_task:
            return f"📋 下一個任務：{next_task['title']}"
        return "🎯 沒有待辦任務"

    # ── 相容層：ProactiveExecutor 需要的 API ──

    def values(self):
        return self.tasks

    def get(self, task_id, default=None):
        for task in self.tasks:
            if str(task["id"]) == str(task_id):
                return task
        return default

    def add_task(self, title: str, description: str = "", priority: str = "medium", task_type: str = "general") -> str:
        return self.add(title, description, priority)

    def update_task_status(self, task_id, status: str):
        for task in self.tasks:
            if str(task["id"]) == str(task_id):
                task["status"] = status
                task.setdefault("history", []).append({
                    "status": status,
                    "at": datetime.now().isoformat()
                })
                self._save()
                return
        # 不存在則自動建立
        self.add(title=f"任務 #{task_id}", description="")
        self.update_task_status(task_id, status)

    def complete_task(self, task_id):
        return self.complete(task_id)

    def _save_to_disk(self):
        self._save()
