"""
眼睛 - 視覺感測器 (V2 組裝大師相容版)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skeleton.base_organ import BaseOrgan


class Eye(BaseOrgan):
    def __init__(self):
        super().__init__("eye")
        self.searcher = None       # 延遲載入
        self._ready = False
        self.connected_organs = {}
    
    def init(self) -> bool:
        """組裝大師用初始化 - 延遲載入 WebSearch"""
        try:
            from web.search import WebSearch
            self.searcher = WebSearch()
            self._ready = True
            print(f"  ✅ [eye] WebSearch 已載入")
            return True
        except Exception as e:
            print(f"  ⚠️ [eye] WebSearch 載入失敗: {e}")
            self._ready = False
            return False
    
    def see(self, query: str) -> str:
        if not self.searcher:
            return "[eye] 搜尋引擎未就緒"
        if not query or len(query) < 2:
            return ""
        try:
            return self.searcher.search(query)[:3000]
        except Exception as e:
            return f"搜尋錯誤: {e}"
    
    def run(self, input_data=None):
        """執行搜尋"""
        if input_data:
            return self.see(str(input_data))
        return ""
    
    def connect(self, other):
        """連接其他零件（例如 web_search_plugin）"""
        self.connected_organs[other.name] = other
        # 如果對方有 search 方法，用它當 searcher
        if hasattr(other, 'search'):
            self.searcher = other
        print(f"🔗 [eye] → [{other.name}] 連接成功")
        return True
    
    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "ready": self._ready,
            "has_searcher": self.searcher is not None,
        }
    
    def report(self) -> str:
        s = "✅" if self.is_alive() else "❌"
        r = "🟢" if self._ready else "🔴"
        w = "🔍" if self.searcher else "⬜"
        return f"[eye] {s} {r} {w} | 搜尋: {'有' if self.searcher else '無'}"
