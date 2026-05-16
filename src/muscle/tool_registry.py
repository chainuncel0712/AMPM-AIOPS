"""肌肉 - 工具注册表"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan

class ToolRegistry(BaseOrgan):
    def __init__(self, tools_system):
        super().__init__("tool_registry")
        self.tools = tools_system

    def list_tools(self) -> dict:
        return self.tools.list_all()

    def get_tool(self, name: str) -> dict:
        return self.tools.registry.get(name, {})

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "count": len(self.tools.registry)}
