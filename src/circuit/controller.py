"""
循環控製器 (Phase 7: 降級為 logging/monitoring only)
=====================================================
此模組已不被主動呼叫。所有安全檢查已移入 ContextAssembler pipeline。
保留僅供監控與紀錄用途，不影響主流程。
"""

from pathlib import Path
from typing import Dict

from .breaker import CircuitBreaker
from .contradiction import ContradictionDetector
from .health import HealthChecker

class CircuitController:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.breaker = CircuitBreaker()
        self.contradiction = ContradictionDetector(self.base_dir)
        self.health = HealthChecker()
        self.total_checks = 0
        self.blocks = 0
    
    def pre_process(self, user_input: str) -> Dict:
        self.total_checks += 1
        health = self.health.check_system()
        if health["status"] == "UNHEALTHY":
            return {"allowed": False, "reason": f"系統異常: {', '.join(health['issues'])}"}
        
        loop_check = self.breaker.check(user_input)
        if not loop_check["allowed"]:
            self.blocks += 1
            return {"allowed": False, "reason": loop_check.get("reason", "blocked")}
        
        return {"allowed": True}
    
    def post_process(self, assistant_response: str) -> Dict:
        contradiction = self.contradiction.check(assistant_response)
        if contradiction.get("is_contradiction"):
            self.blocks += 1
            return {"allowed": False, "reason": f"矛盾偵測: {contradiction.get('old_statement', '')}"}
        return {"allowed": True}
    
    def get_status(self) -> Dict:
        return {
            "total_checks": self.total_checks,
            "blocks": self.blocks,
            "breaker": self.breaker.status()
        }
