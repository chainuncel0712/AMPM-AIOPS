"""自我修復 — 決策層：判斷要修什麼，不負責執行"""
from skeleton.base_organ import BaseOrgan


class SelfHeal(BaseOrgan):
    def __init__(self, orchestrator=None):
        super().__init__("self_heal")
        self.heal_count = 0
        self.orchestrator = orchestrator

    def heal(self, organ_name: str, issue: str) -> str:
        """決定修復方式，委託给 RepairOrchestrator 執行"""
        self.heal_count += 1
        if self.orchestrator:
            result = self.orchestrator.execute("restart_service", {
                "service": "ampm-brain.service"
            })
            if result.get("success"):
                return f"已修復 {organ_name}：{result.get('action', '重啟服務')}"
            return f"修復失敗：{result.get('error', '未知錯誤')}"
        return f"修復決策：{organ_name} 需要修復（{issue}），但無修復執行器"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "heal_count": self.heal_count}
