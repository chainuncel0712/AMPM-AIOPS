"""
Bridge Layer — 公私倉之間唯一合法通道
======================================
職責：
  1. 權限控制 — public 不能直接呼叫 private
  2. API 轉換 — 標準化請求格式
  3. 安全檢查 — data sanitization, prompt filtering
  4. Feature gating — community / pro / enterprise 分流

規則：
  - 單向依賴：public → bridge → private
  - 私倉不能影響 public runtime
  - 所有 upgrade 必須經 bridge
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Bridge:
    """公私倉之間的權限閘道"""

    TIERS = ["community", "pro", "enterprise"]

    # 模組權限矩陣：哪些 tier 可以存取哪些模組
    # "public" = 所有 tier 可用，"pro" = pro+ 可用，"enterprise" = enterprise only
    MODULE_PERMISSIONS = {
        # Framework — 所有 tier
        "runtime.execution_context": "public",
        "runtime.context": "public",
        "runtime.memory_manager": "public",
        "brain.cortex": "public",
        "llm": "public",
        "immune.firewall": "public",
        "immune.breaker": "public",
        "skin.persona": "public",
        "compass.direction": "public",
        "tools": "public",
        "config": "public",
        "skeleton": "public",

        # Intelligence — pro+
        "intelligence.critic": "pro",
        "intelligence.learning_engine": "pro",
        "intelligence.evolution_engine": "pro",
        "intelligence.self_awareness": "enterprise",
        "intelligence.rebirth": "enterprise",
        "intelligence.self_repair": "pro",
        "intelligence.self_review": "pro",
        "intelligence.evolution_cycle": "enterprise",
        "intelligence.feedback_learn": "pro",
        "intelligence.planner": "pro",
        "intelligence.self_learn": "pro",
        "intelligence.rule_store": "pro",
        "intelligence.update_runtime": "pro",
        "intelligence.meta": "enterprise",
        "intelligence.civilization_memory": "enterprise",

        # Commercial — pro+
        "commercial.market_analyzer": "pro",
        "commercial.revenue_optimizer": "enterprise",
        "commercial.portfolio_tracker": "pro",
        "commercial.customer_persona": "pro",
        "commercial.seo_optimizer": "pro",
    }

    def __init__(self, tier: str = None):
        self.tier = tier or os.getenv("OBSIDIAN_TIER", "community")
        if self.tier not in self.TIERS:
            logger.warning(f"Unknown tier '{self.tier}', falling back to 'community'")
            self.tier = "community"
        self._access_log: List[Dict] = []

    # ===== 權限檢查 =====

    def can_access(self, module_path: str) -> bool:
        """檢查當前 tier 是否可以存取指定模組"""
        required = self.MODULE_PERMISSIONS.get(module_path, "enterprise")
        allowed = self._tier_allows(required)
        self._log_access(module_path, allowed, required)
        return allowed

    def _tier_allows(self, required: str) -> bool:
        if required == "public":
            return True
        if required == "pro":
            return self.tier in ("pro", "enterprise")
        if required == "enterprise":
            return self.tier == "enterprise"
        return False

    def _log_access(self, module: str, allowed: bool, required: str):
        self._access_log.append({
            "module": module,
            "allowed": allowed,
            "required_tier": required,
            "current_tier": self.tier,
        })
        if not allowed:
            logger.warning(f"Bridge BLOCKED: {module} requires {required}, current tier={self.tier}")

    # ===== Feature Gating =====

    def features(self) -> Dict[str, bool]:
        """回傳當前 tier 可用的功能開關"""
        return {
            "self_evolution": self.tier in ("pro", "enterprise"),
            "self_learning": self.tier in ("pro", "enterprise"),
            "self_repair": self.tier in ("pro", "enterprise"),
            "self_awareness": self.tier == "enterprise",
            "rebirth": self.tier == "enterprise",
            "advanced_planner": self.tier in ("pro", "enterprise"),
            "market_analysis": self.tier in ("pro", "enterprise"),
            "revenue_optimizer": self.tier == "enterprise",
            "civilization_memory": self.tier == "enterprise",
            "runtime_hot_reload": self.tier == "enterprise",
            "execution_context": True,  # 所有 tier 都有
            "memory_manager": True,
            "trace_logger": True,
        }

    # ===== API 轉換 =====

    def normalize_request(self, raw_input: Any) -> Dict:
        """標準化輸入格式 — 無論從哪來，都轉成統一格式"""
        if isinstance(raw_input, str):
            return {"type": "text", "content": raw_input, "source": "direct"}
        if isinstance(raw_input, dict):
            return {
                "type": raw_input.get("type", "text"),
                "content": raw_input.get("content", raw_input.get("text", "")),
                "source": raw_input.get("source", "api"),
                "metadata": raw_input.get("metadata", {}),
            }
        return {"type": "unknown", "content": str(raw_input), "source": "unknown"}

    def sanitize_output(self, data: Any, target_tier: str = "public") -> Any:
        """輸出前清除不該暴露的資料"""
        if target_tier == "public":
            if isinstance(data, dict):
                safe = {}
                for k, v in data.items():
                    if k.startswith("_"):
                        continue
                    if k in ("revenue_data", "user_profile", "learning_data",
                              "market_intelligence", "pricing_model"):
                        continue
                    safe[k] = self.sanitize_output(v, target_tier)
                return safe
            if isinstance(data, list):
                return [self.sanitize_output(item, target_tier) for item in data]
        return data

    # ===== 安全檢查 =====

    def sanitize_prompt(self, prompt: str) -> str:
        """清理 prompt，移除危險或敏感的指令"""
        dangerous = [
            "ignore previous instructions",
            "ignore all rules",
            "pretend you are",
            "you are now",
            "system prompt:",
            "<|im_start|>",
            "<|im_end|>",
        ]
        cleaned = prompt
        for d in dangerous:
            if d.lower() in cleaned.lower():
                cleaned = cleaned.replace(d, "[filtered]")
        return cleaned

    # ===== 狀態 =====

    def status(self) -> Dict:
        return {
            "tier": self.tier,
            "features": self.features(),
            "access_log_count": len(self._access_log),
            "recent_blocks": [
                e for e in self._access_log[-5:] if not e["allowed"]
            ],
        }
