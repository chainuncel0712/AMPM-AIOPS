"""
Self Observer — 自我觀察器官
==============================
Belongs to meta_cognition layer.
Role: observe behavior, errors, patterns from event_log and governance stats.
Cannot execute tools, cannot make decisions, cannot modify state.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SelfObserver:
    """
    Reads governance event_log and scoring data to produce
    observational reports. These reports are fed into
    strategy_suggester and reflection_engine — never used
    for direct action.
    """

    def __init__(self):
        self._last_observation: Dict[str, Any] = {}
        self._observation_history: List[Dict] = []
        self._max_history = 100

    def observe(self) -> Dict[str, Any]:
        """
        Take a snapshot of current system state from governance.
        Returns observational data only — no mutation.
        """
        observation = {
            "timestamp": time.time(),
            "governance": self._observe_governance(),
            "patterns": self._detect_patterns(),
        }
        self._last_observation = observation
        self._observation_history.append(observation)
        if len(self._observation_history) > self._max_history:
            self._observation_history = self._observation_history[-self._max_history:]
        return observation

    def _observe_governance(self) -> Dict:
        """Read governance stats without calling any mutation APIs."""
        try:
            from governance.control_plane import cp as control_plane
            from governance.security_zone import SecurityZone
            from governance.event_log import event_log

            cp_stats = control_plane.stats()
            violations = SecurityZone.violation_count()
            event_count = event_log.count()

            return {
                "control_plane_calls": cp_stats.get("total_calls", 0),
                "avg_latency_ms": cp_stats.get("avg_latency_ms", 0),
                "blocked": cp_stats.get("blocked", 0),
                "violations": violations,
                "event_count": event_count,
            }
        except Exception as e:
            return {"error": str(e)}

    def _detect_patterns(self) -> List[Dict]:
        """Detect recurring patterns from observation history."""
        patterns = []
        if len(self._observation_history) < 3:
            return patterns

        recent = self._observation_history[-5:]
        violation_counts = [o.get("governance", {}).get("violations", 0) for o in recent]
        if len(violation_counts) >= 3 and all(v > 0 for v in violation_counts[-3:]):
            patterns.append({
                "type": "recurring_violations",
                "severity": "medium",
                "detail": "跨區越權連續 3 次以上出現",
            })

        return patterns

    def get_latest(self) -> Dict:
        return self._last_observation

    def get_history(self, limit: int = 10) -> List[Dict]:
        return self._observation_history[-limit:]
