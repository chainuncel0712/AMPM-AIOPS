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
        self._facts = {}

    def check(self, text: str, memory=None) -> dict:
        """檢查輸入是否與之前記錄矛盾"""
        result = {
            "is_contradiction": False,
            "old_statement": "",
            "reason": "",
            "recorded": True
        }

        statement = {
            "text": text,
            "timestamp": time.time(),
            "length": len(text),
        }
        self._statements.append(statement)

        if len(self._statements) > self._max_statements:
            self._statements = self._statements[-self._max_statements:]

        if memory:
            try:
                facts = memory.get_all_facts()
                text_lower = text.lower()
                for fact, value in facts.items():
                    fact_lower = fact.lower()
                    if fact_lower in text_lower or value.lower() in text_lower:
                        continue
                    negations = ["不是", "沒有", "不再", "已取消", "已刪除", "已改變", "不再是", "不存在"]
                    if any(neg in text_lower for neg in negations):
                        if fact_lower in text_lower:
                            result["is_contradiction"] = True
                            result["old_statement"] = fact
                            result["reason"] = f"新回覆與已記住的事實「{fact}」矛盾"
                            break
            except Exception as e:
                result["check_error"] = str(e)

        return result

    def add_fact(self, fact: str, value: str = ""):
        self._facts[fact] = value or fact

    def remove_fact(self, fact: str):
        self._facts.pop(fact, None)

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "statements": len(self._statements),
            "facts": len(self._facts),
        }
