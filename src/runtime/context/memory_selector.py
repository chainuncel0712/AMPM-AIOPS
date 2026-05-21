"""
Memory Selector — 记忆進入 Context 的唯一入口
===============================================
這是系统最關键的一層。

架構原則：
  Memory ≠ Input
  Memory → Context → Input

Memory 不是直接给 LLM 的。
Memory 是给 Context「用來挑選的」。

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
    """记忆選择器 — 從原始记忆到精炼上下文的完整管线

    整合四個步骤：
    1. Retrieve  — 從多源记忆系统捞候選
    2. Score     — relevance + recency + importance
    3. Filter    — 取 top-N
    4. Compress  — 壓缩為摘要，避免爆 token
    """

    def __init__(
        self,
        memory_organ=None,
        vector_memory=None,
        episodic_memory=None,
        llm_call: Optional[Callable] = None,
        max_candidates: int = 200,
        max_output: int = 50,
    ):
        self.memory = memory_organ
        self.vector_memory = vector_memory
        self.episodic_memory = episodic_memory
        self.scorer = PriorityScorer()  # 權重讀取 config，可由 RuntimeUpdate 覆寫
        self.summarizer = Summarizer(llm_call=llm_call)
        self.max_candidates = max_candidates
        self.max_output = max_output

    def sync_weights(self, weights: dict):
        """同步權重 — 讓 RuntimeUpdate 的演化结果生效"""
        if not weights:
            return
        if "relevance" in weights:
            self.scorer.relevance_weight = weights["relevance"]
        if "recency" in weights:
            self.scorer.recency_weight = weights["recency"]
        if "importance" in weights:
            self.scorer.importance_weight = weights["importance"]

    def select(self, query: str, top_n: int = None) -> str:
        """核心方法：记忆 → 選择 → 壓缩 → 輸出摘要"""
        if top_n is None:
            top_n = self.max_output

        candidates = self._retrieve_all(query)
        total = len(candidates)
        scored = self._score_and_filter(candidates, query, top_n)
        summary = self._compress(scored, query)

        if self.scorer.transparency_log and total > 0:
            sources = {}
            for item in scored:
                src = item.get("_source", "?")
                sources[src] = sources.get(src, 0) + 1
            print(f"🔍 [MemorySelector] {total} candidates → {len(scored)} selected → sources={sources}")

        return summary

    def _retrieve_all(self, query: str) -> List[Dict]:
        """第一步：從所有记忆來源捞候選

        來源：
        - Memory 工作记忆 (working)
        - Memory 語義记忆 (semantic)
        - VectorMemory 向量搜尋
        - EpisodicMemory 事件记忆
        """
        candidates: List[Dict] = []
        query_lower = query.lower() if query else ""

        if self.memory:
            try:
                working = self.memory.get_recent_conversations(limit=50)
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
                # 高重要性事件直接撈，不靠 tag
                episodes = self.episodic_memory.recall_by_tags(
                    ["任務", "important", "user"], limit=20
                )
                # 也試 query 關鍵字
                query_tags = (query or "").split()[:5] + ["任務", "重要"]
                extra = self.episodic_memory.recall_by_tags(query_tags, limit=10)
                seen = {id(e): True for e in episodes}
                for e in extra:
                    if id(e) not in seen:
                        episodes.append(e)
                        seen[id(e)] = True
                for e in episodes[-15:]:
                    e["_source"] = "episodic"
                    candidates.append(e)
            except Exception:
                pass

        return candidates[: self.max_candidates]

    def _score_and_filter(
        self, candidates: List[Dict], query: str, top_n: int
    ) -> List[Dict]:
        scored = []
        must_include = []
        for item in candidates:
            s = self.scorer.score(item, query)
            # 重要性 >= 0.7 必過，不靠評分
            if item.get("importance", 0) >= 0.7:
                must_include.append(item)
            elif s >= 0.1:
                scored.append((s, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        result = [item for _, item in scored[:top_n - len(must_include)]]
        return must_include + result

    def _compress(self, items: List[Dict], query: str = "") -> str:
        """第四步：将精選记忆壓缩為一段精炼摘要

        輸出格式：
          [working] 最近對話摘要
          [semantic] 使用者叫 Hao，喜歡自然語气
          [episodic] 昨天修了 VPS CPU 問题
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
            "working": "最近對話",
            "semantic": "已知事实",
            "vector": "相關知識",
            "episodic": "最近事件",
        }

        for src, texts in by_source.items():
            label = labels.get(src, src)
            combined = "；".join(texts[:15])
            parts.append(f"[{label}] {combined}")

        result = "\n".join(parts)

        if len(result) > 600:
            result = self.summarizer.summarize(result, query)

        return result

    def _item_to_text(self, item: Dict) -> str:
        """将單条记忆轉换為文字"""
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
