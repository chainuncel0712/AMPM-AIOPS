"""
Runtime Update — 運行時回寫層
==============================
讓 Learning 的结果真正影响下一次 LLM 調用。

這是系统闭环的最后一环。
沒有這一層，学习就是空的。

回寫目標：
- Context Pipeline   — 改思考方式
- Memory Weights     — 改记忆检索權重
- Tool Priorities    — 改工具調用順序
- Planner Behavior   — 改规劃策略

核心公式：
  Learning = 修改「下一次怎么做」
  NOT Learning = 记录结果
"""

from typing import Any, Dict, List, Optional

from runtime.rule_store import Rule, RuleStore


class RuntimeUpdate:
    """運行時更新器 — 将学习规則回寫到運行系统"""

    def __init__(self, rule_store: Optional[RuleStore] = None):
        self.rule_store = rule_store or RuleStore()
        self.updates: List[Dict] = []
        self.memory_weight_overrides: Dict[str, float] = {}
        self.tool_priority_overrides: Dict[str, float] = {}
        self.planner_strategy_overrides: List[str] = []

    def apply_rule(self, rule: Rule):
        """應用單条规則到運行時

        根据规則的 impact 字段，修改對應的系统行為：
        - reduce_hallucination  → 提高 importance 權重
        - improve_memory        → 提高 relevance 權重
        - fix_tool              → 調整工具優先级
        - stabilize_identity    → 加强身份註入
        """
        impact = rule.impact
        self.rule_store.record_application(rule.id)

        if impact == "reduce_hallucination":
            # 幻觉頻繁時：降低 recency，提高 importance
            self.memory_weight_overrides["recency"] = max(
                0.1, self.memory_weight_overrides.get("recency", 0.3) - 0.05
            )
            self.memory_weight_overrides["importance"] = min(
                0.5, self.memory_weight_overrides.get("importance", 0.2) + 0.05
            )

        elif impact == "improve_memory":
            # 记忆检索不好時：提高 relevance 權重
            self.memory_weight_overrides["relevance"] = min(
                0.7, self.memory_weight_overrides.get("relevance", 0.5) + 0.05
            )

        elif impact == "fix_tool":
            # 工具失败時：提高稳健工具優先级
            self.tool_priority_overrides["fallback_first"] = 1.0

        elif impact == "stabilize_identity":
            # 身份漂移時：加入额外身份保護规則
            strategy = "身份验證前置：在生成回應前检查身份一致性"
            if strategy not in self.planner_strategy_overrides:
                self.planner_strategy_overrides.append(strategy)

        self.updates.append({
            "rule_id": rule.id,
            "impact": impact,
            "memory_weights": dict(self.memory_weight_overrides),
            "tool_priorities": dict(self.tool_priority_overrides),
            "planner_strategies": list(self.planner_strategy_overrides),
        })

        if len(self.updates) > 100:
            self.updates = self.updates[-100:]

    def apply_evolution(
        self,
        memory_weights: Optional[Dict[str, float]] = None,
        tool_priorities: Optional[Dict[str, float]] = None,
        planner_strategies: Optional[List[str]] = None,
    ):
        """應用 Evolution Engine 的輸出"""
        if memory_weights:
            self.memory_weight_overrides = memory_weights
        if tool_priorities:
            self.tool_priority_overrides.update(tool_priorities)
        if planner_strategies:
            for s in planner_strategies:
                if s not in self.planner_strategy_overrides:
                    self.planner_strategy_overrides.append(s)

    def get_memory_weights(self) -> Dict[str, float]:
        """取得當前记忆權重（可用于覆盖 PriorityScorer）"""
        default = {"relevance": 0.5, "recency": 0.3, "importance": 0.2}
        default.update(self.memory_weight_overrides)
        return default

    def get_tool_hints(self) -> str:
        """取得工具選择提示"""
        if not self.tool_priority_overrides:
            return ""
        return "工具優先策略：優先使用稳健工具，失败時立即切换備選"

    def get_planner_strategies(self) -> List[str]:
        """取得规劃策略覆寫"""
        return self.planner_strategy_overrides

    def get_extra_system_prompt(self) -> str:
        """從 RuleStore 和覆寫产生额外的系统提示"""
        parts = []

        rules_context = self.rule_store.get_rules_for_context()
        if rules_context:
            parts.append(rules_context)

        if self.tool_priority_overrides:
            parts.append(self.get_tool_hints())

        if self.planner_strategy_overrides:
            strategies = "\n".join(f"- {s}" for s in self.planner_strategy_overrides)
            parts.append(f"[演化后的规劃策略]\n{strategies}")

        return "\n\n".join(parts)

    def get_latest_config(self) -> Dict:
        """取得最新配置快照"""
        return {
            "memory_weights": self.get_memory_weights(),
            "tool_priorities": self.tool_priority_overrides,
            "planner_strategies": self.planner_strategy_overrides,
            "active_rules": self.rule_store.status(),
            "updates_count": len(self.updates),
        }

    def status(self) -> dict:
        return self.get_latest_config()
