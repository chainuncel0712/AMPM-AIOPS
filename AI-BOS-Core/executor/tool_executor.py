"""
Tool Executor — 工具執行器
"""


class ToolExecutor:
    def __init__(self, tool_manager):
        self.tool_manager = tool_manager

    def execute(self, tool_name: str, args: dict = None) -> str:
        return self.tool_manager.execute({"action": tool_name, "args": args or {}})
