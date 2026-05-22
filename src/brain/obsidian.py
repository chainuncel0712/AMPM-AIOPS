"""
黑曜大腦 — 中央處理單元 (obsidian.py) — 精簡版
==============================================
只載入核心器官，其餘按需載入。
核心: 思考＋記憶＋對話＋執行＋修復＋進化＋上網
"""
import os, sys, threading
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config

from runtime.memory_manager import MemoryManager
from tools import ToolSystem
from breath import BreathSystem
from nose import NoseSystem
from llm import LLMClient
from executor import ToolExecutor as OldExecutor
from core.input_guard import InputGuard
from core.conversation import ConversationManager
from web.search import WebSearch
from skin.persona import Persona
from muscle.executor import MuscularExecutor

from skeleton.dna import DNA
from brain.organ_registry import OrganRegistry
from brain.thalamus import Thalamus
from brain.hypothalamus import Hypothalamus
from brain.cortex import Cortex
from runtime.context import ContextAssembler
from agents import AgentManager


class Obsidian:
    def __init__(self):
        self.name = DNA["name"]
        self.base_dir = config.base_dir
        self.organs: dict = {}

        self.mode = os.getenv("OBSIDIAN_MODE", "stable")
        print(f"⚙️ OBSIDIAN_MODE = {self.mode}")

        self.organs_registry = OrganRegistry()

        # ═══ 核心器官（必備） ═══
        self.memory = self.organs_registry.add(MemoryManager(self.base_dir))
        self.tools = self.organs_registry.add(ToolSystem(str(self.base_dir / "data" / "tools" / "registry.json")))
        from tools import set_tool_system
        set_tool_system(self.tools)
        self.breath = self.organs_registry.add(BreathSystem(call_ai_func=self._call_ai))
        self.nose = self.organs_registry.add(NoseSystem(self.base_dir, call_ai_func=self._call_ai, memory=self.memory))
        self.thalamus = Thalamus()
        self.llm = LLMClient(self.breath, thalamus=self.thalamus)
        self.thalamus.llm = self.llm
        self.old_executor = OldExecutor(self.tools)
        self.web_search = self.organs_registry.add(WebSearch())
        self.input_guard = self.organs_registry.add(InputGuard(max_input_length=5000))
        self.conversation = self.organs_registry.add(ConversationManager(base_dir=self.base_dir, max_history=20, max_tokens=8000))
        self.persona = self.organs_registry.add(Persona())
        self.muscle = self.organs_registry.add(MuscularExecutor(self.tools))
        self.hypothalamus = self.organs_registry.add(Hypothalamus(self.memory, self.tools, self.nose, None, None, None, self._call_ai))
        self.context_assembler = ContextAssembler(
            persona_organ=self.persona, memory_organ=self.memory, episodic_memory=self.memory,
            compass_organ=None, llm_call=self._call_ai, runtime_update=None,
            max_conversation_turns=200, max_summary_turns=200,
        )
        self.cortex = self.organs_registry.add(Cortex(
            self.llm, self.memory, None, None, None,
            self.muscle, self.organs_registry, self.persona, None, None,
            context_assembler=self.context_assembler,
            critic=None, learning_engine=None, evolution_engine=None,
            runtime_update=None, thalamus=self.thalamus,
        ))

        # ═══ 懶載入器官（需要時才實例化） ═══
        self.organs_registry.register_factory("evolution", lambda: self._build_evolution())
        self.organs_registry.register_factory("evolution_cycle", lambda: self._build_evolution_cycle())
        self.organs_registry.register_factory("repair_orchestrator", lambda: self._build_repair())

        self.organs = self.organs_registry.all()

        print(f"⚙️ {self.name} 核心啟動完成")
        print(f"📁 工作目錄: {self.base_dir}")
        print(f"💾 記憶引擎: 就緒")
        print(f"🧠 Cortex: 就緒")
        print(f"🔧 工具: {len(self.tools.registry)} 個")
        print(f"💪 執行器: 就緒")
        print(f"🌐 上網: 就緒")
        print(f"🔁 進化/修復: 按需載入")
        print("=" * 50)

        self.telegram_token: Optional[str] = None
        self.telegram_chat_id: Optional[int] = None
        self.db_path: Optional[str] = None
        self.langgraph: Optional[Any] = None
        self.running = True
        self.pending_approval = None

    # ═══ 懶載入工廠 ═══

    def _build_evolution(self):
        from evolution import Evolution
        agents = AgentManager(self.base_dir)
        evo = Evolution(base_dir=self.base_dir, memory=self.memory, tools=self.tools, agents=agents, call_ai_func=self._call_ai)
        return self.organs_registry.add(evo)

    def _build_evolution_cycle(self):
        from core.evolution_cycle import EvolutionCycleOrgan
        return self.organs_registry.add(EvolutionCycleOrgan(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            web_search=self.web_search, awareness=None, rebirth=None, llm=self.llm
        ))

    def _build_repair(self):
        from governance.repair_orchestrator import RepairOrchestrator
        return self.organs_registry.add(RepairOrchestrator(self.base_dir))

    def _call_ai(self, messages, temperature=0.7):
        return self.llm.call(messages, temperature)

    def _on_alert(self, alert):
        print(f"🚨 警報: {alert}")

    def process_message(self, user_msg, send_func):
        reply = self.cortex.process(user_msg, send_func)
        return reply
