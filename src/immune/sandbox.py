"""
Sandbox Execution v1 — 隔離執行、資源限製、清理
在受限環境中安全執行程式碼/命令，防止系統破壞
"""
import os
import sys
import time
import json
import signal
import tempfile
import subprocess
import resource
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class Sandbox(BaseOrgan):
    """
    沙箱執行環境 — 隔離、限資源、限時、限網路
    僅執行已驗證的工具，不允許任意程式碼
    """

    DEFAULT_LIMITS = {
        "timeout": 30,           # 秒
        "max_memory_mb": 256,    # MB
        "max_output_bytes": 1024 * 1024,  # 1MB
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allow_network": False,
        "allow_file_write": False,
        "allowed_dirs": [tempfile.gettempdir()],
    }

    def __init__(self, limits: Dict = None):
        super().__init__("sandbox")
        self._limits = {**self.DEFAULT_LIMITS, **(limits or {})}
        self._execution_count = 0
        self._failure_count = 0
        self._work_dir = tempfile.mkdtemp(prefix="ampm_sandbox_")
        self._allowed_commands = {
            "python": ["python3", "-c"],
            "bash": ["bash", "-c"],
            "node": ["node", "-e"],
        }

    # ── 執行 ────────────────────────────────────────────────

    def execute(self, tool_name: str, code: str, lang: str = "python", params: Dict = None) -> Dict:
        """在沙箱中執行程式碼"""
        self._execution_count += 1
        result = {
            "tool": tool_name,
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "duration_ms": 0,
            "sandbox": True,
        }

        # 前置檢查
        precheck = self._precheck(code, lang)
        if not precheck["allowed"]:
            result["error"] = precheck["reason"]
            result["blocked"] = True
            self._failure_count += 1
            return result

        # 準備執行
        cmd_base = self._allowed_commands.get(lang, ["python3", "-c"])
        cmd = cmd_base + [code]

        env = os.environ.copy()
        env["SANDBOX_MODE"] = "1"
        if not self._limits["allow_network"]:
            env["http_proxy"] = ""
            env["https_proxy"] = ""
            env["no_proxy"] = "*"

        start = time.time()

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self._work_dir,
                preexec_fn=self._setup_resource_limits if sys.platform != "win32" else None,
            )

            try:
                stdout, stderr = proc.communicate(
                    timeout=self._limits["timeout"]
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result["error"] = f"執行超時 ({self._limits['timeout']}s)"
                result["timeout"] = True
                self._failure_count += 1
                elapsed = (time.time() - start) * 1000
                result["duration_ms"] = elapsed
                result["stdout"] = stdout.decode("utf-8", errors="replace")[:self._limits["max_output_bytes"]]
                result["stderr"] = stderr.decode("utf-8", errors="replace")[:self._limits["max_output_bytes"]]
                return result

            elapsed = (time.time() - start) * 1000
            result["duration_ms"] = elapsed
            result["exit_code"] = proc.returncode
            result["stdout"] = stdout.decode("utf-8", errors="replace")[:self._limits["max_output_bytes"]]
            result["stderr"] = stderr.decode("utf-8", errors="replace")[:self._limits["max_output_bytes"]]
            result["success"] = proc.returncode == 0

            if proc.returncode != 0:
                self._failure_count += 1

        except Exception as e:
            result["error"] = str(e)
            self._failure_count += 1

        self._cleanup_work_dir()
        return result

    def _precheck(self, code: str, lang: str) -> Dict:
        """執行前安全檢查"""
        # 檢查語言是否允許
        if lang not in self._allowed_commands:
            return {"allowed": False, "reason": f"不允許的語言: {lang}"}

        code_lower = code.lower()

        # 禁止的模式（即使在沙箱中也不允許）
        forbidden = [
            "import os", "import subprocess", "import shutil",
            "os.system", "os.popen", "os.exec", "os.spawn",
            "subprocess.Popen", "subprocess.call", "subprocess.run",
            "import socket", "socket.connect",
            "__import__", "eval(", "exec(",
            "open(", "file(",
            "import ctypes", "import multiprocessing",
            "rm -rf", "mkfs.", "dd if=",
            ">/dev/", ">/etc/",
        ]
        for pattern in forbidden:
            if pattern in code_lower:
                return {"allowed": False, "reason": f"偵測到禁止模式: {pattern}"}

        # 長度限製
        if len(code) > 50000:
            return {"allowed": False, "reason": "程式碼過長"}

        return {"allowed": True}

    def _setup_resource_limits(self):
        """設定資源限製（POSIX only）"""
        try:
            mem_bytes = self._limits["max_memory_mb"] * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            resource.setrlimit(resource.RLIMIT_CPU, (self._limits["timeout"], self._limits["timeout"]))
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))
            if not self._limits["allow_file_write"]:
                resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        except Exception:
            pass

    def _cleanup_work_dir(self):
        """清理暫存目錄"""
        try:
            for item in Path(self._work_dir).iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                except Exception:
                    pass
        except Exception:
            pass

    # ── 安全命令執行 ───────────────────────────────────────

    def safe_command(self, command: str, timeout: int = None) -> Dict:
        """安全的系統命令執行（僅允許白名單命令）"""
        timeout = timeout or self._limits["timeout"]

        # 白名單命令
        allowed_prefixes = [
            "ls", "pwd", "cat", "head", "tail", "wc",
            "grep", "find", "du", "df", "free",
            "echo", "date", "whoami", "uname",
            "git status", "git log", "git diff", "git branch",
            "python3 --version", "pip list", "npm list",
            "docker ps", "docker images",
            "curl -I", "wget --spider",
        ]

        cmd_lower = command.lower().strip()
        if not any(cmd_lower.startswith(prefix) for prefix in allowed_prefixes):
            return {
                "success": False,
                "error": "命令不在白名單中",
                "stdout": "",
                "stderr": "",
                "allowed_prefixes": allowed_prefixes,
            }

        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True,
                timeout=timeout,
                cwd=self._work_dir,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[-10000:],
                "stderr": result.stderr[-5000:],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout", "stdout": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": ""}

    # ── 限製管理 ───────────────────────────────────────────

    def set_limits(self, **kwargs):
        self._limits.update(kwargs)

    def get_limits(self) -> Dict:
        return dict(self._limits)

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "executions": self._execution_count,
            "failures": self._failure_count,
            "success_rate": round((1 - self._failure_count / max(self._execution_count, 1)) * 100, 1),
            "limits": self._limits,
            "work_dir": self._work_dir,
        }
