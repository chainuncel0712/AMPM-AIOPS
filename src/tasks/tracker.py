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
            return json.loads(self.tasks_file.read_text())
        return []
    
    def _save(self):
        self.tasks_file.write_text(json.dumps(self.tasks, ensure_ascii=False, indent=2))
    
    def add(self, title: str, description: str = "", priority: str = "medium") -> str:
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "description": description[:300],
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self._save()
        return f"✅ 已新增任務：{title}"
    
    def complete(self, task_id: int) -> str:
        for task in self.tasks:
            if task["id"] == task_id and task["status"] == "pending":
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
