"""
Context Assembler — 统筹组裝器
===============================
这是 Context Layer 的核心入口。
每次 LLM 呼叫前，都必须通过此组裝器建立完整的 messages 清单。

正确流程：
  User Message
  → Conversation Window (记录本轮)
  → Memory Selector (Retrieve → Score → Filter → Compress)
  → Persona Injection (固定身份注入)
  → Prompt Assembly (组裝 messages)
  → LLM

Memory ≠ Input
Memory → Context → Input

使用方式：
  assembler = ContextAssembler(persona=persona, memory=memory, ...)
  messages = assembler.assemble(user_msg="帮我检查 VPS")
  reply = llm.call(messages)
  assembler.record_response(reply)
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from runtime.context.persona_builder import PersonaBuilder
from runtime.context.conversation_window import ConversationWindow
from runtime.context.memory_selector import MemorySelector
from runtime.context.memory_writer import MemoryWriter
from runtime.context.prompt_builder import PromptBuilder


class ContextAssembler:
    """Context Layer 核心统籌器"""

    def __init__(
        self,
        persona_organ=None,
        memory_organ=None,
        vector_memory=None,
        episodic_memory=None,
        compass_organ=None,
        llm_call: Optional[Callable] = None,
        runtime_update=None,
        max_conversation_turns: int = 10,
        max_summary_turns: int = 30,
    ):
        self.persona_builder = PersonaBuilder(persona_organ)
        self.conversation_window = ConversationWindow(
            max_turns=max_conversation_turns,
            max_summary_turns=max_summary_turns,
        )
        self.memory_selector = MemorySelector(
            memory_organ=memory_organ,
            vector_memory=vector_memory,
            episodic_memory=episodic_memory,
            llm_call=llm_call,
            max_candidates=200,
            max_output=50,
        )
        self.prompt_builder = PromptBuilder()
        self.compass = compass_organ
        self.llm_call = llm_call
        self.runtime_update = runtime_update
        self.memory_writer = MemoryWriter(
            memory_organ=memory_organ,
            episodic_memory=episodic_memory,
            vector_memory=vector_memory,
        )

    def assemble(
        self,
        user_msg: str,
        include_memory: bool = True,
        include_goals: bool = True,
        extra_system: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """组裝完整 messages 清单（核心方法）

        每次叫用都：
        1. 注入固定身份 + 人格
        2. 呼叫 Memory Selector：Retrieve → Score → Filter → Compress
        3. 撷取对话历史
        4. 撷取目标方向
        5. 组裝为 messages

        Args:
            user_msg: 使用者当前输入
            include_memory: 是否检索记忆
            include_goals: 是否包含目标
            extra_system: 额外系统提示（如工具清单）

        Returns:
            完整 messages 清单，直接传给 LLMClient.call()
        """
        # 1. 统一身份 + 人格（单一系统消息，避免人格分裂）
        identity = self.persona_builder.build_combined()
        persona = None

        # 2. 记忆 → Memory Selector（Retrieve → Score → Filter → Compress）
        # 先同步 RuntimeUpdate 演化后的权重
        if self.runtime_update:
            self.memory_selector.sync_weights(
                self.runtime_update.get_memory_weights()
            )
        memory_context = ""
        if include_memory:
            memory_context = self.memory_selector.select(query=user_msg)

        # 3. 对话历史摘要
        history_summary = self.conversation_window.get_summary()
        if history_summary and memory_context:
            memory_context = f"{history_summary}\n\n{memory_context}"

        # 4. Compass 方向/目标
        compass_context = ""
        if include_goals and self.compass:
            try:
                compass_context = self.compass.get_system_prompt()
            except Exception:
                pass

        # 5. RuntimeUpdate 學習規則 (自動注入，不用手動傳 extra_system)
        if not extra_system and self.runtime_update:
            extra_system = self.runtime_update.get_extra_system_prompt() or None

        # 5. 对话历史 messages
        history_messages = self.conversation_window.build_messages(n=200)

        # 6. 组裝
        messages = self.prompt_builder.build(
            identity_messages=identity,
            persona_message=persona,
            memory_context=memory_context,
            compass_context=compass_context,
            conversation_messages=history_messages,
            user_input=user_msg,
            extra_system=extra_system,
        )

        # ===== Phase 8: runtime guard — 確保 system 永遠在前 =====
        if messages and messages[0].get("role") != "system":
            print("⚠️ [Guard] ContextAssembler 輸出異常：第一則不是 system message")
        system_count = sum(1 for m in messages if m.get("role") == "system")
        if system_count == 0:
            print("⚠️ [Guard] ContextAssembler 輸出異常：沒有任何 system message")

        return messages

    def record_response(self, assistant_msg: str, user_msg: str = ""):
        """记录本轮对话到 ConversationWindow"""
        self.conversation_window.add_turn(
            user_msg=user_msg,
            assistant_msg=assistant_msg,
        )

    def write_memory(self, user_msg: str, assistant_msg: str):
        """将对话分类写入记忆（读写统一入口）

        MemoryWriter 负责分析对话内容，自动分类写入：
        - identity_memory (身份/偏好)
        - semantic_memory (知识事实)
        - episodic_memory (事件)
        - working_memory (短期缓冲)
        - vector_memory (语义搜索)
        """
        self.memory_writer.write(
            user_msg=user_msg,
            assistant_msg=assistant_msg,
        )

    def get_system_context(self, task_hint: str = "", include_history: bool = False) -> List[Dict[str, str]]:
        """取得系統上下文訊息（不含 user input）

        給 self_review、self_repair、_auto_reflect 等次級 LLM 呼叫使用。
        確保它們也吃到相同的身份 + 記憶 + 規則。

        Args:
            task_hint: 任務提示（如「你正在審查自己的回覆」）
            include_history: 是否包含對話歷史

        Returns:
            系統訊息清單，caller 自行 append user message
        """
        identity = self.persona_builder.build_identity_messages()
        persona = self.persona_builder.build_persona_message()

        if self.runtime_update:
            self.memory_selector.sync_weights(
                self.runtime_update.get_memory_weights()
            )

        rules_context = ""
        if self.runtime_update:
            rules_context = self.runtime_update.get_extra_system_prompt()

        memory_context = self.memory_selector.select(query=task_hint)

        history_summary = self.conversation_window.get_summary()
        if history_summary and memory_context:
            memory_context = f"{history_summary}\n\n{memory_context}"

        messages = identity
        if persona:
            messages.append(persona)

        if task_hint:
            messages.append({"role": "system", "content": task_hint})

        if rules_context:
            messages.append({"role": "system", "content": rules_context})

        if memory_context:
            messages.append(
                {"role": "system", "content": f"[記憶上下文]\n{memory_context}"}
            )

        if include_history:
            history_messages = self.conversation_window.build_messages(n=3)
            messages.extend(history_messages)

        return messages

    def clear_conversation(self):
        """清空对话视窗（开始新话题）"""
        self.conversation_window.clear()

    def get_status(self) -> dict:
        return {
            "conversation_window": self.conversation_window.status(),
            "memory_selector": self.memory_selector.status(),
            "has_persona": self.persona_builder.persona is not None,
            "has_compass": self.compass is not None,
            "has_llm_for_summary": self.llm_call is not None,
        }
