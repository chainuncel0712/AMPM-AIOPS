"""
Context Assembly Layer — 每次 LLM 呼叫的統一上下文組裝

這是黑曜「持續意識層」(Persistent Consciousness Layer)。
確保 LLM 每次呼叫都吃到一致的 identity、persona、記憶、對話、任務狀態，
不再每回合重新出生。

正確管線：
  User Input
  → Memory Selector (Retrieve → Score → Filter → Compress)
  → Context Assembler (Persona + Memory + Conversation → Messages)
  → LLM

核心原則：
1. Context 每次重建，但規則一致
2. Memory 不直接餵給 LLM，先經過 Memory Selector 挑選
3. System 訊息永遠在最前面
4. 不讓 LLM 自行決定自己是誰
"""

from runtime.context.persona_builder import PersonaBuilder, RUNTIME_IDENTITY, RUNTIME_RULES
from runtime.context.conversation_window import ConversationWindow
from runtime.context.priority_scorer import PriorityScorer
from runtime.context.summarizer import Summarizer
from runtime.context.memory_retriever import MemoryRetriever
from runtime.context.memory_selector import MemorySelector
from runtime.context.memory_writer import MemoryWriter
from runtime.context.prompt_builder import PromptBuilder
from runtime.context.context_assembler import ContextAssembler

__all__ = [
    "PersonaBuilder",
    "RUNTIME_IDENTITY",
    "RUNTIME_RULES",
    "ConversationWindow",
    "PriorityScorer",
    "Summarizer",
    "MemoryRetriever",
    "MemorySelector",
    "PromptBuilder",
    "ContextAssembler",
]
