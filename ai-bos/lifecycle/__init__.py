"""
Lifecycle — 生命週期流程
============================
"""
from typing import Any, Dict, List


class LifecyclePipeline:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def boot(self) -> List[Dict]:
        """啟動所有器官"""
        return self.lifecycle.health_check()

    def health(self) -> List[Dict]:
        """健康檢查"""
        return self.lifecycle.health_check()

    def shutdown(self):
        """優雅關閉"""
        for name, organ in self.lifecycle.all().items():
            if hasattr(organ, "disable"):
                organ.disable()
