"""
TrendMemory — 趨勢記憶
=======================
記住一段時間內的變化趨勢（上升/下降/週期），
讓 AI 理解「這件事正在惡化」或「這個問題正在好轉」。
"""
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class TrendMemory:

    TREND_DIRECTIONS = {"rising": "上升", "falling": "下降", "stable": "穩定", "unknown": "未知"}

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "temporal" / "trends.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.trend_cache: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                raw = data.get("metrics", {})
                self.metrics = defaultdict(list, {k: v for k, v in raw.items()})
                self.trend_cache = data.get("trends", {})
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.data_file.write_text(json.dumps({
                "metrics": {k: v[-200:] for k, v in self.metrics.items()},
                "trends": self.trend_cache,
            }, ensure_ascii=False, indent=2))

    def record(self, metric_name: str, value: float, tags: List[str] = None):
        """Record a metric value with timestamp."""
        with self._lock:
            self.metrics[metric_name].append({
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "tags": tags or [],
            })
            if len(self.metrics[metric_name]) > 200:
                self.metrics[metric_name] = self.metrics[metric_name][-200:]
        self._analyze(metric_name)
        self._save()

    def _analyze(self, metric_name: str):
        points = self.metrics.get(metric_name, [])
        if len(points) < 3:
            return

        values = [p["value"] for p in points]
        n = len(values)

        # Short-term trend (last 30% of points)
        short_n = max(3, n // 3)
        short_values = values[-short_n:]
        short_slope = self._linear_slope(short_values)

        # Long-term trend (all points)
        long_slope = self._linear_slope(values)

        avg = sum(values) / n
        recent_avg = sum(short_values) / short_n

        if abs(short_slope) < 0.01:
            direction = "stable"
        else:
            direction = "rising" if short_slope > 0 else "falling"

        # Acceleration: is the trend speeding up?
        acceleration = "steady"
        if direction != "stable":
            if abs(short_slope) > abs(long_slope) * 1.5:
                acceleration = "accelerating"
            elif abs(short_slope) < abs(long_slope) * 0.5:
                acceleration = "decelerating"

        self.trend_cache[metric_name] = {
            "metric": metric_name,
            "direction": direction,
            "direction_label": self.TREND_DIRECTIONS.get(direction, direction),
            "short_slope": round(short_slope, 6),
            "long_slope": round(long_slope, 6),
            "current_avg": round(recent_avg, 4),
            "overall_avg": round(avg, 4),
            "acceleration": acceleration,
            "data_points": n,
            "last_updated": datetime.now().isoformat(),
        }

    def _linear_slope(self, values: List[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den != 0 else 0.0

    def get_trend(self, metric_name: str) -> Dict[str, Any]:
        return self.trend_cache.get(metric_name, {
            "metric": metric_name,
            "direction": "unknown",
            "direction_label": "未知",
            "data_points": 0,
        })

    def is_deteriorating(self, metric_name: str) -> bool:
        t = self.get_trend(metric_name)
        return t.get("direction") == "falling" and t.get("acceleration") == "accelerating"

    def all_worsening(self) -> List[str]:
        return [k for k in self.trend_cache if self.is_deteriorating(k)]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int:
        return sum(len(v) for v in self.metrics.values()) // 300 + 3

    def status(self) -> dict:
        return {
            "name": "TrendMemory",
            "metrics_tracked": len(self.metrics),
            "trends_detected": len(self.trend_cache),
            "worsening": self.all_worsening()[:10],
        }
