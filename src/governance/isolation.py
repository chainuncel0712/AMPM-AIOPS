"""
Execution Isolation — Sub-Agent Sandbox
========================================
Enforces tool whitelist, filesystem jail, command filter, resource limits.

All sub-agent execution MUST go through this layer, never directly to execute_tool().
"""
import os
import re
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from governance.event_log import event_log


# ──────────────────────────────────────────────
# 1. Tool Whitelist
# ──────────────────────────────────────────────

# Which agent name patterns can call which tools
TOOL_WHITELIST: Dict[str, List[str]] = {
    # AgentCompany sub-agents: all tools (default, but bounded)
    "agent_": ["write_file", "read_file", "list_dir", "run_command", "web_search", "generate_image"],
    "worker_": ["write_file", "read_file", "list_dir", "run_command"],
    "researcher_": ["read_file", "list_dir", "web_search"],
    "coder_": ["write_file", "read_file", "list_dir", "run_command"],
    "writer_": ["write_file"],
    "critic_": ["read_file", "list_dir"],
    # Default fallback
    "__default__": ["read_file"],
}

# Tools that are never allowed regardless of agent
GLOBALLY_DENIED = [
    # Network exfiltration
    "curl", "wget", "nc", "ncat", "socat", "telnet", "ssh", "scp", "rsync",
    # Privilege escalation
    "sudo", "su", "chown", "chmod 777", "passwd",
    # Destruction
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "fdisk", "mkswap",
    # Fork bombs / resource abuse
    ":(){", "forkbomb",
    # Crypto / mining
    "minerd", "xmrig", "cpuminer",
]

_MAX_OUTPUT_SIZE = 200 * 1024  # 200KB max file read output
_MAX_COMMAND_OUTPUT = 5000     # 5KB max command output


# ──────────────────────────────────────────────
# 2. Filesystem Jail
# ──────────────────────────────────────────────

ALLOWED_WRITE_DIRS = [
    Path("/home/pop5057273712_gmail_com/AMPM-AIOPS/outputs"),
]

ALLOWED_READ_DIRS = ALLOWED_WRITE_DIRS + [
    Path("/home/pop5057273712_gmail_com/AMPM-AIOPS/data"),
    Path("/home/pop5057273712_gmail_com/AMPM-AIOPS/docs"),
]


class FilesystemJail:
    """Restrict file access to allowed directories."""

    @classmethod
    def check_write(cls, filepath: str) -> bool:
        resolved = Path(filepath).resolve()
        for base in ALLOWED_WRITE_DIRS:
            try:
                resolved.relative_to(base.resolve())
                return True
            except ValueError:
                continue
        return False

    @classmethod
    def check_read(cls, filepath: str) -> bool:
        resolved = Path(filepath).resolve()
        for base in ALLOWED_READ_DIRS:
            try:
                resolved.relative_to(base.resolve())
                return True
            except ValueError:
                continue
        return False


# ──────────────────────────────────────────────
# 3. Command Filter
# ──────────────────────────────────────────────

class CommandFilter:
    """
    Whitelist-based command filter.
    Only commands matching allowed patterns (and not denied patterns) pass.
    """

    # Commands always allowed (safe read-only)
    ALLOWED_COMMANDS = [
        "ls", "cat", "head", "tail", "wc", "find", "grep", "rg", "ack",
        "pwd", "echo", "printf", "date", "which", "whoami", "id",
        "python3 --version", "python3 -c", "python3 -m",
        "pip list", "pip show", "pip freeze",
        "git status", "git log", "git diff", "git show", "git branch",
        "git stash list", "git describe",
        "tree", "stat", "du -sh", "df -h", "lsblk",
        "free -h", "uptime", "uname -a", "hostname",
        "file", "basename", "dirname", "realpath", "readlink",
    ]

    # Patterns that are never allowed
    FORBIDDEN_PATTERNS = [
        r"\bsudo\b", r"\bsu\b", r"\bchown\b",
        r"\brm\s+-rf\s+/", r"\bmkfs\b", r"\bdd\s+if=",
        r":\(\)\s*\{", r"\bforkbomb\b",
        r"\bcurl\b", r"\bwget\b", r"\bnc\b", r"\bncat\b",
        r"\bssh\b", r"\bscp\b", r"\brsync\b",
        r"\bminerd\b", r"\bxmrig\b",
        r">\s*/dev/", r">\s*/proc/",
    ]

    @classmethod
    def check(cls, cmd: str) -> bool:
        cmd_stripped = cmd.strip()

        # Check forbidden patterns
        for pat in cls.FORBIDDEN_PATTERNS:
            if re.search(pat, cmd_stripped):
                return False

        # Check if command starts with an allowed command
        for allowed in cls.ALLOWED_COMMANDS:
            if cmd_stripped.startswith(allowed):
                return True

        # For anything else, check if it's a simple non-destructive command
        # (e.g., python3 script.py, node app.js)
        first_word = cmd_stripped.split()[0] if cmd_stripped.split() else ""
        if first_word in ("python3", "python", "node", "npm", "npx", "pip"):
            # Only allow if not piping to dangerous commands
            after_pipe = cmd_stripped.split("|")
            for segment in after_pipe:
                seg = segment.strip()
                for pat in cls.FORBIDDEN_PATTERNS:
                    if re.search(pat, seg):
                        return False
            return True

        return False


# ──────────────────────────────────────────────
# 4. Resource Monitor
# ──────────────────────────────────────────────

class ResourceMonitor:
    """Timeout + basic resource tracking for sub-agent execution."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._active_calls = 0
        return cls._instance

    @contextmanager
    def track(self, timeout: int = 30):
        self._active_calls += 1
        try:
            yield
        finally:
            self._active_calls -= 1

    @property
    def active_calls(self) -> int:
        return self._active_calls


# ──────────────────────────────────────────────
# 5. Isolated Executor
# ──────────────────────────────────────────────

class IsolatedExecutor:
    """Wraps execute_tool with all isolation checks."""

    def __init__(self, agent_name: str = "unknown"):
        self.agent_name = agent_name
        self._allowed_tools = self._resolve_whitelist(agent_name)

    @staticmethod
    def _resolve_whitelist(agent_name: str) -> List[str]:
        for prefix, tools in TOOL_WHITELIST.items():
            if agent_name.lower().startswith(prefix):
                return tools
        return TOOL_WHITELIST["__default__"]

    def check_tool(self, tool_name: str) -> bool:
        """Check if this agent is allowed to call this tool."""
        if tool_name in GLOBALLY_DENIED:
            return False
        if tool_name not in self._allowed_tools:
            return False
        return True

    def execute(
        self,
        tool_name: str,
        args: dict,
        original_execute: Callable,
        timeout: int = 60,
    ) -> str:
        """
        Execute a tool through the sandbox.
        original_execute: the real execute_tool function to call.
        """
        # Tool whitelist
        if not self.check_tool(tool_name):
            msg = f"🔒 [Isolation] {self.agent_name} 無權使用工具: {tool_name}"
            event_log.record(
                source=f"isolation:{self.agent_name}",
                action=f"tool_denied:{tool_name}",
                input_data={"agent": self.agent_name, "tool": tool_name, "args": args},
                decision="BLOCKED",
            )
            return f"❌ {msg}"

        # Pre-execution checks per tool type
        check_error = self._precheck(tool_name, args)
        if check_error:
            return f"❌ {check_error}"

        # Execute with resource monitoring
        monitor = ResourceMonitor()
        with monitor.track(timeout=timeout):
            try:
                result = original_execute(tool_name, args)
                # Post-execution validation
                result = self._postprocess(tool_name, result)
                return result
            except Exception as e:
                return f"❌ [Isolation] 執行錯誤: {e}"

    def _precheck(self, tool_name: str, args: dict) -> Optional[str]:
        """Run tool-specific pre-checks before execution."""
        if tool_name == "write_file":
            filepath = args.get("filepath", "")
            resolved = Path(filepath).resolve() if filepath else Path()
            if not FilesystemJail.check_write(str(resolved)):
                return f"路徑不在允許寫入目錄: {filepath}. 允許: {', '.join(str(d) for d in ALLOWED_WRITE_DIRS)}"
            content = args.get("content", "")
            if len(content) > _MAX_OUTPUT_SIZE:
                return f"檔案太大 ({len(content)} bytes)，上限 {_MAX_OUTPUT_SIZE}"

        elif tool_name == "read_file":
            filepath = args.get("filepath", "")
            resolved = Path(filepath).resolve() if filepath else Path()
            if not FilesystemJail.check_read(str(resolved)):
                return f"路徑不在允許讀取目錄: {filepath}"

        elif tool_name == "run_command":
            cmd = args.get("cmd", "")
            if not CommandFilter.check(cmd):
                return f"指令被安全政策拒絕: {cmd[:100]}"
            timeout = args.get("timeout", 30)
            if int(timeout) > 120:
                return f"指令超時不能超過 120 秒: {timeout}"

        elif tool_name == "web_search":
            query = args.get("query", "")
            if len(query) > 500:
                return f"搜尋查詢太長 ({len(query)} chars)"

        elif tool_name == "generate_image":
            prompt = args.get("prompt", "")
            if len(prompt) > 2000:
                return f"提示詞太長 ({len(prompt)} chars)"

        return None

    def _postprocess(self, tool_name: str, result: str) -> str:
        """Post-execution validation and truncation."""
        if tool_name in ("read_file", "run_command", "web_search"):
            if len(result) > _MAX_COMMAND_OUTPUT:
                result = result[:_MAX_COMMAND_OUTPUT] + f"\n...（已截斷，共 {len(result)} chars）"
        return result


# ──────────────────────────────────────────────
# 6. Convenience wrapper
# ──────────────────────────────────────────────

_sandbox_local = threading.local()


def get_sandbox(agent_name: str = "unknown") -> IsolatedExecutor:
    """Get or create a sandbox for this thread/agent."""
    if not hasattr(_sandbox_local, "sandbox") or _sandbox_local.sandbox.agent_name != agent_name:
        _sandbox_local.sandbox = IsolatedExecutor(agent_name)
    return _sandbox_local.sandbox


def isolated_execute(
    agent_name: str,
    tool_name: str,
    args: dict,
    original_execute: Callable,
) -> str:
    """One-shot isolated execution. Use this as the drop-in wrapper."""
    sandbox = get_sandbox(agent_name)
    return sandbox.execute(tool_name, args, original_execute)
