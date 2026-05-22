"""Meta Cortex — 世界模型：全系統因果圖與狀態感知"""
import json, time, threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class WorldModel:
    """持續維護的系統世界狀態圖"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data" / "meta"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "world_state.json"
        self.causal_file = self.data_dir / "causal_graph.json"
        self._lock = threading.Lock()
        self.state = self._load_state()
        self.causal_graph: Dict[str, List[str]] = self._load_json(self.causal_file) or {}
        self.event_log: List[Dict] = []
        self._running = False

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return self._default_state()

    def _default_state(self) -> dict:
        return {
            "system_health": "unknown",
            "last_updated": None,
            "nodes": {},
            "relations": [],
            "alerts": [],
            "trends": {},
        }

    def _load_json(self, path: Path) -> Optional[dict]:
        if path.exists():
            try: return json.loads(path.read_text())
            except Exception: return None
        return None

    def _save(self):
        with self._lock:
            self.state["last_updated"] = datetime.now().isoformat()
            self.state_file.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
            self.causal_file.write_text(json.dumps(self.causal_graph, ensure_ascii=False, indent=2))

    # ── 節點管理 ──
    def update_node(self, name: str, data: dict):
        self.state["nodes"][name] = {**self.state["nodes"].get(name, {}), **data, "ts": time.time()}

    def get_node(self, name: str) -> dict:
        return self.state["nodes"].get(name, {})

    # ── 因果關係 ──
    def add_causal_link(self, cause: str, effect: str, confidence: float = 0.5):
        if cause not in self.causal_graph:
            self.causal_graph[cause] = []
        if effect not in self.causal_graph[cause]:
            self.causal_graph[cause].append(effect)
        self.state["relations"].append({
            "cause": cause, "effect": effect,
            "confidence": confidence,
            "ts": datetime.now().isoformat(),
        })

    def trace_causal_chain(self, symptom: str, depth: int = 3) -> List[str]:
        """從症狀回溯因果鏈"""
        chain = [symptom]
        current = symptom
        for _ in range(depth):
            causes = [k for k, v in self.causal_graph.items() if current in v]
            if not causes:
                break
            current = causes[0]
            chain.insert(0, current)
        return chain

    # ── 系統健康評估 ──
    def assess_health(self, organ_statuses: Dict[str, bool],
                      resource_stats: Dict[str, float],
                      error_rates: Dict[str, float]) -> str:
        unhealthy = sum(1 for v in organ_statuses.values() if not v)
        total = len(organ_statuses) or 1
        cpu = resource_stats.get("cpu", 0)
        mem = resource_stats.get("mem", 0)
        err = sum(error_rates.values())

        if unhealthy > total * 0.3 or cpu > 90 or mem > 90:
            self.state["system_health"] = "critical"
        elif unhealthy > 0 or cpu > 70 or mem > 70 or err > 10:
            self.state["system_health"] = "degraded"
        else:
            self.state["system_health"] = "healthy"

        self.state["alerts"] = []
        if unhealthy > 0:
            self.state["alerts"].append(f"{unhealthy}/{total} 器官異常")
        if cpu > 80:
            self.state["alerts"].append(f"CPU {cpu}%")
        if mem > 80:
            self.state["alerts"].append(f"RAM {mem}%")
        if err > 10:
            self.state["alerts"].append(f"錯誤率偏高")

        self._save()
        return self.state["system_health"]

    def get_world_snapshot(self) -> dict:
        return {
            "health": self.state["system_health"],
            "node_count": len(self.state["nodes"]),
            "relation_count": len(self.state["relations"]),
            "alerts": self.state["alerts"][-5:],
            "causal_chains": len(self.causal_graph),
            "last_updated": self.state["last_updated"],
        }

    def status(self) -> dict:
        return {"name": "world_model", "alive": True, **self.get_world_snapshot()}
