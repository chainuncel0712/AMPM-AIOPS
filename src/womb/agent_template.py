"""子代理模板 - 定義每個子代理的標準结構"""
from skeleton.base_organ import BaseOrgan

class AgentTemplate(BaseOrgan):
    def __init__(self):
        super().__init__("agent_template")

    def default_config(self, role: str) -> dict:
        """根据角色返回默認配置"""
        templates = {
            "爬虫": {
                "tools": ["http", "web_search"],
                "memory_shared": True,
                "prompt": "你是一個专門爬取网络数据的代理，只返回数据，不闲聊。",
            },
            "市场調查": {
                "tools": ["web_search", "http"],
                "memory_shared": True,
                "prompt": "你是一個市场調查专家，分析市场趋勢并给出报告。",
            },
            "绘图": {
                "tools": ["python_exec"],
                "memory_shared": False,
                "prompt": "你是一個绘图代理，用代码生成图表。",
            },
            "寫作": {
                "tools": [],
                "memory_shared": True,
                "prompt": "你是一個专业寫作代理，根据要求撰寫文章。",
            },
        }
        return templates.get(role, {
            "tools": [],
            "memory_shared": False,
            "prompt": f"你是{role}代理，完成分配的任務。",
        })

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
