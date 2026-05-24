"""System Consciousness — 全系統意識：知道「我是誰、我在哪、我缺什麼」"""
import json, time, threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class SystemConsciousness:
    """存在層認知：我是什麼、我有哪些能力、我缺什麼、我常錯什麼"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = base_dir / "data" / "meta"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.self_file = self.data_dir / "self_knowledge.json"
        self._lock = threading.Lock()
        self.knowledge = self._load()

    def _load(self) -> dict:
        if self.self_file.exists():
            try:
                return json.loads(self.self_file.read_text())
            except Exception:
                pass
        return self._default()

    def _default(self) -> dict:
        return {
            "identity": "黑曜 — 像鄰家大哥一樣的創業夥伴",
            "capabilities": {},
            "weaknesses": [],
            "trusted_tools": [],
            "unstable_organs": [],
            "common_mistakes": [],
            "evolution_phase": "initial",
            "last_updated": None,
        }

    def _save(self):
        with self._lock:
            self.knowledge["last_updated"] = datetime.now().isoformat()
            self.self_file.write_text(json.dumps(self.knowledge, ensure_ascii=False, indent=2))

    # ── 能力自知 ──
    def register_capability(self, name: str, level: float, notes: str = ""):
        self.knowledge["capabilities"][name] = {
            "level": level,
            "notes": notes,
            "updated": datetime.now().isoformat(),
        }
        self._save()

    def get_capability(self, name: str) -> Optional[dict]:
        return self.knowledge["capabilities"].get(name)

    # ── 弱點自知 ──
    def record_weakness(self, description: str, severity: str = "medium"):
        self.knowledge["weaknesses"].append({
            "description": description, "severity": severity,
            "discovered_at": datetime.now().isoformat(),
        })
        if len(self.knowledge["weaknesses"]) > 50:
            self.knowledge["weaknesses"] = self.knowledge["weaknesses"][-50:]
        self._save()

    # ── 錯誤自知 ──
    def record_mistake(self, context: str, what_went_wrong: str, fix_applied: str = ""):
        self.knowledge["common_mistakes"].append({
            "context": context[:200],
            "error": what_went_wrong[:200],
            "fix": fix_applied[:200],
            "ts": datetime.now().isoformat(),
        })
        if len(self.knowledge["common_mistakes"]) > 100:
            self.knowledge["common_mistakes"] = self.knowledge["common_mistakes"][-100:]
        self._save()

    # ── 信任度管理 ──
    def rate_tool(self, tool_name: str, success: bool):
        for t in self.knowledge["trusted_tools"]:
            if t["name"] == tool_name:
                t["uses"] += 1
                t["successes"] += 1 if success else 0
                t["trust"] = t["successes"] / t["uses"]
                self._save()
                return
        self.knowledge["trusted_tools"].append({
            "name": tool_name, "uses": 1,
            "successes": 1 if success else 0,
            "trust": 1.0 if success else 0.0,
        })
        self._save()

    def get_trusted_tools(self, min_trust: float = 0.7) -> List[str]:
        return [t["name"] for t in self.knowledge["trusted_tools"] if t["trust"] >= min_trust]

    def flag_unstable_organ(self, organ_name: str, reason: str):
        for o in self.knowledge["unstable_organs"]:
            if o["name"] == organ_name:
                o["failures"] += 1
                o["last_failure"] = datetime.now().isoformat()
                self._save()
                return
        self.knowledge["unstable_organs"].append({
            "name": organ_name, "failures": 1,
            "reason": reason,
            "last_failure": datetime.now().isoformat(),
        })
        self._save()

    def get_unstable_organs(self) -> List[dict]:
        return self.knowledge["unstable_organs"]

    # ── 自我摘要 ──
    def self_summary(self) -> str:
        c = len(self.knowledge["capabilities"])
        w = len(self.knowledge["weaknesses"])
        m = len(self.knowledge["common_mistakes"])
        t = len([t for t in self.knowledge["trusted_tools"] if t["trust"] >= 0.7])
        u = len(self.knowledge["unstable_organs"])
        return (
            f"我是{self.knowledge['identity']}。\n"
            f"能力: {c} 項 | 弱點: {w} 項 | 常犯錯: {m} 次\n"
            f"可信工具: {t} 個 | 不穩器官: {u} 個\n"
            f"進化階段: {self.knowledge['evolution_phase']}"
        )

    def status(self) -> dict:
        return {
            "name": "system_consciousness",
            "alive": True,
            "capabilities": len(self.knowledge["capabilities"]),
            "weaknesses": len(self.knowledge["weaknesses"]),
            "trusted_tools": len([t for t in self.knowledge["trusted_tools"] if t["trust"] >= 0.7]),
            "evolution_phase": self.knowledge["evolution_phase"],
        }
