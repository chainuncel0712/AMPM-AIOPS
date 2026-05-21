"""肌肉 - 自創工具能力"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan

class ToolCreator(BaseOrgan):
    def __init__(self, tools_system, call_ai_func):
        super().__init__("tool_creator")
        self.tools = tools_system
        self.call_ai = call_ai_func

    def create_from_need(self, need: str) -> str:
        """根据需求自动創造新工具"""
        return self.tools.create_tool_from_need(need, self.call_ai)

    def learn(self, name: str, description: str, code: str) -> str:
        """直接学一個新工具"""
        return self.tools.learn_tool(name, description, "custom", code)

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
