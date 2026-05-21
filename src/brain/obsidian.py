"""
黑曜大腦 — 中央處理單元 (obsidian.py)
======================================
Contains the Obsidian class. Re-exported from brain/__init__.py.
"""
import os, sys, threading
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config

from memory import Memory
from runtime.memory_manager import MemoryManager
from tools import ToolSystem
from agents import AgentManager
from monitor import Monitor
from evolution import Evolution
from models import ModelCapability
from breath import BreathSystem
from nose import NoseSystem
from compass.direction import Compass
from decisions.recorder import DecisionRecorder
from tasks.tracker import TaskTracker
from circuit.controller import CircuitController
from llm import LLMClient
from executor import ToolExecutor as OldExecutor

from skeleton.dna import DNA
from brain.organ_registry import OrganRegistry
from brain.agent_executor import run_agent_executor

from blood.event_bus import EventBus
from blood.scheduler import Scheduler
from blood.monitor import VitalMonitor

from brain.thalamus import Thalamus
from brain.hypothalamus import Hypothalamus
from brain.cortex import Cortex

from immune.firewall import Firewall
from immune.breaker import Breaker
from immune.contradiction import Contradiction
from immune.self_heal import SelfHeal

from muscle.executor import MuscularExecutor
from muscle.tool_registry import ToolRegistry
from muscle.tool_creator import ToolCreator

from skin.persona import Persona
from skin.wardrobe import Wardrobe
from skin.face import Face
from skin.voice import Voice

from womb.birth import Birth
from womb.agent_template import AgentTemplate
from womb.placenta import Placenta
from womb.nursery import Nursery

from bag.plugin_loader import PluginLoader
from web.search import WebSearch

from waste.cleaner import MemoryCleaner
from waste.tool_garbage import ToolGarbage
from waste.log_rotator import LogRotator

from brain.self_awareness import SelfAwareness
from brain.rebirth import Rebirth
from core.evolution_cycle import EvolutionCycleOrgan
from womb.inheritance import Inheritance
from core.crash_recovery import CrashRecovery
from core.input_guard import InputGuard
from core.conversation import ConversationManager
from core.feedback_learn import FeedbackLearn
from core.task_planner import TaskPlanner
from core.performance_profiler import PerformanceProfiler
from runtime import LifeCycleManager

from meta import WorldModel, SystemConsciousness, EvolutionGovernor

from runtime.context import ContextAssembler
from runtime.rule_store import RuleStore
from runtime.update_runtime import RuntimeUpdate
from runtime.execution_context import ExecutionContext
from brain.critic import Critic
from brain.learning_engine import LearningEngine
from brain.evolution_engine import EvolutionEngine


class Obsidian:
    def __init__(self):
        self.name = DNA["name"]
        self.base_dir = config.base_dir
        self.organs: dict = {}

        self.mode = os.getenv("OBSIDIAN_MODE", "stable")
        print(f"⚙️ OBSIDIAN_MODE = {self.mode}")

        self.organs_registry = OrganRegistry()

        self.memory = self.organs_registry.add(MemoryManager(self.base_dir))
        self.tools = self.organs_registry.add(ToolSystem(str(self.base_dir / "data" / "tools" / "registry.json")))
        from tools import set_tool_system
        set_tool_system(self.tools)
        self.agents = self.organs_registry.add(AgentManager(self.base_dir))
        self.models = self.organs_registry.add(ModelCapability(self.base_dir))
        self.breath = self.organs_registry.add(BreathSystem(call_ai_func=self._call_ai))
        self.nose = self.organs_registry.add(NoseSystem(self.base_dir, call_ai_func=self._call_ai, memory=self.memory))
        self.compass = self.organs_registry.add(Compass(self.base_dir))
        self.decisions = self.organs_registry.add(DecisionRecorder(self.base_dir))
        self.tasks = self.organs_registry.add(TaskTracker(self.base_dir))
        self.circuit = self.organs_registry.add(CircuitController(self.base_dir))
        self.monitor = self.organs_registry.add(Monitor(self.base_dir, alert_callback=self._on_alert, call_ai_func=self._call_ai))
        self.evolution = self.organs_registry.add(Evolution(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            agents=self.agents, call_ai_func=self._call_ai
        ))

        self.thalamus = Thalamus()

        self.llm = LLMClient(self.breath, thalamus=self.thalamus)
        self.thalamus.llm = self.llm
        self.old_executor = OldExecutor(self.tools)

        self.bus = self.organs_registry.add(EventBus())
        self.scheduler = self.organs_registry.add(Scheduler())
        self.vital_monitor = self.organs_registry.add(VitalMonitor(self.organs_registry))

        self.firewall = self.organs_registry.add(Firewall())
        self.breaker = self.organs_registry.add(Breaker())
        self.contradiction = self.organs_registry.add(Contradiction(self.base_dir))
        self.self_heal = self.organs_registry.add(SelfHeal())

        self.muscle = self.organs_registry.add(MuscularExecutor(self.tools))
        self.tool_registry = self.organs_registry.add(ToolRegistry(self.tools))
        self.tool_creator = self.organs_registry.add(ToolCreator(self.tools, self._call_ai))

        self.hypothalamus = self.organs_registry.add(Hypothalamus(
            self.memory, self.tools, self.nose, self.evolution, self.scheduler,
            self.tasks, self._call_ai
        ))

        self.life_cycle = LifeCycleManager(self)

        self.persona = self.organs_registry.add(Persona())

        self.rule_store = RuleStore()
        self.runtime_update = RuntimeUpdate(rule_store=self.rule_store)
        self.context_assembler = ContextAssembler(
            persona_organ=self.persona,
            memory_organ=self.memory,
            episodic_memory=self.memory,
            compass_organ=self.compass,
            llm_call=self._call_ai,
            runtime_update=self.runtime_update,
            max_conversation_turns=200,
            max_summary_turns=200,
        )
        self.critic = Critic()
        self.learning_engine = LearningEngine(
            llm_call=self._call_ai,
            rule_store=self.rule_store,
            runtime_update=self.runtime_update,
        )
        self.evolution_engine = EvolutionEngine()
        print("🧠 Context Layer (組裝器 + 記憶選擇器): 就緒")
        print("📏 Critic + Learning Engine + Rule Store: 就緒")
        print("🔄 Evolution Engine + Runtime Update: 就緒")

        self.execution_context = ExecutionContext(self) if self.mode == "stable" else None
        if self.execution_context:
            print("⚡ ExecutionContext (單一控制鏈): 就緒")

        self.cortex = self.organs_registry.add(Cortex(
            self.llm, self.memory, self.compass, self.decisions, self.tasks,
            self.muscle, self.organs_registry, self.persona, self.contradiction, self.life_cycle,
            context_assembler=self.context_assembler,
            critic=self.critic,
            learning_engine=self.learning_engine,
            evolution_engine=self.evolution_engine,
            runtime_update=self.runtime_update,
            thalamus=self.thalamus,
        ))
        self.wardrobe = self.organs_registry.add(Wardrobe())
        self.face = self.organs_registry.add(Face())
        self.voice = self.organs_registry.add(Voice())

        self.birth = self.organs_registry.add(Birth(self.agents))
        self.agent_template = self.organs_registry.add(AgentTemplate())
        self.placenta = self.organs_registry.add(Placenta(
            self.llm, self.memory, self.tools, self.muscle, self.birth
        ))
        self.nursery = self.organs_registry.add(Nursery())

        self.plugin_loader = self.organs_registry.add(PluginLoader())

        self.memory_cleaner = self.organs_registry.add(MemoryCleaner(self.memory))
        self.tool_garbage = self.organs_registry.add(ToolGarbage(self.tools))
        self.log_rotator = self.organs_registry.add(LogRotator(self.base_dir / "data" / "logs"))
        self.web_search = self.organs_registry.add(WebSearch())

        self.self_awareness = self.organs_registry.add(SelfAwareness(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            compass=self.compass
        ))

        self.rebirth = self.organs_registry.add(Rebirth(
            base_dir=self.base_dir, organs=self.organs, assembler=None,
            memory=self.memory, awareness=self.self_awareness
        ))

        self.evolution_cycle = self.organs_registry.add(EvolutionCycleOrgan(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            web_search=self.web_search, awareness=self.self_awareness,
            rebirth=self.rebirth, llm=self.llm
        )) if self.web_search else self.organs_registry.add(EvolutionCycleOrgan(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            awareness=self.self_awareness, rebirth=self.rebirth, llm=self.llm
        ))

        self.inheritance = self.organs_registry.add(Inheritance(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            awareness=self.self_awareness, evolution_cycle=self.evolution_cycle,
            dna=DNA
        ))

        self.input_guard = self.organs_registry.add(InputGuard(max_input_length=5000))

        self.conversation = self.organs_registry.add(ConversationManager(
            base_dir=self.base_dir, max_history=20, max_tokens=8000
        ))

        self.feedback_learn = self.organs_registry.add(FeedbackLearn(
            memory=self.memory, awareness=self.self_awareness,
            conversation=self.conversation
        ))

        self.crash_recovery = self.organs_registry.add(CrashRecovery(
            base_dir=self.base_dir, organ_refs={}
        ))

        self.task_planner = self.organs_registry.add(TaskPlanner(
            llm=self.llm, memory=self.memory, tasks=self.tasks
        ))

        self.perf = self.organs_registry.add(PerformanceProfiler())

        self.world_model = WorldModel(self.base_dir)
        self.system_consciousness = SystemConsciousness(self.base_dir)
        self.evolution_governor = EvolutionGovernor(self.base_dir)

        self.organs = self.organs_registry.all()

        self.agents.set_executor(lambda a, t: run_agent_executor(self, a, t))

        if self.mode != "stable":
            self.life_cycle.start()
            self.hypothalamus.start_autonomous_tasks()
            threading.Thread(target=self.scheduler.start, daemon=True).start()
            print(f"⚙️ {self.name} 核心機組已啟動（自治模式）")
            print(f"📁 工作目錄: {self.base_dir}")
            print(f"🔧 工具模組: {len(self.tools.registry)} 個")
            print(f"💾 記憶體: {self.memory.get_stats().get('working_count', 0)} 條")
            print(f"👥 代理節點: {len(self.agents._agents)}")
            print(f"🛡️ 防護陣列: 防火牆、熔斷器、衝突檢測、自修復")
            print(f"🏭 模組工廠: 就緒")
            print(f"🔌 擴充槽: 就緒")
            print(f"📊 狀態監控: 就緒")
            print(f"🔄 系統還原: 就緒")
            print(f"🧬 進化循環: 就緒")
            print(f"🛡️ 輸入安全: 就緒")
            print(f"💬 對話管理: 就緒")
            print(f"📝 回饋學習: 就緒")
            print(f"⚡ 崩潰恢復: 就緒")
            print(f"📋 任務規劃: 就緒")
            print(f"📊 效能監控: 就緒")
            print(f"🌐 世界模型: 就緒")
            print(f"🧘 系統意識: 就緒")
            print(f"🎯 進化治理: 就緒")
            print("=" * 50)
        else:
            self.life_cycle = None
            self.langgraph = None
            self.cortex.langgraph = None
            self.cortex.execution_context = self.execution_context
            self.cortex.critic = None
            self.cortex.learning_engine = None
            self.cortex.evolution_engine = None
            self.cortex.runtime_update = None
            print(f"⚙️ {self.name} 核心機組已啟動（可控模式）")
            print(f"📁 工作目錄: {self.base_dir}")
            print(f"💾 MemoryManager 記憶引擎: 就緒")
            print(f"🧠 Cortex (單路徑): 就緒")
            print(f"📋 ContextAssembler: 就緒")
            print(f"🛡️ Firewall (只記錄): 就緒")
            print(f"📝 自治模組: 全部停用")
            print("=" * 50)

        self.telegram_token: Optional[str] = None
        self.telegram_chat_id: Optional[int] = None
        self.db_path: Optional[str] = None
        self.email_smtp_host: Optional[str] = None
        self.email_port: int = 587
        self.email_user: Optional[str] = None
        self.email_password: Optional[str] = None
        self.email_to: Optional[str] = None
        self.langgraph: Optional[Any] = None

        self.running = True
        self.pending_approval = None

    def _call_ai(self, messages, temperature=0.7):
        return self.llm.call(messages, temperature)

    def _on_alert(self, alert):
        print(f"🚨 警報: {alert}")

    def process_message(self, user_msg, send_func):
        reply = self.cortex.process(user_msg, send_func)
        return reply
