"""
Priority Scorer — 記憶相關性評分
==================================
對記憶條目進行評分，只取最相關的內容進 prompt。

公式：
  score = relevance_weight * relevance
        + recency_weight * recency
        + importance_weight * importance

不把所有記憶塞進 prompt，只取 top-N。
"""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    from config import config
    _DEFAULT_RELEVANCE = config.memory_relevance_weight
    _DEFAULT_RECENCY = config.memory_recency_weight
    _DEFAULT_IMPORTANCE = config.memory_importance_weight
    _DEFAULT_HALFLIFE = config.memory_recency_halflife_hours
    _TRANSPARENCY_LOG = config.memory_transparency_log
except ImportError:
    _DEFAULT_RELEVANCE = 0.5
    _DEFAULT_RECENCY = 0.3
    _DEFAULT_IMPORTANCE = 0.2
    _DEFAULT_HALFLIFE = 72.0
    _TRANSPARENCY_LOG = False


class PriorityScorer:
    """記憶優先級評分器

    計算每個記憶條目的綜合分數：
    - relevance: 與當前查詢的關鍵字匹配度 (0~1)
    - recency: 時間衰減後的新近性 (0~1)
    - importance: 記憶自身的重要性分數 (0~1)
    """

    def __init__(
        self,
        relevance_weight: float = None,
        recency_weight: float = None,
        importance_weight: float = None,
        recency_halflife_hours: float = None,
    ):
        self.relevance_weight = relevance_weight if relevance_weight is not None else _DEFAULT_RELEVANCE
        self.recency_weight = recency_weight if recency_weight is not None else _DEFAULT_RECENCY
        self.importance_weight = importance_weight if importance_weight is not None else _DEFAULT_IMPORTANCE
        self.recency_halflife_hours = recency_halflife_hours if recency_halflife_hours is not None else _DEFAULT_HALFLIFE
        self.transparency_log = _TRANSPARENCY_LOG

        if self.transparency_log:
            print(f"🔍 [Transparency] PriorityScorer 權重: "
                  f"relevance={self.relevance_weight}, "
                  f"recency={self.recency_weight}, "
                  f"importance={self.importance_weight}, "
                  f"halflife={self.recency_halflife_hours}h")

    def score_relevance(self, item: Dict, query: str) -> float:
        """計算關鍵字相關性分數 (0~1)"""
        if not query:
            return 0.0

        query_lower = query.lower()
        text_fields = []

        for key in ("fact", "user", "assistant", "summary", "content", "value"):
            val = item.get(key, "")
            if isinstance(val, str):
                text_fields.append(val)

        combined = " ".join(text_fields).lower()

        if not combined:
            return 0.0

        query_terms = query_lower.split()
        matches = sum(1 for term in query_terms if term in combined)
        return min(1.0, matches / max(1, len(query_terms)))

    def score_recency(self, item: Dict) -> float:
        """計算時間衰減後的新近性分數 (0~1)

        使用半衰期公式：score = 0.5 ^ (age_hours / halflife_hours)
        """
        for key in ("time", "timestamp", "created_at", "last_recalled"):
            ts = item.get(key)
            if ts:
                try:
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts)
                    elif isinstance(ts, datetime):
                        dt = ts
                    else:
                        continue
                    age_hours = (datetime.now() - dt).total_seconds() / 3600
                    age_hours = max(0, age_hours)
                    return math.pow(0.5, age_hours / self.recency_halflife_hours)
                except (ValueError, TypeError):
                    pass
        return 0.1

    def score_importance(self, item: Dict) -> float:
        """提取內建重要性分數 (0~1)"""
        imp = item.get("importance", 0.5)
        try:
            imp = float(imp)
        except (ValueError, TypeError):
            imp = 0.5
        return min(1.0, max(0.0, imp))

    def score(self, item: Dict, query: str = "") -> float:
        """計算綜合分數"""
        r = self.score_relevance(item, query)
        c = self.score_recency(item)
        i = self.score_importance(item)
        return (
            self.relevance_weight * r
            + self.recency_weight * c
            + self.importance_weight * i
        )

    def rank(self, items: List[Dict], query: str = "", top_n: int = 5) -> List[Dict]:
        """對記憶列表評分排序，取 top-N"""
        scored = [(self.score(item, query), item) for item in items]
        scored.sort(key=lambda x: x[0], reverse=True)

        if self.transparency_log and scored:
            top_scores = [f"{s:.2f}" for s, _ in scored[:top_n]]
            print(f"🔍 [Rank] 從 {len(items)} 取 top-{top_n}: scores={top_scores}")

        return [item for _, item in scored[:top_n]]

    def filter_and_rank(
        self, items: List[Dict], query: str = "", top_n: int = 5, min_score: float = 0.1
    ) -> List[Dict]:
        """評分 + 過濾閾值 + 取 top-N"""
        scored = [(self.score(item, query), item) for item in items]
        before = len(scored)
        scored = [(s, item) for s, item in scored if s >= min_score]
        scored.sort(key=lambda x: x[0], reverse=True)

        if self.transparency_log:
            filtered = before - len(scored)
            top_scores = [f"{s:.2f}" for s, _ in scored[:top_n]]
            print(f"🔍 [Filter] {before}→{len(scored)} (濾掉{filtered}), threshold={min_score}, top-{top_n}: {top_scores}")

        return [item for _, item in scored[:top_n]]
