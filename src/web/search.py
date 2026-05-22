"""
網頁搜尋工具 - 讓黑曜能夠上網查資料
"""

from ddgs import DDGS

class WebSearch:
    def __init__(self):
        self.ddgs = DDGS()
    
    def search(self, query: str, max_results: int = 5) -> str:
        """搜尋網頁並返回結果"""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"{i}. {r['title']}")
                output.append(f"   {r['body'][:200]}")
                output.append(f"   🔗 {r['href']}")
                output.append("")
            return "\n".join(output) if output else f"沒有找到關於「{query}」的結果"
        except Exception as e:
            return f"搜尋失敗: {e}"
    
    def search_news(self, query: str, max_results: int = 3) -> str:
        """搜尋新聞"""
        try:
            results = self.ddgs.news(query, max_results=max_results)
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"{i}. {r['title']}")
                output.append(f"   {r['body'][:150]}")
                output.append(f"   📅 {r.get('date', '未知')}")
                output.append("")
            return "\n".join(output) if output else f"沒有找到關於「{query}」的新聞"
        except Exception as e:
            return f"搜尋失敗: {e}"
