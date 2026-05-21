"""
文明快照 — 拍攝文明記憶當前狀態的快照
========================================
用於備份、審計、開源版展示。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class CivilizationSnapshot:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def take(self) -> Dict:
        """拍攝完整的文明記憶快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "episodic_memory": self._snapshot_episodic(),
            "failure_memory": self._snapshot_failures(),
            "evolution_memory": self._snapshot_evolution(),
            "evolution_state": self._snapshot_evolution_state(),
        }
        return snapshot

    def _snapshot_episodic(self) -> Dict:
        try:
            from civilization_memory import EpisodicMemory
            em = EpisodicMemory(self.base_dir)
            recent = em.recall_by_time(hours=24)
            return {
                "total_episodes": len(em.episodes if hasattr(em, 'episodes') else []),
                "recent_24h": len(recent),
                "sample": [{"type": e.get("type"), "summary": e.get("summary", "")[:100],
                            "importance": e.get("importance")} for e in recent[-5:]],
            }
        except Exception as e:
            return {"error": str(e)}

    def _snapshot_failures(self) -> Dict:
        try:
            from civilization_memory import FailureMemory
            fm = FailureMemory(self.base_dir)
            top = fm.top_patterns(5) if hasattr(fm, 'top_patterns') else []
            return {
                "total_failures": len(fm.failures if hasattr(fm, 'failures') else []),
                "risk_patterns": top,
            }
        except Exception as e:
            return {"error": str(e)}

    def _snapshot_evolution(self) -> Dict:
        try:
            from civilization_memory import EvolutionMemory
            em = EvolutionMemory(self.base_dir)
            return {
                "version": em.version if hasattr(em, 'version') else 0,
                "total_changes": len(em.evolution_log if hasattr(em, 'evolution_log') else []),
                "recent": [{"v": e.get("version"), "type": e.get("change_type"),
                            "desc": e.get("description", "")[:100]}
                           for e in (em.get_history(5) if hasattr(em, 'get_history') else [])],
            }
        except Exception as e:
            return {"error": str(e)}

    def _snapshot_evolution_state(self) -> Dict:
        try:
            from pathlib import Path
            f = Path(self.base_dir) / "data" / "evolution" / "cycle_state.json"
            if f.exists():
                import json
                return json.loads(f.read_text())
        except Exception:
            pass
        return {}
