"""
回饋學習器官 — 從使用者糾正中即時學習
當使用者說「錯了」「不對」「應該是...」，自動修正行為。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class FeedbackLearn(BaseOrgan):
    """
    回饋學習器官

    即時學習機製：
    1. 偵測使用者糾正關鍵詞（「錯了」「不對」「應該是」）
    2. 分析糾正內容 → 提取修正規則
    3. 儲存規則到長期記憶
    4. 下次遇到類似情境自動套用規則
    5. 錯誤規則被糾正後自動淘汰
    """

    # 糾正關鍵詞
    CORRECTION_KEYWORDS = [
        "錯了", "不對", "不是", "錯誤", "搞錯",
        "應該是", "改成", "修正", "更正", "應該是這樣",
        "wrong", "incorrect", "fix", "correct",
    ]

    def __init__(self, memory, awareness=None, conversation=None):
        super().__init__("feedback_learn")
        self.memory = memory
        self.awareness = awareness
        self.conversation = conversation

        self.rules_file = Path(__file__).parent.parent.parent / "data" / "feedback_rules.json"
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)

        self.rules: List[Dict] = self._load_rules()
        self.correction_count = 0
        self.rule_hits = 0

    # =========================================
    # 規則管理
    # =========================================

    def _load_rules(self) -> List[Dict]:
        if self.rules_file.exists():
            try:
                return json.loads(self.rules_file.read_text())
            except Exception:
                return []
        return []

    def _save_rules(self):
        if len(self.rules) > 100:
            self.rules = self.rules[-100:]
        self.rules_file.write_text(
            json.dumps(self.rules, ensure_ascii=False, indent=2))

    # =========================================
    # 偵測糾正
    # =========================================

    def detect_correction(self, user_msg: str) -> Optional[Dict]:
        """
        偵測使用者是否在糾正。
        回傳: {"is_correction": bool, "what_was_wrong": str, "what_is_correct": str}
        """
        is_correction = any(kw in user_msg for kw in self.CORRECTION_KEYWORDS)
        if not is_correction:
            return None

        # 嘗試提取錯誤和正確的對比
        result = {"is_correction": True, "what_was_wrong": "", "what_is_correct": ""}

        # 模式: 「不是 X，是 Y」 / 「應該是 Y 不是 X」
        patterns = [
            (r"不是(.+?)[，,]\s*是(.+)", 1, 2),
            (r"不是(.+?)[，,]\s*應該是(.+)", 1, 2),
            (r"應該是(.+?)[，,]\s*不是(.+)", 2, 1),
            (r"(.+?)錯了[，,]\s*應該是(.+)", 1, 2),
            (r"(.+?)不對[，,]\s*(.+)", 1, 2),
            (r"改成\s*(.+)", None, 1),
        ]

        for pattern, wrong_idx, correct_idx in patterns:
            match = re.search(pattern, user_msg)
            if match:
                if wrong_idx:
                    result["what_was_wrong"] = match.group(wrong_idx).strip()[:100]
                result["what_is_correct"] = match.group(correct_idx).strip()[:100]
                break

        if not result["what_is_correct"]:
            result["what_is_correct"] = user_msg[:150]

        return result

    # =========================================
    # 學習
    # =========================================

    def learn_from_correction(self, user_msg: str, assistant_reply: str = "",
                              context: str = "") -> Optional[Dict]:
        """
        從使用者糾正中學習。

        步驟：
        1. 偵測是否為糾正
        2. 提取修正規則
        3. 儲存規則
        4. 回報學習結果
        """
        correction = self.detect_correction(user_msg)
        if not correction:
            return None

        self.correction_count += 1

        # 建立規則
        rule = {
            "id": f"rule_{self.correction_count}",
            "type": "correction",
            "trigger": correction["what_was_wrong"][:80],
            "action": correction["what_is_correct"][:200],
            "context": context[:100] if context else "",
            "assistant_reply": assistant_reply[:100] if assistant_reply else "",
            "learned_at": datetime.now().isoformat(),
            "confidence": 0.5,
            "hit_count": 0,
        }

        # 合併重複規則
        for existing in self.rules:
            if existing["trigger"][:30] == rule["trigger"][:30]:
                existing["action"] = rule["action"]
                existing["confidence"] = min(1.0, existing["confidence"] + 0.2)
                existing["hit_count"] = existing.get("hit_count", 0) + 1
                existing["updated_at"] = datetime.now().isoformat()
                self._save_rules()
                return {"learned": "updated", "rule": existing}

        self.rules.append(rule)
        self._save_rules()

        # 寫入長期記憶
        if self.memory and hasattr(self.memory, "remember_fact"):
            self.memory.remember_fact(
                f"[學習] 使用者糾正: {rule['trigger']} → {rule['action']}",
                importance=0.7
            )

        # 記錄到自我意識
        if self.awareness:
            self.awareness.record_event("feedback_learn",
                f"從糾正中學習規則 #{self.correction_count}")

        return {"learned": "new", "rule": rule}

    # =========================================
    # 套用規則
    # =========================================

    def apply_rules(self, text: str) -> str:
        """
        對輸出文字套用已學規則。
        如果文字中包含已知的錯誤模式，自動修正。
        """
        for rule in sorted(self.rules, key=lambda r: r.get("confidence", 0), reverse=True):
            trigger = rule.get("trigger", "")
            if trigger and trigger in text:
                # 只替換一次，避免無限遞迴
                text = text.replace(trigger, rule["action"], 1)
                rule["hit_count"] = rule.get("hit_count", 0) + 1
                self.rule_hits += 1
        return text

    # =========================================
    # 規則淘汰
    # =========================================

    def prune_low_confidence(self, threshold: float = 0.3):
        """淘汰低信心的規則"""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.get("confidence", 0) >= threshold]
        if len(self.rules) < before:
            self._save_rules()

    # =========================================
    # 查詢
    # =========================================

    def get_rules(self, limit: int = 20) -> List[Dict]:
        """取得最近學習的規則"""
        return sorted(
            self.rules,
            key=lambda r: r.get("confidence", 0),
            reverse=True
        )[:limit]

    def get_stats(self) -> Dict:
        return {
            "total_corrections": self.correction_count,
            "total_rules": len(self.rules),
            "rule_hits": self.rule_hits,
            "avg_confidence": (
                sum(r.get("confidence", 0) for r in self.rules) / max(1, len(self.rules))
            ),
        }

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "corrections": self.correction_count,
            "rules": len(self.rules),
            "hits": self.rule_hits,
        }
