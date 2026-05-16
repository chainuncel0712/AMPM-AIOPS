"""
迴圈斷路器 - 防止無限迴圈和重複
"""

from collections import deque
from typing import Dict

class CircuitBreaker:
    def __init__(self, max_history: int = 10, max_similarity: float = 0.85):
        self.max_history = max_history
        self.max_similarity = max_similarity
        self.history = deque(maxlen=max_history)
        self.loop_count = 0
        self.last_break_at = None
    
    def record(self, text: str) -> Dict:
        for old in self.history:
            similarity = self._calculate_similarity(text, old)
            if similarity > self.max_similarity:
                self.loop_count += 1
                if self.loop_count >= 3:
                    return {"status": "BREAK", "reason": f"迴圈偵測", "loop_count": self.loop_count}
                return {"status": "WARNING", "reason": f"重複內容", "loop_count": self.loop_count}
        
        self.history.append(text)
        self.loop_count = max(0, self.loop_count - 1)
        return {"status": "OK"}
    
    def _calculate_similarity(self, a: str, b: str) -> float:
        set_a = set(a[:200].split())
        set_b = set(b[:200].split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)
    
    def get_status(self) -> Dict:
        return {"history_size": len(self.history), "loop_count": self.loop_count}
