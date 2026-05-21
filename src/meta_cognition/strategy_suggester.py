"""
Strategy Suggester — 策略建議器官
====================================
Belongs to meta_cognition layer.
Role: analyze observations and produce improvement suggestions.
Cannot modify code, config, prompts, or routing.
Suggestions are read-only and logged to event_log for human review.
"""
from typing import Any, Dict, List, Optional

from governance.event_log import event_log


class StrategySuggester:
    """
    Reads SelfObserver observations and produces strategy suggestions.
    Never auto-applies — suggestions must be reviewed.
    """

    def __init__(self):
        self._suggestions: List[Dict] = []
        self._max_history = 50

    def analyze(self, observation: Dict) -> List[Dict]:
        """
        Analyze an observation snapshot and produce suggestions.
        Returns list of suggestion dicts. Each has:
          - area: str (governance / performance / stability / security)
          - suggestion: str
          - rationale: str
          - estimated_impact: str (low/medium/high)
        """
        suggestions = []

        gov = observation.get("governance", {})

        # Governance suggestions
        violations = gov.get("violations", 0)
        if violations > 0:
            suggestions.append({
                "area": "governance",
                "suggestion": "檢查 SecurityZone 設定，考慮收緊跨區權限或提升模式至 WARN",
                "rationale": f"偵測到 {violations} 次越權，表示 zone boundary 仍有模糊地帶",
                "estimated_impact": "high",
            })

        blocked = gov.get("blocked", 0)
        if blocked > 5:
            suggestions.append({
                "area": "security",
                "suggestion": "ControlPlane 阻擋次數偏高，檢查是否有惡意輸入或誤擋正常操作",
                "rationale": f"已阻擋 {blocked} 次呼叫",
                "estimated_impact": "medium",
            })

        avg_lat = gov.get("avg_latency_ms", 0)
        if avg_lat > 10:
            suggestions.append({
                "area": "performance",
                "suggestion": f"ControlPlane 平均延遲 {avg_lat:.1f}ms，考慮優化 EventLog 寫入批次",
                "rationale": "高延遲可能影響決策迴圈時效",
                "estimated_impact": "low",
            })

        # Detect patterns from observation
        patterns = observation.get("patterns", [])
        for p in patterns:
            if p.get("type") == "recurring_violations":
                suggestions.append({
                    "area": "governance",
                    "suggestion": "持續越權模式偵測到，建議檢視 permissions.json 是否遺漏必要權限",
                    "rationale": p.get("detail", ""),
                    "estimated_impact": "high",
                })

        # Log new suggestions to event_log
        for s in suggestions:
            event_log.record(
                source="meta_cognition:strategy_suggester",
                action="suggestion",
                input_data={"area": s["area"]},
                decision=s["suggestion"][:100],
            )

        self._suggestions.extend(suggestions)
        if len(self._suggestions) > self._max_history:
            self._suggestions = self._suggestions[-self._max_history:]

        return suggestions

    def get_all_suggestions(self) -> List[Dict]:
        return list(self._suggestions)

    def latest(self) -> Optional[Dict]:
        return self._suggestions[-1] if self._suggestions else None
