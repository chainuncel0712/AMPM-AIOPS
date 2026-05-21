"""
演化追蹤 — 記錄與查詢演化歷史足跡
===================================
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class EvolutionTrace:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def get_recent(self, limit: int = 20) -> List[Dict]:
        """取得最近的演化記錄"""
        entries = []
        try:
            from civilization_memory import EvolutionMemory
            em = EvolutionMemory(self.base_dir)
            entries = em.get_history(limit)
        except Exception:
            pass

        try:
            from pathlib import Path
            f = Path(self.base_dir) / "data" / "evolution" / "cycle_state.json"
            if f.exists():
                import json
                state = json.loads(f.read_text())
                entries.append({
                    "version": state.get("cycle_count", 0),
                    "change_type": "cycle_state",
                    "description": f"cycles={state.get('cycle_count')}, "
                                   f"enhanced={state.get('total_enhanced')}, "
                                   f"score={state.get('evolution_score')}",
                    "timestamp": state.get("last_cycle", ""),
                })
        except Exception:
            pass

        return entries[-limit:]

    def get_evolution_score(self) -> Dict:
        try:
            from pathlib import Path
            f = Path(self.base_dir) / "data" / "evolution" / "cycle_state.json"
            if f.exists():
                import json
                state = json.loads(f.read_text())
                return {
                    "score": state.get("evolution_score", 0),
                    "cycles": state.get("cycle_count", 0),
                    "enhanced": state.get("total_enhanced", 0),
                    "learned": state.get("total_learned", 0),
                }
        except Exception:
            pass
        return {"score": 0, "cycles": 0, "enhanced": 0, "learned": 0}
