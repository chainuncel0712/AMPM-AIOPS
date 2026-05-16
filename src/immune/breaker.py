"""断路器 - 防止重複輸入死循環 + 熔斷機制"""
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class Breaker(BaseOrgan):
    def __init__(self, max_history=10, failure_threshold=5, cooldown=60):
        super().__init__("breaker")
        self._history = []
        self._max_history = max_history
        self._failure_threshold = failure_threshold
        self._cooldown = cooldown
        self._failures = defaultdict(int)
        self._open_circuits = {}
        self._total_checks = 0

    def check(self, text: str) -> dict:
        """檢查輸入是否重複或觸發熔斷"""
        self._total_checks += 1
        text_hash = hash(text)

        # 檢查是否在最近歷史中出現過
        for entry in self._history[-self._max_history:]:
            if isinstance(entry, dict) and entry.get("hash") == text_hash:
                count = sum(1 for e in self._history[-self._max_history:] if isinstance(e, dict) and e.get("hash") == text_hash)
                return {"allowed": False, "reason": f"重複輸入 ({count} 次)", "total": self._total_checks}

        self._history.append({"hash": text_hash, "text": text[:100], "timestamp": time.time()})
        if len(self._history) > self._max_history * 2:
            self._history = self._history[-self._max_history:]

        return {"allowed": True, "total": self._total_checks}

    def record_failure(self, organ: str):
        self._failures[organ] += 1
        if self._failures[organ] >= self._failure_threshold:
            self._open_circuits[organ] = time.time()

    def record_success(self, organ: str):
        self._failures[organ] = 0
        self._open_circuits.pop(organ, None)

    def is_circuit_open(self, organ: str) -> bool:
        opened_at = self._open_circuits.get(organ)
        if not opened_at:
            return False
        if time.time() - opened_at > self._cooldown:
            self._open_circuits.pop(organ, None)
            return False
        return True

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_checks": self._total_checks,
            "open_circuits": len(self._open_circuits),
            "failure_threshold": self._failure_threshold,
        }
