"""
Conversation Window — 滑動對話視窗
====================================
管理最近 N 輪對話，確保 LLM 能看到連續的上下文。
超出視窗的舊對話可壓縮為摘要而非直接丟棄。

不把所有 200 則聊天全部塞進 prompt。
只保留最近 max_turns 輪 + 摘要。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class ConversationWindow:
    """滑動對話視窗 — 管理最近對話歷史"""

    def __init__(self, max_turns: int = 10, max_summary_turns: int = 30):
        self.max_turns = max_turns
        self.max_summary_turns = max_summary_turns
        self.turns: List[Dict[str, Any]] = []
        self.summary: str = ""

    def add_turn(self, user_msg: str, assistant_msg: str, metadata: Dict = None):
        """新增一輪對話"""
        turn = {
            "user": user_msg[:1000],
            "assistant": assistant_msg[:2000] if assistant_msg else "",
            "time": datetime.now().isoformat(),
            "meta": metadata or {},
        }
        self.turns.append(turn)
        self._trim()

    def _trim(self):
        """超出上限時壓縮舊對話"""
        if len(self.turns) <= self.max_summary_turns:
            return

        overflow = self.turns[: len(self.turns) - self.max_summary_turns]
        self.turns = self.turns[-self.max_summary_turns:]

        if overflow:
            topics = set()
            for t in overflow:
                msg = t["user"][:30]
                if msg:
                    topics.add(msg)
            old_summary = self.summary
            if old_summary:
                self.summary = f"{old_summary}\n[更早] 討論過: {'; '.join(list(topics)[:5])}"
            else:
                self.summary = f"[歷史對話摘要] 討論過: {'; '.join(list(topics)[:5])}"

    def get_recent(self, n: int = None) -> List[Dict[str, Any]]:
        """取得最近 n 輪對話"""
        if n is None:
            n = self.max_turns
        return self.turns[-n:]

    def get_summary(self) -> str:
        """取得歷史摘要（壓縮過的舊對話）"""
        return self.summary

    def get_recent_text(self, n: int = None, max_chars: int = 2000) -> str:
        """取得最近對話的文字表示"""
        recent = self.get_recent(n)
        lines = []
        total = 0
        for t in reversed(recent):
            line = f"使用者: {t['user'][:200]}\n黑曜: {t['assistant'][:200]}"
            if total + len(line) > max_chars:
                break
            lines.insert(0, line)
            total += len(line)
        return "\n---\n".join(lines)

    def build_messages(self, n: int = None) -> List[Dict[str, str]]:
        """轉換為 messages 格式（給 LLM）"""
        recent = self.get_recent(n)
        messages = []
        for t in recent:
            if t["user"]:
                messages.append({"role": "user", "content": t["user"][:1500]})
            if t["assistant"]:
                messages.append({"role": "assistant", "content": t["assistant"][:1500]})
        return messages

    def clear(self):
        """清空對話視窗（開始新話題時用）"""
        self.turns = []
        self.summary = ""

    def status(self) -> dict:
        return {
            "turns": len(self.turns),
            "max_turns": self.max_turns,
            "has_summary": bool(self.summary),
        }
