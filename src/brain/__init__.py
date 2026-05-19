#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑曜大腦 — 中央處理單元
所有機組已就緒：骨架、匯流排、防護、執行、運算、介面、工廠、擴充、清理

模式控制：
  OBSIDIAN_MODE=stable  → 只跑可控核心鏈，停用所有自治模組
  OBSIDIAN_MODE=full    → 完整自治模式（舊行為）
  預設為 stable
"""
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config

# 頂層模組
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
# from handler import MessageHandler  # Phase 1: 死碼，已被 Cortex.process() 取代

# 骨架
from skeleton.registry import Registry
from skeleton.dna import DNA

# 匯流排
from blood.event_bus import EventBus
from blood.scheduler import Scheduler
from blood.monitor import VitalMonitor

# 中樞
from brain.hypothalamus import Hypothalamus
from brain.cortex import Cortex

# 防護
from immune.firewall import Firewall
from immune.breaker import Breaker
from immune.contradiction import Contradiction
from immune.self_heal import SelfHeal

# 執行
from muscle.executor import MuscularExecutor
from muscle.tool_registry import ToolRegistry
from muscle.tool_creator import ToolCreator

# 介面
from skin.persona import Persona
from skin.wardrobe import Wardrobe
from skin.face import Face
from skin.voice import Voice

# 工廠
from womb.birth import Birth
from womb.agent_template import AgentTemplate
from womb.placenta import Placenta
from womb.nursery import Nursery

# 擴充
from bag.plugin_loader import PluginLoader
from web.search import WebSearch

# 清理
from waste.cleaner import MemoryCleaner
from waste.tool_garbage import ToolGarbage
from waste.log_rotator import LogRotator

# 新增閉環器官
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

# Meta 層 — 世界模型
from meta import WorldModel, SystemConsciousness, EvolutionGovernor

# Context + Memory + Learning 三層整合
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

        # ===== 模式控制 =====
        self.mode = os.getenv("OBSIDIAN_MODE", "stable")
        print(f"⚙️ OBSIDIAN_MODE = {self.mode}")

        # ===== 骨架：註冊表 =====
        self.registry = Registry()

        # ===== 舊器官初始化 =====
        self.memory = self.registry.add(MemoryManager(self.base_dir))
        self.tools = self.registry.add(ToolSystem(str(self.base_dir / "data" / "tools" / "registry.json")))
        from tools import set_tool_system
        set_tool_system(self.tools)
        self.agents = self.registry.add(AgentManager(self.base_dir))
        self.models = self.registry.add(ModelCapability(self.base_dir))
        self.breath = self.registry.add(BreathSystem(call_ai_func=self._call_ai))
        self.nose = self.registry.add(NoseSystem(self.base_dir, call_ai_func=self._call_ai, memory=self.memory))
        self.compass = self.registry.add(Compass(self.base_dir))
        self.decisions = self.registry.add(DecisionRecorder(self.base_dir))
        self.tasks = self.registry.add(TaskTracker(self.base_dir))
        self.circuit = self.registry.add(CircuitController(self.base_dir))
        self.monitor = self.registry.add(Monitor(self.base_dir, alert_callback=self._on_alert, call_ai_func=self._call_ai))
        self.evolution = self.registry.add(Evolution(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            agents=self.agents, call_ai_func=self._call_ai
        ))

        # 舊 LLM 和執行器
        self.llm = LLMClient(self.breath)
        self.old_executor = OldExecutor(self.tools)
        # self.handler = MessageHandler(...)  # Phase 1: 死碼

        # ===== 數據匯流排 =====
        self.bus = self.registry.add(EventBus())
        self.scheduler = self.registry.add(Scheduler())
        self.vital_monitor = self.registry.add(VitalMonitor(self.registry))

        # ===== 防護陣列 =====
        self.firewall = self.registry.add(Firewall())
        self.breaker = self.registry.add(Breaker())
        self.contradiction = self.registry.add(Contradiction(self.base_dir))
        self.self_heal = self.registry.add(SelfHeal())

        # ===== 執行機構 =====
        self.muscle = self.registry.add(MuscularExecutor(self.tools))
        self.tool_registry = self.registry.add(ToolRegistry(self.tools))
        self.tool_creator = self.registry.add(ToolCreator(self.tools, self._call_ai))

        # ===== 運算核心 =====
        self.hypothalamus = self.registry.add(Hypothalamus(
            self.memory, self.tools, self.nose, self.evolution, self.scheduler,
            self.tasks, self._call_ai
        ))

        # ===== 新增：生命週期狀態機 (Runtime State Machine) =====
        # 必須在 Cortex 之前初始化，因為 Cortex 需要引用它
        self.life_cycle = LifeCycleManager(self)
        
        # ===== 介面層 =====
        self.persona = self.registry.add(Persona())

        # ==================================================================
        # Context + Memory + Learning 三層整合 (Persistent Consciousness)
        # 必須在 Cortex 之前初始化，因為 Cortex 需要引用 context_assembler
        # ==================================================================
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

        # ===== ExecutionContext — 單一執行權威（stable 模式核心）=====
        self.execution_context = ExecutionContext(self) if self.mode == "stable" else None
        if self.execution_context:
            print("⚡ ExecutionContext (單一控制鏈): 就緒")

        self.cortex = self.registry.add(Cortex(
            self.llm, self.memory, self.compass, self.decisions, self.tasks,
            self.muscle, self.registry, self.persona, self.contradiction, self.life_cycle,
            context_assembler=self.context_assembler,
            critic=self.critic,
            learning_engine=self.learning_engine,
            evolution_engine=self.evolution_engine,
            runtime_update=self.runtime_update,
        ))
        self.wardrobe = self.registry.add(Wardrobe())
        self.face = self.registry.add(Face())
        self.voice = self.registry.add(Voice())

        # ===== 模組工廠 =====
        self.birth = self.registry.add(Birth(self.agents))
        self.agent_template = self.registry.add(AgentTemplate())
        self.placenta = self.registry.add(Placenta(
            self.llm, self.memory, self.tools, self.muscle, self.birth
        ))
        self.nursery = self.registry.add(Nursery())

        # ===== 擴充模組 =====
        self.plugin_loader = self.registry.add(PluginLoader())

        # ===== 清理程序 =====
        self.memory_cleaner = self.registry.add(MemoryCleaner(self.memory))
        self.tool_garbage = self.registry.add(ToolGarbage(self.tools))
        self.log_rotator = self.registry.add(LogRotator(self.base_dir / "data" / "logs"))
        self.web_search = self.registry.add(WebSearch())

        # ===== 狀態監控 =====
        self.self_awareness = self.registry.add(SelfAwareness(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            compass=self.compass
        ))

        # ===== 系統還原 =====
        self.rebirth = self.registry.add(Rebirth(
            base_dir=self.base_dir, organs=self.organs, assembler=None,
            memory=self.memory, awareness=self.self_awareness
        ))

        # ===== 進化循環 =====
        self.evolution_cycle = self.registry.add(EvolutionCycleOrgan(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            web_search=self.web_search, awareness=self.self_awareness,
            rebirth=self.rebirth, llm=self.llm
        )) if self.web_search else self.registry.add(EvolutionCycleOrgan(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            awareness=self.self_awareness, rebirth=self.rebirth, llm=self.llm
        ))

        # ===== 技能傳承 =====
        self.inheritance = self.registry.add(Inheritance(
            base_dir=self.base_dir, memory=self.memory, tools=self.tools,
            awareness=self.self_awareness, evolution_cycle=self.evolution_cycle,
            dna=DNA
        ))

        # ===== 輸入安全閘 =====
        self.input_guard = self.registry.add(InputGuard(max_input_length=5000))

        # ===== 對話管理器 =====
        self.conversation = self.registry.add(ConversationManager(
            base_dir=self.base_dir, max_history=20, max_tokens=8000
        ))

        # ===== 回饋學習 =====
        self.feedback_learn = self.registry.add(FeedbackLearn(
            memory=self.memory, awareness=self.self_awareness,
            conversation=self.conversation
        ))

        # ===== 崩潰恢復 =====
        self.crash_recovery = self.registry.add(CrashRecovery(
            base_dir=self.base_dir, organ_refs={}
        ))

        # ===== 任務規劃 =====
        self.task_planner = self.registry.add(TaskPlanner(
            llm=self.llm, memory=self.memory, tasks=self.tasks
        ))

        # ===== 效能監控 =====
        self.perf = self.registry.add(PerformanceProfiler())

        # ===== Meta 層 — 世界模型 =====
        self.world_model = WorldModel(self.base_dir)
        self.system_consciousness = SystemConsciousness(self.base_dir)
        self.evolution_governor = EvolutionGovernor(self.base_dir)

        # ===== 將所有註冊的器官同步到 self.organs（LangGraph 依賴此 dict） =====
        self.organs = self.registry.all()

        # ===== agent executor =====
        def _agent_executor(agent, task):
            role = agent.get("role", "")
            prompt = agent.get("prompt", "")
            desc = task.get("description", "")
            tools_list = agent.get("tools", [])
            capabilities = agent.get("capabilities", set())
            tools_str = ", ".join(tools_list) if tools_list else "無"
            agent_name = agent.get("name", "?")
            agent_id = agent.get("id", "")

            # 從黑曜記憶提取相關上下文
            memory_context = ""
            if hasattr(self, 'memory') and self.memory:
                try:
                    recent = self.memory.query(desc[:80], limit=3)
                    if recent:
                        memory_context = "已知相關背景：\n" + "\n".join(
                            f"  - {r}" for r in recent if r
                        )[:500]
                except Exception:
                    pass

            think_prompt = f"""你是 AMPM-AIOPS 黑曜的 {role} 子代理，代號 {agent_name}。
嚴禁罐頭話、客服模板、道歉句。語氣像真人，直接給答案。

{memory_context}

## 任務
{desc}

## 角色能力
{prompt}
技能：{', '.join(capabilities) if capabilities else role}
工具：{tools_str}

## 規則
- 不編造數據，不知道就說不知道
- 不問「需要我繼續嗎？」「這樣可以嗎？」
- 不回「再跟我說」「請告訴我」等罐頭句
- 完成後直接用【結果】給出最終答案"""
            messages = [
                {"role": "system", "content": think_prompt},
                {"role": "user", "content": f"任務：{desc}"},
            ]
            result = self.llm.call(messages, temperature=0.3)
            if not result:
                return f"[{agent_name}] 任務完成（無詳細結果）"
            return f"[{agent_name}/{role}]\n{result}"

        self.agents.set_executor(_agent_executor)

        # ===== 模式分歧：stable vs full =====
        if self.mode != "stable":
            # ── 自治模式 (full) ──
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
            # ── 可控模式 (stable) ──
            # 停用所有自治迴圈，只保留核心 chain
            self.life_cycle = None
            self.langgraph = None  # 強制走 cortex 單一路徑
            self.cortex.langgraph = None
            self.cortex.execution_context = self.execution_context
            # critic/learning/evolution 存在但不啟動（cortex 內會檢查 mode）
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

        # ── 動態屬性初始化（供 main.py 和 langgraph_executor.py 使用） ──
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
        """處理使用者訊息 - 使用新架構的 Cortex"""
        # 使用大腦皮層處理（包含免疫、路由、工具、LLM）
        reply = self.cortex.process(user_msg, send_func)
        return reply

        # ===== 儀表板由 main.py 統一啟動 =====
        pass
