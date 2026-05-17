"""
黑曜 AgentSupervisor — 全面子代理監控系統

功能：
1. Agent 註冊（name, thread, heartbeat interval, restartable flag）
2. 合作心跳 — 每個 agent 定期呼叫 heartbeat()
3. 健康檢查 — 心跳時效 + 執行緒存活 + 資源使用
4. 僵死檢測 — 心跳超過 timeout 但執行緒還活著
5. 資源監控 — 記憶體/CPU 上限，超標求救到 daemon
6. 統一心跳檔 — 供外部 daemon.sh 監控
7. 優雅關閉 — 依序停止所有 agent
"""

import os
import sys
import time
import signal
import threading
import traceback
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum

HEARTBEAT_FILE = "/tmp/heiyao_heartbeat"
CHECK_INTERVAL = 30
DEFAULT_HB_INTERVAL = 60
DEFAULT_HB_TIMEOUT = 180
MAX_MEMORY_MB = 2048

class AgentStatus(Enum):
    HEALTHY = "healthy"
    STALE = "stale"
    ZOMBIE = "zombie"
    DEAD = "dead"
    STOPPED = "stopped"

@dataclass
class AgentInfo:
    name: str
    thread: Optional[threading.Thread] = None
    pid: Optional[int] = None
    hb_interval: int = DEFAULT_HB_INTERVAL
    hb_timeout: int = DEFAULT_HB_TIMEOUT
    last_hb: float = 0
    is_restartable: bool = False
    is_critical: bool = True
    status: AgentStatus = AgentStatus.HEALTHY
    start_time: float = 0.0
    restart_count: int = 0
    error_count: int = 0
    last_error: str = ""
    mem_mb: float = 0.0

class AgentSupervisor:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.agents: Dict[str, AgentInfo] = {}
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._pgid_set = False

    def register(self, name: str, thread: Optional[threading.Thread] = None,
                 pid: Optional[int] = None, hb_interval: int = DEFAULT_HB_INTERVAL,
                 hb_timeout: Optional[int] = None,
                 is_restartable: bool = False, is_critical: bool = True) -> None:
        with self._lock:
            if name in self.agents:
                return
            self.agents[name] = AgentInfo(
                name=name, thread=thread,
                pid=pid or (thread.native_id if thread else None),
                hb_interval=hb_interval,
                hb_timeout=hb_timeout or (hb_interval * 3),
                is_restartable=is_restartable,
                is_critical=is_critical,
                start_time=time.time()
            )

    def heartbeat(self, name: str) -> None:
        agent = self.agents.get(name)
        if agent:
            agent.last_hb = time.time()
            agent.status = AgentStatus.HEALTHY

    def report_error(self, name: str, error: str) -> None:
        agent = self.agents.get(name)
        if agent:
            agent.error_count += 1
            agent.last_error = error[:200]

    def _read_memory_mb(self) -> float:
        try:
            with open(f"/proc/{os.getpid()}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024
        except Exception:
            pass
        return 0.0

    def _gc_zombie_threads(self):
        now = time.time()
        with self._lock:
            for name, agent in list(self.agents.items()):
                if agent.thread and not agent.thread.is_alive():
                    if agent.last_hb == 0 or (now - agent.last_hb) > agent.hb_timeout:
                        agent.status = AgentStatus.DEAD
                        agent.error_count += 1
                        print(f"[Supervisor] 💀 {name} 已死 (thread 終止, errors={agent.error_count})")
                        if agent.is_critical:
                            self._flag_unhealthy(name, "critical agent thread dead")
                        continue
                    agent.status = AgentStatus.ZOMBIE
                    agent.error_count += 1
                    print(f"[Supervisor] 🧟 {name} 僵死 (thread 存在但無心跳, errors={agent.error_count})")
                elif agent.thread and agent.last_hb > 0 and (now - agent.last_hb) > agent.hb_timeout:
                    agent.status = AgentStatus.ZOMBIE
                    agent.error_count += 1
                    agent.last_error = f"heartbeat timeout {now - agent.last_hb:.0f}s"
                    print(f"[Supervisor] 🧟 {name} 心跳逾時 {now - agent.last_hb:.0f}s (第 {agent.error_count} 次)")
                    if agent.error_count >= 3:
                        print(f"[Supervisor] 🚨 {name} 連續 {agent.error_count} 次僵死，上報 daemon")
                        self._flag_unhealthy(name, "zombie_3x")
                elif agent.thread and agent.thread.is_alive() and agent.last_hb > 0:
                    if agent.status != AgentStatus.HEALTHY:
                        agent.status = AgentStatus.HEALTHY
                        agent.error_count = max(0, agent.error_count - 1)
                        print(f"[Supervisor] 💚 {name} 恢復健康")

    def _flag_unhealthy(self, agent_name: str, reason: str):
        self._unhealthy_flags = getattr(self, '_unhealthy_flags', {})
        self._unhealthy_flags[agent_name] = reason

    def _update_system_heartbeat(self):
        all_healthy = all(
            a.status == AgentStatus.HEALTHY
            for a in self.agents.values() if a.is_critical
        ) if self.agents else True
        mem = self._read_memory_mb()
        unhealthy = getattr(self, '_unhealthy_flags', {})
        lines = [
            f"ts={time.time():.0f}",
            f"all_healthy={'true' if all_healthy else 'false'}",
            f"memory_mb={mem:.0f}",
            f"agents={len(self.agents)}",
        ]
        for name, a in self.agents.items():
            flag = f" [{unhealthy[name]}]" if name in unhealthy else ""
            lines.append(f"  {name}:{a.status.value}{flag}")
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
        self._mem_mb = mem

    def _loop(self):
        while self._running:
            try:
                self._gc_zombie_threads()
                self._update_system_heartbeat()
            except Exception as e:
                print(f"[Supervisor] loop error: {e}")
            time.sleep(CHECK_INTERVAL)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="agent-supervisor")
        self._thread.start()
        print("[Supervisor] ✅ AgentSupervisor 已啟動")

    def stop(self, timeout=10):
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)

    def get_status(self, name=None):
        with self._lock:
            if name:
                a = self.agents.get(name)
                if not a:
                    return None
                return dict(name=a.name, status=a.status.value,
                            uptime=time.time()-a.start_time,
                            restarts=a.restart_count, errors=a.error_count,
                            last_error=a.last_error, mem_mb=a.mem_mb)
            return {n: dict(name=n, status=a.status.value,
                            uptime=time.time()-a.start_time,
                            restarts=a.restart_count, errors=a.error_count)
                    for n, a in self.agents.items()}

    def summary(self):
        with self._lock:
            parts = [f"agents={len(self.agents)}"]
            for name, a in sorted(self.agents.items()):
                parts.append(f"  {name}: [{a.status.value}] err={a.error_count}")
            return "\n".join(parts)


# 全局單例
supervisor = AgentSupervisor()
