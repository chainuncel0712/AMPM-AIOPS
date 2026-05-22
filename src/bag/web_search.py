"""
包包 - 上網搜尋外掛 (V2 組裝大師相容版)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skeleton.base_organ import BaseOrgan


class WebSearchPlugin(BaseOrgan):
    def __init__(self, searcher=None):
        super().__init__("web_search_plugin")
        self.searcher = searcher
        self._ready = False
        self.connected_organs = {}
    
    def init(self) -> bool:
        """如果沒有 searcher，自動載入"""
        if self.searcher is None:
            try:
                from web.search import WebSearch
                self.searcher = WebSearch()
                print(f"  ✅ [web_search_plugin] 自動載入 WebSearch")
            except Exception as e:
                print(f"  ⚠️ [web_search_plugin] 載入失敗: {e}")
                return False
        self._ready = True
        return True
    
    def search(self, query: str) -> str:
        if self.searcher:
            return self.searcher.search(query)
        return "[web_search_plugin] 搜尋引擎未就緒"
    
    def run(self, input_data=None):
        if input_data:
            return self.search(str(input_data))
        return ""
    
    def connect(self, other):
        self.connected_organs[other.name] = other
        if hasattr(other, 'search') and self.searcher is None:
            self.searcher = other
        return True
    
    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "ready": self._ready,
        }
