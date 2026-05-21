"""
Rule Store — 结構化规則庫
==========================
持久化储存系统從失败中学习的修正规則。

规則格式（结構化，不是心得）：
{
  "id": "rule_001",
  "pattern": "context_overflow",
  "condition": "memory_tokens > 8000",
  "rule": "apply memory compression before prompt build",
  "impact": "reduce_hallucination",
  "confidence": 0.92,
  "enabled": true,
  "applied_count": 0,
  "created_at": "...",
  "last_applied": "..."
}

储存位置：data/rules/runtime_rules.json
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Rule:
    """單条规則"""

    def __init__(
        self,
        pattern: str = "",
        condition: str = "",
        rule: str = "",
        impact: str = "",
        confidence: float = 0.5,
    ):
        self.id: str = str(uuid.uuid4())[:8]
        self.pattern: str = pattern
        self.condition: str = condition
        self.rule: str = rule
        self.impact: str = impact
        self.confidence: float = confidence
        self.enabled: bool = True
        self.applied_count: int = 0
        self.created_at: str = datetime.now().isoformat()
        self.last_applied: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pattern": self.pattern,
            "condition": self.condition,
            "rule": self.rule,
            "impact": self.impact,
            "confidence": self.confidence,
            "enabled": self.enabled,
            "applied_count": self.applied_count,
            "created_at": self.created_at,
            "last_applied": self.last_applied,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        r = cls(
            pattern=data.get("pattern", ""),
            condition=data.get("condition", ""),
            rule=data.get("rule", ""),
            impact=data.get("impact", ""),
            confidence=data.get("confidence", 0.5),
        )
        r.id = data.get("id", r.id)
        r.enabled = data.get("enabled", True)
        r.applied_count = data.get("applied_count", 0)
        r.created_at = data.get("created_at", r.created_at)
        r.last_applied = data.get("last_applied", "")
        return r


class RuleStore:
    """规則庫 — 持久化储存和管理系统规則"""

    def __init__(self, rules_file: str = "data/rules/runtime_rules.json"):
        self.rules_file = Path(rules_file)
        self.rules: Dict[str, Rule] = {}
        self._load()

    def _load(self):
        if self.rules_file.exists():
            try:
                data = json.loads(self.rules_file.read_text())
                for item in data:
                    rule = Rule.from_dict(item)
                    self.rules[rule.id] = rule
            except Exception:
                pass

    def _save(self):
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self.rules.values()]
        self.rules_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    def add(self, rule: Rule) -> str:
        """添加规則，自动去重"""
        for existing in self.rules.values():
            if existing.pattern == rule.pattern and existing.rule == rule.rule:
                existing.confidence = max(existing.confidence, rule.confidence)
                existing.last_applied = datetime.now().isoformat()
                self._save()
                return existing.id

        self.rules[rule.id] = rule
        self._save()
        return rule.id

    def get(self, rule_id: str) -> Optional[Rule]:
        return self.rules.get(rule_id)

    def get_active(self) -> List[Rule]:
        """取得所有啟用的规則"""
        return [r for r in self.rules.values() if r.enabled]

    def get_by_pattern(self, pattern: str) -> List[Rule]:
        """按模式查询"""
        return [r for r in self.rules.values() if r.pattern == pattern and r.enabled]

    def get_by_impact(self, impact: str) -> List[Rule]:
        """按影响范围查询"""
        return [r for r in self.rules.values() if r.impact == impact and r.enabled]

    def enable(self, rule_id: str):
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = True
            self._save()

    def disable(self, rule_id: str):
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = False
            self._save()

    def record_application(self, rule_id: str):
        """记录规則被應用"""
        rule = self.rules.get(rule_id)
        if rule:
            rule.applied_count += 1
            rule.last_applied = datetime.now().isoformat()
            self._save()

    def get_rules_for_context(self) -> str:
        """产生可註入 Context 的规則摘要（只取前 5 条高信心）"""
        active = sorted(self.get_active(), key=lambda r: -r.confidence)[:5]
        if not active:
            return ""

        lines = ["[规則摘要]"]
        for r in active:
            lines.append(f"- {r.rule[:80]}")

        return "\n".join(lines)

    def get_rules_for_tools(self) -> List[str]:
        """取得影响工具使用的规則"""
        tool_rules = []
        for r in self.get_active():
            if "tool" in r.impact.lower() or "tool" in r.pattern.lower():
                tool_rules.append(r.rule)
        return tool_rules

    def get_rules_for_planner(self) -> List[str]:
        """取得影响规劃策略的规則"""
        planner_rules = []
        for r in self.get_active():
            if "planner" in r.impact.lower() or "plan" in r.pattern.lower():
                planner_rules.append(r.rule)
        return planner_rules

    def remove_low_confidence(self, min_confidence: float = 0.3):
        """删除低信心规則"""
        to_remove = []
        for rid, rule in self.rules.items():
            if rule.confidence < min_confidence and rule.applied_count == 0:
                to_remove.append(rid)
        for rid in to_remove:
            del self.rules[rid]
        if to_remove:
            self._save()

    def status(self) -> dict:
        active = self.get_active()
        return {
            "total_rules": len(self.rules),
            "active_rules": len(active),
            "by_impact": {
                impact: len(self.get_by_impact(impact))
                for impact in set(r.impact for r in active if r.impact)
            },
        }
