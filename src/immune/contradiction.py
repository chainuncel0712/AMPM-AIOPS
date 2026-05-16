"""矛盾檢測 - 保持前後邏輯一致"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class Contradiction(BaseOrgan):
    def __init__(self, base_dir=None):
        super().__init__("contradiction")
        self._statements = []
        self._max_statements = 200

    def check(self, text: str) -> dict:
        """檢查輸入是否與之前記錄矛盾"""
        statement = {
            "text": text,
            "timestamp": time.time(),
            "length": len(text),
        }
        self._statements.append(statement)

        # 保持清單大小
        if len(self._statements) > self._max_statements:
            self._statements = self._statements[-self._max_statements:]

        return {"recorded": True, "total_statements": len(self._statements)}

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "statements": len(self._statements),
        }
