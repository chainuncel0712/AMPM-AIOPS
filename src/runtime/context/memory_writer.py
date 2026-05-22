"""
Memory Writer — 記憶寫入層
===========================
每次對話結束後，將對話內容分類寫入記憶。
不再像以前全部 dump 進 working memory。

分類邏輯：
- identity_memory: 使用者名稱、偏好、習慣、作息
- semantic_memory: 知識性事實
- episodic_memory: 事件（做了什麼）
- working_memory: 原始對話（短期緩衝）
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class MemoryWriter:
    """記憶寫入器 — 分析對話後分類寫入記憶"""

    # 身份相關關鍵字
    IDENTITY_KEYWORDS = [
        "我叫", "我是", "我喜歡", "我討厭", "我習慣", "我通常",
        "我每天", "我每週", "我住在", "我的工作是", "我用",
        "改名", "稱呼", "叫我", "名字", "偏好", "作息",
    ]

    # 事件相關關鍵字
    EPISODIC_KEYWORDS = [
        "修", "部署", "安裝", "設定", "重啟", "檢查", "掃描",
        "完成", "執行", "建立", "寫了", "改了", "修正",
    ]

    # 任務/規劃相關關鍵字（高分）
    TASK_KEYWORDS = [
        "任務", "規劃", "專案", "計畫", "目標", "公司",
        "組織", "架構", "架設", "網站", "工具書", "電子書",
        "生成", "自動化", "代理", "AI", "銷售", "客服",
        "審核", "上架", "追蹤", "創作", "選題", "童書",
        "一條龍", "客製化", "安裝服務", "網域",
    ]

    def __init__(
        self,
        memory_organ=None,
        episodic_memory=None,
        vector_memory=None,
    ):
        self.memory = memory_organ
        self.episodic = episodic_memory
        self.vector_memory = vector_memory

    def write(self, user_msg: str, assistant_msg: str):
        """分析對話並分類寫入記憶

        一輪對話可能同時寫入多個記憶層：
        - 一定寫 working（短期緩衝）
        - 如有身份資訊 → 寫 semantic（identity）
        - 如有事件 → 寫 episodic
        - 如有重要事實 → 寫 semantic
        """
        if not user_msg and not assistant_msg:
            return

        # 1. working memory — 永遠寫（短期緩衝）
        importance = self._score_importance(user_msg, assistant_msg)
        if self.memory:
            try:
                self.memory.remember_conversation(
                    user_msg=user_msg,
                    assistant_msg=assistant_msg,
                    importance=importance,
                )
            except Exception:
                pass

        # 2. identity memory — 檢查是否含身份資訊
        self._write_identity(user_msg, importance)

        # 3. semantic memory — 檢查是否含重要事實
        self._write_semantic(user_msg, assistant_msg, importance)

        # 4. episodic memory — 檢查是否含事件
        self._write_episodic(user_msg, assistant_msg, importance)

        # 5. vector memory — 寫入向量搜尋
        self._write_vector(user_msg, assistant_msg)

    def _score_importance(self, user_msg: str, assistant_msg: str) -> float:
        """評分本輪對話的重要性 (0~1)"""
        score = 0.3

        combined = (user_msg + " " + assistant_msg).lower()

        # 身份資訊
        if any(kw in user_msg for kw in self.IDENTITY_KEYWORDS):
            score = max(score, 0.85)

        # 任務/規劃 → 最高優先
        if any(kw in combined for kw in self.TASK_KEYWORDS):
            score = max(score, 0.9)

        # 事件/行動
        if any(kw in combined for kw in self.EPISODIC_KEYWORDS):
            score = max(score, 0.7)

        # 一般對話（長訊息）
        if len(user_msg) > 30:
            score = max(score, 0.5)

        return min(1.0, score)

    def _write_identity(self, user_msg: str, importance: float):
        """萃取並寫入身份記憶"""
        if not self.memory:
            return

        identity_lines = []
        for line in user_msg.replace("。", "\n").replace("，", "\n").split("\n"):
            line = line.strip()
            if not line:
                continue
            if any(kw in line for kw in self.IDENTITY_KEYWORDS):
                identity_lines.append(line[:200])

        for line in identity_lines[:2]:
            try:
                self.memory.remember_fact(
                    fact=f"使用者資訊: {line}",
                    importance=max(0.7, importance),
                    value=line,
                )
            except Exception:
                pass

    def _write_semantic(self, user_msg: str, assistant_msg: str, importance: float):
        """萃取並寫入語義記憶（知識性事實）"""
        if not self.memory or importance < 0.5:
            return

        # 高重要性（任務/身份）→ 無條件寫入，不限 assistant 關鍵字
        if importance >= 0.7:
            try:
                self.memory.remember_fact(
                    fact=f"對話: {user_msg[:120]}",
                    importance=importance,
                    value=assistant_msg[:300],
                )
            except Exception:
                pass
            return

        # 中重要性 → 需要 assistant 回覆含關鍵資訊
        if len(assistant_msg) > 30 and any(
            kw in assistant_msg for kw in ["是", "有", "可以", "需要", "建議", "規劃", "建立", "完成"]
        ):
            try:
                self.memory.remember_fact(
                    fact=f"對話: {user_msg[:80]}",
                    importance=importance * 0.7,
                    value=assistant_msg[:200],
                )
            except Exception:
                pass

    def _write_episodic(self, user_msg: str, assistant_msg: str, importance: float):
        """萃取並寫入事件記憶"""
        if not self.episodic or importance < 0.6:
            return

        event_type = "conversation"
        tags = []

        combined = user_msg + " " + assistant_msg
        if any(kw in combined for kw in ["修", "部署", "重啟"]):
            event_type = "task"
            tags = ["maintenance"]
        elif any(kw in combined for kw in ["建立", "寫了", "改了"]):
            event_type = "creation"
            tags = ["development"]
        elif any(kw in combined for kw in ["檢查", "掃描", "查看"]):
            event_type = "inspection"
            tags = ["monitoring"]

        try:
            self.episodic.record(
                event_type=event_type,
                summary=f"使用者: {user_msg[:100]} → 黑曜: {assistant_msg[:100]}",
                importance=importance,
                tags=tags,
                context={"user_msg": user_msg[:200], "reply": assistant_msg[:200]},
            )
        except Exception:
            pass

    def _write_vector(self, user_msg: str, assistant_msg: str):
        """寫入向量記憶（語義搜尋用）"""
        if not self.vector_memory:
            return

        text = f"使用者: {user_msg[:200]} | 黑曜: {assistant_msg[:200]}"
        try:
            self.vector_memory.remember(
                text=text,
                metadata={
                    "user_msg": user_msg[:100],
                    "time": datetime.now().isoformat(),
                },
            )
        except Exception:
            pass
