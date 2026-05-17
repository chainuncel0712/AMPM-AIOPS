"""
Memory Selector — 记忆进入 Context 的唯一入口
===============================================
这是系统最关键的一层。

架构原则：
  Memory ≠ Input
  Memory → Context → Input

Memory 不是直接给 LLM 的。
Memory 是给 Context「用来挑选的」。

正确管线：
  Memory (raw data)
    ↓ Retrieve
  candidates = memory.search(user_input)
    ↓ Score
  score = relevance*0.5 + recency*0.3 + importance*0.2
    ↓ Filter
  top_memories = sort_by_score(candidates)[:N]
    ↓ Compress
  summary = summarize(top_memories)
    ↓ Output
  return summary  → 喂给 ContextAssembler → LLM
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from runtime.context.priority_scorer import PriorityScorer
from runtime.context.summarizer import Summarizer


class MemorySelector:
    """记忆选择器 — 从原始记忆到精炼上下文的完整管线

    整合四个步骤：
    1. Retrieve  — 从多源记忆系统捞候选
    2. Score     — relevance + recency + importance
    3. Filter    — 取 top-N
    4. Compress  — 压缩为摘要，避免爆 token
    """

    def __init__(
        self,
        memory_organ=None,
        vector_memory=None,
        episodic_memory=None,
        llm_call: Optional[Callable] = None,
        max_candidates: int = 30,
        max_output: int = 5,
    ):
        self.memory = memory_organ
        self.vector_memory = vector_memory
        self.episodic_memory = episodic_memory
        self.scorer = PriorityScorer(
            relevance_weight=0.5,
            recency_weight=0.3,
            importance_weight=0.2,
        )
        self.summarizer = Summarizer(llm_call=llm_call)
        self.max_candidates = max_candidates
        self.max_output = max_output

    def sync_weights(self, weights: dict):
        """同步权重 — 让 RuntimeUpdate 的演化结果生效"""
        if not weights:
            return
        if "relevance" in weights:
            self.scorer.relevance_weight = weights["relevance"]
        if "recency" in weights:
            self.scorer.recency_weight = weights["recency"]
        if "importance" in weights:
            self.scorer.importance_weight = weights["importance"]

    def select(self, query: str, top_n: int = None) -> str:
        """核心方法：记忆 → 选择 → 压缩 → 输出摘要

        Args:
            query: 使用者当前输入，用于检索相关记忆
            top_n: 最终取几条记忆，默认用 max_output

        Returns:
            精选压缩后的记忆摘要字串，可直接注入 prompt
        """
        if top_n is None:
            top_n = self.max_output

        candidates = self._retrieve_all(query)
        scored = self._score_and_filter(candidates, query, top_n)
        summary = self._compress(scored, query)

        return summary

    def _retrieve_all(self, query: str) -> List[Dict]:
        """第一步：从所有记忆来源捞候选

        来源：
        - Memory 工作记忆 (working)
        - Memory 语义记忆 (semantic)
        - VectorMemory 向量搜尋
        - EpisodicMemory 事件记忆
        """
        candidates: List[Dict] = []
        query_lower = query.lower() if query else ""

        if self.memory:
            try:
                working = self.memory.get_recent_conversations(limit=10)
                for w in working:
                    w["_source"] = "working"
                    candidates.append(w)

                for fact in self.memory.semantic:
                    if query_lower and query_lower not in fact.get("fact", "").lower():
                        if fact.get("importance", 0.5) < 0.5:
                            continue
                    fact["_source"] = "semantic"
                    candidates.append(fact)
            except Exception:
                pass

        if self.vector_memory and query:
            try:
                vec_results = self.vector_memory.recall(query, n=5)
                for r in vec_results:
                    if r:
                        candidates.append({
                            "fact": r,
                            "importance": 0.6,
                            "_source": "vector",
                            "created_at": datetime.now().isoformat(),
                        })
            except Exception:
                pass

        if self.episodic_memory:
            try:
                query_tags = query.split()[:3] if query else []
                episodes = self.episodic_memory.recall_by_tags(
                    query_tags + ["conversation", "task"], limit=10
                )
                for e in episodes:
                    e["_source"] = "episodic"
                    candidates.append(e)
            except Exception:
                pass

        return candidates[: self.max_candidates]

    def _score_and_filter(
        self, candidates: List[Dict], query: str, top_n: int
    ) -> List[Dict]:
        """第二步+第三步：评分 + 滤出 top-N"""
        scored = []
        for item in candidates:
            s = self.scorer.score(item, query)
            if s >= 0.1:
                scored.append((s, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_n]]

    def _compress(self, items: List[Dict], query: str = "") -> str:
        """第四步：将精选记忆压缩为一段精炼摘要

        输出格式：
          [working] 最近对话摘要
          [semantic] 使用者叫 Hao，喜欢自然语气
          [episodic] 昨天修了 VPS CPU 问题
        """
        if not items:
            return ""

        by_source: Dict[str, List[str]] = {}
        for item in items:
            src = item.get("_source", "unknown")
            text = self._item_to_text(item)
            if text:
                by_source.setdefault(src, []).append(text)

        parts = []
        labels = {
            "working": "最近对话",
            "semantic": "已知事实",
            "vector": "相关知识",
            "episodic": "最近事件",
        }

        for src, texts in by_source.items():
            label = labels.get(src, src)
            combined = "；".join(texts[:3])
            parts.append(f"[{label}] {combined}")

        result = "\n".join(parts)

        if len(result) > 600:
            result = self.summarizer.summarize(result, query)

        return result

    def _item_to_text(self, item: Dict) -> str:
        """将单条记忆转换为文字"""
        user = item.get("user", "")
        assistant = item.get("assistant", "")
        if user:
            return f"使用者: {user[:80]}"
        if assistant:
            return f"回覆: {assistant[:80]}"

        fact = item.get("fact", "")
        value = item.get("value", "")
        if fact:
            text = fact[:120]
            if value and value != fact:
                text += f": {value[:60]}"
            return text

        summary = item.get("summary", "")
        if summary:
            return summary[:120]

        return str(item)[:120]

    def status(self) -> dict:
        return {
            "has_memory": self.memory is not None,
            "has_vector": self.vector_memory is not None,
            "has_episodic": self.episodic_memory is not None,
            "max_candidates": self.max_candidates,
            "max_output": self.max_output,
        }
