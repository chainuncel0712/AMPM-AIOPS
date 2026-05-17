"""
Memory Retriever — 統一記憶檢索
================================
統合所有記憶系統，提供單一檢索入口。

記憶來源（分層，不混在一起）：
- identity_memory: 使用者偏好、語言、角色關係
- episodic_memory: 最近事件（修 VPS、部署 agent）
- goal_memory: 目前任務、長期目標
- semantic_memory: 知識/RAG
- working_memory: 最近聊天

使用 PriorityScorer 評分，只取最相關內容。
"""

from typing import Any, Dict, List, Optional

from runtime.context.priority_scorer import PriorityScorer


class MemoryRetriever:
    """統一記憶檢索器

    整合以下記憶來源：
    - memory_organ: Memory 類（工作、情節、語義記憶）
    - vector_memory: VectorMemory（ChromaDB 向量搜尋）
    - episodic_memory: EpisodicMemory（文明級事件記憶）
    - compass_organ: Compass（目標/方向）
    """

    def __init__(
        self,
        memory_organ=None,
        vector_memory=None,
        episodic_memory=None,
        compass_organ=None,
    ):
        self.memory = memory_organ
        self.vector_memory = vector_memory
        self.episodic_memory = episodic_memory
        self.compass = compass_organ
        self.scorer = PriorityScorer()

    def retrieve(
        self,
        query: str = "",
        top_n: int = 5,
        include_working: bool = True,
        include_semantic: bool = True,
        include_episodic: bool = True,
        include_goals: bool = True,
    ) -> Dict[str, Any]:
        """統一檢索 — 從所有記憶來源取最相關內容

        Returns:
            {
                "identity": {...},       # 使用者身份/偏好
                "recent_chat": [...],    # 最近對話
                "relevant_facts": [...], # 相關事實
                "recent_events": [...],  # 最近事件
                "active_goals": [...],   # 活躍目標
                "context_text": str,     # 組合後的純文字（給 prompt 用）
            }
        """
        result: Dict[str, Any] = {
            "identity": {},
            "recent_chat": [],
            "relevant_facts": [],
            "recent_events": [],
            "active_goals": [],
            "context_text": "",
        }

        # 1. 使用者身份記憶（不評分，全部取）
        result["identity"] = self._retrieve_identity()

        # 2. 最近對話（從 Memory 的工作記憶）
        if include_working and self.memory:
            result["recent_chat"] = self._retrieve_working(limit=top_n)

        # 3. 相關語義事實（評分後取 top-N）
        if include_semantic and self.memory:
            result["relevant_facts"] = self._retrieve_semantic(query, top_n)

        # 4. 向量記憶搜尋（語義相似度）
        if self.vector_memory and query:
            try:
                vec_results = self.vector_memory.recall(query, n=3)
                if vec_results:
                    result["relevant_facts"].extend(
                        [{"fact": r, "source": "vector"} for r in vec_results if r]
                    )
            except Exception:
                pass

        # 5. 最近事件（從文明級事件記憶）
        if include_episodic and self.episodic_memory:
            result["recent_events"] = self._retrieve_episodic(query, top_n)

        # 6. 活躍目標（從 Compass）
        if include_goals and self.compass:
            result["active_goals"] = self._retrieve_goals()

        # 7. 組裝純文字上下文
        result["context_text"] = self._build_context_text(result)

        return result

    def _retrieve_identity(self) -> Dict[str, Any]:
        """取使用者身份記憶"""
        identity: Dict[str, Any] = {}
        if not self.memory:
            return identity

        try:
            important = self.memory.get_important_facts(min_importance=0.6)
            identity["facts"] = important

            stats = self.memory.get_stats()
            identity["total_memories"] = stats.get("semantic_count", 0)
        except Exception:
            pass

        return identity

    def _retrieve_working(self, limit: int = 5) -> List[Dict]:
        """取最近工作記憶（對話）"""
        try:
            recent = self.memory.get_recent_conversations(limit=limit)
            return self.scorer.rank(recent, query="", top_n=limit)
        except Exception:
            return []

    def _retrieve_semantic(self, query: str, top_n: int = 5) -> List[Dict]:
        """取相關語義事實"""
        results = []
        try:
            all_facts = self.memory.get_all_facts()
            items = [
                {"fact": k, "value": v, "importance": 0.5}
                for k, v in all_facts.items()
            ]
            results = self.scorer.filter_and_rank(items, query, top_n=top_n)
        except Exception:
            pass
        return results

    def _retrieve_episodic(self, query: str, top_n: int = 5) -> List[Dict]:
        """取最近事件"""
        try:
            query_tags = query.split()[:5] if query else []
            episodes = self.episodic_memory.recall_by_tags(
                query_tags + ["conversation", "task", "system"],
                limit=20,
            )
            return self.scorer.rank(episodes, query, top_n=top_n)
        except Exception:
            return []

    def _retrieve_goals(self) -> List[Dict]:
        """取活躍目標"""
        try:
            return self.compass.get_active_goals()[:5]
        except Exception:
            return []

    def _build_context_text(self, result: Dict) -> str:
        """將檢索結果轉為精簡的純文字（給 prompt 用）

        記憶分類標記，讓 LLM 知道每段的來源類型。
        """
        parts = []

        identity = result.get("identity", {})
        facts = identity.get("facts", {})
        if facts:
            lines = [f"- {k}: {v}" for k, v in list(facts.items())[:8]]
            parts.append("[使用者身份記憶]\n" + "\n".join(lines))

        goals = result.get("active_goals", [])
        if goals:
            lines = [f"- [{g.get('priority', '?')}] {g.get('title', '?')} (進度 {int(g.get('progress', 0) * 100)}%)" for g in goals[:3]]
            parts.append("[目前任務目標]\n" + "\n".join(lines))

        events = result.get("recent_events", [])
        if events:
            lines = [
                f"- [{e.get('type', '?')}] {e.get('summary', '')[:100]}"
                for e in events[:3]
            ]
            parts.append("[最近事件]\n" + "\n".join(lines))

        facts = result.get("relevant_facts", [])
        if facts:
            lines = [
                f"- {f.get('fact', str(f))[:150]}"
                for f in facts[:5]
            ]
            parts.append("[相關記憶]\n" + "\n".join(lines))

        return "\n\n".join(parts)
