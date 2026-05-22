"""
TokenBudget — 每 agent / 每 task 的 token 預算分配器
--------------------------------------------------
核心原則：
- 簡單任務不值用大模型 → 自動降級
- 高價值任務可升級 → 自動升級
- 預算耗盡時拒絕或降級
- 支援日/週/月預算循環
"""
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BudgetPool:
    name: str
    token_limit: int
    used: int = 0
    reset_interval_hours: int = 24
    last_reset: float = field(default_factory=time.time)
    overage_count: int = 0


class TokenBudget:
    """
    多層級預算管理

    層級：
    1. 全域預算 (global) — 整個 AI 每天可用 token 上限
    2. Agent 預算 — 每個 agent 的配額
    3. Task 預算 — 單一任務最大 token 消耗
    """

    MODEL_TIERS = {
        "cheap": {
            "max_tokens_per_call": 1000,
            "providers": ["Ollama", "DeepSeek"],
            "suitable_for": ["simple_reply", "formatting", "status_check"],
        },
        "normal": {
            "max_tokens_per_call": 4000,
            "providers": ["DeepSeek", "OR-DeepSeek"],
            "suitable_for": ["code_generation", "analysis", "conversation"],
        },
        "premium": {
            "max_tokens_per_call": 8000,
            "providers": ["GPT-4.1", "Claude", "ATXP"],
            "suitable_for": ["complex_reasoning", "architecture", "security"],
        },
    }

    def __init__(self, base_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self.base_dir = base_dir

        self.pools: Dict[str, BudgetPool] = {}
        self.task_limits: Dict[str, int] = {}

        self._init_defaults()

    def _init_defaults(self):
        self.pools["global"] = BudgetPool("global", token_limit=1_000_000, reset_interval_hours=24)
        self.pools["agent_default"] = BudgetPool("agent_default", token_limit=100_000, reset_interval_hours=24)
        self.pools["research"] = BudgetPool("research", token_limit=200_000, reset_interval_hours=24)
        self.pools["trading"] = BudgetPool("trading", token_limit=50_000, reset_interval_hours=24)
        self.pools["social"] = BudgetPool("social", token_limit=30_000, reset_interval_hours=24)

        self.task_limits["simple_reply"] = 500
        self.task_limits["code_generation"] = 4000
        self.task_limits["analysis"] = 4000
        self.task_limits["complex_reasoning"] = 8000
        self.task_limits["architecture"] = 8000
        self.task_limits["default"] = 2000

    def _check_reset(self, pool: BudgetPool):
        now = time.time()
        if now - pool.last_reset > pool.reset_interval_hours * 3600:
            pool.used = 0
            pool.last_reset = now

    def _try_consume(self, pool_name: str, tokens: int) -> bool:
        pool = self.pools.get(pool_name, self.pools["agent_default"])
        with self._lock:
            self._check_reset(pool)
            if pool.used + tokens <= pool.token_limit:
                pool.used += tokens
                return True
            pool.overage_count += 1
            return False

    def allocate(self, task_type: str, estimated_tokens: int,
                 agent_id: str = "default") -> Dict[str, Any]:
        """
        為任務分配 token 預算。

        回傳：
        {
            "allowed": bool,
            "tier": "cheap"|"normal"|"premium",
            "max_tokens": int,
            "reason": str,
        }
        """
        pool_name = f"agent_{agent_id}" if f"agent_{agent_id}" in self.pools else "agent_default"

        if not self._try_consume("global", estimated_tokens):
            return {"allowed": False, "tier": "cheap", "max_tokens": 0,
                    "reason": "global_budget_exhausted"}

        if not self._try_consume(pool_name, estimated_tokens):
            return {"allowed": False, "tier": "cheap", "max_tokens": 0,
                    "reason": f"agent_budget_exhausted ({pool_name})"}

        task_limit = self.task_limits.get(task_type, self.task_limits["default"])

        if estimated_tokens <= self.MODEL_TIERS["cheap"]["max_tokens_per_call"]:
            tier = "cheap"
        elif estimated_tokens <= self.MODEL_TIERS["normal"]["max_tokens_per_call"]:
            tier = "normal"
        else:
            tier = "premium"

        return {
            "allowed": True,
            "tier": tier,
            "max_tokens": min(estimated_tokens, task_limit),
            "reason": "allocated",
        }

    def release(self, pool_name: str, tokens: int):
        """釋放未用完的 token"""
        pool = self.pools.get(pool_name, self.pools["agent_default"])
        with self._lock:
            pool.used = max(0, pool.used - tokens)

    def get_status(self, pool_name: str = "global") -> Dict[str, Any]:
        pool = self.pools.get(pool_name, self.pools["global"])
        with self._lock:
            self._check_reset(pool)
            remaining = max(0, pool.token_limit - pool.used)
            pct = pool.used / pool.token_limit * 100 if pool.token_limit > 0 else 0
            return {
                "pool": pool.name,
                "limit": pool.token_limit,
                "used": pool.used,
                "remaining": remaining,
                "usage_pct": round(pct, 1),
                "overage_count": pool.overage_count,
            }

    def all_pools_status(self) -> List[Dict[str, Any]]:
        return [self.get_status(name) for name in self.pools]

    def status(self) -> dict:
        s = self.get_status("global")
        return {
            "name": "TokenBudget",
            "global_usage_pct": s["usage_pct"],
            "pool_count": len(self.pools),
            "pools": {k: self.get_status(k) for k in self.pools},
        }
