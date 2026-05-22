"""
CycleDetector — 週期偵測器
===========================
檢測時間模式：哪些 bug 每 N 天重現？哪些資源在特定時間尖峰？

這讓 AI 有真正的時間感，而不是只活在「當下」。
"""
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CycleDetector:

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "temporal" / "cycles.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.event_streams: Dict[str, List[Dict]] = defaultdict(list)
        self.detected_cycles: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                self.detected_cycles = data.get("cycles", {})
                raw = data.get("streams", {})
                self.event_streams = defaultdict(list, {k: v for k, v in raw.items()})
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.data_file.write_text(json.dumps({
                "cycles": self.detected_cycles,
                "streams": {k: v[-500:] for k, v in self.event_streams.items()},
            }, ensure_ascii=False, indent=2))

    def record_event(self, stream_name: str, event: Dict[str, Any]):
        """Record a timestamped event in a named stream."""
        event["_ts"] = datetime.now().isoformat()
        with self._lock:
            self.event_streams[stream_name].append(event)
            if len(self.event_streams[stream_name]) > 500:
                self.event_streams[stream_name] = self.event_streams[stream_name][-500:]

        if len(self.event_streams[stream_name]) >= 3:
            self._detect_cycle(stream_name)
        self._save()

    def _detect_cycle(self, stream_name: str):
        """Detect recurring patterns in event timestamps."""
        events = self.event_streams.get(stream_name, [])
        if len(events) < 3:
            return

        timestamps = []
        for e in events:
            try:
                ts = datetime.fromisoformat(e["_ts"])
                timestamps.append(ts)
            except Exception:
                continue

        if len(timestamps) < 3:
            return

        intervals = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i - 1]).total_seconds()
            if delta > 0:
                intervals.append(delta)

        if len(intervals) < 2:
            return

        mean_interval = sum(intervals) / len(intervals)
        if mean_interval == 0:
            return

        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = sqrt(variance)
        cv = std_dev / mean_interval if mean_interval > 0 else 999

        # Only consider it a cycle if coefficient of variation < 0.4 (reasonably regular)
        if cv < 0.4 and len(intervals) >= 2:
            period_label = self._format_period(mean_interval)
            self.detected_cycles[stream_name] = {
                "stream": stream_name,
                "period_seconds": round(mean_interval, 1),
                "period_label": period_label,
                "regularity": round(1.0 - cv, 4),  # 1.0 = perfectly regular
                "event_count": len(events),
                "last_detected": datetime.now().isoformat(),
                "predicted_next": (
                    timestamps[-1] + timedelta(seconds=mean_interval)
                ).isoformat(),
            }

    def _format_period(self, seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f}h"
        elif seconds < 604800:
            return f"{seconds / 86400:.1f}d"
        else:
            return f"{seconds / 604800:.1f}w"

    def get_cycle(self, stream_name: str) -> Optional[Dict]:
        return self.detected_cycles.get(stream_name)

    def all_cycles(self) -> List[Dict]:
        return sorted(
            self.detected_cycles.values(),
            key=lambda x: -x["regularity"]
        )

    def upcoming_events(self, within_hours: float = 24) -> List[Dict]:
        """Predict events due within N hours."""
        now = datetime.now()
        upcoming = []
        for stream, cycle in self.detected_cycles.items():
            try:
                predicted = datetime.fromisoformat(cycle["predicted_next"])
                delta_h = (predicted - now).total_seconds() / 3600
                if 0 < delta_h <= within_hours:
                    upcoming.append({
                        "stream": stream,
                        "predicted_at": cycle["predicted_next"],
                        "in_hours": round(delta_h, 1),
                        "regularity": cycle["regularity"],
                    })
            except Exception:
                pass
        upcoming.sort(key=lambda x: x["in_hours"])
        return upcoming

    def is_cyclical(self, stream_name: str) -> bool:
        """Check if a stream exhibits cyclical behavior."""
        cycle = self.detected_cycles.get(stream_name, {})
        return cycle.get("regularity", 0) > 0.5

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int:
        return sum(len(v) for v in self.event_streams.values()) // 500 + 3

    def status(self) -> dict:
        return {
            "name": "CycleDetector",
            "streams_tracked": len(self.event_streams),
            "cycles_detected": len(self.detected_cycles),
            "upcoming_24h": len(self.upcoming_events(24)),
        }
