"""
Evolution Engine — 进化引擎
============================
负责：从失败模式中检测规律，演化系统行为。

不是记录，而是修改行为。
3 条修改路径：
1. planner strategy — 改任务规划策略
2. memory weighting — 改记忆评分权重
3. tool priority — 改工具调用优先级

与 Learning Loop 的关系：
  Learning Loop → fix_rules → Evolution Engine → behavior mutation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class EvolutionEngine:
    """进化引擎 — 从学习结果中演化行为

    检测重复失败模式，调整系统参数。
    不只记录，真的改。
    """

    def __init__(self):
        self.mutations: List[Dict] = []
        self.patterns: Dict[str, Dict] = {}
        self.memory_weights = {
            "relevance": 0.5,
            "recency": 0.3,
            "importance": 0.2,
        }
        self.tool_priorities: Dict[str, float] = {}
        self.planner_strategies: List[str] = []

    def detect_patterns(self, learning_records: List[Dict]) -> List[Dict]:
        """从学习记录中检测重复失败模式

        Args:
            learning_records: LearningLoop.records

        Returns:
            检测到的重复模式列表
        """
        pattern_counts: Dict[str, int] = {}
        pattern_contexts: Dict[str, List] = {}

        for record in learning_records[-100:]:
            ft = record.get("failure_type", "unknown")
            root = record.get("root_cause", "")[:80]

            key = f"{ft}:{root}"
            pattern_counts[key] = pattern_counts.get(key, 0) + 1
            pattern_contexts.setdefault(key, []).append(record)

        detected = []
        for key, count in pattern_counts.items():
            if count >= 3:  # 重复出现 3 次以上才视为模式
                self.patterns[key] = {
                    "count": count,
                    "first_seen": pattern_contexts[key][0].get("timestamp", ""),
                    "last_seen": pattern_contexts[key][-1].get("timestamp", ""),
                }
                detected.append({
                    "pattern": key,
                    "count": count,
                    "fix_rule": pattern_contexts[key][-1].get("fix_rule", ""),
                })

        return detected

    def mutate_memory_weights(self, failure_patterns: List[Dict]) -> Dict[str, float]:
        """演化记忆权重

        如果 hallucination 频繁发生 → 降低 recency 权重（别太信最近记忆）
        如果回应太泛 → 提高 relevance 权重
        如果忘记重要事实 → 提高 importance 权重
        """
        old_weights = dict(self.memory_weights)

        for p in failure_patterns:
            key = p.get("pattern", "")
            if "hallucination" in key:
                self.memory_weights["recency"] *= 0.9
                self.memory_weights["importance"] *= 1.05
            elif "identity_drift" in key:
                self.memory_weights["relevance"] *= 1.05
            elif "low_quality" in key:
                self.memory_weights["relevance"] *= 1.05

        # 正规化
        total = sum(self.memory_weights.values())
        if total > 0:
            self.memory_weights = {k: round(v / total, 2) for k, v in self.memory_weights.items()}

        if self.memory_weights != old_weights:
            self._record_mutation("memory_weights", old_weights, self.memory_weights)

        return self.memory_weights

    def mutate_tool_priorities(self, failure_patterns: List[Dict]) -> Dict[str, float]:
        """演化工具优先级

        如果某工具频繁失败 → 降低优先级
        如果某工具结果很好 → 提高优先级
        """
        for p in failure_patterns:
            key = p.get("pattern", "")
            if "tool_failure" in key:
                root = p.get("fix_rule", "")
                for tool_prefix in ["run_command", "self_upgrade", "generate_tool", "web_search"]:
                    if tool_prefix in root:
                        self.tool_priorities[tool_prefix] = self.tool_priorities.get(tool_prefix, 1.0) * 0.8

        self._record_mutation("tool_priorities", {}, self.tool_priorities)
        return self.tool_priorities

    def mutate_planner_strategies(self, failure_patterns: List[Dict]) -> List[str]:
        """演化规划策略

        根据失败模式调整规划优先顺序
        """
        for p in failure_patterns:
            key = p.get("pattern", "")
            if "hallucination" in key:
                strategy = "执行前验证工具可用性"
                if strategy not in self.planner_strategies:
                    self.planner_strategies.append(strategy)
            elif "tool_failure" in key:
                strategy = "优先选择稳定工具"
                if strategy not in self.planner_strategies:
                    self.planner_strategies.append(strategy)

        self._record_mutation("planner_strategies", [], self.planner_strategies)
        return self.planner_strategies

    def evolve(self, learning_records: List[Dict]) -> Dict[str, Any]:
        """完整演化周期

        1. 检测模式
        2. 演化记忆权重
        3. 演化工具优先级
        4. 演化规划策略

        Returns:
            本次演化的所有修改
        """
        patterns = self.detect_patterns(learning_records)

        if not patterns:
            return {"mutated": False, "reason": "未检测到重复失败模式"}

        result: Dict[str, Any] = {
            "mutated": True,
            "patterns_detected": len(patterns),
            "memory_weights": self.mutate_memory_weights(patterns),
            "tool_priorities": self.mutate_tool_priorities(patterns),
            "planner_strategies": self.mutate_planner_strategies(patterns),
            "timestamp": datetime.now().isoformat(),
        }

        return result

    def _record_mutation(self, field: str, old_value: Any, new_value: Any):
        self.mutations.append({
            "field": field,
            "old": old_value,
            "new": new_value,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.mutations) > 500:
            self.mutations = self.mutations[-500:]

    def get_current_config(self) -> Dict:
        """取得当前所有演化后的配置"""
        return {
            "memory_weights": self.memory_weights,
            "tool_priorities": self.tool_priorities,
            "planner_strategies": self.planner_strategies,
        }

    def status(self) -> dict:
        return {
            "mutations": len(self.mutations),
            "patterns": len(self.patterns),
            "memory_weights": self.memory_weights,
        }
