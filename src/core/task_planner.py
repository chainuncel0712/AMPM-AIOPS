"""
任務規劃器官 — 將複雜請求分解為可執行子任務
支援依賴排序、優先級分配、平行執行。
"""
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class TaskPlanner(BaseOrgan):
    """
    任務規劃器官

    功能：
    1. 將複雜請求分解為子任務列表
    2. 依賴分析 — 決定執行順序
    3. 優先級排序
    4. 平行標記 — 標記可同時執行的任務
    """

    def __init__(self, llm=None, memory=None, tasks=None):
        super().__init__("task_planner")
        self.llm = llm
        self.memory = memory
        self.tasks = tasks
        self._lock = threading.Lock()
        self.total_planned = 0

    def decompose(self, request: str) -> List[Dict]:
        """
        將請求分解為子任務。

        每個子任務格式:
        {
            "id": "subtask_1",
            "title": "任務名稱",
            "description": "具體步驟",
            "depends_on": [],      # 依賴的任務 id
            "parallel_group": null, # 可平行執行的群組
            "estimated_tools": [], # 需要的工具
            "priority": 1-5,
        }
        """
        subtasks = []

        # 用關鍵字進行快速分解（不使用 LLM 的輕量版本）
        if any(kw in request for kw in ["部署", "deploy", "上線"]):
            subtasks.extend([
                {"id": "subtask_1", "title": "檢查環境", "description": "確認依賴和設定", "depends_on": [], "priority": 1, "estimated_tools": ["ls", "cat"]},
                {"id": "subtask_2", "title": "執行測試", "description": "跑測試確保無誤", "depends_on": ["subtask_1"], "priority": 2, "estimated_tools": ["bash", "pytest"]},
                {"id": "subtask_3", "title": "備份現狀", "description": "備份目前版本", "depends_on": [], "priority": 1, "estimated_tools": ["git", "cp"]},
                {"id": "subtask_4", "title": "執行部署", "description": "上線新版本", "depends_on": ["subtask_2", "subtask_3"], "priority": 3, "estimated_tools": ["git", "bash"]},
                {"id": "subtask_5", "title": "驗證部署", "description": "確認服務正常", "depends_on": ["subtask_4"], "priority": 4, "estimated_tools": ["curl", "grep"]},
            ])
        elif any(kw in request for kw in ["搜尋", "search", "查找", "找"]):
            subtasks.extend([
                {"id": "subtask_1", "title": "分析關鍵字", "description": "提取搜尋關鍵字", "depends_on": [], "priority": 1, "estimated_tools": []},
                {"id": "subtask_2", "title": "執行搜尋", "description": "使用搜尋工具", "depends_on": ["subtask_1"], "priority": 2, "estimated_tools": ["web_search"]},
                {"id": "subtask_3", "title": "整理結果", "description": "過濾和摘要", "depends_on": ["subtask_2"], "priority": 3, "estimated_tools": []},
            ])
        elif any(kw in request for kw in ["修復", "fix", "修", "錯誤", "bug"]):
            subtasks.extend([
                {"id": "subtask_1", "title": "診斷問題", "description": "檢查錯誤訊息和日誌", "depends_on": [], "priority": 1, "estimated_tools": ["bash", "grep"]},
                {"id": "subtask_2", "title": "定位程式碼", "description": "找到出錯的程式碼", "depends_on": ["subtask_1"], "priority": 2, "estimated_tools": ["grep", "read"]},
                {"id": "subtask_3", "title": "修復問題", "description": "修改程式碼", "depends_on": ["subtask_2"], "priority": 3, "estimated_tools": ["edit"]},
                {"id": "subtask_4", "title": "驗證修復", "description": "確認修復有效", "depends_on": ["subtask_3"], "priority": 4, "estimated_tools": ["bash", "pytest"]},
            ])
        elif any(kw in request for kw in ["建立", "create", "新增", "寫"]):
            subtasks.extend([
                {"id": "subtask_1", "title": "確認需求", "description": "理解和確認規格", "depends_on": [], "priority": 1, "estimated_tools": []},
                {"id": "subtask_2", "title": "設計架構", "description": "規劃檔案和模組", "depends_on": ["subtask_1"], "priority": 2, "estimated_tools": []},
                {"id": "subtask_3", "title": "撰寫代碼", "description": "實作功能", "depends_on": ["subtask_2"], "priority": 3, "estimated_tools": ["edit", "write"]},
                {"id": "subtask_4", "title": "測試驗證", "description": "跑測試確認", "depends_on": ["subtask_3"], "priority": 4, "estimated_tools": ["bash", "pytest"]},
            ])
        else:
            # 通用分解
            subtasks.extend([
                {"id": "subtask_1", "title": "分析請求", "description": "理解要做什麼", "depends_on": [], "priority": 1, "estimated_tools": []},
                {"id": "subtask_2", "title": "執行任務", "description": "完成主要工作", "depends_on": ["subtask_1"], "priority": 2, "estimated_tools": []},
                {"id": "subtask_3", "title": "驗證結果", "description": "確認結果正確", "depends_on": ["subtask_2"], "priority": 3, "estimated_tools": []},
            ])

        with self._lock:
            self.total_planned += len(subtasks)

        return subtasks

    def get_execution_order(self, subtasks: List[Dict]) -> List[List[str]]:
        """
        拓樸排序 — 回傳分層的執行順序。
        同層內的任務可平行執行。
        """
        completed = set()
        remaining = {t["id"]: t for t in subtasks}
        layers = []

        while remaining:
            layer = []
            for tid, t in list(remaining.items()):
                if all(d in completed for d in t.get("depends_on", [])):
                    layer.append(tid)
            if not layer:
                break  # 有循環依賴，中斷
            for tid in layer:
                completed.add(tid)
                del remaining[tid]
            layers.append(layer)

        return layers

    def plan(self, request: str) -> Dict:
        """完整規劃：分解 + 排序"""
        subtasks = self.decompose(request)
        order = self.get_execution_order(subtasks)
        return {
            "request": request[:200],
            "subtasks": subtasks,
            "execution_layers": order,
            "total_steps": len(subtasks),
            "parallel_layers": len(order),
            "planned_at": datetime.now().isoformat(),
        }

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_planned": self.total_planned,
        }
