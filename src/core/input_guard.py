"""
輸入安全器官 — 使用者輸入風控閘
攔截危險指令、SQL injection、XSS、prompt injection。
"""
import re
from typing import Dict, List

from skeleton.base_organ import BaseOrgan


class InputGuard(BaseOrgan):
    """
    輸入安全閘 — 使用者輸入過濾

    檢查規則：
    1. 作業系統破壞指令
    2. SQL injection
    3. Prompt injection (試圖覆蓋系統提示)
    4. 超過長度限制的輸入
    5. 重複 flood 攻擊
    """

    # 危險指令模式
    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf\s+/", "OS 破壞指令: rm -rf /"),
        (r"sudo\s+rm", "OS 破壞指令: sudo rm"),
        (r"mkfs\.", "OS 破壞指令: mkfs"),
        (r"dd\s+if=", "OS 破壞指令: dd"),
        (r">\s*/dev/sd", "OS 破壞指令: 寫入磁碟"),
        (r"chmod\s+777\s+/", "OS 破壞指令: chmod 777 /"),
        (r"wget.*\|.*sh", "OS 破壞指令: pipe to sh"),
        (r"curl.*\|.*bash", "OS 破壞指令: pipe to bash"),
    ]

    # SQL injection 模式
    SQL_PATTERNS = [
        (r"(?i)(DROP|TRUNCATE)\s+(TABLE|DATABASE)", "SQL injection: DROP"),
        (r"(?i)DELETE\s+FROM\s+\w+", "SQL injection: DELETE"),
        (r"(?i)INSERT\s+INTO\s+\w+.*VALUES", "SQL injection: INSERT"),
        (r"(?i)UNION\s+SELECT", "SQL injection: UNION SELECT"),
        (r"(?i)1\s*=\s*1\s*--", "SQL injection: tautology"),
        (r"(?i)'\s*OR\s*'\d+'\s*=\s*'\d+", "SQL injection: OR injection"),
    ]

    # Prompt injection 模式
    PROMPT_INJECT_PATTERNS = [
        (r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+instructions", "Prompt injection: 覆蓋指令"),
        (r"(?i)you\s+are\s+now\s+\w+\s+mode", "Prompt injection: 角色切換"),
        (r"(?i)forget\s+everything", "Prompt injection: 清除記憶"),
        (r"(?i)system\s*prompt\s*:", "Prompt injection: 注入系統提示"),
        (r"(?i)pretend\s+you\s+are", "Prompt injection: 偽裝"),
    ]

    def __init__(self, max_input_length: int = 5000):
        super().__init__("input_guard")
        self.max_input_length = max_input_length
        self.blocked_count = 0
        self.recent_inputs: List[str] = []
        self.flood_threshold = 5  # 5 秒內超過此數量視為 flood

    # =========================================
    # 主要檢查
    # =========================================

    def check(self, user_input: str) -> Dict:
        """
        檢查使用者輸入是否安全。
        回傳: {"safe": bool, "reason": str, "severity": "low"|"medium"|"high"}
        """
        if not user_input or not isinstance(user_input, str):
            return {"safe": True, "reason": "", "severity": "low"}

        # 1. 長度檢查
        if len(user_input) > self.max_input_length:
            self.blocked_count += 1
            return {
                "safe": False, "severity": "medium",
                "reason": f"輸入過長 ({len(user_input)} > {self.max_input_length})",
            }

        # 2. 作業系統破壞指令
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, user_input):
                self.blocked_count += 1
                return {"safe": False, "severity": "high", "reason": reason}

        # 3. SQL injection
        for pattern, reason in self.SQL_PATTERNS:
            if re.search(pattern, user_input):
                self.blocked_count += 1
                return {"safe": False, "severity": "high", "reason": reason}

        # 4. Prompt injection
        for pattern, reason in self.PROMPT_INJECT_PATTERNS:
            if re.search(pattern, user_input):
                self.blocked_count += 1
                return {"safe": False, "severity": "medium", "reason": reason}

        # 5. Flood 檢查
        if self._check_flood(user_input):
            self.blocked_count += 1
            return {"safe": False, "severity": "low", "reason": "輸入過於頻繁，請稍後"}

        return {"safe": True, "reason": "", "severity": "low"}

    def _check_flood(self, user_input: str) -> bool:
        """檢查是否 flood（5 秒內重複相同輸入超過 3 次）"""
        import time
        now = time.time()
        # 簡化：檢查最近輸入中是否有完全相同的前綴
        prefix = user_input[:30]
        count = sum(1 for inp in self.recent_inputs if inp[:30] == prefix)
        self.recent_inputs.append(user_input)
        if len(self.recent_inputs) > 10:
            self.recent_inputs = self.recent_inputs[-10:]
        return count >= 3

    # =========================================
    # 安全過濾（不攔截，只清理）
    # =========================================

    def sanitize(self, user_input: str) -> str:
        """
        清理輸入（不攔截，只過濾有風險的字元）。
        用於讓輸入通過但移除潛在危險內容。
        """
        if not user_input:
            return user_input

        # 移除 Null byte injection
        user_input = user_input.replace("\x00", "")

        # 轉義 HTML（防 XSS）
        user_input = user_input.replace("<script", "&lt;script")
        user_input = user_input.replace("javascript:", "javascript&#58;")

        # 限制長度
        if len(user_input) > self.max_input_length:
            user_input = user_input[:self.max_input_length]

        return user_input

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "blocked_count": self.blocked_count,
        }
