"""
電子工具書自動化生產線
選題 → 內容生成 → 審核 → 上架 → 銷售追蹤
"""
import json, os, threading, time
from pathlib import Path
from datetime import datetime, timedelta
import hashlib, random

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "publisher"

class EbookPipeline:
    def __init__(self):
        self.books_file = DATA / "ebooks.json"
        self.keywords_file = DATA / "keywords.json"
        self.sales_file = DATA / "ebook_sales.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        for f, default in [(self.books_file, []), (self.keywords_file, []), (self.sales_file, {})]:
            if f.exists():
                try:
                    setattr(self, f.stem, json.loads(f.read_text()))
                except:
                    setattr(self, f.stem, default() if callable(default) else default)
            else:
                setattr(self, f.stem, default() if callable(default) else default)

    def _save(self):
        self.books_file.write_text(json.dumps(self.ebooks, ensure_ascii=False, indent=2))
        self.keywords_file.write_text(json.dumps(self.keywords, ensure_ascii=False, indent=2))
        self.sales_file.write_text(json.dumps(self.ebook_sales, ensure_ascii=False, indent=2))

    # ── 選題 ──
    def suggest_topics(self, count=5):
        """回傳建議選題（目前用樣板，之後可接爬蟲）"""
        topics = [
            "Python 自動化入門", "ChatGPT 提示詞大全",
            "Google Ads 從零開始", "Shopify 開店指南",
            "Excel 数据分析 50 招", "Linux 伺服器管理",
            "AI 繪圖提示詞寶典", "YouTube 頻道經營",
            "Notion 專案管理", "SEO 關鍵字策略"
        ]
        return random.sample(topics, min(count, len(topics)))

    def select_topic(self, topic):
        book_id = hashlib.md5(f"EB-{topic}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.ebooks.append({
            "id": book_id, "topic": topic, "status": "selected",
            "created_at": datetime.now().isoformat(),
            "outline": None, "content": None, "cover": None,
            "platforms": [], "sales_data": {}
        })
        self._save()
        return book_id

    # ── 內容生成 ──
    def generate_outline(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if llm_call:
            prompt = f"為 '{book['topic']}' 這本新手電子工具書產生完整目錄架構，包含 6-8 個章節，每個章節 3-5 個小節。只要目錄，不要內容。"
            outline = llm_call(prompt)
        else:
            outline = f"# {book['topic']} 目錄\n\n## 第一章：什麼是{book['topic']}\n## 第二章：開始前的準備\n## 第三章：基礎操作\n## 第四章：進階技巧\n## 第五章：常見問題\n## 第六章：下一步行動"
        book["outline"] = outline
        book["status"] = "outline_done"
        self._save()
        return outline

    def write_content(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if llm_call:
            prompt = f"根據以下目錄，寫出 '{book['topic']}' 的完整內容。用繁體中文，每章約 500 字，初學者看得懂。\n\n目錄：{book['outline'][:500]}"
            content = llm_call(prompt)
        else:
            content = f"# {book['topic']}\n\n這是 {book['topic']} 的完整內容。"
        book["content"] = content
        book["status"] = "content_done"
        self._save()
        return content

    # ── 審核 ──
    def submit_for_review(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "pending_review"
        book["submitted_at"] = datetime.now().isoformat()
        self._save()
        return f"📖 《{book['topic']}》已送審"

    def approve(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "approved"
        self._save()
        return f"✅ 《{book['topic']}》已批准，可上架"

    def reject(self, book_id, reason):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "rejected"
        book["reject_reason"] = reason
        self._save()
        return f"❌ 《{book['topic']}》已退回：{reason}"

    # ── 上架 ──
    def publish(self, book_id, platforms=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if book["status"] != "approved":
            return "請先審核通過"
        plats = platforms or ["Amazon KDP", "Google Books", "Apple Books", "Kobo", "Readmoo"]
        book["platforms"] = plats
        book["status"] = "published"
        book["published_at"] = datetime.now().isoformat()
        self._save()
        return f"📚 《{book['topic']}》已上架到 {len(plats)} 個平台"

    # ── 銷售追蹤 ──
    def record_sale(self, book_id, platform, amount):
        book = self._find(book_id)
        if not book:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"{book_id}_{today}"
        if key not in self.ebook_sales:
            self.ebook_sales[key] = {"book_id": book_id, "date": today, "sales": {}}
        self.ebook_sales[key]["sales"][platform] = self.ebook_sales[key]["sales"].get(platform, 0) + amount
        self._save()

    def get_sales_summary(self, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        total = 0
        for key, data in self.ebook_sales.items():
            if data["date"] >= cutoff:
                total += sum(data["sales"].values())
        return f"過去 {days} 天銷售總額：${total}"

    def get_pipeline_status(self):
        stages = {"selected": 0, "outline_done": 0, "content_done": 0,
                  "pending_review": 0, "approved": 0, "published": 0}
        for b in self.ebooks:
            s = b.get("status", "selected")
            if s in stages:
                stages[s] += 1
        lines = ["📊 電子工具書生產線狀態："]
        for stage, count in stages.items():
            lines.append(f"  {stage}: {count} 本")
        return "\n".join(lines)

    def _find(self, book_id):
        for b in self.ebooks:
            if b["id"] == book_id:
                return b
        return None

ebook_pipeline = EbookPipeline()
