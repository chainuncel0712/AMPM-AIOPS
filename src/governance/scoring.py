"""
Agent Scoring — 模組評分系統
==============================
每個 agent / module 的評分維度：
  - 準確率 (accuracy)   — decision 匹配度（event_log replay）
  - 穩定性 (stability)   — latency 變異係數
  - 越權次數 (violations) — SecurityZone & Gatekeeper 記錄
  - 汙染率 (pollution)   — 非 memory zone 對 memory 的寫入比例

所有分數 0–100，週期性由 background thread 或 on-demand 計算。
"""
import os
import statistics
import threading
import time
from typing import Dict, List

from governance.event_log import event_log
from governance.security_zone import SecurityZone


class AgentScoring:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._scores: Dict[str, Dict] = {}
                    cls._instance._history: Dict[str, List[float]] = {}
                    cls._instance._last_update = 0.0
        return cls._instance

    def compute_scores(self) -> Dict[str, Dict]:
        """
        即時計算所有 module 分數。
        回傳 { "brain": {"accuracy": 85, "stability": 92, ...}, ... }
        """
        scores = {}
        events = event_log.replay(limit=500)

        # 依 source 分組
        by_source: Dict[str, List[dict]] = {}
        for e in events:
            src = e.get("source", "unknown")
            by_source.setdefault(src, []).append(e)

        for src, evts in by_source.items():
            total = len(evts)
            if total == 0:
                continue

            # Accuracy: 正常完成的 action 比例（有 output 或 decision 非空）
            completed = sum(1 for e in evts if e.get("output") or e.get("decision"))
            accuracy = round(completed / total * 100, 1)

            # Stability: latency 變異係數 (CV = std/mean)
            latencies = [e.get("duration_ms", 0) for e in evts if e.get("duration_ms", 0) > 0]
            if len(latencies) >= 3:
                mean_lat = statistics.mean(latencies)
                stdev_lat = statistics.stdev(latencies)
                cv = stdev_lat / mean_lat if mean_lat > 0 else 0
                stability = max(0, round(100 - cv * 50, 1))
            else:
                stability = 50.0  # default

            # Violations: SecurityZone 越權次數
            violations = SecurityZone.violation_count()
            violation_penalty = min(violations * 10, 50)
            # 但這個是全域的，不準確。改從 event_log 中分析 cross_zone_violation
            my_violations = sum(
                1 for e in evts
                if e.get("action", "").startswith("cross_zone_violation")
                   or e.get("action", "").startswith("permission_denied")
            )
            violation_score = max(0, 100 - my_violations * 20)

            # Pollution: 非 memory module 對 memory 的寫入比例
            memory_writes = sum(
                1 for e in evts
                if e.get("memory_write") and "memory" not in src.lower()
            )
            pollution = round(memory_writes / total * 100, 1) if total > 0 else 0
            pollution_score = max(0, 100 - pollution * 2)

            # Composite
            score = {
                "accuracy": accuracy,
                "stability": stability,
                "violation_score": violation_score,
                "pollution_score": pollution_score,
                "composite": round(
                    accuracy * 0.35 + stability * 0.25 + violation_score * 0.25 + pollution_score * 0.15, 1
                ),
                "total_events": total,
                "violations": my_violations,
                "pollution_pct": pollution,
            }
            scores[src] = score

        # 儲存
        with self._lock:
            self._scores = scores
            self._last_update = time.time()
            for src, sc in scores.items():
                self._history.setdefault(src, []).append(sc["composite"])

        return scores

    def get(self, module: str = None) -> Dict:
        """
        取得最新分數。如果 module 為 None，回傳全部。
        若從未計算過，自動計算。
        """
        with self._lock:
            if not self._scores:
                return self.compute_scores()
            if module:
                return {module: self._scores.get(module, {})}
            return dict(self._scores)

    def get_composite(self, module: str) -> float:
        scores = self.get(module)
        return scores.get(module, {}).get("composite", 0.0)

    def performance_trend(self, module: str) -> List[float]:
        """回傳該 module 的歷史 composite 分數序列"""
        with self._lock:
            return list(self._history.get(module, []))

    def worst_performers(self, top_n: int = 3) -> List[str]:
        scores = self.get()
        sorted_modules = sorted(
            scores.items(),
            key=lambda x: x[1].get("composite", 0),
        )
        return [m for m, _ in sorted_modules[:top_n]]


scoring = AgentScoring()
