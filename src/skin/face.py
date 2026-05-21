"""脸 - 回覆格式控製"""
from skeleton.base_organ import BaseOrgan

class Face(BaseOrgan):
    def __init__(self):
        super().__init__("face")

    def format_reply(self, raw: str, thought: str = "") -> str:
        """给回覆穿上表情"""
        if thought:
            return f"💭 {thought}\n\n{raw}"
        return raw

    def format_tool_result(self, tool_name: str, result: str) -> str:
        return f"🔧 使用工具 [{tool_name}]：\n{result}"

    def error(self, msg: str) -> str:
        return f"⚠️ {msg}"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
