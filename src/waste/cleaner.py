"""排泄 - 清理无用記憶"""
from skeleton.base_organ import BaseOrgan

class MemoryCleaner(BaseOrgan):
    def __init__(self, memory):
        super().__init__("memory_cleaner")
        self.memory = memory

    def flush_short_term(self):
        """清空短期記憶"""
        self.memory.clear_working()

    def forget_old(self, days: int = 30):
        """遗忘超过指定天数不重要的記憶"""
        self.memory.forget(min_importance=0.2)

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
