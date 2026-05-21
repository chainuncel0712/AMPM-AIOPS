"""Evolution Governor — 進化方向控製，避免自爆"""
import json, time, threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class EvolutionGovernor:
    """控製進化方向：不讓 AI 變成無頭蒼蠅或自我毀滅"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data" / "meta"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.direction_file = self.data_dir / "evolution_direction.json"
        self._lock = threading.Lock()
        self.direction = self._load()

    def _load(self) -> dict:
        if self.direction_file.exists():
            try: return json.loads(self.direction_file.read_text())
            except Exception: pass
        return self._default()

    def _default(self) -> dict:
        return {
            "current_phase": "exploration",
            "phases": ["exploration", "specialization", "expansion", "consolidation"],
            "focus_areas": [],
            "forbidden_directions": [],
            "evolution_rate": 1.0,
            "safety_limits": {
                "max_code_changes_per_hour": 3,
                "max_new_organs_per_day": 2,
                "max_self_modification_depth": 3,
                "require_human_approval_for": ["delete_organ", "modify_core_loop"],
            },
            "evolution_log": [],
            "last_check": None,
        }

    def _save(self):
        with self._lock:
            self.direction["last_check"] = datetime.now().isoformat()
            self.direction_file.write_text(json.dumps(self.direction, ensure_ascii=False, indent=2))

    # ── 進化方向設定 ──
    def set_focus(self, areas: List[str], phase: str = "specialization"):
        self.direction["focus_areas"] = areas
        self.direction["current_phase"] = phase
        self._save()

    def get_focus(self) -> List[str]:
        return self.direction["focus_areas"]

    def forbid_direction(self, direction: str, reason: str):
        self.direction["forbidden_directions"].append({
            "direction": direction, "reason": reason,
            "ts": datetime.now().isoformat(),
        })
        self._save()

    def is_allowed(self, action: str) -> bool:
        for fb in self.direction["forbidden_directions"]:
            if fb["direction"] in action:
                return False
        limits = self.direction["safety_limits"]
        for critical in limits.get("require_human_approval_for", []):
            if critical in action:
                return False  # 需人工核準
        return True

    # ── 速率控製 ──
    def can_evolve_now(self) -> bool:
        """檢查現在是否可以進化（速率限製）"""
        recent = [e for e in self.direction["evolution_log"]
                  if (datetime.now() - datetime.fromisoformat(e["ts"])).total_seconds() < 3600]
        max_per_hour = self.direction["safety_limits"]["max_code_changes_per_hour"]
        return len(recent) < max_per_hour

    def record_evolution(self, action: str, result: str):
        self.direction["evolution_log"].append({
            "action": action, "result": result,
            "ts": datetime.now().isoformat(),
        })
        if len(self.direction["evolution_log"]) > 200:
            self.direction["evolution_log"] = self.direction["evolution_log"][-200:]
        self._save()

    # ── 階段管理 ──
    def advance_phase(self) -> str:
        phases = self.direction["phases"]
        current = self.direction["current_phase"]
        idx = phases.index(current) if current in phases else 0
        if idx < len(phases) - 1:
            self.direction["current_phase"] = phases[idx + 1]
            self._save()
        return self.direction["current_phase"]

    def get_evolution_directive(self) -> str:
        """給進化循環的指令"""
        focus = ", ".join(self.direction["focus_areas"]) or "全面探索"
        phase = self.direction["current_phase"]
        return (
            f"進化階段: {phase}\n"
            f"重點方向: {focus}\n"
            f"速率限製: {self.direction['safety_limits']['max_code_changes_per_hour']}次/時\n"
            f"禁止: {', '.join(f['direction'] for f in self.direction['forbidden_directions'][-3:])}"
        )

    def status(self) -> dict:
        return {
            "name": "evolution_governor",
            "alive": True,
            "phase": self.direction["current_phase"],
            "focus_areas": self.direction["focus_areas"],
            "recent_evolutions": len([e for e in self.direction["evolution_log"]
                if (datetime.now() - datetime.fromisoformat(e["ts"])).total_seconds() < 3600]),
        }
