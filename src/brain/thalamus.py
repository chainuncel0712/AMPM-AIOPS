"""丘腦 - 判斷使用者意圖，決定是否呼叫工具"""
from skeleton.base_organ import BaseOrgan

class Thalamus(BaseOrgan):
    def __init__(self):
        super().__init__("thalamus")

    def route(self, user_msg: str, tool_list: list) -> dict:
        """分析訊息，回傳決策：是否用工具、用哪個工具"""
        # 簡單的意圖判斷（未來可換成 LLM 判斷，但這層保持輕量）
        search_keywords = ["查", "搜", "找", "搜尋", "搜索", "search",
                           "價格", "天氣", "新聞", "股價", "比特幣", "最新"]
        if any(kw in user_msg for kw in search_keywords):
            return {"use_tool": True, "tool": "web_search", "params": user_msg}
        return {"use_tool": False, "tool": None, "params": None}

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
