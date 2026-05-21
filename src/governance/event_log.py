"""
Event Log — 強製行為記錄
=========================
每一次 decision / tool call / memory write 都要有：
- action_id (唯一)
- timestamp
- source (哪個 module)
- action (做了什麼)
- input (收到的參數)
- output (回傳的結果)
- parent_id (上層 action，用於建立 lineage)

支援：
- 線性 replay：依時間序重播
- 樹狀 trace：從 root decision 展開完整子樹
- 回滾點標記：rollback point
"""
import hashlib
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class EventLog:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._events: List[Dict] = []
                    cls._instance._log_file: Optional[Path] = None
        return cls._instance

    def configure(self, log_dir: str = None):
        if log_dir:
            self._log_file = Path(log_dir) / "event_log.jsonl"
            self._log_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_action_id(source: str, action: str, context: str = "") -> str:
        raw = f"{time.time()}|{source}|{action}|{context}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def record(self, source: str, action: str, input_data: Any = None,
               output_data: Any = None, parent_id: str = "",
               decision: str = "", route: str = "",
               memory_write: Dict = None, duration_ms: float = 0,
               rollback_point: bool = False) -> str:
        action_id = self.make_action_id(source, action, str(input_data)[:100])
        entry = {
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "action": action,
            "input": self._truncate(input_data),
            "output": self._truncate(output_data),
            "parent_id": parent_id,
            "decision": decision,
            "route": route,
            "memory_write": memory_write,
            "duration_ms": round(duration_ms, 2),
            "rollback_point": rollback_point,
        }
        with self._lock:
            self._events.append(entry)
            if self._log_file:
                try:
                    with open(self._log_file, "a") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    # 避免單一檔案過大
                    if self._log_file.stat().st_size > 50 * 1024 * 1024:
                        self._rotate()
                except Exception:
                    pass
        return action_id

    def _truncate(self, data: Any, max_len: int = 500) -> Any:
        if isinstance(data, str):
            return data[:max_len]
        if isinstance(data, dict):
            return {k: self._truncate(v, max_len) for k, v in list(data.items())[:10]}
        if isinstance(data, list):
            return [self._truncate(v, max_len) for v in data[:5]]
        return data

    def _rotate(self):
        """超過 50MB 自動輪替"""
        if self._log_file:
            base = self._log_file.with_suffix("")
            for i in range(9, 0, -1):
                old = Path(f"{base}.{i}.jsonl")
                if old.exists():
                    if i == 9:
                        old.unlink()
                    else:
                        old.rename(Path(f"{base}.{i + 1}.jsonl"))
            self._log_file.rename(Path(f"{base}.1.jsonl"))

    # ── 查詢 ──────────────────────────────────────────

    def get_by_action_id(self, action_id: str) -> Optional[Dict]:
        with self._lock:
            for e in reversed(self._events):
                if e["action_id"] == action_id:
                    return e
        return None

    def get_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        with self._lock:
            return [e for e in self._events if e["source"] == source][-limit:]

    def get_tree(self, root_action_id: str) -> List[Dict]:
        """回傳以 root_action_id 為根的行為樹。"""
        with self._lock:
            children = [e for e in self._events if e.get("parent_id") == root_action_id]
            result = []
            for c in children:
                subtree = self.get_tree(c["action_id"])
                result.append(c)
                result.extend(subtree)
            return result

    def replay(self, start_id: str = None, end_id: str = None, limit: int = None) -> List[Dict]:
        """
        重播：回傳時間序列表。
        如果指定 start_id / end_id，則只回傳該區間。
        limit: 最多回傳筆數（最新的 N 筆）。
        """
        with self._lock:
            events = list(self._events)
        if start_id:
            start_idx = next((i for i, e in enumerate(events) if e["action_id"] == start_id), 0)
            events = events[start_idx:]
        if end_id:
            end_idx = next((i for i, e in enumerate(events) if e["action_id"] == end_id), len(events))
            events = events[:end_idx + 1]
        if limit:
            events = events[-limit:]
        return events

    def last_rollback_point(self) -> Optional[str]:
        """回傳最近的 rollback point action_id"""
        with self._lock:
            for e in reversed(self._events):
                if e.get("rollback_point"):
                    return e["action_id"]
        return None

    def export_json(self, path: str):
        with self._lock:
            Path(path).write_text(
                json.dumps(self._events, ensure_ascii=False, indent=2)
            )

    def clear(self):
        with self._lock:
            self._events = []

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def stats(self) -> Dict:
        with self._lock:
            sources = {}
            for e in self._events:
                s = e["source"]
                sources[s] = sources.get(s, 0) + 1
            return {
                "total_events": len(self._events),
                "by_source": sources,
                "last_rollback": self.last_rollback_point(),
            }


# 單例
event_log = EventLog()
