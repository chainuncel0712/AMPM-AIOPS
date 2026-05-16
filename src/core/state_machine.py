"""
Runtime State Machine — 黑曜的生命週期核心
定義 AI 的 11 個生命狀態，讓它從「被動反應」變成「主動活著」。
"""
import time
import threading
from enum import Enum
from typing import Callable, Dict, Any

class State(Enum):
    IDLE = "IDLE"           # 空閒：等待指令或背景任務
    OBSERVE = "OBSERVE"     # 觀察：接收輸入、檢查系統狀態、讀取記憶
    THINK = "THINK"         # 思考：分析意圖、決定策略
    PLAN = "PLAN"           # 計畫：拆解任務、選擇工具
    SIMULATE = "SIMULATE"   # 模擬：預演後果（沙盒測試）
    EXECUTE = "EXECUTE"     # 執行：呼叫工具或 LLM
    VERIFY = "VERIFY"       # 驗證：檢查執行結果是否正確
    REFLECT = "REFLECT"     # 反省：自我審查、矛盾檢測
    LEARN = "LEARN"         # 學習：寫入記憶、更新知識
    EVOLVE = "EVOLVE"       # 進化：定期評估自身能力、優化參數
    CHECKPOINT = "CHECKPOINT" # 存檔：保存狀態，準備進入下一輪

class LifeCycleManager:
    def __init__(self, brain):
        self.brain = brain
        self.current_state = State.IDLE
        self.is_running = False
        self.thread = None
        
        # 狀態對應的處理函數（稍後由外部注入或預設）
        self.handlers: Dict[State, Callable] = {
            State.IDLE: self._handle_idle,
            State.OBSERVE: self._handle_observe,
            State.THINK: self._handle_think,
            State.PLAN: self._handle_plan,
            State.SIMULATE: self._handle_simulate,
            State.EXECUTE: self._handle_execute,
            State.VERIFY: self._handle_verify,
            State.REFLECT: self._handle_reflect,
            State.LEARN: self._handle_learn,
            State.EVOLVE: self._handle_evolve,
            State.CHECKPOINT: self._handle_checkpoint,
        }
        
        # 上下文數據，用於在狀態間傳遞資訊
        self.context: Dict[str, Any] = {
            "input_data": None,
            "plan": None,
            "result": None,
            "reflection": None,
        }

    def start(self):
        """啟動生命週期循環（背景執行）"""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("🧬 [LifeCycle] 生命週期狀態機已啟動")

    def stop(self):
        """停止生命週期循環"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        print("🧬 [LifeCycle] 生命週期狀態機已停止")

    def trigger(self, input_data=None):
        """外部觸發：當收到使用者訊息時，強制進入 OBSERVE 狀態"""
        print(f"⚡ [LifeCycle] 收到外部觸發: {input_data[:30]}...")
        self.context["input_data"] = input_data
        self._transition_to(State.OBSERVE)

    def _run_loop(self):
        """背景循環：定期檢查狀態並推進"""
        while self.is_running:
            try:
                # 執行當前狀態的邏輯
                handler = self.handlers.get(self.current_state)
                if handler:
                    handler()
                
                # 短暫休眠，避免 CPU 飆升
                time.sleep(1) 
            except Exception as e:
                print(f"❌ [LifeCycle] 狀態機執行錯誤: {e}")
                self._transition_to(State.IDLE) # 出錯回空閒

    def _transition_to(self, new_state: State):
        """狀態轉換"""
        if self.current_state == new_state:
            return
        
        print(f"🔄 [LifeCycle] {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state

    # ==================================================================
    # 狀態處理函數 (接上真實大腦功能)
    # ==================================================================

    def _handle_idle(self):
        """IDLE: 空閒等待。如果有輸入數據則進入 OBSERVE"""
        if self.context.get("input_data"):
            self._transition_to(State.OBSERVE)

    def _handle_observe(self):
        """OBSERVE: 觀察環境。讀取記憶、檢查系統狀態"""
        brain = self.brain
        ctx = self.context
        
        user_msg = ctx.get("input_data", "")
        if not user_msg:
            self._transition_to(State.IDLE)
            return
        
        # 讀取相關記憶，填充觀察結果
        if hasattr(brain, 'memory'):
            try:
                relevant = brain.memory.get_recent_conversations(limit=5)
                ctx["observed_memory"] = relevant
            except:
                pass
        
        self._transition_to(State.THINK)

    def _handle_think(self):
        """THINK: 分析意圖。判斷使用者想要什麼"""
        user_msg = self.context.get("input_data", "")
        if not user_msg:
            self._transition_to(State.IDLE)
            return
        
        # 快速意圖分類（不呼叫 LLM，節省資源）
        intent = "chat"
        task_keywords = ["幫我", "做", "寫", "查", "找", "執行", "跑", "建立", "刪除"]
        if any(k in user_msg for k in task_keywords):
            intent = "task"
        if "硬碟" in user_msg or "記憶體" in user_msg or "cpu" in user_msg:
            intent = "system_check"
        
        self.context["intent"] = intent
        self._transition_to(State.PLAN) if intent == "task" else self._transition_to(State.EXECUTE)

    def _handle_plan(self):
        """PLAN: 制定計畫。拆解任務"""
        # 需要更複雜的任務才拆解，簡單任務直接跳過
        self.context["plan"] = {"steps": 1, "type": "direct"}
        self._transition_to(State.SIMULATE)

    def _handle_simulate(self):
        """SIMULATE: 模擬執行。檢查任務是否有明顯風險"""
        user_msg = self.context.get("input_data", "")
        ctx = self.context
        
        # 簡單風險檢查：是否涉及危險指令
        dangerous = ["rm -rf", "sudo", "chmod 777"]
        risk = any(d in user_msg for d in dangerous)
        ctx["simulation_risk"] = "high" if risk else "low"
        
        if risk:
            ctx["simulation_blocked"] = True
            self._transition_to(State.CHECKPOINT)  # 跳過執行
            return
        
        self._transition_to(State.EXECUTE)

    def _handle_execute(self):
        """EXECUTE: 實際執行。快速路徑已在 cortex.process 完成，這裡記錄狀態"""
        # 主要的執行已經在 cortex.process 中同步完成
        # 狀態機在這裡只是確認執行已觸發
        self._transition_to(State.VERIFY)

    def _handle_verify(self):
        """VERIFY: 快速驗證結果。檢查回覆是否不為空"""
        reply = self.context.get("reply", "")
        if not reply:
            self.context["verification"] = "empty_reply"
        else:
            self.context["verification"] = "ok"
        self._transition_to(State.REFLECT)

    def _handle_reflect(self):
        """REFLECT: 自我反省。矛盾檢測 + 品質審查"""
        brain = self.brain
        ctx = self.context
        
        if not ctx.get("pending_reflect"):
            self._transition_to(State.CHECKPOINT)
            return
        
        user_msg = ctx.get("user_msg", "")
        reply = ctx.get("reply", "")
        
        has_contradiction = False
        contradiction_detail = ""
        
        # 1. 矛盾檢測：檢查新回覆與舊記憶是否衝突
        if hasattr(brain, 'contradiction') and reply:
            try:
                memory = brain.memory if hasattr(brain, 'memory') else None
                result = brain.contradiction.check(reply, memory=memory)
                if result.get("is_contradiction"):
                    has_contradiction = True
                    contradiction_detail = result.get("reason", "")
                    print(f"🪞 [Reflect] 檢測到矛盾：{contradiction_detail}")
            except Exception as e:
                print(f"⚠️ [Reflect] 矛盾檢測失敗：{e}")
        
        # 2. 品質審查：檢查回覆長度和關鍵內容
        quality_issue = ""
        if reply:
            if len(reply) < 5:
                quality_issue = "回覆太短"
            elif "身為一個 AI" in reply:
                quality_issue = "說了禁句(身為AI)"
        
        # 3. 記錄反省結果
        ctx["reflection"] = {
            "has_contradiction": has_contradiction,
            "contradiction_detail": contradiction_detail,
            "quality_issue": quality_issue,
            "passed": not has_contradiction and not quality_issue
        }
        
        if not ctx["reflection"]["passed"]:
            print(f"🪞 [Reflect] 反省發現問題：{contradiction_detail or quality_issue}")
        
        ctx["pending_reflect"] = False
        self._transition_to(State.LEARN)

    def _handle_learn(self):
        """LEARN: 學習記憶。將有價值的資訊寫入長期記憶"""
        brain = self.brain
        ctx = self.context
        
        user_msg = ctx.get("user_msg", "")
        reply = ctx.get("reply", "")
        
        if not user_msg or not reply:
            self._transition_to(State.EVOLVE)
            return
        
        # 將對話寫入情節記憶（如果尚未寫入）
        if hasattr(brain, 'memory'):
            try:
                brain.memory.remember_conversation(
                    user_msg=user_msg[:500],
                    assistant_msg=reply[:500],
                    importance=0.6
                )
                print("📝 [Learn] 已將對話寫入情節記憶")
            except Exception as e:
                print(f"⚠️ [Learn] 寫入記憶失敗：{e}")
        
        # 如果有反省結果，也寫入記憶
        reflection = ctx.get("reflection", {})
        if reflection and reflection.get("has_contradiction"):
            try:
                brain.memory.remember_fact(
                    f"矛盾記錄：{reflection.get('contradiction_detail', '')}",
                    importance=0.9
                )
            except:
                pass
        
        self._transition_to(State.EVOLVE)

    def _handle_evolve(self):
        """EVOLVE: 自我進化。觸發進化循環檢查"""
        brain = self.brain
        
        # 檢查進化循環是否就緒
        if hasattr(brain, 'evolution_cycle') and hasattr(brain.evolution_cycle, 'run_check'):
            try:
                brain.evolution_cycle.run_check()
                print("🧬 [Evolve] 已觸發進化循環檢查")
            except Exception as e:
                print(f"⚠️ [Evolve] 進化循環觸發失敗：{e}")
        
        self._transition_to(State.CHECKPOINT)

    def _handle_checkpoint(self):
        """CHECKPOINT: 保存狀態。清空上下文，回到 IDLE"""
        # 保留 reflection 記錄供後續查詢
        self.context = {
            "input_data": None,
            "user_msg": None,
            "reply": None,
            "observed_memory": None,
            "intent": None,
            "plan": None,
            "simulation_risk": None,
            "simulation_blocked": None,
            "verification": None,
            "reflection": self.context.get("reflection"),  # 保留反省結果
            "pending_reflect": False,
        }
        self._transition_to(State.IDLE)

    def status(self) -> dict:
        return {
            "state": self.current_state.value,
            "is_running": self.is_running,
            "context_keys": list(self.context.keys())
        }
