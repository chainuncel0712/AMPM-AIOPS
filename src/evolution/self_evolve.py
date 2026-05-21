"""
自我演化引擎 — 統一演化管線
=============================
封裝 EvolutionCycleOrgan 與其他演化來源，
提供乾淨的 self_evolve() API。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class SelfEvolve:
    def __init__(self, base_dir, memory=None, tools=None,
                 evolution_cycle_organ=None, evolution_engine=None,
                 llm=None):
        self.base_dir = base_dir
        self.memory = memory
        self.tools = tools
        self.evolution_cycle = evolution_cycle_organ
        self.evolution_engine = evolution_engine
        self.llm = llm
        self._trace: List[Dict] = []
        self._version = 0

    def cycle(self, sources: List[str] = None) -> Dict:
        """執行一次完整演化循環"""
        if self.evolution_cycle:
            result = self.evolution_cycle.run_cycle()
            self._version += 1
            self._trace.append({
                "version": self._version,
                "type": "cycle",
                "timestamp": datetime.now().isoformat(),
                "result": str(result)[:200],
            })
            return {"status": "completed", "version": self._version, "detail": str(result)[:200]}
        return {"status": "skipped", "reason": "no evolution_cycle_organ"}

    def reflect_and_evolve(self, reflection: str) -> Dict:
        """接收反思文字，觸發演化"""
        if self.evolution_cycle and hasattr(self.evolution_cycle, "absorb"):
            self.evolution_cycle.absorb()
        if self.evolution_cycle and hasattr(self.evolution_cycle, "learn"):
            learnings = self.evolution_cycle.learn([reflection])
        else:
            learnings = [{"content": reflection[:500], "source": "reflection"}]

        self._version += 1
        self._trace.append({
            "version": self._version,
            "type": "reflect_evolve",
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection[:200],
        })
        return {"status": "completed", "version": self._version, "learnings": len(learnings)}

    def produce_new_version(self, change_type: str, description: str,
                            reasoning: str = "") -> Dict:
        """產生新版本記錄（使用 EvolutionMemory）"""
        try:
            from civilization_memory import EvolutionMemory
            em = EvolutionMemory(self.base_dir)
            em.record_change(change_type, description,
                             agent_id="self_evolve", reasoning=reasoning)
            self._version = em.version
            return {"status": "recorded", "version": self._version}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_trace(self, limit: int = 50) -> List[Dict]:
        return self._trace[-limit:]

    def get_version(self) -> int:
        return self._version
