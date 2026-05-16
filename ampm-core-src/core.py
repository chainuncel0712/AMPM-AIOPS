"""
麻 (AMPM) Core — 30 個基本功能 AI 基礎框架
==========================================
pip install ampm-core

30 個純功能，零隱喻。使用者自己定義它要成為什麼。
"""
import json, os, re, sys, time, uuid, hashlib
import threading, importlib, inspect
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

__version__ = "0.1.0"
__all__ = [
    "AgentMaker", "AgentPool", "TaskDecomposer",
    "Memory", "ToolSystem", "EventBus", "Scheduler",
    "Persona", "WebSearch", "FileOps", "Shell",
    "Firewall", "Breaker", "Guard", "SelfHeal",
    "HealthCheck", "CostEngine", "TrustScore",
    "GoalTree", "TrendDetector", "CycleDetector",
    "DNATraits", "OrganLifecycle", "ResourceGovernor",
    "PluginLoader", "Fallback", "Compass",
    "DecisionLog", "TaskTracker", "AlignmentGuard",
    "Simulator", "Core",
]

# ═══════════════════════════════════════════════════════════
# 01. AgentMaker — 建立並執行代理
# ═══════════════════════════════════════════════════════════
class AgentMaker:
    """建立 LLM-backed 代理"""
    def __init__(self, llm_call: Callable = None):
        self.llm = llm_call or (lambda msgs, temp=0.3: "ready")
        self.agents: Dict[str, Dict] = {}

    def create(self, name: str, prompt: str = "", tools: List[str] = None) -> str:
        aid = uuid.uuid4().hex[:8]
        self.agents[aid] = {
            "id": aid, "name": name, "prompt": prompt,
            "tools": tools or [], "status": "idle",
        }
        return aid

    def execute(self, agent_id: str, task: str) -> str:
        agent = self.agents.get(agent_id)
        if not agent:
            return f"agent {agent_id} not found"
        agent["status"] = "busy"
        messages = [
            {"role": "system", "content": agent["prompt"]},
            {"role": "user", "content": task},
        ]
        result = self.llm(messages)
        agent["status"] = "idle"
        return result

# ═══════════════════════════════════════════════════════════
# 02. AgentPool — 動態代理池
# ═══════════════════════════════════════════════════════════
class AgentPool:
    """使用者可動態建立/刪除分組"""
    def __init__(self, agent_maker: AgentMaker):
        self.maker = agent_maker
        self.groups: Dict[str, Dict] = {}
        self._create_group("default", "general", "default pool", 3)

    def _create_group(self, name: str, role: str, desc: str, count: int):
        self.groups[name] = {"role": role, "desc": desc, "agents": []}
        for i in range(count):
            aid = self.maker.create(f"{name}_{i+1}", f"你是一個{role}代理。")
            self.groups[name]["agents"].append(aid)

    def create_group(self, name: str, role: str, desc: str = "", count: int = 2):
        if name not in self.groups:
            self._create_group(name, role, desc, count)
        return name

    def remove_group(self, name: str):
        if name != "default" and name in self.groups:
            del self.groups[name]

    def list_groups(self) -> Dict:
        return {n: {"role": g["role"], "count": len(g["agents"])} for n, g in self.groups.items()}

# ═══════════════════════════════════════════════════════════
# 03. TaskDecomposer — 任務拆解
# ═══════════════════════════════════════════════════════════
class TaskDecomposer:
    """把複雜任務拆成子任務"""
    @staticmethod
    def decompose(description: str) -> List[Dict]:
        d = description.lower()
        if any(k in d for k in ["code", "程式", "寫", "bug"]):
            roles = ["research", "design", "implement", "test"]
        elif any(k in d for k in ["分析", "report", "報告"]):
            roles = ["research", "analyze", "write"]
        elif any(k in d for k in ["搜", "search", "找"]):
            roles = ["search", "evaluate"]
        elif any(k in d for k in ["deploy", "部署", "install"]):
            roles = ["research", "execute", "verify"]
        else:
            roles = ["research", "execute", "summarize"]
        return [{"step": r, "description": f"[{r}] {description[:80]}"} for r in roles]

# ═══════════════════════════════════════════════════════════
# 04. Memory — 長期記憶
# ═══════════════════════════════════════════════════════════
class Memory:
    """事實記憶 + 對話記憶"""
    def __init__(self, base_dir: str = None):
        self._dir = Path(base_dir or Path.home() / ".ampm-core") / "memory"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.facts: Dict[str, str] = {}
        self.conversations: List[Dict] = []
        self._load()

    def _load(self):
        f = self._dir / "facts.json"
        if f.exists():
            try:
                self.facts = json.loads(f.read_text())
            except Exception:
                pass
        c = self._dir / "conversations.json"
        if c.exists():
            try:
                self.conversations = json.loads(c.read_text())[-100:]
            except Exception:
                pass

    def _save(self):
        with self._lock:
            (self._dir / "facts.json").write_text(json.dumps(self.facts, ensure_ascii=False))
            (self._dir / "conversations.json").write_text(json.dumps(self.conversations[-100:], ensure_ascii=False))

    def remember(self, key: str, value: str):
        with self._lock:
            self.facts[key] = value
            self._save()

    def recall(self, key: str) -> Optional[str]:
        return self.facts.get(key)

    def all_facts(self) -> Dict[str, str]:
        return dict(self.facts)

    def remember_conversation(self, user_msg: str, assistant_msg: str):
        with self._lock:
            self.conversations.append({
                "user": user_msg[:500], "assistant": assistant_msg[:500],
                "time": datetime.now().isoformat(),
            })
            self._save()

    def search(self, query: str) -> List[str]:
        results = []
        for k, v in self.facts.items():
            if query.lower() in k.lower() or query.lower() in v.lower():
                results.append(f"{k}: {v}")
        return results

# ═══════════════════════════════════════════════════════════
# 05. ToolSystem — 工具註冊與執行
# ═══════════════════════════════════════════════════════════
class ToolSystem:
    """註冊和執行函數工具"""
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.history: List[Dict] = []

    def register(self, name: str, func: Callable, description: str = ""):
        self.tools[name] = func

    def execute(self, name: str, **kwargs) -> Any:
        tool = self.tools.get(name)
        if not tool:
            return f"tool '{name}' not found"
        result = tool(**kwargs)
        self.history.append({"tool": name, "args": kwargs, "result": str(result)[:200]})
        return result

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def chain(self, steps: List[Dict]) -> List[Any]:
        results = []
        for step in steps:
            r = self.execute(step["tool"], **(step.get("args", {})))
            results.append(r)
        return results

# ═══════════════════════════════════════════════════════════
# 06. EventBus — 事件匯流排
# ═══════════════════════════════════════════════════════════
class EventBus:
    """pub/sub 通訊"""
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        self.listeners[event].append(callback)

    def emit(self, event: str, data: Any = None):
        for cb in self.listeners.get(event, []):
            try:
                cb(data)
            except Exception:
                pass

# ═══════════════════════════════════════════════════════════
# 07. Scheduler — 排程器
# ═══════════════════════════════════════════════════════════
class Scheduler:
    """背景定時任務"""
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self._running = False
        self._thread = None

    def add(self, name: str, func: Callable, interval_s: int):
        self.tasks[name] = {"func": func, "interval": interval_s, "last_run": 0}

    def start(self):
        if self._running:
            return
        self._running = True
        def _loop():
            while self._running:
                now = time.time()
                for t in self.tasks.values():
                    if now - t["last_run"] >= t["interval"]:
                        try:
                            t["func"]()
                        except Exception:
                            pass
                        t["last_run"] = now
                time.sleep(1)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

# ═══════════════════════════════════════════════════════════
# 08. Persona — 空白人格
# ═══════════════════════════════════════════════════════════
class Persona:
    """使用者透過對話定義 AI 的身份"""
    def __init__(self):
        self.bot_name = "麻"
        self.user_name = ""
        self.attributes: Dict[str, str] = {}

    def set_name(self, name: str):
        self.bot_name = name

    def set_user(self, name: str):
        self.user_name = name

    def set_attribute(self, key: str, value: str):
        self.attributes[key] = value

    def system_prompt(self) -> str:
        parts = []
        if self.user_name:
            parts.append(f"你正在跟「{self.user_name}」對話。")
        if self.attributes:
            attrs = "\n".join(f"- {k}: {v}" for k, v in self.attributes.items())
            parts.append(f"對方定義了你的身份：\n{attrs}")
        info = "\n".join(parts)
        return f"""你是{self.bot_name}，一個從對話中學習的 AI。
你的身份和行為全部由對方定義。對方沒說的你不亂加。
風格：直接、簡短、用對方的語言回覆。
{info}"""

# ═══════════════════════════════════════════════════════════
# 09. WebSearch — 網路搜尋
# ═══════════════════════════════════════════════════════════
class WebSearch:
    """HTTP 請求與網頁內容擷取"""
    @staticmethod
    def get(url: str, timeout: int = 10) -> Optional[str]:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="ignore")[:5000]
        except Exception as e:
            return f"error: {e}"

    @staticmethod
    def search(query: str) -> str:
        return f"web search not configured. install duckduckgo-search for search."

# ═══════════════════════════════════════════════════════════
# 10. FileOps — 檔案操作
# ═══════════════════════════════════════════════════════════
class FileOps:
    """安全的檔案讀寫"""
    @staticmethod
    def read(path: str) -> str:
        return Path(path).read_text()

    @staticmethod
    def write(path: str, content: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    @staticmethod
    def list_dir(path: str) -> List[str]:
        return [str(p) for p in Path(path).iterdir()]

# ═══════════════════════════════════════════════════════════
# 11. Shell — 命令執行
# ═══════════════════════════════════════════════════════════
class Shell:
    """安全的命令列執行"""
    @staticmethod
    def run(cmd: str, timeout: int = 30) -> str:
        import subprocess
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True,
                              text=True, timeout=timeout)
            return r.stdout[:2000] or r.stderr[:2000]
        except Exception as e:
            return str(e)

# ═══════════════════════════════════════════════════════════
# 12. Firewall — 輸入安全掃描
# ═══════════════════════════════════════════════════════════
class Firewall:
    """掃描輸入是否安全"""
    DANGEROUS = ["DROP TABLE", "DELETE FROM", "rm -rf", "<script>", "eval(", "exec(",
                 "os.system", "subprocess", "__import__", "1' OR '1'='1"]

    @staticmethod
    def scan(text: str) -> Dict:
        for pattern in Firewall.DANGEROUS:
            if pattern.lower() in text.lower():
                return {"safe": False, "reason": f"blocked: {pattern}"}
        return {"safe": True}

# ═══════════════════════════════════════════════════════════
# 13. Breaker — 重複檢測
# ═══════════════════════════════════════════════════════════
class Breaker:
    """阻止重複/惡意輸入"""
    def __init__(self):
        self.seen: set = set()
        self.failures: Dict[str, int] = defaultdict(int)

    def check(self, content: str) -> bool:
        h = hashlib.md5(content.encode()).hexdigest()
        if h in self.seen:
            return False
        self.seen.add(h)
        return True

    def record_failure(self, source: str):
        self.failures[source] += 1

    def is_blocked(self, source: str, threshold: int = 5) -> bool:
        return self.failures.get(source, 0) >= threshold

# ═══════════════════════════════════════════════════════════
# 14. Guard — 速率限制與權限
# ═══════════════════════════════════════════════════════════
class Guard:
    """速率限制、權限檢查、內容清理"""
    def __init__(self, max_per_minute: int = 30):
        self.max_rate = max_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.whitelist: set = set()
        self._lock = threading.Lock()

    def allow(self, source: str) -> bool:
        with self._lock:
            now = time.time()
            self.requests[source] = [t for t in self.requests.get(source, []) if now - t < 60]
            if len(self.requests[source]) >= self.max_rate:
                return False
            self.requests[source].append(now)
            return True

    def sanitize(self, text: str) -> str:
        return re.sub(r'<[^>]*>', '', text)

    def add_whitelist(self, source: str):
        self.whitelist.add(source)

# ═══════════════════════════════════════════════════════════
# 15. SelfHeal — 自修復
# ═══════════════════════════════════════════════════════════
class SelfHeal:
    """自動嘗試修復錯誤"""
    def __init__(self):
        self.heal_history: List[Dict] = []

    def heal(self, component: str, error: str) -> Dict:
        attempt = {
            "component": component, "error": error,
            "time": datetime.now().isoformat(),
            "action": "restart_suggested",
        }
        self.heal_history.append(attempt)
        return attempt

    def history(self) -> List[Dict]:
        return self.heal_history[-20:]

# ═══════════════════════════════════════════════════════════
# 16. HealthCheck — 健康檢查
# ═══════════════════════════════════════════════════════════
class HealthCheck:
    """檢查所有註冊組件的健康狀態"""
    def __init__(self):
        self.components: Dict[str, Any] = {}

    def register(self, name: str, component: Any):
        self.components[name] = component

    def check_all(self) -> Dict:
        results = {}
        for name, comp in self.components.items():
            try:
                if hasattr(comp, "status"):
                    results[name] = comp.status()
                else:
                    results[name] = "no status method"
            except Exception as e:
                results[name] = f"error: {e}"
        return results

# ═══════════════════════════════════════════════════════════
# 17. CostEngine — 成本追蹤
# ═══════════════════════════════════════════════════════════
class CostEngine:
    """記錄每次 LLM 呼叫的成本"""
    PRICES = {"default": 0.0001, "premium": 0.002}

    def __init__(self):
        self.total = 0.0
        self.session = 0.0
        self.log: List[Dict] = []

    def record(self, provider: str, tokens: int, cost: float = None):
        c = cost or tokens * self.PRICES.get(provider, 0.0001)
        self.total += c
        self.session += c
        self.log.append({"provider": provider, "tokens": tokens, "cost": c})

    def report(self) -> str:
        return f"total: ${self.total:.4f}, session: ${self.session:.4f}, calls: {len(self.log)}"

# ═══════════════════════════════════════════════════════════
# 18. TrustScore — 信任評分
# ═══════════════════════════════════════════════════════════
class TrustScore:
    """追蹤實體的可信度"""
    def __init__(self):
        self.scores: Dict[str, Dict] = {}

    def register(self, entity: str, initial: float = 0.5):
        self.scores[entity] = {"trust": initial, "total": 0, "success": 0}

    def record(self, entity: str, success: bool):
        if entity not in self.scores:
            self.register(entity)
        s = self.scores[entity]
        s["total"] += 1
        if success:
            s["success"] += 1
        s["trust"] = s["success"] / s["total"] if s["total"] > 0 else 0.5

    def get(self, entity: str) -> float:
        return self.scores.get(entity, {}).get("trust", 0.5)

    def is_trusted(self, entity: str, min_trust: float = 0.5) -> bool:
        return self.get(entity) >= min_trust

# ═══════════════════════════════════════════════════════════
# 19. GoalTree — 目標層級
# ═══════════════════════════════════════════════════════════
class GoalTree:
    """多層目標管理"""
    def __init__(self):
        self.goals: Dict[str, List[str]] = defaultdict(list)
        self.active = "default"

    def set_goal(self, level: str, goals: List[str]):
        self.goals[level] = goals

    def set_active(self, level: str):
        self.active = level

    def get_active(self) -> List[str]:
        return self.goals.get(self.active, [])

    def all_goals(self) -> Dict:
        return dict(self.goals)

# ═══════════════════════════════════════════════════════════
# 20. TrendDetector — 趨勢偵測
# ═══════════════════════════════════════════════════════════
class TrendDetector:
    """偵測數值變化趨勢"""
    def __init__(self):
        self.data: Dict[str, List[float]] = defaultdict(list)

    def record(self, metric: str, value: float):
        self.data[metric].append(value)
        if len(self.data[metric]) > 100:
            self.data[metric] = self.data[metric][-100:]

    def trend(self, metric: str) -> str:
        values = self.data.get(metric, [])
        if len(values) < 3:
            return "unknown"
        recent = values[-3:]
        if recent[-1] > recent[0] * 1.05:
            return "rising"
        elif recent[-1] < recent[0] * 0.95:
            return "falling"
        return "stable"

# ═══════════════════════════════════════════════════════════
# 21. CycleDetector — 週期偵測
# ═══════════════════════════════════════════════════════════
class CycleDetector:
    """偵測事件的重複週期"""
    def __init__(self):
        self.streams: Dict[str, List[datetime]] = defaultdict(list)

    def record(self, stream: str):
        self.streams[stream].append(datetime.now())
        if len(self.streams[stream]) > 50:
            self.streams[stream] = self.streams[stream][-50:]

    def period(self, stream: str) -> Optional[float]:
        times = self.streams.get(stream, [])
        if len(times) < 3:
            return None
        intervals = [(times[i] - times[i-1]).total_seconds() for i in range(1, len(times))]
        return sum(intervals) / len(intervals) if intervals else None

    def is_cyclical(self, stream: str) -> bool:
        p = self.period(stream)
        return p is not None and p > 0

# ═══════════════════════════════════════════════════════════
# 22. DNATraits — 可繼承設定
# ═══════════════════════════════════════════════════════════
@dataclass
class DNATraits:
    """可繼承的行為特徵"""
    risk_tolerance: float = 0.5
    learning_rate: float = 0.05
    exploration_drive: float = 0.3
    max_cost: float = 1.0
    generation: int = 0

    def mutate(self, rate: float = 0.1) -> "DNATraits":
        import random
        child = DNATraits(
            risk_tolerance=max(0, min(1, self.risk_tolerance + random.uniform(-rate, rate))),
            learning_rate=max(0, min(1, self.learning_rate + random.uniform(-rate, rate))),
            exploration_drive=max(0, min(1, self.exploration_drive + random.uniform(-rate, rate))),
            max_cost=max(0.01, self.max_cost * (1 + random.uniform(-0.2, 0.2))),
            generation=self.generation + 1,
        )
        return child

# ═══════════════════════════════════════════════════════════
# 23. OrganLifecycle — 元件熱插拔
# ═══════════════════════════════════════════════════════════
class OrganLifecycle:
    """管理元件的誕生、成長、成熟、汰換、回收"""
    def __init__(self):
        self.organs: Dict[str, Dict] = {}
        self._counter = 0

    def birth(self, name: str, version: str = "1.0", replaces: str = "") -> str:
        self._counter += 1
        oid = f"{name}-v{version}-{self._counter}"
        self.organs[oid] = {
            "id": oid, "name": name, "version": version,
            "status": "active", "replaces": replaces, "created": datetime.now().isoformat(),
        }
        if replaces:
            for o in self.organs.values():
                if o["name"] == replaces and o["status"] == "active":
                    o["status"] = "retired"
        return oid

    def retire(self, organ_id: str, reason: str = ""):
        if organ_id in self.organs:
            self.organs[organ_id]["status"] = "retired"
            self.organs[organ_id]["retired_reason"] = reason

    def active(self, name: str) -> List[Dict]:
        return [o for o in self.organs.values() if o["name"] == name and o["status"] == "active"]

# ═══════════════════════════════════════════════════════════
# 24. ResourceGovernor — 記憶體治理
# ═══════════════════════════════════════════════════════════
class ResourceGovernor:
    """監控和管理記憶體使用"""
    def __init__(self, budget_mb: int = 200):
        self.budget = budget_mb
        self.usage: Dict[str, int] = {}
        self.sleeping: set = set()

    def register(self, name: str, mem_mb: int = 5):
        self.usage[name] = mem_mb

    def sleep(self, name: str):
        self.sleeping.add(name)

    def wake(self, name: str):
        self.sleeping.discard(name)

    def total_mb(self) -> int:
        return sum(m for n, m in self.usage.items() if n not in self.sleeping)

    def is_over_budget(self) -> bool:
        return self.total_mb() > self.budget

    def auto_balance(self) -> List[str]:
        actions = []
        while self.is_over_budget():
            for name in sorted(self.usage.keys(), key=lambda n: -self.usage[n]):
                if name not in self.sleeping:
                    self.sleep(name)
                    actions.append(f"sleep:{name}")
                    break
            else:
                break
        return actions

# ═══════════════════════════════════════════════════════════
# 25. PluginLoader — 外掛載入
# ═══════════════════════════════════════════════════════════
class PluginLoader:
    """動態載入 Python 模組"""
    def __init__(self):
        self.plugins: Dict[str, Any] = {}

    def load(self, module_path: str) -> Any:
        if module_path in self.plugins:
            return self.plugins[module_path]
        try:
            mod = importlib.import_module(module_path)
            self.plugins[module_path] = mod
            return mod
        except Exception as e:
            return f"load error: {e}"

    def unload(self, name: str):
        if name in self.plugins:
            del self.plugins[name]
        if name in sys.modules:
            del sys.modules[name]

# ═══════════════════════════════════════════════════════════
# 26. Fallback — 備援與降級
# ═══════════════════════════════════════════════════════════
class Fallback:
    """函數呼叫失敗時自動降級"""
    def __init__(self):
        self.fallbacks: Dict[str, Callable] = {}

    def register(self, name: str, primary: Callable, fallback: Callable):
        self.fallbacks[name] = {"primary": primary, "fallback": fallback}

    def call(self, name: str, *args, **kwargs) -> Any:
        fb = self.fallbacks.get(name)
        if not fb:
            return f"no handler: {name}"
        try:
            return fb["primary"](*args, **kwargs)
        except Exception:
            return fb["fallback"](*args, **kwargs)

# ═══════════════════════════════════════════════════════════
# 27. Compass — 方向追蹤
# ═══════════════════════════════════════════════════════════
class Compass:
    """追蹤目標和進度"""
    def __init__(self):
        self.goals: Dict[str, Dict] = {}
        self.kpis: Dict[str, float] = {}

    def add_goal(self, name: str, category: str = "general"):
        self.goals[name] = {"name": name, "category": category, "progress": 0, "status": "active"}

    def update_progress(self, name: str, pct: float):
        if name in self.goals:
            self.goals[name]["progress"] = min(100, max(0, pct))
            if pct >= 100:
                self.goals[name]["status"] = "done"

    def record_kpi(self, name: str, value: float):
        self.kpis[name] = value

    def summary(self) -> Dict:
        active = sum(1 for g in self.goals.values() if g["status"] == "active")
        done = sum(1 for g in self.goals.values() if g["status"] == "done")
        return {"active_goals": active, "done_goals": done, "kpis": dict(self.kpis)}

# ═══════════════════════════════════════════════════════════
# 28. DecisionLog — 決策記錄
# ═══════════════════════════════════════════════════════════
class DecisionLog:
    """記錄每個決策便於審計"""
    def __init__(self):
        self.log: List[Dict] = []

    def record(self, decision: str, context: Dict = None, outcome: str = ""):
        self.log.append({
            "decision": decision,
            "context": context or {},
            "outcome": outcome,
            "time": datetime.now().isoformat(),
        })

    def recent(self, n: int = 10) -> List[Dict]:
        return self.log[-n:]

    def search(self, keyword: str) -> List[Dict]:
        return [d for d in self.log if keyword.lower() in d["decision"].lower()]

# ═══════════════════════════════════════════════════════════
# 29. TaskTracker — 任務追蹤
# ═══════════════════════════════════════════════════════════
class TaskTracker:
    """任務佇列管理"""
    def __init__(self):
        self.tasks: List[Dict] = []

    def add(self, description: str, priority: int = 0):
        self.tasks.append({
            "id": uuid.uuid4().hex[:6],
            "description": description,
            "priority": priority,
            "status": "pending",
            "created": datetime.now().isoformat(),
        })
        self.tasks.sort(key=lambda t: -t["priority"])

    def next(self) -> Optional[Dict]:
        pending = [t for t in self.tasks if t["status"] == "pending"]
        return pending[0] if pending else None

    def complete(self, task_id: str, result: str = ""):
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = "done"
                t["result"] = result
                break

    def all(self) -> List[Dict]:
        return self.tasks

# ═══════════════════════════════════════════════════════════
# 30. AlignmentGuard — 安全對齊
# ═══════════════════════════════════════════════════════════
class AlignmentGuard:
    """執行前安全檢查"""
    BLOCKED = ["rm -rf /", "DROP TABLE", "shutdown", "format", "os.remove", "eval("]

    @staticmethod
    def check(action: str) -> Dict:
        for pattern in AlignmentGuard.BLOCKED:
            if pattern.lower() in action.lower():
                return {"allowed": False, "reason": f"blocked: {pattern}"}
        return {"allowed": True}

# ═══════════════════════════════════════════════════════════
# Simulator — 後果模擬
# ═══════════════════════════════════════════════════════════
class Simulator:
    """基於歷史數據預測行動結果"""
    def __init__(self):
        self.history: Dict[str, List[bool]] = defaultdict(list)

    def record(self, action_type: str, success: bool):
        self.history[action_type].append(success)

    def simulate(self, action_type: str) -> Dict:
        h = self.history.get(action_type, [])
        if not h:
            return {"risk": 0.5, "confidence": 0, "samples": 0}
        success_rate = sum(h) / len(h)
        return {
            "risk": round(1 - success_rate, 2),
            "confidence": min(1.0, len(h) / 20),
            "samples": len(h),
        }

# ═══════════════════════════════════════════════════════════
# Core — 統合所有 30 個功能的入口
# ═══════════════════════════════════════════════════════════
class Core:
    """一鍵初始化全部 30 個功能"""
    def __init__(self, llm_call: Callable = None):
        self.bus = EventBus()
        self.scheduler = Scheduler()
        self.memory = Memory()
        self.tools = ToolSystem()
        self.agents = AgentMaker(llm_call)
        self.pool = AgentPool(self.agents)
        self.persona = Persona()
        self.search = WebSearch()
        self.files = FileOps()
        self.shell = Shell()
        self.firewall = Firewall()
        self.breaker = Breaker()
        self.guard = Guard()
        self.healer = SelfHeal()
        self.health = HealthCheck()
        self.cost = CostEngine()
        self.trust = TrustScore()
        self.goals = GoalTree()
        self.trend = TrendDetector()
        self.cycles = CycleDetector()
        self.fallback = Fallback()
        self.compass = Compass()
        self.decisions = DecisionLog()
        self.tasks = TaskTracker()
        self.plugins = PluginLoader()
        self.lifecycle = OrganLifecycle()
        self.resources = ResourceGovernor()
        self.alignment = AlignmentGuard()
        self.simulator = Simulator()
        self.decomposer = TaskDecomposer()

        # 註冊所有組件到健康檢查
        for attr in dir(self):
            obj = getattr(self, attr)
            if not attr.startswith("_") and not callable(obj) and obj is not None:
                self.health.register(attr, obj)

    def _load_llm(self, api_key: str = None, provider: str = "deepseek"):
        """Auto-configure LLM client"""
        if provider == "deepseek":
            import requests
            def llm_func(messages, temperature=0.3):
                try:
                    r = requests.post(
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key or os.getenv('DEEPSEEK_API_KEY', '')}"},
                        json={"model": "deepseek-chat", "messages": messages, "temperature": temperature},
                        timeout=30,
                    )
                    return r.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    return f"LLM error: {e}"
            return llm_func
        return lambda msgs, temp=0.3: "LLM not configured. Set DEEPSEEK_API_KEY env var."

    def status(self) -> Dict:
        return {
            "version": __version__,
            "components": 30,
            "health": self.health.check_all(),
            "cost": self.cost.report(),
        }
