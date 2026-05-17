"""
ExecutionContext — 單一執行權威
==============================
整個系統只有一條執行鏈。每一層只能 observe，不能 override。

Pipeline（固定，不可跳過）：
  security → intent → route → execute → respond → remember

原則：
  - 每個請求獨立 sandbox，不共享 mutable state
  - 所有 decision 都可追蹤（TraceLogger）
  - 其他模組（immune/contradiction/governance）只能 observe + log
  - 禁止任何模組改寫 execution path、reroute、或 override response
"""

import uuid
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


# ===== Request Sandbox =====

@dataclass
class RequestSandbox:
    """每個請求的隔離上下文 — 不共享任何 mutable state"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_msg: str = ""
    raw_input: str = ""

    # Phase outputs
    security_ok: bool = True
    security_reason: str = ""
    blocked: bool = False
    intent_type: str = "chat"  # chat / command / tool / vision / system
    intent_params: Dict = field(default_factory=dict)
    route_target: str = "llm"  # llm / system_cmd / vision / model_switch
    route_params: Dict = field(default_factory=dict)
    llm_messages: List[Dict] = field(default_factory=list)
    llm_response: str = ""
    tool_results: List[str] = field(default_factory=list)
    response: str = ""

    # Metadata
    started_at: str = ""
    finished_at: str = ""
    phase_times: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    model_used: str = ""

    def duration_ms(self) -> float:
        if self.started_at and self.finished_at:
            try:
                s = datetime.fromisoformat(self.started_at)
                e = datetime.fromisoformat(self.finished_at)
                return (e - s).total_seconds() * 1000
            except Exception:
                return 0
        return 0


# ===== Trace Logger =====

class TraceLogger:
    """可觀測層 — 記錄每次請求的完整 decision chain"""

    def __init__(self, max_entries: int = 200):
        self.entries: List[Dict] = []
        self.max_entries = max_entries

    def start(self, sandbox: RequestSandbox):
        sandbox.started_at = datetime.now().isoformat()
        self._add({
            "type": "request_start",
            "id": sandbox.id,
            "user_msg": sandbox.user_msg[:100],
            "time": sandbox.started_at,
        })

    def phase(self, sandbox: RequestSandbox, phase: str, detail: Dict = None):
        t = time.time()
        sandbox.phase_times[phase] = t
        self._add({
            "type": "phase",
            "id": sandbox.id,
            "phase": phase,
            "detail": detail or {},
            "time": datetime.now().isoformat(),
        })

    def decision(self, sandbox: RequestSandbox, made_by: str, decision: str, reason: str = ""):
        self._add({
            "type": "decision",
            "id": sandbox.id,
            "made_by": made_by,
            "decision": decision,
            "reason": reason,
            "time": datetime.now().isoformat(),
        })

    def tool_call(self, sandbox: RequestSandbox, tool_name: str, args: Dict = None, result: str = ""):
        self._add({
            "type": "tool_call",
            "id": sandbox.id,
            "tool": tool_name,
            "args": args or {},
            "result": result[:200],
            "time": datetime.now().isoformat(),
        })

    def memory_write(self, sandbox: RequestSandbox, importance: float, layers: List[str]):
        self._add({
            "type": "memory_write",
            "id": sandbox.id,
            "importance": importance,
            "layers": layers,
            "time": datetime.now().isoformat(),
        })

    def observer(self, sandbox: RequestSandbox, observer_name: str, observation: str):
        self._add({
            "type": "observer",
            "id": sandbox.id,
            "observer": observer_name,
            "observation": observation[:200],
            "time": datetime.now().isoformat(),
        })

    def error(self, sandbox: RequestSandbox, error: Exception):
        sandbox.errors.append(str(error)[:200])
        self._add({
            "type": "error",
            "id": sandbox.id,
            "error": str(error)[:300],
            "traceback": traceback.format_exc()[-500:],
            "time": datetime.now().isoformat(),
        })

    def finish(self, sandbox: RequestSandbox):
        sandbox.finished_at = datetime.now().isoformat()
        self._add({
            "type": "request_finish",
            "id": sandbox.id,
            "duration_ms": round(sandbox.duration_ms(), 1),
            "phases": list(sandbox.phase_times.keys()),
            "errors": len(sandbox.errors),
            "response": sandbox.response[:100],
            "time": sandbox.finished_at,
        })

    def _add(self, entry: Dict):
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_trace(self, request_id: str) -> List[Dict]:
        return [e for e in self.entries if e.get("id") == request_id]

    def recent(self, n: int = 20) -> List[Dict]:
        return self.entries[-n:]

    def summary(self) -> Dict:
        total = len([e for e in self.entries if e["type"] == "request_finish"])
        errors = len([e for e in self.entries if e["type"] == "error"])
        phases = {}
        for e in self.entries:
            if e["type"] == "phase":
                phases[e["phase"]] = phases.get(e["phase"], 0) + 1
        return {
            "total_requests": total,
            "total_entries": len(self.entries),
            "errors": errors,
            "phases": phases,
            "recent_request_ids": list(set(
                e["id"] for e in self.entries[-50:] if "id" in e
            ))[-5:],
        }


# ===== Observer Protocol =====

class Observer:
    """觀察者 — 只能看和記錄，不能修改 execution"""
    def __init__(self, name: str):
        self.name = name

    def observe(self, sandbox: RequestSandbox, tracer: TraceLogger) -> Optional[str]:
        """回傳 observation string 或 None。不會被用來修改 sandbox。"""
        raise NotImplementedError


# ===== Execution Context =====

class ExecutionContext:
    """單一執行權威 — 整個系統唯一控制鏈"""

    PHASES = ["security", "intent", "route", "execute", "respond", "remember"]

    def __init__(self, brain):
        self.brain = brain
        self.observers: List[Observer] = []
        self.tracer = TraceLogger()
        self.llm = getattr(brain, "llm", None)
        self.memory = getattr(brain, "memory", None)
        self.firewall = getattr(brain, "firewall", None)
        self.context_assembler = getattr(brain, "context_assembler", None)
        self.tools = getattr(brain, "tools", None)

    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    def handle(self, user_msg: str, send_func=None) -> str:
        sandbox = RequestSandbox(user_msg=user_msg, raw_input=user_msg)
        self.tracer.start(sandbox)

        try:
            sandbox = self._phase_security(sandbox)
            if sandbox.blocked:
                self.tracer.finish(sandbox)
                return sandbox.response

            sandbox = self._phase_intent(sandbox)

            sandbox = self._phase_route(sandbox)
            if sandbox.response:
                self.tracer.finish(sandbox)
                return sandbox.response

            sandbox = self._phase_execute(sandbox)

            sandbox = self._phase_respond(sandbox)

            sandbox = self._phase_remember(sandbox)

            self._notify_observers(sandbox)

            self.tracer.finish(sandbox)
            return sandbox.response

        except Exception as e:
            self.tracer.error(sandbox, e)
            return f"⚠️ 執行錯誤: {e}"

    # ===== Phase 1: Security =====
    def _phase_security(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "security")
        if self.firewall:
            try:
                result = self.firewall.scan(sandbox.user_msg)
                if not result.get("allowed", True):
                    sandbox.blocked = True
                    sandbox.security_reason = result.get("reason", "blocked")
                    sandbox.response = f"⛔ {sandbox.security_reason}"
                    self.tracer.decision(sandbox, "firewall", "blocked", sandbox.security_reason)
                    return sandbox
            except Exception as e:
                self.tracer.error(sandbox, e)
        sandbox.security_ok = True
        return sandbox

    # ===== Phase 2: Intent Analysis =====
    def _phase_intent(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "intent")
        msg = sandbox.user_msg

        if self._is_model_switch(msg):
            sandbox.intent_type = "model_switch"
            sandbox.intent_params = self._parse_model_switch(msg)
            self.tracer.decision(sandbox, "intent", "model_switch",
                                 str(sandbox.intent_params))
        elif self._is_vision(msg):
            sandbox.intent_type = "vision"
            sandbox.intent_params = self._parse_vision(msg)
            self.tracer.decision(sandbox, "intent", "vision")
        elif self._is_system_cmd(msg):
            sandbox.intent_type = "system_cmd"
            sandbox.intent_params = self._parse_system_cmd(msg)
            self.tracer.decision(sandbox, "intent", "system_cmd")
        else:
            sandbox.intent_type = "chat"
            self.tracer.decision(sandbox, "intent", "chat")
        return sandbox

    # ===== Phase 3: Route =====
    def _phase_route(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "route")

        if sandbox.intent_type == "model_switch":
            return self._route_model_switch(sandbox)
        elif sandbox.intent_type == "vision":
            return self._route_vision(sandbox)
        elif sandbox.intent_type == "system_cmd":
            return self._route_system_cmd(sandbox)
        else:
            sandbox.route_target = "llm"
            self.tracer.decision(sandbox, "route", "llm")
        return sandbox

    # ===== Phase 4: Execute =====
    def _phase_execute(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "execute")

        if sandbox.route_target == "llm":
            return self._execute_llm(sandbox)
        return sandbox

    # ===== Phase 5: Respond =====
    def _phase_respond(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "respond")
        if not sandbox.response and sandbox.llm_response:
            sandbox.response = sandbox.llm_response
        if not sandbox.response:
            sandbox.response = "🤔 無法產生回覆"
        sandbox.model_used = getattr(self.llm, "current_model", lambda: "unknown")()
        return sandbox

    # ===== Phase 6: Remember =====
    def _phase_remember(self, sandbox: RequestSandbox) -> RequestSandbox:
        self.tracer.phase(sandbox, "remember")
        if self.memory and sandbox.response:
            try:
                importance = self.memory.remember(sandbox.user_msg, sandbox.response)
                self.tracer.memory_write(sandbox, importance, ["working", "semantic", "episodic"])
            except Exception as e:
                self.tracer.error(sandbox, e)
        if self.context_assembler and sandbox.response:
            try:
                self.context_assembler.record_response(
                    assistant_msg=sandbox.response,
                    user_msg=sandbox.user_msg,
                )
            except Exception as e:
                self.tracer.error(sandbox, e)
        return sandbox

    # ===== Route Handlers =====

    def _route_model_switch(self, sandbox: RequestSandbox) -> RequestSandbox:
        if not self.llm:
            sandbox.response = "⚠️ LLM 不可用"
            return sandbox
        action = sandbox.intent_params.get("action", "smart")
        if action == "list":
            models = self.llm.list_models()
            lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
            sandbox.response = f"可用模型：\n{lines}\n\n目前使用：{self.llm.current_model()}\n輸入「切換到 XXX」來切換"
        elif action == "switch":
            name = sandbox.intent_params.get("model_name", "")
            result = self.llm.switch_model(name)
            sandbox.response = f"🔄 {result}\n目前模型：{self.llm.current_model()}"
        elif action == "smart":
            task = sandbox.intent_params.get("task_type", "general")
            best = self._pick_best_model(task)
            if best:
                current = self.llm.current_model()
                if best.lower() not in current.lower():
                    self.llm.switch_model(best)
                    sandbox.response = f"🧠 已為 {task} 任務切換到 {best}"
                else:
                    sandbox.response = f"✅ 已在最適合的模型：{best}"
            else:
                sandbox.response = f"目前模型：{self.llm.current_model()}"
        elif action == "auto":
            self.llm.switch_model("auto")
            sandbox.response = "🔄 已恢復自動 fallback"
        self.tracer.decision(sandbox, "route:model_switch", action, sandbox.response[:50])
        return sandbox

    def _pick_best_model(self, task_type: str) -> str:
        models = self.llm.list_models()
        model_names = [m["name"] for m in models]

        def has(name): return any(name.lower() in n.lower() for n in model_names)

        # 推理/複雜任務 → 最強模型
        if task_type == "reasoning":
            for name in ["DeepSeek", "ATXP", "OR-DeepSeek"]:
                if has(name): return name
            if has("NV-Llama"): return "NV-Llama"
            if has("Ollama"): return "Ollama"

        # 圖片分析
        if task_type == "vision":
            for name in ["OR-Gemini"]:
                if has(name): return name
            for name in ["DeepSeek", "ATXP"]:
                if has(name): return name

        # 程式碼
        if task_type == "coding":
            for name in ["DeepSeek", "NV-Llama", "OR-DeepSeek"]:
                if has(name): return name
            if has("Ollama"): return "Ollama"

        # 快速回覆（最便宜/最快）
        if task_type == "fast":
            for name in ["NV-Llama", "Ollama"]:
                if has(name): return name
            for name in ["DeepSeek", "OR-DeepSeek", "ATXP"]:
                if has(name): return name

        # 通用：最強優先
        for name in ["DeepSeek", "ATXP", "OR-DeepSeek"]:
            if has(name): return name
        for name in ["NV-Llama"]:
            if has(name): return name
        if has("Ollama"): return "Ollama"
        return model_names[0] if model_names else ""

    def _route_vision(self, sandbox: RequestSandbox) -> RequestSandbox:
        import re
        url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', sandbox.user_msg)
        if url_match and self.llm:
            try:
                self.llm.switch_model("gemini")
            except Exception:
                pass
            image_url = url_match.group()
            prompt = sandbox.user_msg.replace(image_url, "").strip() or "請描述這張圖片的內容"
            sandbox.response = "🔍 正在分析圖片...\n\n" + self.llm.call_vision(prompt=prompt, image_url=image_url)
            self.tracer.decision(sandbox, "route:vision", "call_vision", image_url[:50])
        elif self.llm:
            try:
                self.llm.switch_model("gemini")
            except Exception:
                pass
            sandbox.response = "👁️ 已切換到視覺模型，目前：{0}\n請提供圖片網址或直接上傳圖片。".format(self.llm.current_model())
        else:
            sandbox.response = "⚠️ LLM 不可用，無法切換視覺模型。"
        return sandbox

    def _route_system_cmd(self, sandbox: RequestSandbox) -> RequestSandbox:
        import subprocess
        cmd = sandbox.intent_params.get("command", "")
        if cmd:
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                sandbox.response = r.stdout.strip() or r.stderr.strip() or "（無輸出）"
                self.tracer.decision(sandbox, "route:system_cmd", cmd, sandbox.response[:50])
            except Exception as e:
                sandbox.response = f"⚠️ 指令失敗: {e}"
        else:
            sandbox.response = "系統正常運作中"
        return sandbox

    def _execute_llm(self, sandbox: RequestSandbox) -> RequestSandbox:
        if not self.llm:
            sandbox.response = "⚠️ LLM 不可用"
            return sandbox

        if self.context_assembler:
            try:
                messages = self.context_assembler.assemble(user_msg=sandbox.user_msg)
                sandbox.llm_messages = messages
            except Exception as e:
                self.tracer.error(sandbox, e)
                messages = [
                    {"role": "system", "content": "你是黑曜，一個 AI 夥伴。用繁體中文簡短回覆。"},
                    {"role": "user", "content": sandbox.user_msg},
                ]
        else:
            messages = [
                {"role": "system", "content": "你是黑曜，一個 AI 夥伴。用繁體中文簡短回覆。"},
                {"role": "user", "content": sandbox.user_msg},
            ]

        try:
            sandbox.llm_response = self.llm.call(messages)
            self.tracer.decision(sandbox, "execute:llm", "called",
                                 sandbox.llm_response[:50] if sandbox.llm_response else "empty")
        except Exception as e:
            self.tracer.error(sandbox, e)
            sandbox.llm_response = f"⚠️ LLM 調用失敗: {e}"
        return sandbox

    # ===== Observers =====
    def _notify_observers(self, sandbox: RequestSandbox):
        for obs in self.observers:
            try:
                observation = obs.observe(sandbox, self.tracer)
                if observation:
                    self.tracer.observer(sandbox, obs.name, observation)
            except Exception as e:
                self.tracer.error(sandbox, e)

    # ===== Intent Detection =====

    def _is_model_switch(self, msg: str) -> bool:
        # 變數語法：MODEL=xxx 或 model=xxx
        import re as _re
        if _re.search(r'(?i)\bmodel\s*=', msg):
            return True
        if "模型" not in msg:
            return False
        return True

    def _parse_model_switch(self, msg: str) -> Dict:
        import re as _re
        m = _re.search(r'(?i)\bmodel\s*=\s*(\S+)', msg)
        if m:
            return {"action": "switch", "model_name": m.group(1)}
        if any(k in msg for k in ["有哪些", "列表"]):
            return {"action": "list"}
        if "auto" in msg.lower() or "自動" in msg:
            return {"action": "auto"}
        for kw in ["切換到", "換到", "改用", "換成", "切換成", "切成"]:
            if kw in msg:
                name = msg.split(kw)[-1].strip().split()[0]
                if len(name) > 1 and name not in ("什麼", "哪個", "哪", "什麽", "模型"):
                    return {"action": "switch", "model_name": name}
        return {"action": "smart", "task_type": "general"}

    def _is_vision(self, msg: str) -> bool:
        import re
        # 有圖片網址 + 視覺相關關鍵字
        if re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', msg):
            if any(kw in msg for kw in ["看圖", "分析", "圖片", "這張", "照片"]):
                return True
        # 檢查「看圖」在句首且沒有延後意圖
        if "看圖" in msg:
            idx = msg.index("看圖")
            after = msg[idx+2:].strip()
            if after and any(after.startswith(w) for w in ["先", "等等", "等一下", "稍等", "晚點", "之後"]):
                return False
            return True
        # 其他視覺關鍵字
        if any(kw in msg for kw in ["分析圖片", "這張圖"]):
            return True
        return False

    def _parse_vision(self, msg: str) -> Dict:
        import re
        url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', msg)
        return {"image_url": url_match.group() if url_match else ""}

    def _is_system_cmd(self, msg: str) -> bool:
        sys_cmds = {"硬碟": "df -h", "磁碟": "df -h", "記憶體": "free -h", "cpu": "top -bn1 | head -5", "系統": "uname -a"}
        return any(kw in msg for kw in sys_cmds)

    def _parse_system_cmd(self, msg: str) -> Dict:
        sys_cmds = {"硬碟": "df -h", "磁碟": "df -h", "記憶體": "free -h", "cpu": "top -bn1 | head -5", "系統": "uname -a"}
        for kw, cmd in sys_cmds.items():
            if kw in msg:
                return {"command": cmd}
        return {}

    # ===== Status =====
    def status(self) -> Dict:
        return {
            "observers": len(self.observers),
            "trace": self.tracer.summary(),
            "has_llm": self.llm is not None,
            "has_memory": self.memory is not None,
            "has_context_assembler": self.context_assembler is not None,
        }
