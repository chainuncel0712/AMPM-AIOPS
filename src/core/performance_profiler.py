"""
效能監控器官 — 追蹤每個器官的延遲、成功率、錯誤率。
"""
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class PerformanceProfiler(BaseOrgan):
    """
    效能監控器官

    追蹤：
    1. 每個器官的呼叫次數
    2. 平均延遲 (ms)
    3. 成功率
    4. 錯誤率
    5. 最後錯誤訊息
    """

    def __init__(self):
        super().__init__("performance_profiler")
        self._lock = threading.RLock()

        # organ_name -> {
        #   calls, total_latency, success, failures,
        #   last_error, last_call, avg_latency_ms
        # }
        self.stats: Dict[str, Dict] = defaultdict(lambda: {
            "calls": 0, "total_latency": 0, "success": 0, "failures": 0,
            "last_error": "", "last_call": None, "avg_latency_ms": 0,
        })

        # 即時延遲（用於熔斷判斷）
        self.recent_latencies: Dict[str, List[float]] = defaultdict(list)

        self.total_calls = 0
        self.start_time = datetime.now()

    def record_call(self, organ_name: str, duration_ms: float, success: bool,
                    error: str = ""):
        """記錄一次器官呼叫"""
        with self._lock:
            s = self.stats[organ_name]
            s["calls"] += 1
            s["total_latency"] += duration_ms
            s["success"] += 1 if success else 0
            if not success:
                s["failures"] += 1
                s["last_error"] = error[:200]
            s["last_call"] = datetime.now().isoformat()
            s["avg_latency_ms"] = s["total_latency"] / s["calls"]

            self.recent_latencies[organ_name].append(duration_ms)
            if len(self.recent_latencies[organ_name]) > 50:
                self.recent_latencies[organ_name] = (
                    self.recent_latencies[organ_name][-50:])

            self.total_calls += 1

    def get_organ_stats(self, organ_name: str) -> Dict:
        """取得單一器官統計"""
        with self._lock:
            return dict(self.stats.get(organ_name, {}))

    def get_all_stats(self) -> Dict:
        """取得所有統計"""
        with self._lock:
            return {
                "total_calls": self.total_calls,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "organs": {k: dict(v) for k, v in self.stats.items()},
            }

    def get_slow_organs(self, threshold_ms: float = 500) -> List[str]:
        """回傳平均延遲超過閾值的器官"""
        with self._lock:
            return [
                name for name, s in self.stats.items()
                if s["calls"] > 0 and s["avg_latency_ms"] > threshold_ms
            ]

    def get_failing_organs(self, threshold: float = 0.3) -> List[str]:
        """回傳失敗率超過閾值的器官"""
        with self._lock:
            return [
                name for name, s in self.stats.items()
                if s["calls"] > 0 and (s["failures"] / s["calls"]) > threshold
            ]

    def get_summary(self) -> str:
        """效能摘要報告"""
        with self._lock:
            slow = self.get_slow_organs(500)
            failing = self.get_failing_organs(0.3)
            total_organs = len(self.stats)
            active = sum(1 for s in self.stats.values() if s["calls"] > 0)

        return (
            f"📊 效能報告:\n"
            f"  呼叫總數: {self.total_calls}\n"
            f"  活躍器官: {active}/{total_organs}\n"
            f"  慢器官 (>500ms): {len(slow)}\n"
            f"  高失敗率: {len(failing)}"
        )

    # 裝飾器：自動追蹤函數呼叫
    def track(self, organ_name: str):
        """裝飾器：自動記錄被裝飾函數的呼叫效能"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start) * 1000
                    self.record_call(organ_name, duration, True)
                    return result
                except Exception as e:
                    duration = (time.time() - start) * 1000
                    self.record_call(organ_name, duration, False, str(e))
                    raise
            return wrapper
        return decorator

    def status(self) -> dict:
        with self._lock:
            slow = self.get_slow_organs(500)
            failing = self.get_failing_organs(0.3)
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_calls": self.total_calls,
            "tracked_organs": len(self.stats),
            "slow_organs": slow,
            "failing_organs": failing,
        }
