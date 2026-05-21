"""托兒所 - 管理所有子代理的状态"""
from skeleton.base_organ import BaseOrgan

class Nursery(BaseOrgan):
    def __init__(self):
        super().__init__("nursery")
        self._agents = {}

    def register(self, child_id: str, info: dict):
        self._agents[child_id] = info

    def unregister(self, child_id: str):
        self._agents.pop(child_id, None)

    def list_children(self) -> list:
        return [{"id": cid, "name": info.get("name"), "role": info.get("role")}
                for cid, info in self._agents.items()]

    def clean_orphans(self, placenta):
        """清理胎盘里已经沒有但在托兒所還存在的孤兒"""
        for cid in list(self._agents.keys()):
            if cid not in placenta._children:
                self.unregister(cid)

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "count": len(self._agents)}
