"""
Critic — 回应品质评分层
=========================
没有评分就没有学习。Critic 是 Learning Loop 的前置条件。

每次 LLM 输出后，Critic 必须评分：
- 品质分数 (0~1)
- 成功/失败
- 错误类型
- 改进方向
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class CriticResponse:
    """评分结果"""

    def __init__(self):
        self.score: float = 0.5
        self.success: bool = True
        self.failure_type: str = ""
        self.root_cause: str = ""
        self.error_patterns: List[str] = []
        self.improvement_hint: str = ""
        self.confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "success": self.success,
            "failure_type": self.failure_type,
            "root_cause": self.root_cause,
            "error_patterns": self.error_patterns,
            "improvement_hint": self.improvement_hint,
            "confidence": self.confidence,
        }


class Critic:
    """回应品质评分器

    评分面向：
    1. 工具调用是否正确执行
    2. 回应是否完成使用者请求
    3. 是否有幻觉/编造
    4. 语气是否自然
    """

    def __init__(self):
        self.history: List[Dict] = []

    def evaluate(
        self,
        user_msg: str = "",
        assistant_msg: str = "",
        tool_called: str = "",
        tool_result: str = "",
        expected_action: str = "",
    ) -> CriticResponse:
        """核心方法：评估本次回应品质

        Args:
            user_msg: 使用者输入
            assistant_msg: AI 回应
            tool_called: 调用的工具名称
            tool_result: 工具执行结果
            expected_action: 预期行为描述

        Returns:
            CriticResponse 评分结果
        """
        result = CriticResponse()

        # 1. 幻觉检测：是否宣称做了但没工具调用
        if self._check_hallucination(assistant_msg, tool_called, tool_result):
            result.score = 0.2
            result.success = False
            result.failure_type = "hallucination"
            result.root_cause = "宣称执行了操作但没有实际工具调用结果"
            result.error_patterns.append("无中生有")
            result.improvement_hint = "没有实际执行时不要说完成了什么"
            result.confidence = 0.9

        # 2. 工具调用失败检测
        elif tool_called and tool_result and self._check_tool_failure(tool_result):
            result.score = 0.3
            result.success = False
            result.failure_type = "tool_failure"
            result.root_cause = f"工具 {tool_called} 返回异常"
            result.error_patterns.append("工具执行失败")
            result.improvement_hint = "工具不可用时寻找替代方案，不要放弃"
            result.confidence = 0.8

        # 3. 空回应检测
        elif not assistant_msg or len(assistant_msg) < 5:
            result.score = 0.1
            result.success = False
            result.failure_type = "empty_response"
            result.root_cause = "回应为空或过短"
            result.error_patterns.append("空回应")
            result.improvement_hint = "产生有意义的回应"
            result.confidence = 1.0

        # 4. 身份漂移检测
        elif self._check_identity_drift(assistant_msg):
            result.score = 0.4
            result.success = False
            result.failure_type = "identity_drift"
            result.root_cause = "回应中表现出身份不确定"
            result.error_patterns.append("身份漂移")
            result.improvement_hint = "永远不要问'我应该扮演什么角色'"
            result.confidence = 0.85

        # 5. 成功评分
        else:
            result.score = self._calculate_success_score(
                user_msg, assistant_msg, tool_called, tool_result
            )
            result.success = result.score >= 0.6
            if not result.success:
                result.failure_type = "low_quality"
                result.root_cause = "回应品质低于阈值"
                result.improvement_hint = "更具体、更有行动性的回应"

        record = {
            "timestamp": datetime.now().isoformat(),
            "user_msg": user_msg[:200],
            "assistant_msg": assistant_msg[:200],
            "tool_called": tool_called,
            "result": result.to_dict(),
        }
        self.history.append(record)
        if len(self.history) > 500:
            self.history = self.history[-500:]

        return result

    def _check_hallucination(self, msg: str, tool: str, result: str) -> bool:
        """检测幻觉：说了做了但没实际执行"""
        if not msg:
            return False
        action_words = ["已", "完成", "执行", "扫描", "检查", "修复", "写入", "建立", "删除"]
        has_action = any(w in msg for w in action_words)

        if has_action and not tool and not result:
            return True
        if has_action and tool and result and "error" in str(result).lower():
            return True
        return False

    def _check_tool_failure(self, result: str) -> bool:
        """检测工具失败"""
        failure_indicators = ["error", "failed", "exception", "错误", "失败", "异常", "❌"]
        return any(w in str(result).lower() for w in failure_indicators)

    def _check_identity_drift(self, msg: str) -> bool:
        """检测身份漂移"""
        drift_patterns = [
            "扮演什么角色",
            "你想让我扮演",
            "我是chatgpt",
            "我是 assistant",
            "我是AI助手",
            "你想要我扮演",
            "我该怎么称呼自己",
        ]
        return any(p in msg for p in drift_patterns)

    def _calculate_success_score(
        self, user_msg: str, assistant_msg: str, tool_called: str, tool_result: str
    ) -> float:
        """计算成功品质分数"""
        score = 0.5

        # 有工具调用 + 成功结果
        if tool_called and tool_result:
            score += 0.2
        # 有具体行动
        action_words = ["已", "完成", "执行", "扫描", "检查", "修复"]
        if any(w in assistant_msg for w in action_words):
            score += 0.1
        # 长度适中
        if 20 < len(assistant_msg) < 2000:
            score += 0.1
        # 没有不确定词汇
        uncertain = ["或许", "可能", "不确定", "不知道能不能", "试试看"]
        if not any(w in assistant_msg for w in uncertain):
            score += 0.1

        return min(1.0, score)

    def get_failure_stats(self) -> Dict[str, int]:
        """错误类型统计"""
        stats: Dict[str, int] = {}
        for record in self.history:
            ft = record.get("result", {}).get("failure_type", "unknown")
            stats[ft] = stats.get(ft, 0) + 1
        return stats

    def get_recent_failures(self, n: int = 10) -> List[Dict]:
        """最近失败记录"""
        failures = [r for r in self.history if not r.get("result", {}).get("success", True)]
        return failures[-n:]

    def status(self) -> dict:
        return {
            "total_evaluations": len(self.history),
            "failure_stats": self.get_failure_stats(),
        }
