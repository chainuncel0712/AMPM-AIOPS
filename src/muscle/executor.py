"""肌肉 - 工具执行器"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan

class MuscularExecutor(BaseOrgan):
    def __init__(self, tools_system):
        super().__init__("muscle")
        self.tools = tools_system

    def execute(self, tool_name: str, params: dict = None) -> str:
        """执行工具，并返回结果"""
        try:
            return self.tools.execute(tool_name, params or {})
        except Exception as e:
            return f"肌肉无法执行：{e}"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "tools_available": list(self.tools.list_all().keys())}
