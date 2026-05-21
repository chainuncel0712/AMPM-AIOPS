"""
Critic — 回應品質評分層
=========================
沒有評分就沒有学习。Critic 是 Learning Loop 的前置条件。

每次 LLM 輸出后，Critic 必须評分：
- 品質分数 (0~1)
- 成功/失败
- 错誤类型
- 改進方向
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class CriticResponse:
    """評分结果"""

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
    """回應品質評分器

    評分面向：
    1. 工具調用是否正确执行
    2. 回應是否完成使用者請求
    3. 是否有幻觉/编造
    4. 語气是否自然
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
        """核心方法：評估本次回應品質

        Args:
            user_msg: 使用者輸入
            assistant_msg: AI 回應
            tool_called: 調用的工具名称
            tool_result: 工具执行结果
            expected_action: 預期行為描述

        Returns:
            CriticResponse 評分结果
        """
        result = CriticResponse()

        # 1. 幻觉检測：是否宣称做了但沒工具調用
        if self._check_hallucination(assistant_msg, tool_called, tool_result):
            result.score = 0.2
            result.success = False
            result.failure_type = "hallucination"
            result.root_cause = "宣称执行了操作但沒有实際工具調用结果"
            result.error_patterns.append("无中生有")
            result.improvement_hint = "沒有实際执行時不要說完成了什么"
            result.confidence = 0.9

        # 2. 工具調用失败检測
        elif tool_called and tool_result and self._check_tool_failure(tool_result):
            result.score = 0.3
            result.success = False
            result.failure_type = "tool_failure"
            result.root_cause = f"工具 {tool_called} 返回异常"
            result.error_patterns.append("工具执行失败")
            result.improvement_hint = "工具不可用時寻找替代方案，不要放弃"
            result.confidence = 0.8

        # 3. 空回應检測
        elif not assistant_msg or len(assistant_msg) < 5:
            result.score = 0.1
            result.success = False
            result.failure_type = "empty_response"
            result.root_cause = "回應為空或過短"
            result.error_patterns.append("空回應")
            result.improvement_hint = "产生有意義的回應"
            result.confidence = 1.0

        # 4. 身份漂移检測
        elif self._check_identity_drift(assistant_msg):
            result.score = 0.4
            result.success = False
            result.failure_type = "identity_drift"
            result.root_cause = "回應中表现出身份不确定"
            result.error_patterns.append("身份漂移")
            result.improvement_hint = "永遠不要問'我應该扮演什么角色'"
            result.confidence = 0.85

        # 5. 成功評分
        else:
            result.score = self._calculate_success_score(
                user_msg, assistant_msg, tool_called, tool_result
            )
            result.success = result.score >= 0.6
            if not result.success:
                result.failure_type = "low_quality"
                result.root_cause = "回應品質低于阈值"
                result.improvement_hint = "更具體、更有行动性的回應"

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
        """检測幻觉：說了做了但沒实際执行"""
        if not msg:
            return False
        action_words = ["已", "完成", "执行", "扫描", "检查", "修復", "寫入", "建立", "删除"]
        has_action = any(w in msg for w in action_words)

        if has_action and not tool and not result:
            return True
        if has_action and tool and result and "error" in str(result).lower():
            return True
        return False

    def _check_tool_failure(self, result: str) -> bool:
        """检測工具失败"""
        failure_indicators = ["error", "failed", "exception", "错誤", "失败", "异常", "❌"]
        return any(w in str(result).lower() for w in failure_indicators)

    def _check_identity_drift(self, msg: str) -> bool:
        """检測身份漂移"""
        drift_patterns = [
            "扮演什么角色",
            "你想讓我扮演",
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
        """计算成功品質分数"""
        score = 0.5

        # 有工具調用 + 成功结果
        if tool_called and tool_result:
            score += 0.2
        # 有具體行动
        action_words = ["已", "完成", "执行", "扫描", "检查", "修復"]
        if any(w in assistant_msg for w in action_words):
            score += 0.1
        # 長度适中
        if 20 < len(assistant_msg) < 2000:
            score += 0.1
        # 沒有不确定词匯
        uncertain = ["或許", "可能", "不确定", "不知道能不能", "試試看"]
        if not any(w in assistant_msg for w in uncertain):
            score += 0.1

        return min(1.0, score)

    def get_failure_stats(self) -> Dict[str, int]:
        """错誤类型统计"""
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
