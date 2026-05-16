"""
Trust Layer — AI 文明信任系統
-----------------------------
核心問題：哪些工具常錯？哪些 agent 愛幻覺？哪些資料源最準？

信任分數基於：
1. 歷史成功率
2. 最近趨勢（上升/下降）
3. 懲罰因子（幻覺、說謊、重複失敗）
4. 時間衰減（很久以前的正確不代表現在還可信）
"""
import json
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TrustScore:
    """
    通用信任評分引擎

    信任分數 = 基礎分 + 歷史調整 + 趨勢調整 - 懲罰 － 時間衰減
    """

    # 衰減半衰期（秒）—— 7 天
    DECAY_HALF_LIFE = 7 * 24 * 3600

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.trust_file = self.base_dir / "data" / "trust" / "scores.json"
        self.history_file = self.base_dir / "data" / "trust" / "history.json"
        self.trust_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.scores: Dict[str, Dict] = {}
        self.history: Dict[str, List[Dict]] = defaultdict(list)
        self._load()

    def _load(self):
        if self.trust_file.exists():
            try:
                self.scores = json.loads(self.trust_file.read_text())
            except Exception:
                pass
        if self.history_file.exists():
            try:
                raw = json.loads(self.history_file.read_text())
                self.history = defaultdict(list, {k: v for k, v in raw.items()})
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.trust_file.write_text(json.dumps(self.scores, ensure_ascii=False, indent=2))
            serializable = {
                k: v[-1000:] for k, v in self.history.items()
            }
            self.history_file.write_text(json.dumps(serializable, ensure_ascii=False, indent=2))

    def register(self, entity_id: str, entity_type: str, initial_trust: float = 0.5):
        with self._lock:
            if entity_id not in self.scores:
                self.scores[entity_id] = {
                    "type": entity_type,
                    "trust": initial_trust,
                    "total_events": 0,
                    "total_success": 0,
                    "total_failure": 0,
                    "last_updated": datetime.now().isoformat(),
                    "trend": "stable",
                    "tags": [],
                }

    def record(self, entity_id: str, success: bool, weight: float = 1.0,
               tags: List[str] = None):
        with self._lock:
            if entity_id not in self.scores:
                self.register(entity_id, "unknown", 0.5)

            score = self.scores[entity_id]
            score["total_events"] += 1
            if success:
                score["total_success"] += 1
            else:
                score["total_failure"] += 1

            if tags:
                score["tags"] = list(set(score.get("tags", []) + tags))

            event = {
                "success": success,
                "weight": weight,
                "timestamp": datetime.now().isoformat(),
                "tags": tags or [],
            }
            self.history[entity_id].append(event)

            self._recalc(entity_id)
            self._save()

    def _recalc(self, entity_id: str):
        score = self.scores[entity_id]
        total = score["total_events"]
        if total == 0:
            return

        success_rate = score["total_success"] / total

        history = self.history.get(entity_id, [])
        recent_window = [
            h for h in history
            if (datetime.now() - datetime.fromisoformat(h["timestamp"])).total_seconds()
            < 86400
        ]

        recent_pct = 0.5
        if recent_window:
            recent_success = sum(1 for h in recent_window if h["success"])
            recent_pct = recent_success / len(recent_window)

        if recent_pct > success_rate + 0.1:
            score["trend"] = "rising"
        elif recent_pct < success_rate - 0.1:
            score["trend"] = "falling"
        else:
            score["trend"] = "stable"

        alpha = 0.3 if len(recent_window) > 5 else 0.5
        adjusted = (1 - alpha) * success_rate + alpha * recent_pct

        score["trust"] = round(max(0.0, min(1.0, adjusted)), 4)
        score["last_updated"] = datetime.now().isoformat()

    def get_trust(self, entity_id: str) -> float:
        with self._lock:
            return self.scores.get(entity_id, {}).get("trust", 0.5)

    def get_detail(self, entity_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self.scores.get(entity_id, {}))

    def is_trustworthy(self, entity_id: str, threshold: float = 0.5) -> bool:
        return self.get_trust(entity_id) >= threshold

    def penalize(self, entity_id: str, penalty: float = 0.1, reason: str = ""):
        with self._lock:
            if entity_id in self.scores:
                old = self.scores[entity_id]["trust"]
                self.scores[entity_id]["trust"] = round(max(0.0, old - penalty), 4)
                self.scores[entity_id]["last_updated"] = datetime.now().isoformat()
                self._save()

    def reward(self, entity_id: str, reward: float = 0.05, reason: str = ""):
        with self._lock:
            if entity_id in self.scores:
                old = self.scores[entity_id]["trust"]
                self.scores[entity_id]["trust"] = round(min(1.0, old + reward), 4)
                self.scores[entity_id]["last_updated"] = datetime.now().isoformat()
                self._save()

    def low_trust_entities(self, threshold: float = 0.3) -> List[str]:
        with self._lock:
            return [
                eid for eid, s in self.scores.items()
                if s["trust"] < threshold
            ]

    def top_trusted(self, entity_type: str = None, top_n: int = 10) -> List[Tuple[str, float]]:
        with self._lock:
            filtered = self.scores.items()
            if entity_type:
                filtered = ((k, v) for k, v in filtered if v.get("type") == entity_type)
            ranked = sorted(filtered, key=lambda x: -x[1]["trust"])
            return [(k, v["trust"]) for k, v in ranked[:top_n]]

    def status(self) -> dict:
        with self._lock:
            low = self.low_trust_entities(0.3)
            return {
                "name": "TrustScore",
                "total_entities": len(self.scores),
                "avg_trust": round(
                    sum(s["trust"] for s in self.scores.values()) / max(1, len(self.scores)), 4),
                "low_trust_count": len(low),
                "low_trust_entities": low[:10],
            }
