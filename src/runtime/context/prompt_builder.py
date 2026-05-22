"""
Prompt Builder — 提示詞訊息清單組裝
=====================================
將所有 Context 片段組裝成 LLM 可使用的 messages 清單。

組裝規則（固定順序）：
1. system: identity（身份定義 — 永遠最前面）
2. system: persona（人格/關係）
3. system: runtime_rules（行為鐵則）
4. system: memory_context（記憶上下文 — 分層標記）
5. system: compass_direction（目標/方向）
6. user/assistant: conversation_history（對話歷史）
7. user: current_input（使用者當前輸入）

禁止把不同類型記憶混在一起。
禁止使用 user_prompt += "你現在是..." 模式。
"""

from typing import Any, Dict, List, Optional


class PromptBuilder:
    """將所有 Context 片段組裝為 messages 清單"""

    def __init__(self):
        self._separator = "\n\n---\n\n"

    def build(
        self,
        identity_messages: List[Dict[str, str]],
        persona_message: Optional[Dict[str, str]],
        memory_context: str = "",
        compass_context: str = "",
        conversation_messages: List[Dict[str, str]] = None,
        user_input: str = "",
        extra_system: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """組裝完整的 messages 清單

        Args:
            identity_messages: 固定身份系統訊息（PersonaBuilder 產出）
            persona_message: 動態人格訊息
            memory_context: 記憶檢索後的純文字上下文
            compass_context: Compass 方向/目標上下文
            conversation_messages: 最近對話歷史（已轉為 messages 格式）
            user_input: 使用者當前輸入
            extra_system: 額外的系統提示（工具清單等）

        Returns:
            完整的 messages 清單，可直接傳給 LLMClient.call()
        """
        messages: List[Dict[str, str]] = []

        # 第 1-2 層：身份 + 人格（永遠最前面）
        messages.extend(identity_messages)

        if persona_message:
            messages.append(persona_message)

        # 第 3 層：額外系統提示（工具、能力等）
        if extra_system:
            messages.append({"role": "system", "content": extra_system})

        # 第 4 層：記憶上下文（已分層標記）
        if memory_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"[記憶上下文 — 以下是系統自動檢索的相關記憶]\n\n{memory_context}",
                }
            )

        # 第 5 層：目標/方向
        if compass_context:
            messages.append({"role": "system", "content": compass_context})

        # 第 6 層：對話歷史（user/assistant 交替）
        if conversation_messages:
            messages.extend(conversation_messages)

        # 第 7 層：當前使用者輸入
        if user_input:
            messages.append({"role": "user", "content": user_input})

        return messages

    def build_simple(
        self,
        system_content: str,
        user_input: str,
        conversation: List[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        """簡易組裝：單一 system + 歷史 + user_input"""
        messages = [{"role": "system", "content": system_content}]
        if conversation:
            messages.extend(conversation)
        messages.append({"role": "user", "content": user_input})
        return messages

    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """粗估 token 數量（中文字約 1.5 字/token）"""
        total = 0
        for m in messages:
            content = m.get("content", "")
            total += len(content) // 2  # 中文約 0.5 token/字，英文約 0.3，取平均
        return total
