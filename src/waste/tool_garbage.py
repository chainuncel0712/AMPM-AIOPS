"""排泄 - 淘汰无用工具"""
from skeleton.base_organ import BaseOrgan

class ToolGarbage(BaseOrgan):
    def __init__(self, tools_system):
        super().__init__("tool_garbage")
        self.tools = tools_system

    def clean(self, days: int = 30) -> str:
        """清理从未使用过的工具"""
        unused = [name for name, info in self.tools.registry.items()
                  if info.get("use_count", 0) == 0]
        if unused:
            for name in unused:
                self.tools.registry.pop(name, None)
            self.tools._save_registry()
            return f"已淘汰工具：{', '.join(unused)}"
        return "没有需要淘汰的工具"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
