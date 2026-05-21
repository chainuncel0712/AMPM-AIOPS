"""
Executor — 執行器目錄
=========================
"""
from .base import Executor


class SimpleExecutor(Executor):
    def execute(self, task: str) -> str:
        return f"AI-BOS executing: {task}"
