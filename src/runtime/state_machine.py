"""
Runtime State Machine — AIOS 的生命週期核心
定義 11 個生命狀態，驅動「感知 → 思考 → 執行 → 反省 → 進化」閉環。
"""
import time
import threading
from enum import Enum
from typing import Callable, Dict, Any
from runtime.protocol import AgentState, EventType, new_event


class State(Enum):
    IDLE = "IDLE"
    OBSERVE = "OBSERVE"
    THINK = "THINK"
    PLAN = "PLAN"
    SIMULATE = "SIMULATE"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REFLECT = "REFLECT"
    LEARN = "LEARN"
    EVOLVE = "EVOLVE"
    CHECKPOINT = "CHECKPOINT"


class LifeCycleManager:
    def __init__(self, brain):
        self.brain = brain
        self.current_state = State.IDLE
        self.is_running = False
        self.thread = None
        self.event_bus = []  # 暫存事件，後續接 EventBus

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

        self.context: Dict[str, Any] = {}
        self._init_context()

    def _init_context(self):
        self.context = {
            "input_data": None,
            "user_msg": None,
            "reply": None,
            "observed_memory": None,
            "intent": None,
            "plan": None,
            "simulation_risk": None,
            "verification": None,
            "reflection": None,
            "pending_reflect": False,
        }

    def _emit(self, event_type: str, payload: dict = None):
        """發送 runtime 事件"""
        event = new_event(
            source="lifecycle",
            target="*",
            event_type=event_type,
            payload=payload or {},
        )
        self.event_bus.append(event)
        if hasattr(self.brain, 'bus'):
            try:
                self.brain.bus.emit(event.to_dict())
            except:
                pass

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self._emit(EventType.LIFECYCLE_HEARTBEAT.value, {"state": "started"})
        print("🧬 [Runtime] 生命週期狀態機已啟動")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        self._emit(EventType.LIFECYCLE_HEARTBEAT.value, {"state": "stopped"})

    def trigger(self, input_data=None):
        self.context["input_data"] = input_data
        self._transition_to(State.OBSERVE)

    def _run_loop(self):
        while self.is_running:
            try:
                handler = self.handlers.get(self.current_state)
                if handler:
                    handler()
                time.sleep(0.5)
            except Exception as e:
                self._emit(EventType.SYSTEM_ERROR.value, {"error": str(e)})
                self._transition_to(State.IDLE)

    def _transition_to(self, new_state: State):
        if self.current_state == new_state:
            return
        old = self.current_state.value
        self.current_state = new_state
        self._emit(EventType.LIFECYCLE_STATE_CHANGE.value, {
            "from": old, "to": new_state.value
        })

    # ========= 狀態處理 =========

    def _handle_idle(self):
        if self.context.get("input_data"):
            self._transition_to(State.OBSERVE)

    def _handle_observe(self):
        brain = self.brain
        ctx = self.context
        user_msg = ctx.get("input_data", "")
        if not user_msg:
            self._transition_to(State.IDLE)
            return
        if hasattr(brain, 'memory'):
            try:
                ctx["observed_memory"] = brain.memory.get_recent_conversations(limit=5)
            except:
                pass
        self._transition_to(State.THINK)

    def _handle_think(self):
        user_msg = self.context.get("input_data", "")
        if not user_msg:
            self._transition_to(State.IDLE)
            return
        intent = "chat"
        task_kw = ["幫我", "做", "寫", "查", "找", "執行", "跑", "建立", "刪除"]
        if any(k in user_msg for k in task_kw):
            intent = "task"
        if any(k in user_msg for k in ["硬碟", "記憶體", "cpu"]):
            intent = "system_check"
        self.context["intent"] = intent
        if intent == "task":
            self._transition_to(State.PLAN)
        else:
            self._transition_to(State.EXECUTE)

    def _handle_plan(self):
        self.context["plan"] = {"steps": 1, "type": "direct"}
        self._transition_to(State.SIMULATE)

    def _handle_simulate(self):
        user_msg = self.context.get("input_data", "")
        dangerous = ["rm -rf", "sudo", "chmod 777"]
        risk = any(d in user_msg for d in dangerous)
        self.context["simulation_risk"] = "high" if risk else "low"
        if risk:
            self.context["simulation_blocked"] = True
            self._transition_to(State.CHECKPOINT)
            return
        self._transition_to(State.EXECUTE)

    def _handle_execute(self):
        self._transition_to(State.VERIFY)

    def _handle_verify(self):
        reply = self.context.get("reply", "")
        self.context["verification"] = "ok" if reply else "empty_reply"
        self._transition_to(State.REFLECT)

    def _handle_reflect(self):
        brain = self.brain
        ctx = self.context
        if not ctx.get("pending_reflect"):
            self._transition_to(State.CHECKPOINT)
            return
        reply = ctx.get("reply", "")
        has_contra = False
        contra_detail = ""
        if hasattr(brain, 'contradiction') and reply:
            try:
                mem = brain.memory if hasattr(brain, 'memory') else None
                result = brain.contradiction.check(reply, memory=mem)
                if result.get("is_contradiction"):
                    has_contra = True
                    contra_detail = result.get("reason", "")
                    self._emit(EventType.MEMORY_CONTRADICTION.value, {"reason": contra_detail})
            except Exception as e:
                pass
        quality_issue = ""
        if reply:
            if len(reply) < 5:
                quality_issue = "回覆太短"
            elif "身為一個 AI" in reply:
                quality_issue = "說了禁句"
        ctx["reflection"] = {
            "has_contradiction": has_contra,
            "contradiction_detail": contra_detail,
            "quality_issue": quality_issue,
            "passed": not has_contra and not quality_issue,
        }
        ctx["pending_reflect"] = False
        self._transition_to(State.LEARN)

    def _handle_learn(self):
        brain = self.brain
        ctx = self.context
        user_msg = ctx.get("user_msg", "")
        reply = ctx.get("reply", "")
        if user_msg and reply and hasattr(brain, 'memory'):
            try:
                brain.memory.remember_conversation(
                    user_msg=user_msg[:500],
                    assistant_msg=reply[:500],
                    importance=0.6,
                )
                self._emit(EventType.MEMORY_STORED.value, {"type": "conversation"})
            except:
                pass
        reflection = ctx.get("reflection", {})
        if reflection.get("has_contradiction") and hasattr(brain, 'memory'):
            try:
                brain.memory.remember_fact(
                    f"矛盾記錄：{reflection.get('contradiction_detail', '')}",
                    importance=0.9,
                )
            except:
                pass
        self._transition_to(State.EVOLVE)

    def _handle_evolve(self):
        brain = self.brain
        if hasattr(brain, 'evolution_cycle') and hasattr(brain.evolution_cycle, 'run_check'):
            try:
                brain.evolution_cycle.run_check()
                self._emit(EventType.SYSTEM_EVOLUTION.value, {"status": "checked"})
            except:
                pass
        self._transition_to(State.CHECKPOINT)

    def _handle_checkpoint(self):
        self._init_context()
        self._transition_to(State.IDLE)

    def status(self) -> dict:
        return {
            "state": self.current_state.value,
            "is_running": self.is_running,
            "context_keys": list(self.context.keys()),
            "events_pending": len(self.event_bus),
        }
