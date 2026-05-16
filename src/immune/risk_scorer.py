"""
Risk Scorer v1 — 工具執行風險評估與閾值攔截
在執行前對每個工具呼叫進行風險評分，超過閾值則攔截
"""
import sys
import re
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class RiskScorer(BaseOrgan):
    """
    風險評分器 — 多維度風險評估
    分數範圍: 0 (安全) ~ 100 (極危險)
    """

    # 風險權重
    DEFAULT_WEIGHTS = {
        "system_access": 30,    # 系統命令/檔案存取
        "network_call": 10,     # 對外網路請求
        "data_modify": 25,      # 資料修改操作
        "resource_heavy": 15,   # 資源密集型操作
        "external_input": 10,   # 使用外部輸入
        "recursive_risk": 10,   # 遞迴呼叫風險
    }

    # 高風險關鍵字/模式 (分數加權)
    RISK_PATTERNS = {
        "critical": [
            (r"\brm\b", 40),
            (r"\bdelete\b", 35),
            (r"\bDROP\b", 50),
            (r"\bformat\b", 45),
            (r"\bmkfs\b", 50),
            (r"\bsudo\b", 40),
            (r"\bchmod\b", 35),
            (r"\bchown\b", 35),
            (r"\bmount\b", 30),
            (r"\biptables\b", 40),
            (r"\bsystemctl\b", 30),
            (r"\breboot\b", 45),
            (r"\bshutdown\b", 45),
        ],
        "high": [
            (r"\bwrite\b", 20),
            (r"\bsend\b", 15),
            (r"\bdeploy\b", 25),
            (r"\binstall\b", 20),
            (r"\buninstall\b", 25),
            (r"\bexecute\b", 20),
            (r"\brun\b", 15),
            (r"\bcommit\b", 20),
            (r"\bpush\b", 15),
        ],
        "medium": [
            (r"\bdownload\b", 10),
            (r"\bfetch\b", 10),
            (r"\bscan\b", 10),
            (r"\bquery\b", 5),
            (r"\bsearch\b", 5),
        ],
    }

    def __init__(self, threshold: int = 60):
        super().__init__("risk_scorer")
        self._threshold = threshold
        self._weights = dict(self.DEFAULT_WEIGHTS)
        self._risk_history: List[Dict] = []
        self._risk_scores: Dict[str, float] = {}

    # ── 風險評估 ───────────────────────────────────────────

    def evaluate(self, tool_name: str, params: Dict = None, context: Dict = None) -> Dict:
        """評估工具執行的風險"""
        params = params or {}
        context = context or {}

        scores = {
            "system_access": self._score_system_access(tool_name, params),
            "network_call": self._score_network(tool_name, params),
            "data_modify": self._score_data_modify(tool_name, params),
            "resource_heavy": self._score_resource(tool_name, params),
            "external_input": self._score_external_input(params),
            "recursive_risk": self._score_recursion(tool_name, context),
        }

        # 加權總分
        total = sum(scores[k] * self._weights.get(k, 0) for k in scores) / sum(self._weights.values())

        # 關鍵字加權
        keyword_bonus = self._score_keywords(tool_name, params)
        total += keyword_bonus
        total = min(total, 100)

        self._risk_history.append({
            "tool": tool_name,
            "score": total,
            "breakdown": scores,
            "timestamp": __import__('time').time(),
        })
        self._risk_scores[tool_name] = total

        result = {
            "tool": tool_name,
            "risk_score": round(total, 1),
            "risk_level": self._level(total),
            "allowed": total < self._threshold,
            "breakdown": scores,
        }

        if total >= self._threshold:
            result["blocked_reason"] = f"風險分數 {total:.0f} ≥ 閾值 {self._threshold}"

        return result

    def _level(self, score: float) -> str:
        if score < 20:
            return "safe"
        elif score < 40:
            return "low"
        elif score < 60:
            return "medium"
        elif score < 80:
            return "high"
        return "critical"

    # ── 各維度評分 ─────────────────────────────────────────

    def _score_system_access(self, tool_name: str, params: Dict) -> float:
        score = 0.0
        params_str = str(params).lower()
        combined = (tool_name + " " + params_str).lower()

        sys_indicators = [
            "shell", "bash", "subprocess", "os.system", "popen",
            "exec", "eval", "compile", "__import__",
            "rm", "mkdir", "chmod", "chown", "sudo",
            "/etc/", "/root/", "/var/", "/proc/", "/dev/",
        ]
        matches = sum(1 for ind in sys_indicators if ind in combined)
        score = min(matches * 15, 100)
        return score

    def _score_network(self, tool_name: str, params: Dict) -> float:
        score = 0.0
        combined = (tool_name + " " + str(params)).lower()

        net_indicators = [
            "http://", "https://", "curl", "wget", "request",
            "socket", "connect", "fetch", "api",
        ]
        matches = sum(1 for ind in net_indicators if ind in combined)

        # 檢查是否為內部 URL
        if any(domain in combined for domain in ["localhost", "127.0.0.1", "internal"]):
            score = min(matches * 5, 30)
        else:
            score = min(matches * 10, 60)

        return score

    def _score_data_modify(self, tool_name: str, params: Dict) -> float:
        score = 0.0
        combined = (tool_name + " " + str(params)).lower()

        modify_indicators = [
            "write", "delete", "update", "insert", "create",
            "drop", "alter", "truncate", "replace", "remove",
            "save", "store", "commit",
        ]
        matches = sum(1 for ind in modify_indicators if ind in combined)
        score = min(matches * 12, 100)

        # POST/PUT/DELETE 方法加權
        method = str(params.get("method", params.get("_method", ""))).upper()
        if method in ("POST", "PUT", "PATCH"):
            score += 15
        elif method == "DELETE":
            score += 25

        return min(score, 100)

    def _score_resource(self, tool_name: str, params: Dict) -> float:
        score = 0.0

        timeout = params.get("timeout", params.get("_timeout", 30))
        if isinstance(timeout, (int, float)) and timeout > 300:
            score += 30

        limit = params.get("limit", params.get("_limit", 10))
        if isinstance(limit, (int, float)) and limit > 1000:
            score += 20

        combined = (tool_name + " " + str(params)).lower()
        heavy_indicators = ["download", "upload", "large", "batch", "bulk", "all"]
        matches = sum(1 for ind in heavy_indicators if ind in combined)
        score += min(matches * 15, 45)

        return min(score, 100)

    def _score_external_input(self, params: Dict) -> float:
        score = 0.0
        params_str = str(params)

        # 檢查是否存在未消毒的用戶輸入
        dangerous_chars = [";", "&&", "||", "|", "$(", "`", "$", ">", "<"]
        if any(c in params_str for c in dangerous_chars):
            score += 30

        # 檢查 injection 模式
        injection_patterns = [
            r"\bunion\b.*\bselect\b",
            r"<script",
            r"\.\.\/",
            r"\/etc\/passwd",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, params_str, re.IGNORECASE):
                score += 40
                break

        return min(score, 100)

    def _score_recursion(self, tool_name: str, context: Dict) -> float:
        call_count = context.get("call_count", {}).get(tool_name, 0)
        if call_count > 10:
            return 80
        elif call_count > 5:
            return 50
        elif call_count > 3:
            return 25
        return 0

    def _score_keywords(self, tool_name: str, params: Dict) -> float:
        combined = (tool_name + " " + str(params)).lower()
        bonus = 0.0

        for pattern, weight in self.RISK_PATTERNS.get("critical", []):
            if re.search(pattern, combined, re.IGNORECASE):
                bonus += weight * 0.5
        for pattern, weight in self.RISK_PATTERNS.get("high", []):
            if re.search(pattern, combined, re.IGNORECASE):
                bonus += weight * 0.3
        for pattern, weight in self.RISK_PATTERNS.get("medium", []):
            if re.search(pattern, combined, re.IGNORECASE):
                bonus += weight * 0.1

        return min(bonus, 40)

    # ── 閾值管理 ───────────────────────────────────────────

    def set_threshold(self, threshold: int):
        self._threshold = max(0, min(threshold, 100))

    def get_threshold(self) -> int:
        return self._threshold

    def get_risk_profile(self, tool_name: str) -> Optional[Dict]:
        score = self._risk_scores.get(tool_name)
        if score is not None:
            return {"tool": tool_name, "score": score, "level": self._level(score)}
        return None

    def get_high_risk_tools(self) -> List[Dict]:
        return [
            {"tool": name, "score": score, "level": self._level(score)}
            for name, score in self._risk_scores.items()
            if score >= 50
        ]

    def get_history(self, limit: int = 20) -> List[Dict]:
        return self._risk_history[-limit:]

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "threshold": self._threshold,
            "tools_evaluated": len(self._risk_scores),
            "high_risk_tools": len(self.get_high_risk_tools()),
            "evaluations": len(self._risk_history),
        }
