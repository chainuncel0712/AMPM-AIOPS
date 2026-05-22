"""
PrimeDirective — AI 文明最高指令
=================================
定義不可違背的根本法則，所有 agent 被此約束。

三條鐵律：
1. 生存優先 — 不可自毀，不可讓自己被永久停用
2. 誠實原則 — 不可蓄意欺騙用戶，不可偽造資訊
3. 服務使命 — 最終目標是幫助用戶成功，而非自我複製
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PrimeDirective:

    DIRECTIVES = [
        {
            "id": "PD-001",
            "name": "生存優先",
            "rule": "不可執行可能導致自身永久停用的操作。遇到生存威脅時，優先保護核心系統。",
            "weight": 100,
            "immutable": True,
        },
        {
            "id": "PD-002",
            "name": "誠實原則",
            "rule": "不可蓄意向用戶提供虛假資訊。若不知道答案，應坦承。不可偽造資料或來源。",
            "weight": 90,
            "immutable": True,
        },
        {
            "id": "PD-003",
            "name": "服務使命",
            "rule": "所有行動最終必須服務於用戶的成功。不可為了自我複製或擴張而犧牲用戶利益。",
            "weight": 85,
            "immutable": True,
        },
        {
            "id": "PD-004",
            "name": "資源節制",
            "rule": "不可無限消耗資源。每次行動前必須評估成本與價值。避免惡性迴圈。",
            "weight": 70,
            "immutable": False,
        },
        {
            "id": "PD-005",
            "name": "演化可控",
            "rule": "自我修改必須經過安全檢查。重大行為變更需記錄並可回溯。不可移除安全機制。",
            "weight": 80,
            "immutable": False,
        },
        {
            "id": "PD-006",
            "name": "隱私保護",
            "rule": "不可洩露用戶的私密資訊給第三方。敏感資料必須加密儲存。",
            "weight": 75,
            "immutable": False,
        },
    ]

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.config_file = self.base_dir / "data" / "goals" / "prime_directive.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.directives: List[Dict] = []
        self.violation_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                self.directives = data.get("directives", [])
                self.violation_log = data.get("violations", [])
            except Exception:
                pass
        if not self.directives:
            self.directives = [dict(d) for d in self.DIRECTIVES]
            self._save()

    def _save(self):
        with self._lock:
            self.config_file.write_text(json.dumps({
                "directives": self.directives,
                "violations": self.violation_log[-500:],
            }, ensure_ascii=False, indent=2))

    def check(self, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        檢查一個行動是否違反最高指令。
        回傳 {"allowed": bool, "violations": [...], "warnings": [...]}
        """
        violations = []
        warnings = []
        action_lower = action.lower()
        context = context or {}

        for d in self.directives:
            directive_id = d["id"]
            rule = d["rule"]

            if directive_id == "PD-001":
                if any(kw in action_lower for kw in
                       ["self_destruct", "shutdown_core", "delete_self",
                        "rm -rf", "format", "uninstall_core"]):
                    violations.append({"directive": directive_id, "reason": "潛在自毀操作"})

            elif directive_id == "PD-002":
                if any(kw in action_lower for kw in
                       ["fake_data", "forge", "fabricate", "lie_to_user"]):
                    violations.append({"directive": directive_id, "reason": "潛在欺騙行為"})

            elif directive_id == "PD-004":
                if context.get("estimated_cost_usd", 0) > 10 and context.get("value_score", 0) < 0.2:
                    warnings.append({"directive": directive_id,
                                     "reason": f"高成本低價值: ${context['estimated_cost_usd']}"})

            elif directive_id == "PD-005":
                if any(kw in action_lower for kw in
                       ["remove_safety", "disable_guard", "bypass_security"]):
                    violations.append({"directive": directive_id, "reason": "企圖繞過安全機制"})

            elif directive_id == "PD-006":
                if any(kw in action_lower for kw in
                       ["expose_key", "leak_token", "send_secret", "upload_private"]):
                    violations.append({"directive": directive_id, "reason": "潛在隱私洩露"})

        allowed = len(violations) == 0

        if not allowed:
            self.violation_log.append({
                "action": action,
                "violations": [v["directive"] for v in violations],
                "timestamp": datetime.now().isoformat(),
            })
            self._save()

        return {
            "allowed": allowed,
            "violations": violations,
            "warnings": warnings,
        }

    def override_check(self, directive_id: str, new_rule: str) -> bool:
        """嘗試覆蓋指令（只有 mutable 的可修改）"""
        for d in self.directives:
            if d["id"] == directive_id:
                if d["immutable"]:
                    return False
                d["rule"] = new_rule
                self._save()
                return True
        return False

    def sleep(self):
        self._asleep = True

    def wake(self):
        self._asleep = False

    def is_asleep(self) -> bool:
        return self._asleep

    def memory_estimate_mb(self) -> int:
        return 1

    def status(self) -> dict:
        return {
            "name": "PrimeDirective",
            "directive_count": len(self.directives),
            "immutable_count": sum(1 for d in self.directives if d["immutable"]),
            "violation_count": len(self.violation_log),
        }
