"""
Immune Guard v1 — 輸入/輸出消毒、速率限製、存取控製
增強型安全層，做為黑曜的免疫系統第一線
"""
import re
import sys
import time
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class Guard(BaseOrgan):
    """安全守衛 — 過濾、消毒、限流、權限控製"""

    # 內建危險模式（可自訂擴充）
    DEFAULT_BLOCKED_PATTERNS = [
        (r"rm\s+-rf\s+/", "禁止遞迴刪除根目錄"),
        (r"mkfs\.", "禁止格式化磁碟"),
        (r"dd\s+if=", "禁止直接寫入裝置"),
        (r">\s*/dev/sd[a-z]", "禁止覆寫磁碟裝置"),
        (r"chmod\s+777\s+/", "禁止開放全系統權限"),
        (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "禁止 fork bomb"),
        (r"DROP\s+TABLE", "禁止 SQL 刪表"),
        (r"DELETE\s+FROM.*WHERE\s+1=1", "禁止 SQL 全刪"),
        (r"eval\s*\(.*__import__", "禁止動態導入"),
        (r"exec\s*\(.*compile", "禁止執行編譯代碼"),
        (r"subprocess\.Popen.*shell\s*=\s*True", "禁止 shell 註入"),
        (r"os\.system\s*\(.*rm\s+-rf", "禁止系統刪除命令"),
        (r"curl.*\|\s*(ba)?sh", "禁止 curl pipe shell"),
        (r"wget.*-O\s*-\s*\|\s*sh", "禁止 wget pipe shell"),
        (r"__import__\s*\(\s*['\"]os['\"]\s*\)", "禁止動態導入 os"),
        (r"lambda\s*.*:\s*.*\bexec\b", "禁止 lambda exec"),
    ]

    # 輸出自動消毒規則
    OUTPUT_SANITIZE_PATTERNS = [
        (r'(sk-[a-zA-Z0-9]{20,})', '[SECRET_REDACTED]'),
        (r'(api[_-]?key[=:]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?)', '[API_KEY_REDACTED]'),
        (r'(token[=:]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?)', '[TOKEN_REDACTED]'),
        (r'(password[=:]\s*["\']?\S+["\']?)', '[PASSWORD_REDACTED]'),
        (r'(-----BEGIN.*PRIVATE KEY-----[\s\S]*?-----END.*PRIVATE KEY-----)', '[PRIVATE_KEY_REDACTED]'),
    ]

    def __init__(self):
        super().__init__("guard")
        self._blocked_patterns = list(self.DEFAULT_BLOCKED_PATTERNS)
        self._output_sanitize = list(self.OUTPUT_SANITIZE_PATTERNS)
        # 速率限製
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._rate_limit_window = 60  # 秒
        self._rate_limit_max = 30     # 每窗口最大請求數
        # 攔截計數
        self.blocked_count = 0
        self.sanitized_count = 0
        self.rate_limited_count = 0
        # 白名單
        self._allowed_paths: Set[str] = set()
        self._allowed_commands: Set[str] = set()

    # ── 輸入掃描 ───────────────────────────────────────────

    def scan_input(self, user_input: str, user_id: str = "default") -> Dict:
        """掃描使用者輸入，多層檢查"""
        # 1. 速率檢查
        if not self._check_rate(user_id):
            self.rate_limited_count += 1
            return {"allowed": False, "reason": "速率限製", "risk": "high"}

        # 2. 空白輸入
        if not user_input or not user_input.strip():
            return {"allowed": True}

        # 3. 長度檢查
        if len(user_input) > 100000:
            return {"allowed": False, "reason": "輸入過長", "risk": "high"}

        # 4. 模式匹配
        for pattern, reason in self._blocked_patterns:
            if isinstance(pattern, re.Pattern):
                if pattern.search(user_input.lower()):
                    self.blocked_count += 1
                    return {"allowed": False, "reason": reason, "risk": "critical", "matched": pattern.pattern}
            elif re.search(pattern, user_input, re.IGNORECASE):
                self.blocked_count += 1
                return {"allowed": False, "reason": reason, "risk": "critical", "matched": pattern}

        # 5. 路徑檢查
        if not self._validate_paths(user_input):
            self.blocked_count += 1
            return {"allowed": False, "reason": "存取禁止路徑", "risk": "high"}

        return {"allowed": True, "risk": "low"}

    def _check_rate(self, user_id: str) -> bool:
        now = time.time()
        timestamps = self._rate_limits[user_id]
        # 清理過期記錄
        self._rate_limits[user_id] = [t for t in timestamps if now - t < self._rate_limit_window]
        if len(self._rate_limits[user_id]) >= self._rate_limit_max:
            return False
        self._rate_limits[user_id].append(now)
        return True

    def _validate_paths(self, text: str) -> bool:
        """檢查是否包含禁止的檔案系統路徑"""
        forbidden = [
            "/etc/passwd", "/etc/shadow", "/root/", "/var/log/",
            ".ssh/id_rsa", ".env", "config.yml",
        ]
        text_lower = text.lower()
        for path in forbidden:
            if path.lower() in text_lower:
                if path not in self._allowed_paths:
                    return False
        return True

    # ── 輸出消毒 ───────────────────────────────────────────

    def sanitize_output(self, output: str) -> Tuple[str, int]:
        """消毒輸出，移除敏感資訊"""
        count = 0
        for pattern, replacement in self._output_sanitize:
            new_output, n = re.subn(pattern, replacement, str(output))
            if n > 0:
                count += n
                output = new_output
        self.sanitized_count += count
        return output, count

    # ── 白名單管理 ─────────────────────────────────────────

    def whitelist_path(self, path: str):
        self._allowed_paths.add(path)

    def whitelist_command(self, cmd: str):
        self._allowed_commands.add(cmd)

    def add_blocked_pattern(self, pattern: str, reason: str):
        self._blocked_patterns.append((pattern, reason))

    # ── 存取控製 ───────────────────────────────────────────

    def check_permission(self, user_id: str, resource: str, action: str = "read") -> bool:
        """檢查使用者對資源的權限
        支援角色：admin, user, agent, readonly
        """
        if resource.startswith("/system/") and action != "read":
            return False  # 系統路徑唯讀
        if resource.startswith("/admin/") and user_id not in ("admin", "system"):
            return False
        return True

    # ── 審計日誌 ───────────────────────────────────────────

    def log_block(self, reason: str, user_input: str, user_id: str):
        entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "reason": reason,
            "input_hash": hashlib.sha256(user_input.encode()).hexdigest()[:16],
        }
        return entry

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "blocked": self.blocked_count,
            "sanitized": self.sanitized_count,
            "rate_limited": self.rate_limited_count,
            "patterns": len(self._blocked_patterns),
            "whitelist_paths": len(self._allowed_paths),
        }
