"""
FutureSimulator — 未來模擬器
=============================
在執行行動前，先模擬可能的後果。
基於過去相似行動的結果，預測成功率和風險。

使用方式：
    sim = FutureSimulator(memory, trust)
    result = sim.simulate("update_package", {"package": "requests", "to_version": "2.31"})
    if result["risk_score"] < 0.5:
        execute()
"""
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class FutureSimulator:

    def __init__(self, base_dir: Optional[Path] = None,
                 memory=None, trust=None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.sim_file = self.base_dir / "data" / "simulation" / "simulations.json"
        self.sim_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.memory = memory
        self.trust = trust
        self.action_history: Dict[str, List[Dict]] = defaultdict(list)
        self.simulation_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.sim_file.exists():
            try:
                data = json.loads(self.sim_file.read_text())
                raw = data.get("action_history", {})
                self.action_history = defaultdict(list, {k: v for k, v in raw.items()})
                self.simulation_log = data.get("log", [])
            except Exception:
                pass

    def _save(self):
        with self._lock:
            serializable = {
                k: v[-500:] for k, v in self.action_history.items()
            }
            self.sim_file.write_text(json.dumps({
                "action_history": serializable,
                "log": self.simulation_log[-2000:],
            }, ensure_ascii=False, indent=2))

    def record_outcome(self, action_type: str, success: bool,
                       context: Dict[str, Any] = None, impact_score: float = 0.5):
        """Record actual outcome for future simulations."""
        self.action_history[action_type].append({
            "success": success,
            "context": {k: str(v)[:100] for k, v in (context or {}).items()},
            "impact": impact_score,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.action_history[action_type]) > 500:
            self.action_history[action_type] = self.action_history[action_type][-500:]
        self._save()

    def simulate(self, action_type: str, context: Dict[str, Any] = None,
                 target_organs: List[str] = None) -> Dict[str, Any]:
        """
        Simulate the outcome of an action before execution.

        Returns:
            risk_score: 0.0 (safe) to 1.0 (dangerous)
            predicted_success: estimated success probability
            affected_organs: which organs might be impacted
            recommendation: "safe" / "caution" / "dangerous" / "unknown"
        """
        context = context or {}
        history = self.action_history.get(action_type, [])

        if not history:
            result = {
                "risk_score": 0.5,
                "predicted_success": 0.5,
                "affected_organs": target_organs or [],
                "recommendation": "unknown",
                "confidence": 0.1,
                "sample_size": 0,
                "reasoning": "no historical data",
            }
        else:
            success_rate = sum(1 for h in history if h["success"]) / len(history)

            # Recent history (last 7 days) weight
            cutoff = datetime.now() - timedelta(days=7)
            recent = [
                h for h in history
                if datetime.fromisoformat(h["timestamp"]) > cutoff
            ]
            recent_rate = (
                sum(1 for h in recent if h["success"]) / len(recent)
                if recent else success_rate
            )

            # Trend: rising or falling success?
            trend = "stable"
            if recent_rate > success_rate + 0.1:
                trend = "improving"
            elif recent_rate < success_rate - 0.1:
                trend = "declining"

            # Blend historical + recent
            alpha = 0.4 if len(recent) > 5 else 0.2
            predicted = (1 - alpha) * success_rate + alpha * recent_rate
            risk_score = 1.0 - predicted

            # Adjust for impact history
            avg_impact = sum(h.get("impact", 0.5) for h in history) / len(history)
            if avg_impact > 0.7:
                risk_score = min(1.0, risk_score * 1.3)

            recommendation = (
                "safe" if risk_score < 0.3
                else "caution" if risk_score < 0.6
                else "dangerous"
            )

            result = {
                "risk_score": round(risk_score, 4),
                "predicted_success": round(predicted, 4),
                "trend": trend,
                "affected_organs": target_organs or [],
                "recommendation": recommendation,
                "confidence": round(0.3 + len(history) / 100 * 0.7, 4),
                "sample_size": len(history),
                "reasoning": (
                    f"historical: {success_rate:.0%} ({len(history)} samples), "
                    f"recent: {recent_rate:.0%} ({len(recent)} samples), "
                    f"trend: {trend}"
                ),
            }

        self.simulation_log.append({
            "action_type": action_type,
            "risk_score": result["risk_score"],
            "recommendation": result["recommendation"],
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

        return result

    def batch_simulate(self, actions: List[str],
                       contexts: List[Dict] = None) -> List[Dict]:
        """Simulate multiple actions, return ranked by risk."""
        results = []
        for i, action in enumerate(actions):
            ctx = (contexts or [{}])[i] if contexts and i < len(contexts) else {}
            r = self.simulate(action, ctx)
            results.append(r)
        results.sort(key=lambda x: x["risk_score"])
        return results

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int:
        return sum(len(v) for v in self.action_history.values()) * 2 // 1000 + 5

    def status(self) -> dict:
        return {
            "name": "FutureSimulator",
            "tracked_actions": len(self.action_history),
            "total_samples": sum(len(v) for v in self.action_history.values()),
            "total_simulations": len(self.simulation_log),
        }
