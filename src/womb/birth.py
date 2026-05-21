"""子宫 - 生出新的子代理"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan
from agents import AgentManager

class Birth(BaseOrgan):
    def __init__(self, agent_manager: AgentManager):
        super().__init__("birth")
        self.agent_manager = agent_manager

    def deliver(self, name: str, role: str, parent_id: str = None, tools: list = None) -> dict:
        """生出一個子代理"""
        agent = self.agent_manager.create_agent(name=name, role=role, parent_id=parent_id)
        if agent:
            return {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "tools": tools or [],
                "status": "born",
            }
        return {"error": "failed to create agent"}

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
