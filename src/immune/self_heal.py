"""自我修复 - 发现问题自动重启或恢复"""
import subprocess
from skeleton.base_organ import BaseOrgan

class SelfHeal(BaseOrgan):
    def __init__(self):
        super().__init__("self_heal")
        self.heal_count = 0

    def heal(self, organ_name: str, issue: str) -> str:
        """尝试修复某个器官"""
        self.heal_count += 1
        try:
            # 最简单的修复方式：重启服务
            subprocess.run(["sudo", "systemctl", "restart", "ampm-brain.service"], capture_output=True)
            return f"已尝试修复 {organ_name}：重启服务"
        except Exception as e:
            return f"修复失败：{e}"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "heal_count": self.heal_count}
