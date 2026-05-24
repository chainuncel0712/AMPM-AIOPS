"""System Consciousness — 全系統意識：知道「我是誰、我在哪、我缺什麼」
不寫日記、不累積錯誤。發現問題直接修正原始碼或 SYSTEM_PROMPT。
"""
import json, threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SystemConsciousness:
    """存在層認知：我是什麼、我有什麼能力、我缺什麼。
    不記錄錯誤日記 —— 發現問題就直接修原始碼。
    """

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
            "evolution_phase": "initial",
            "last_updated": None,
        }

    def _save(self):
        with self._lock:
            self.knowledge["last_updated"] = datetime.now().isoformat()
            self.self_file.write_text(json.dumps(self.knowledge, ensure_ascii=False, indent=2))

    # ── 能力自知（唯獨資料持久化是正當的）──
    def register_capability(self, name: str, level: float, notes: str = ""):
        self.knowledge["capabilities"][name] = {
            "level": level,
            "notes": notes,
            "updated": datetime.now().isoformat(),
        }
        self._save()

    def get_capability(self, name: str) -> Optional[dict]:
        return self.knowledge["capabilities"].get(name)

    # ── 錯誤自知 → 不記錄，直接修正源碼 ──
    def record_mistake(self, context: str, what_went_wrong: str, fix_applied: str = ""):
        pass

    # ── 弱點自知 → 不記錄，直接強化系統 ──
    def record_weakness(self, description: str, severity: str = "medium"):
        pass

    # ── 不穩器官 → 不記錄，直接觸發修復 ──
    def flag_unstable_organ(self, organ_name: str, reason: str):
        pass

    def get_unstable_organs(self) -> List[dict]:
        return []

    # ── 自我摘要 ──
    def self_summary(self) -> str:
        c = len(self.knowledge["capabilities"])
        return (
            f"我是{self.knowledge['identity']}。\n"
            f"能力: {c} 項 | 無日記模式\n"
            f"進化階段: {self.knowledge['evolution_phase']}"
        )

    def status(self) -> dict:
        return {
            "name": "system_consciousness",
            "alive": True,
            "capabilities": len(self.knowledge["capabilities"]),
            "mode": "source-code-repair",
            "lessons_accumulated": 0,
        }
