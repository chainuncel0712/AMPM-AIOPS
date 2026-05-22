"""
AMPM-AIOPS Runtime Protocol — 統一事件、任務、工具、代理通訊格式
所有器官必須透過此協定進行溝通，確保系統一致性。
"""
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum


# ==================================================================
# 列舉定義
# ==================================================================

class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class AgentState(Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    REFLECTING = "REFLECTING"
    LEARNING = "LEARNING"
    REPAIRING = "REPAIRING"
    SAFE_MODE = "SAFE_MODE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"

class TaskStatus(Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class RiskLevel(Enum):
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BLOCKED = 4

class EventType(Enum):
    # 生命週期事件
    LIFECYCLE_STATE_CHANGE = "lifecycle.state_change"
    LIFECYCLE_HEARTBEAT = "lifecycle.heartbeat"
    
    # 任務事件
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # 工具事件
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"
    TOOL_CREATED = "tool.created"
    
    # 記憶事件
    MEMORY_STORED = "memory.stored"
    MEMORY_RECALLED = "memory.recalled"
    MEMORY_FORGOTTEN = "memory.forgotten"
    MEMORY_CONTRADICTION = "memory.contradiction"
    
    # 系統事件
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_EVOLUTION = "system.evolution"


# ==================================================================
# Schema 定義
# ==================================================================

@dataclass
class Event:
    """統一事件格式 — 所有器官通訊的基本單位"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = ""           # 來源器官/模組
    target: str = ""           # 目標器官/模組（* 表示廣播）
    type: str = ""             # 事件類型（見 EventType）
    priority: str = "normal"   # 優先級
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    correlation_id: str = ""   # 關聯 ID，用於追蹤事件鏈

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Task:
    """統一任務格式"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str = ""             # 任務目標描述
    description: str = ""      # 詳細描述
    status: str = "PENDING"    # 任務狀態
    priority: str = "normal"
    risk_level: str = "safe"   # 風險等級
    assigned_agent: str = ""   # 指派給哪個 Agent
    tools: List[str] = field(default_factory=list)  # 所需工具
    memory_refs: List[str] = field(default_factory=list)  # 相關記憶 ID
    timeout: int = 300         # 逾時秒數
    retries: int = 0           # 已重試次數
    max_retries: int = 3       # 最大重試次數
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ToolSchema:
    """統一工具格式"""
    tool_name: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)  # 能力標籤
    risk_level: str = "safe"
    permissions: List[str] = field(default_factory=list)    # 所需權限
    dependencies: List[str] = field(default_factory=list)   # 依賴的其他工具
    fallback: str = ""         # 備用工具
    timeout: int = 30
    sandbox_required: bool = False
    version: str = "1.0"

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ToolSchema":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AgentStateSchema:
    """Agent 狀態格式"""
    agent_id: str = ""
    state: str = "IDLE"        # 當前狀態（見 AgentState）
    health: str = "healthy"    # healthy / degraded / critical / offline
    memory_usage: int = 0      # 記憶使用量（KB）
    current_task: str = ""     # 目前正在執行的任務 ID
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    error_count: int = 0
    uptime: int = 0            # 運行時間（秒）

    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentStateSchema":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ==================================================================
# Protocol 工廠函數
# ==================================================================

def new_event(source: str, target: str, event_type: str, payload: dict = None,
              priority: str = "normal") -> Event:
    """快速建立事件"""
    return Event(
        source=source,
        target=target,
        type=event_type,
        priority=priority,
        payload=payload or {},
    )

def new_task(goal: str, description: str = "", tools: list = None,
             priority: str = "normal") -> Task:
    """快速建立任務"""
    return Task(
        goal=goal,
        description=description,
        tools=tools or [],
        priority=priority,
    )

def new_tool_schema(name: str, description: str, capabilities: list = None,
                    risk: str = "safe") -> ToolSchema:
    """快速建立工具定義"""
    return ToolSchema(
        tool_name=name,
        description=description,
        capabilities=capabilities or [],
        risk_level=risk,
    )
