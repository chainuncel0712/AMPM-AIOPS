"""
工具執行模組 - 處理工具調用和審批
"""

class ToolExecutor:
    def __init__(self, tools_system):
        self.tools = tools_system
        self.pending_approval = None
    
    def execute(self, tool_name: str, params: dict) -> str:
        """執行工具"""
        if tool_name == "shell" and self.tools.registry.get("shell", {}).get("requires_approval"):
            self.pending_approval = {"tool": tool_name, "params": params}
            return f"⚠️ 需要批准執行指令：{params.get('cmd', '')}\n請回覆「批准」或「拒絕」"
        
        result = self.tools.execute(tool_name, params)
        return result
    
    def approve(self) -> str:
        """批准待執行的工具"""
        if self.pending_approval:
            tool = self.pending_approval["tool"]
            params = self.pending_approval["params"]
            self.pending_approval = None
            return self.tools.execute(tool, params)
        return "沒有待批准的任務"
    
    def reject(self) -> str:
        """拒絕待執行的工具"""
        if self.pending_approval:
            self.pending_approval = None
            return "已拒絕執行"
        return "沒有待拒絕的任務"
