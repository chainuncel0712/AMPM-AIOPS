#!/usr/bin/env python3
"""
黑曜大腦 - 主類別 (精簡版)
各功能已拆分到 llm.py, executor.py, handler.py
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import config
from memory import Memory
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
from executor import ToolExecutor
from handler import MessageHandler


class Obsidian:
    def __init__(self):
        self.name = "黑曜"
        self.base_dir = config.base_dir
        
        # ========== 初始化所有部位 ==========
        self.memory = Memory(self.base_dir)
        self.tools = ToolSystem(self.base_dir)
        self.agents = AgentManager(self.base_dir)
        self.models = ModelCapability(self.base_dir)
        self.breath = BreathSystem(call_ai_func=self._call_ai)
        self.nose = NoseSystem(self.base_dir, call_ai_func=self._call_ai, memory=self.memory)
        
        # 強化系統
        self.compass = Compass(self.base_dir)
        self.decisions = DecisionRecorder(self.base_dir)
        self.tasks = TaskTracker(self.base_dir)
        self.circuit = CircuitController(self.base_dir)
        
        # 監控 (需要 call_ai_func)
        self.monitor = Monitor(self.base_dir, alert_callback=self._on_alert, call_ai_func=self._call_ai)
        
        # 進化
        self.evolution = Evolution(
            base_dir=self.base_dir,
            memory=self.memory,
            tools=self.tools,
            agents=self.agents,
            call_ai_func=self._call_ai
        )
        
        # ========== 拆分出來的模組 ==========
        self.llm = LLMClient(self.breath)
        self.executor = ToolExecutor(self.tools)
        self.handler = MessageHandler(self.llm, self.memory, self.compass, self.decisions, self.tasks)
        
        # 日誌目錄
        self.log_dir = self.base_dir / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 註冊內建工具
        if not self.tools.registry:
            self.tools._register_builtin_tools()
        
        self.running = True
        self.pending_approval = None
        
        # ========== 啟動所有系統 ==========
        self._start_heartbeat()
        threading.Thread(target=self._blood_circulation, daemon=True).start()
        self.breath.start()
        self.nose.start()
        
        print(f"🧠 {self.name} 已啟動")
        print(f"📁 目錄: {self.base_dir}")
        print(f"🔧 工具: {len(self.tools.list_all())}")
        print(f"💾 記憶: {len(self.memory.get_all_facts())}")
        print(f"👥 代理: {self.agents.get_agent_status()['total']}")
        print(f"🤖 模型: {len(self.models.switcher.registry.models)}")
        print(f"🧬 版本: v{self.evolution.version['number']}")
        print("=" * 50)
    
    def _call_ai(self, messages, temperature=0.7):
        """呼叫 AI (相容舊介面)"""
        return self.llm.call(messages, temperature)
    
    def _execute_tool(self, tool_name, params):
        """執行工具 (相容舊介面)"""
        return self.executor.execute(tool_name, params)
    
    def process_message(self, user_msg, send_func):
        """處理訊息 (相容舊介面)"""
        return self.handler.process(user_msg, send_func)
    
    def _on_alert(self, alert):
        print(f"🔔 警報: {alert['title']}")
    
    def _start_heartbeat(self):
        import json
        from datetime import datetime
        
        def heartbeat():
            while self.running:
                try:
                    hb_file = self.base_dir / "data" / "state" / "heartbeat.json"
                    hb_file.parent.mkdir(parents=True, exist_ok=True)
                    hb_file.write_text(json.dumps({
                        "time": datetime.now().isoformat(),
                        "status": "alive",
                        "pid": __import__('os').getpid()
                    }))
                except:
                    pass
                __import__('time').sleep(60)
        
        threading.Thread(target=heartbeat, daemon=True).start()
    
    def _blood_circulation(self):
        """血液循環 - 定期清理和維護"""
        while self.running:
            __import__('time').sleep(300)
            # 清理未使用工具
            self.tools.clean_unused_tools(30, dry_run=False)
