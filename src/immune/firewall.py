"""防火墙 - 过滤危险输入"""
from skeleton.base_organ import BaseOrgan

class Firewall(BaseOrgan):
    def __init__(self):
        super().__init__("firewall")
        self._blocked_patterns = [
            "rm -rf /",
            "DROP TABLE",
            "curl.*|.*sh",
        ]

    def scan(self, user_input: str) -> dict:
        """扫描输入，决定放行或阻挡"""
        for pattern in self._blocked_patterns:
            if pattern.lower() in user_input.lower():
                return {"allowed": False, "reason": f"危险模式：{pattern}"}
        return {"allowed": True}

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
