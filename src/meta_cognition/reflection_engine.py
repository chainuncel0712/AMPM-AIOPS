"""
Reflection Engine — 反思器官
==============================
Belongs to meta_cognition layer.
Role: process feedback, correlate past observations with outcomes.
Produces reflection reports for the evolution cycle — never direct action.
"""
import time
from typing import Any, Dict, List, Optional

from governance.event_log import event_log


class ReflectionEngine:
    """
    Correlates past observations with outcomes recorded in event_log.
    Produces reflection reports that feed into evolution_cycle.
    """

    def __init__(self):
        self._reflections: List[Dict] = []
        self._max_history = 50

    def reflect(self, observation: Dict, suggestions: List[Dict]) -> Dict:
        """
        Produce a reflection report by correlating observations with
        the suggestions that were (or weren't) applied.
        Returns structured reflection with:
          - summary: str
          - key_insights: list
          - unresolved_issues: list
          - confidence: float (0-1)
        """
        gov = observation.get("governance", {})

        insights = []
        unresolved = []

        # Governance reflection
        if gov.get("violations", 0) > 0:
            insights.append(f"越權事件 {gov['violations']} 次，治理層正常攔截")
        if gov.get("blocked", 0) > 0:
            unresolved.append(f"還有 {gov['blocked']} 次阻擋未解決")

        # Suggestions reflection
        high_impact = [s for s in suggestions if s.get("estimated_impact") == "high"]
        if high_impact:
            insights.append(f"提出 {len(high_impact)} 個高影響建議待審查")

        # Performance
        avg_lat = gov.get("avg_latency_ms", 0)
        if avg_lat > 0:
            insights.append(f"ControlPlane 平均延遲 {avg_lat:.1f}ms")

        # Build report
        report = {
            "timestamp": time.time(),
            "summary": f"觀察到 {len(insights)} 項重點，{len(unresolved)} 項待解決",
            "key_insights": insights,
            "unresolved_issues": unresolved,
            "confidence": 0.8 if len(unresolved) == 0 else 0.5,
        }

        # Record to event_log
        event_log.record(
            source="meta_cognition:reflection_engine",
            action="reflection",
            input_data={"observation_timestamp": observation.get("timestamp")},
            output_data=report,
            decision=report["summary"],
        )

        self._reflections.append(report)
        if len(self._reflections) > self._max_history:
            self._reflections = self._reflections[-self._max_history:]

        return report

    def get_recent(self, limit: int = 5) -> List[Dict]:
        return self._reflections[-limit:]

    def latest(self) -> Optional[Dict]:
        return self._reflections[-1] if self._reflections else None
