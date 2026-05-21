"""
Learning Engine — 结構化规則萃取引擎
=====================================
從 Critic 評分中萃取结構化规則，而非「心得」。

核心原則：
  ❌ 不要：「這次回答不好，因為 memory 太長」
  ✅ 要：
  {
    "pattern": "context_overflow",
    "condition": "memory_tokens > 8000",
    "rule": "apply memory compression before prompt build",
    "impact": "reduce_hallucination",
    "confidence": 0.92
  }

规則储存在 RuleStore，透過 RuntimeUpdate 回寫系统行為。
"""

import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from runtime.rule_store import Rule, RuleStore
from runtime.update_runtime import RuntimeUpdate


class LearningEngine:
    """结構化学习引擎

    管线：
    Critic 評分 → 萃取结構化规則 → 寫入 RuleStore → RuntimeUpdate 回寫

    与 learning_loop.py 的區別：
    - learning_loop：产生 fix_rule 字串（心得形式）
    - learning_engine：产生结構化 Rule（可被系统消费）
    """

    def __init__(
        self,
        llm_call: Optional[Callable] = None,
        rule_store: Optional[RuleStore] = None,
        runtime_update: Optional[RuntimeUpdate] = None,
    ):
        self.llm_call = llm_call
        self.rule_store = rule_store or RuleStore()
        self.runtime_update = runtime_update
        self.history: List[Dict] = []

    def learn(
        self,
        critic_result: Dict[str, Any],
        user_msg: str = "",
        assistant_msg: str = "",
        tool_called: str = "",
    ) -> Optional[Rule]:
        """核心方法：從 Critic 評分萃取结構化规則

        Args:
            critic_result: Critic.evaluate() 回傳的 dict
            user_msg: 使用者輸入
            assistant_msg: AI 回應
            tool_called: 調用的工具

        Returns:
            萃取出的 Rule，如果沒有可学习的則 None
        """
        score = critic_result.get("score", 0.5)
        success = critic_result.get("success", True)

        if success and score >= 0.7:
            return None

        failure_type = critic_result.get("failure_type", "unknown")
        root_cause = critic_result.get("root_cause", "")

        rule = None
        if self.llm_call and failure_type != "unknown":
            rule = self._extract_with_llm(
                failure_type, root_cause, user_msg, assistant_msg, tool_called
            )

        if rule is None:
            rule = self._template_extract(failure_type, root_cause)

        if rule is None:
            return None

        self.rule_store.add(rule)

        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "rule": rule.to_dict(),
            "critic_score": score,
        })
        if len(self.history) > 200:
            self.history = self.history[-200:]

        if self.runtime_update:
            self.runtime_update.apply_rule(rule)

        return rule

    def _extract_with_llm(
        self,
        failure_type: str,
        root_cause: str,
        user_msg: str,
        assistant_msg: str,
        tool_called: str,
    ) -> Optional[Rule]:
        """用 LLM 萃取结構化规則"""
        prompt = f"""分析這次 AI 失败，产生一条结構化的修正规則。

失败类型: {failure_type}
根因: {root_cause}
使用者輸入: {user_msg[:200]}
AI 回應: {assistant_msg[:200]}
工具調用: {tool_called or '无'}

輸出格式（纯 JSON）：
{{
  "pattern": "失败模式的简短標签",
  "condition": "触發此规則的条件",
  "rule": "今后應执行的修正规則",
  "impact": "reduce_hallucination/improve_memory/fix_tool/stabilize_identity",
  "confidence": 0.0~1.0
}}

只輸出 JSON，不要其他文字。"""
        try:
            messages = [
                {"role": "system", "content": "你是系统规則萃取助手。只輸出 JSON。"},
                {"role": "user", "content": prompt},
            ]
            result = self.llm_call(messages, temperature=0.15)
            if not result:
                return None

            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            return Rule(
                pattern=data.get("pattern", failure_type),
                condition=data.get("condition", f"failure_type == {failure_type}"),
                rule=data.get("rule", root_cause),
                impact=data.get("impact", "reduce_hallucination"),
                confidence=float(data.get("confidence", 0.6)),
            )
        except Exception:
            return None

    def _template_extract(
        self, failure_type: str, root_cause: str
    ) -> Optional[Rule]:
        """用預設模板萃取规則（LLM 不可用時的 fallback）"""
        templates = {
            "hallucination": Rule(
                pattern="hallucination",
                condition="assistant_claims_action_without_tool_result",
                rule="沒有实際工具执行结果時，禁止宣称已完成任何操作",
                impact="reduce_hallucination",
                confidence=0.7,
            ),
            "tool_failure": Rule(
                pattern="tool_failure",
                condition="tool_execution_failed",
                rule="工具失败時誠实告知使用者，并寻找替代方案继续执行",
                impact="fix_tool",
                confidence=0.7,
            ),
            "empty_response": Rule(
                pattern="empty_response",
                condition="assistant_response_too_short",
                rule="必须产生有意義、可操作的回應，不能空白",
                impact="stabilize_identity",
                confidence=0.8,
            ),
            "identity_drift": Rule(
                pattern="identity_drift",
                condition="assistant_shows_identity_uncertainty",
                rule="永不询問使用者-我應该扮演什么角色-，身份固定不可變",
                impact="stabilize_identity",
                confidence=0.9,
            ),
            "low_quality": Rule(
                pattern="low_quality",
                condition="response_lacks_specific_actions",
                rule="回應時提供具體、可执行的行动步骤，避免空泛",
                impact="improve_memory",
                confidence=0.6,
            ),
        }

        return templates.get(failure_type)

    def periodic_cleanup(self):
        """定期清理低信心规則"""
        self.rule_store.remove_low_confidence(min_confidence=0.3)

    def get_active_rules(self) -> List[Rule]:
        """取得所有活跃规則"""
        return self.rule_store.get_active()

    def get_rules_context(self) -> str:
        """取得可註入 Context 的规則文字"""
        return self.rule_store.get_rules_for_context()

    def status(self) -> dict:
        return {
            "rules": self.rule_store.status(),
            "history_count": len(self.history),
        }
