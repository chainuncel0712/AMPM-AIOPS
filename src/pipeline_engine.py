"""
Publisher Engine — 統一出版循環引擎
=====================================
整合 3 條產線（電子書、童書、AI 客服網站）成一個自動化循環：
  市場調查 → 選題 → 內容生成 → 審核 → 上架 → 銷售追蹤 → 回饋選題

機械組件協作模式：每條產線都是一個機械組件，由引擎統一調度
"""
import json, os, threading, time, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta
from resource_scout import scout as resource_scout
from pipeline_supervisor import supervisor as pipeline_supervisor
from core.image_generator import image_gen
from core.epub_compiler import compiler
from publishers import publisher_manager

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "pipeline"

class CycleLogger:
    def __init__(self):
        self.file = DATA / "cycle_log.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self.log = []
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                self.log = json.loads(self.file.read_text())
            except:
                self.log = []
        else:
            self.log = []

    def _save(self):
        self.file.write_text(json.dumps(self.log, ensure_ascii=False, indent=2))

    def record(self, pipeline: str, stage: str, book_id: str, detail: str = ""):
        entry = {
            "ts": datetime.now().isoformat(),
            "pipeline": pipeline,
            "stage": stage,
            "book_id": book_id,
            "detail": detail,
        }
        self.log.append(entry)
        if len(self.log) > 1000:
            self.log = self.log[-500:]
        self._save()

    def recent(self, n: int = 10) -> list:
        return self.log[-n:]

cycle_log = CycleLogger()

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
        DATA.mkdir(parents=True, exist_ok=True)
        self.books_file.write_text(json.dumps(self.ebooks, ensure_ascii=False, indent=2))
        self.keywords_file.write_text(json.dumps(self.keywords, ensure_ascii=False, indent=2))
        self.sales_file.write_text(json.dumps(self.ebook_sales, ensure_ascii=False, indent=2))

    def trend_analysis(self, llm_call=None) -> list:
        if llm_call:
            prompt = "分析當前繁體中文市場 TOP10 最熱門的電子工具書主題趨勢。列出 5 個主題，每個含主題名稱、目標讀者、市場熱度（1-10）。只要清單。"
            result = llm_call(prompt)
            self.last_trend = result
            self._save()
            return result
        return random.sample([
            "Python 自動化入門", "ChatGPT 提示詞大全",
            "Google Ads 從零開始", "Shopify 開店指南",
            "Excel 数据分析 50 招", "Linux 伺服器管理",
            "AI 繪圖提示詞寶典", "YouTube 頻道經營",
            "Notion 專案管理", "SEO 關鍵字策略"
        ], 5)

    def select_topic(self, topic):
        book_id = hashlib.md5(f"EB-{topic}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.ebooks.append({
            "id": book_id, "topic": topic, "status": "selected",
            "created_at": datetime.now().isoformat(),
            "outline": None, "content": None, "cover": None,
            "platforms": [], "sales_data": {}
        })
        self._save()
        cycle_log.record("ebook", "select_topic", book_id, topic)
        return book_id

    def approve_topic(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if book["status"] != "selected":
            return f"狀態為 {book['status']}，無法審核選題"
        book["status"] = "selected_approved"
        self._save()
        cycle_log.record("ebook", "topic_approved", book_id)
        return f"✅ 《{book['topic']}》選題已通過，進入生成流程"

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
        cycle_log.record("ebook", "generate_outline", book_id)
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
        cycle_log.record("ebook", "write_content", book_id)
        return content

    def compile_epub(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if book.get("epub"):
            return f"📚 《{book['topic']}》EPUB 已存在"
        cover = image_gen.generate_cover(book["topic"])
        interior = []
        for i in range(3):
            ill = image_gen.generate_illustration(f"{book['topic']} 示意圖{i+1}", "vector", book_id, i+1)
            if ill["success"]:
                interior.append(ill["path"])
        epub = compiler.compile_ebook(book, interior, cover["path"] if cover["success"] else None)
        book["epub"] = epub
        book["status"] = "epub_done"
        self._save()
        cycle_log.record("ebook", "compile_epub", book_id, epub.get("epub_id", ""))
        return f"📚 《{book['topic']}》EPUB 編譯完成: {epub.get('epub_id', '')}"

    def submit_for_review(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "pending_review"
        book["submitted_at"] = datetime.now().isoformat()
        self._save()
        cycle_log.record("ebook", "submit_review", book_id)
        return f"📖 《{book['topic']}》已送審"

    def approve(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "approved"
        self._save()
        cycle_log.record("ebook", "approve", book_id)
        return f"✅ 《{book['topic']}》已批准，可上架"

    def reject(self, book_id, reason):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "rejected"
        book["reject_reason"] = reason
        self._save()
        cycle_log.record("ebook", "reject", book_id, reason)
        return f"❌ 《{book['topic']}》已退回：{reason}"

    def publish(self, book_id, platforms=None, auto_platforms=None):
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

        epub = book.get("epub", {})
        epub_path = epub.get("path", "") if isinstance(epub, dict) else book.get("epub_path", "")
        if epub_path and os.path.exists(epub_path):
            meta = {
                "id": book_id, "title": book.get("topic", ""),
                "author": "AMPM AI",
                "description": book.get("content", "")[:300],
                "price": 99, "category": "Computer & Technology",
            }
            publisher_results = publisher_manager.publish_sync(epub_path, meta)
            book["publisher_results"] = publisher_results

        cycle_log.record("ebook", "publish", book_id, str(plats))
        pipeline_supervisor.record_completion(book_id, "ebook")
        return f"📚 《{book['topic']}》已上架到 {len(plats)} 個平台"

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
        stages = {"selected": 0, "outline_done": 0, "content_done": 0, "epub_done": 0,
                  "pending_review": 0, "approved": 0, "published": 0, "rejected": 0}
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

    def total_published(self):
        return sum(1 for b in self.ebooks if b.get("status") == "published")

    def trending_topics(self):
        published = [b for b in self.ebooks if b.get("status") == "published"]
        if not published:
            return []
        sales_by_topic = {}
        for b in published:
            sales = 0
            for key, data in self.ebook_sales.items():
                if data["book_id"] == b["id"]:
                    sales += sum(data["sales"].values())
            sales_by_topic[b["topic"]] = sales
        sorted_topics = sorted(sales_by_topic.items(), key=lambda x: -x[1])
        return [t for t, s in sorted_topics[:5]]

PANEY_MONEY_SERIES = [
    ("PANEY & MONEY 的收收探險：玩具回家了！", "收玩具/生活自理", "3-6", "學會找到→分類→放回家"),
    ("PANEY & MONEY 的洗手任務：泡泡打敗細菌", "洗手/衛生習慣", "3-6", "洗手也能像闖關"),
    ("PANEY & MONEY 的刷牙特攻：牙牙星星亮晶晶", "刷牙/睡前儀式", "3-6", "刷牙流程＋晚安收尾"),
    ("PANEY & MONEY 的睡前安心：我有點怕黑", "怕黑/情緒安撫", "3-6", "把害怕放好再睡"),
    ("PANEY & MONEY 的上學安心：我想家了怎麼辦？", "分離焦慮", "3-6", "分離焦慮的安撫句"),
    ("PANEY & MONEY 的輪流遊戲：一起玩更好玩", "輪流/分享", "3-6", "輪流不等於輸"),
    ("PANEY & MONEY 的生氣火山：我需要冷靜一下", "生氣管理", "3-6", "生氣三步驟"),
    ("PANEY & MONEY 的難過雲朵：我想要抱抱", "難過/表達需求", "3-6", "學會說出需要"),
    ("PANEY & MONEY 的緊張蝴蝶：第一次也可以慢慢來", "緊張/面對新事物", "3-6", "面對新事物的勇氣"),
    ("PANEY & MONEY 的害羞小屋：我想說你好", "害羞/社交勇氣", "3-6", "社交勇氣練習"),
    ("PANEY & MONEY 的吃飯小勇氣：先嘗一口就好", "吃飯/飲食習慣", "3-6", "不逼吃也前進"),
    ("PANEY & MONEY 的穿衣任務：自己來我可以", "穿衣/自理", "3-6", "自理成就感"),
    ("PANEY & MONEY 的上廁所小隊：記得先說一聲", "如廁/自理", "3-6", "如廁提醒與安心"),
    ("PANEY & MONEY 的出門安全：牽手不走丟", "外出安全", "3-6", "安全規則小故事"),
    ("PANEY & MONEY 的收心回家：玩完要收尾", "作息轉場", "3-6", "從玩到收的轉場"),
    ("PANEY & MONEY 的洗澡小泡泡：水不怕我", "洗澡/怕水", "3-6", "怕洗澡也有方法"),
    ("PANEY & MONEY 的睡醒起床：早安三步驟", "起床/早晨作息", "3-6", "起床整理出發"),
    ("PANEY & MONEY 的整理小書包：明天出發準備好", "整理/準備", "3-6", "睡前準備明天"),
    ("PANEY & MONEY 的失敗也可以：再試一次就好", "挫折復原", "3-6", "挫折復原力"),
    ("PANEY & MONEY 的吵吵停一下：小聲也能被聽見", "音量/表達", "3-6", "溝通不吼叫"),
]

PANEY_MONEY_STORIES = {
    "收收探險": ("PANEY & MONEY 的收收探險：玩具回家了！",
"""白天，PANEY 最喜歡出發探險；晚上，MONEY 最會把一切收得剛剛好，準備說晚安。
今天，他們玩得好開心！積木、車車、娃娃都在地上開派對。可是——要睡覺了，房間還是亂亂的。

PANEY 說：「我們來玩一個遊戲吧！幫玩具找到回家的路。」
MONEY 點點頭：「找到家以後，就能安心休息，明天再玩！」

這本書用孩子聽得懂的方式，把「收玩具」變成一場小小探險：
1) 找到：先找一找，哪些玩具還在外面？
2) 分類：一樣的放一起，積木一堆、車車一堆。
3) 放回家：每一堆都有自己的家——玩具箱、籃子、架子。

故事最後，MONEY 會帶孩子做「收尾」：把最後一件玩具放好、伸伸懶腰、深呼吸，然後說晚安。"""),
    "睡前安心": ("PANEY & MONEY 的睡前安心：我有點怕黑",
"""晚上到了，MONEY 把窗簾拉上，房間慢慢變暗。
PANEY 看著角落，小小聲說：「我……有點怕黑。」

MONEY 沒有笑，也沒有說「不要怕」。MONEY 說：「謝謝你告訴我。怕黑不是壞事，是心情在提醒你——你需要安心。」

於是兩隻小貓一起做「晚安安心任務」：
1) 說出來：「我現在覺得怕怕的。」
2) 找一個光：夜燈、窗外的月亮、或手電筒的小星星。
3) 做一個動作：抱抱、深呼吸、或握著小毯子。

PANEY 發現：黑黑的房間裡，其實也有好多小線索——月亮在窗外、星星在天上、玩具在自己的家。
MONEY 說：「我們不是把害怕趕走，我們是把害怕放好，放到安全的地方。」"""),
    "生氣火山": ("PANEY & MONEY 的生氣火山：我需要冷靜一下",
"""白天，PANEY 出發去玩。
可是——積木倒了、輪到別人先玩、想要的東西拿不到……PANEY 的胸口熱熱的，眼睛也熱熱的。
「我生氣了！」PANEY 的生氣像火山一樣，噗——要爆出來了。

MONEY 走過來，沒有說「不要生氣」。MONEY 說：
「生氣是在告訴你：你很在乎。現在，我們先保護自己和別人，做一個冷靜任務。」

PANEY 跟著 MONEY 一步一步做：
1) 停下來：先放下手裡的東西，站到安全的地方。
2) 說出來：用力的時候也可以好好說——「我現在很生氣。」
3) 做一個冷靜動作：深呼吸三次、抱抱自己、或喝一口水。

慢慢的，火山不再噗噗跳了。PANEY 說：「我覺得……好一點了。」
MONEY 微笑：「生氣會來，也會走。你做到了。」"""),
}

class KidBookPipeline:
    def __init__(self):
        self.books_file = DATA / "kidbooks.json"
        self.themes_file = DATA / "kid_themes.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        for f, default in [(self.books_file, []), (self.themes_file, [])]:
            if f.exists():
                try:
                    setattr(self, f.stem, json.loads(f.read_text()))
                except:
                    setattr(self, f.stem, default)
            else:
                setattr(self, f.stem, default)

    def _save(self):
        DATA.mkdir(parents=True, exist_ok=True)
        self.books_file.write_text(json.dumps(self.kidbooks, ensure_ascii=False, indent=2))
        self.themes_file.write_text(json.dumps(self.kid_themes, ensure_ascii=False, indent=2))

    def trend_analysis(self, llm_call=None) -> list:
        if llm_call:
            prompt = "分析當前繁體中文市場 TOP20 最熱門的兒童繪本主題趨勢。列出 5 個主題，每個含書名建議、核心教育價值、適合年齡層。只要清單。"
            result = llm_call(prompt)
            self.last_trend = result
            self._save()
            return result
        return random.sample(PANEY_MONEY_SERIES, 5)

    def select_theme(self, title, theme, age_range, topic_summary=""):
        book_id = hashlib.md5(f"KB-{title}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.kidbooks.append({
            "id": book_id, "title": title, "theme": theme, "age_range": age_range,
            "topic_summary": topic_summary,
            "status": "selected", "characters": [], "story": None, "illustrations": [],
            "created_at": datetime.now().isoformat(),
            "series": "PANEY & MONEY 日夜探險",
            "series_slogan": "白天勇敢出發，晚上安心回家",
        })
        self._save()
        cycle_log.record("kidbook", "select_theme", book_id, f"{title}/{theme}/{age_range}")
        return book_id

    def approve_topic(self, book_id):
        book = self._find(book_id)
        if not book: return "找不到書籍"
        if book["status"] != "selected": return f"狀態為 {book['status']}，無法審核"
        book["status"] = "selected_approved"
        self._save()
        cycle_log.record("kidbook", "topic_approved", book_id)
        return f"✅ 《{book['title']}》選題已通過，進入生成流程"

    def create_characters(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["characters"] = "PANEY（白天貓）：負責出發、探索、開始做的白天任務。\nMONEY（夜晚貓）：負責收尾、安撫、說晚安的夜晚儀式。"
        book["status"] = "characters_done"
        self._save()
        cycle_log.record("kidbook", "create_characters", book_id)
        return "PANEY（白天貓）+ MONEY（夜晚貓）"

    def write_story(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        title = book.get("title", "")
        theme = book.get("theme", "")
        if llm_call:
            prompt = f"""為童書 '{title}'（PANEY & MONEY 系列，主題：{theme}，年齡層：3-6 歲）寫一個完整故事。

系列設定：
- PANEY（白天貓）：負責出發、探索、開始做
- MONEY（夜晚貓）：負責收尾、安撫、說晚安
- 口號：白天勇敢出發，晚上安心回家

故事結構：
1) 白天情境：PANEY 遇到一個狀況
2) 一句話情緒：孩子能說出口的句型
3) 一個小技巧：1 個可做的動作
4) 晚上收尾：MONEY 帶入習慣
5) 最後一頁：系列口號

約 600 字，繁體中文，句子短，3-6 歲聽得懂。"""
            story = llm_call(prompt)
        else:
            for key, (t, s) in PANEY_MONEY_STORIES.items():
                if key in title or key in theme:
                    story = s
                    break
            else:
                story = f"""白天，PANEY 出發去探險。{title}——這是今天的新任務！

PANEY 說：「我們來試試看吧！」
MONEY 在旁邊點點頭：「慢慢來，我可以陪你。」

他們一起完成了任務，學到了新東西。
太陽下山了，MONEY 說：「天黑了，我們把東西收好，準備說晚安吧。」

PANEY 深呼吸一口氣，說：「白天勇敢出發，晚上安心回家。」

任務完成！"""
        book["story"] = story
        book["status"] = "story_done"
        self._save()
        cycle_log.record("kidbook", "write_story", book_id)
        return story

    def compile_epub(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if book.get("epub"):
            return f"📚 《{book['title']}》EPUB 已存在"

        cover = image_gen.generate_cover(book["title"], f"適合{book['age_range']}歲", "picture_book")

        chars_images = image_gen.generate_character_sheet(book_id, str(book.get("characters", "")), "picture_book")
        char_paths = [c["path"] for c in chars_images if c["success"]]

        paras = [p for p in book.get("story", "").split("\n") if p.strip()]
        page_images = []
        for i, para in enumerate(paras[:10]):
            ill = image_gen.generate_illustration(f"{book['title']} - {para[:50]}", "picture_book", book_id, i+1)
            if ill["success"]:
                page_images.append(ill["path"])
            else:
                page_images.append("")

        all_images = char_paths + page_images
        epub = compiler.compile_kidbook(book, all_images, cover["path"] if cover["success"] else None)
        book["epub"] = epub
        book["status"] = "epub_done"
        self._save()
        cycle_log.record("kidbook", "compile_epub", book_id, epub.get("epub_id", ""))
        return f"📚 《{book['title']}》EPUB 編譯完成: {epub.get('epub_id', '')}"

    def submit_for_review(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "pending_review"
        book["submitted_at"] = datetime.now().isoformat()
        self._save()
        cycle_log.record("kidbook", "submit_review", book_id)
        return f"📖 《{book['title']}》已送審"

    def approve(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "approved"
        self._save()
        cycle_log.record("kidbook", "approve", book_id)
        return f"✅ 《{book['title']}》已批准"

    def reject(self, book_id, reason):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "rejected"
        book["reject_reason"] = reason
        self._save()
        cycle_log.record("kidbook", "reject", book_id, reason)
        return f"❌ 《{book['title']}》已退回：{reason}"

    def publish(self, book_id, platforms=None, auto_platforms=None):
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

        epub = book.get("epub", {})
        epub_path = epub.get("path", "") if isinstance(epub, dict) else book.get("epub_path", "")
        if epub_path and os.path.exists(epub_path):
            meta = {
                "id": book_id, "title": book.get("title", ""),
                "author": "AMPM AI",
                "description": book.get("story", "")[:300],
                "price": 99, "category": "Children's Books",
            }
            publisher_results = publisher_manager.publish_sync(epub_path, meta)
            book["publisher_results"] = publisher_results

        cycle_log.record("kidbook", "publish", book_id, str(plats))
        pipeline_supervisor.record_completion(book_id, "kidbook")
        return f"📚 《{book['title']}》已上架到 {len(plats)} 個平台"

    def get_pipeline_status(self):
        stages = {"selected": 0, "characters_done": 0, "story_done": 0, "epub_done": 0,
                  "pending_review": 0, "approved": 0, "published": 0, "rejected": 0}
        for b in self.kidbooks:
            s = b.get("status", "selected")
            if s in stages:
                stages[s] += 1
        lines = ["📊 童書生產線狀態："]
        for stage, count in stages.items():
            lines.append(f"  {stage}: {count} 本")
        return "\n".join(lines)

    def _find(self, book_id):
        for b in self.kidbooks:
            if b["id"] == book_id:
                return b
        return None

    def total_published(self):
        return sum(1 for b in self.kidbooks if b.get("status") == "published")

class ServiceWebsitePipeline:
    """AI 客服+安裝網站產線 — AMPM-AIOPS.COM 全自動化"""

    def __init__(self):
        self.sites_file = DATA / "service_sites.json"
        self.orders_file = DATA / "service_orders.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        for f, default in [(self.sites_file, []), (self.orders_file, [])]:
            if f.exists():
                try:
                    setattr(self, f.stem, json.loads(f.read_text()))
                except:
                    setattr(self, f.stem, default)
            else:
                setattr(self, f.stem, default)

    def _save(self):
        DATA.mkdir(parents=True, exist_ok=True)
        self.sites_file.write_text(json.dumps(self.service_sites, ensure_ascii=False, indent=2))
        self.orders_file.write_text(json.dumps(self.service_orders, ensure_ascii=False, indent=2))

    def create_site(self, domain: str, plan: str) -> str:
        site_id = hashlib.md5(f"SV-{domain}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.service_sites.append({
            "id": site_id, "domain": domain, "plan": plan,
            "status": "provisioning",
            "created_at": datetime.now().isoformat(),
            "installed_at": None, "config": {},
            "orders": []
        })
        self._save()
        cycle_log.record("service", "create_site", site_id, f"{domain}/{plan}")
        return site_id

    def auto_deploy(self, site_id: str) -> str:
        site = self._find(site_id)
        if not site:
            return "找不到站點"
        deploy_script = (
            f"# AMPM-AIOPS.COM 自動部署\n"
            f"domain={site['domain']}\n"
            f"plan={site['plan']}\n"
            f"# 1. 安裝 nginx + docker\n"
            f"# 2. 拉取 AMPM-DASHBOARD 容器\n"
            f"# 3. 設定 SSL (Let's Encrypt)\n"
            f"# 4. 啟動 AI 客服聊天視窗\n"
            f"# 5. 連接 Telegram Bot API\n"
            f"echo '✅ {site['domain']} 部署完成'"
        )
        site["deploy_script"] = deploy_script
        site["status"] = "deploy_ready"
        self._save()
        cycle_log.record("service", "auto_deploy", site_id)
        return deploy_script

    def record_order(self, site_id: str, customer: str, amount: float) -> str:
        order_id = hashlib.md5(f"ORD-{site_id}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.service_orders.append({
            "id": order_id, "site_id": site_id,
            "customer": customer, "amount": amount,
            "status": "paid", "created_at": datetime.now().isoformat()
        })
        site = self._find(site_id)
        if site:
            site.setdefault("orders", []).append(order_id)
            site["status"] = "active"
            self._save()
        cycle_log.record("service", "record_order", site_id, f"{customer}/${amount}")
        return order_id

    def handle_ticket(self, site_id: str, issue: str, llm_call=None) -> str:
        if llm_call:
            prompt = f"客戶站點 {site_id} 回報問題：{issue}。請分析可能原因並給出解決步驟。用繁體中文。"
            return llm_call(prompt)
        return f"🔧 已記錄 {site_id} 的工單：「{issue[:50]}」，工程師將在 24 小時內處理。"

    def upgrade_site(self, site_id: str, new_plan: str) -> str:
        site = self._find(site_id)
        if not site:
            return "找不到站點"
        old_plan = site["plan"]
        site["plan"] = new_plan
        site["status"] = "upgrading"
        self._save()
        cycle_log.record("service", "upgrade", site_id, f"{old_plan}→{new_plan}")
        return f"🔄 {site['domain']} 已從 {old_plan} 升級到 {new_plan}"

    def get_pipeline_status(self):
        stages = {"provisioning": 0, "deploy_ready": 0, "active": 0, "upgrading": 0}
        for s in self.service_sites:
            status = s.get("status", "provisioning")
            if status in stages:
                stages[status] += 1
        lines = ["📊 AI 客服網站產線狀態："]
        for stage, count in stages.items():
            lines.append(f"  {stage}: {count} 個站點")
        return "\n".join(lines)

    def _find(self, site_id):
        for s in self.service_sites:
            if s["id"] == site_id:
                return s
        return None

    def total_active(self):
        return sum(1 for s in self.service_sites if s.get("status") == "active")

class PublisherEngine:
    """統一出版循環引擎 — 三條產線一個循環"""

    def __init__(self):
        self.ebook = EbookPipeline()
        self.kidbook = KidBookPipeline()
        self.service = ServiceWebsitePipeline()
        self.lock = threading.RLock()
        self._running = False
        self._cycle_thread = None
        self._auto_publish = False

    def full_status(self) -> str:
        parts = []
        parts.append("=" * 40)
        parts.append("🏭 統一出版循環引擎狀態")
        parts.append("=" * 40)
        parts.append("")
        parts.append(self.ebook.get_pipeline_status())
        parts.append("")
        parts.append(self.kidbook.get_pipeline_status())
        parts.append("")
        parts.append(self.service.get_pipeline_status())
        parts.append("")
        parts.append(f"📈 銷售摘要：{self.ebook.get_sales_summary()}")
        parts.append(f"🔎 品質監督：{pipeline_supervisor.status()['completion_rate']}% 完成率")
        try:
            pm = __import__("publishers", fromlist=["publisher_manager"]).publisher_manager
            ps = pm.status()
            plat_info = []
            for plat, info in ps.get("platforms", {}).items():
                plat_info.append(f"{plat}: {'🟢' if info.get('logged_in') else '🔴'}")
            parts.append(f"📤 上架機械組件：{' | '.join(plat_info)}")
        except:
            pass
        parts.append("")
        parts.append(f"🔄 循環引擎：{'🟢 運行中' if self._running else '🔴 已停止'}")
        recent = cycle_log.recent(5)
        if recent:
            parts.append("最近活動：")
            for e in recent:
                parts.append(f"  [{e['ts'][:19]}] {e['pipeline']}/{e['stage']} {e['book_id']}")
        return "\n".join(parts)

    def auto_cycle(self, llm_call=None):
        """執行一次完整循環 — 永不跳過，失敗則重試，直到每本書完成"""
        results = []

        # 0. 資源偵查（確保管線不枯竭）
        try:
            scout_result = resource_scout.scout_all()
            total = sum(v["total"] for v in scout_result.values())
            avail = sum(v["available"] for v in scout_result.values())
            results.append(f"🔍 資源偵查：{avail}/{total} 項可用")
        except Exception as e:
            results.append(f"🔍 資源偵查失敗：{e}")

        def retry_call(step_name: str, fn, max_attempts=3):
            """重試包裝 — 失敗不跳過，最多重試 3 次"""
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn()
                except Exception as e:
                    if attempt < max_attempts:
                        time.sleep(5 * attempt)
                        results.append(f"  ⚠️ {step_name} 第{attempt}次失敗，重試中...")
                    else:
                        raise RuntimeError(f"{step_name} 失敗 {max_attempts} 次: {e}")

        # ── 1. 處理未完成的電子書 ──
        ebook_advanced = 0
        for book in self.ebook.ebooks:
            status = book.get("status", "selected")
            bid = book["id"]
            if status == "selected":
                # 選題等待人工審核通過
                results.append(f"  ⏸️ 《{book['topic']}》選題待審核")
                ebook_advanced += 1
                break
            elif status == "selected_approved":
                def _gen_outline(b=book, bid=bid):
                    self.ebook.generate_outline(bid, llm_call)
                    return f"  📝 《{b['topic']}》目錄已生成"
                result = retry_call(f"生成目錄 {bid}", lambda: _gen_outline())
                results.append(result)
                ebook_advanced += 1
                break
            elif status == "outline_done":
                def _write(b=book, bid=bid):
                    self.ebook.write_content(bid, llm_call)
                    return f"  ✍️ 《{b['topic']}》內容已撰寫"
                result = retry_call(f"撰寫內容 {bid}", lambda: _write())
                results.append(result)
                ebook_advanced += 1
                break
            elif status == "content_done":
                def _compile(b=book, bid=bid):
                    return self.ebook.compile_epub(bid)
                result = retry_call(f"編譯EPUB {bid}", lambda: _compile())
                results.append(result)
                ebook_advanced += 1
                break
            elif status == "epub_done":
                gate = pipeline_supervisor.check_quality_gate(book, "ebook")
                if gate["passed"]:
                    self.ebook.submit_for_review(bid)
                    results.append(f"  📋 《{book['topic']}》品質通過，已送審")
                else:
                    self.ebook.submit_for_review(bid)
                    issues_str = "; ".join(gate["issues"][:2])
                    results.append(f"  📋 《{book['topic']}》已送審（⚠️ 品質標記: {issues_str}）")
                ebook_advanced += 1
                break
            elif status == "pending_review":
                if self._auto_publish:
                    self.ebook.approve(bid)
                    r = self.ebook.publish(bid)
                    results.append(f"  🚀 《{book['topic']}》{r}")
                else:
                    results.append(f"  ⏸️ 《{book['topic']}》待審核（/publish approve {bid}）")
                ebook_advanced += 1
                break
            elif status == "rejected":
                results.append(f"  ⏸️ 《{book['topic']}》已被退回，待人工處理")
                ebook_advanced += 1
                break

        # ── 2. 處理未完成的童書 ──
        kid_advanced = 0
        for book in self.kidbook.kidbooks:
            status = book.get("status", "selected")
            bid = book["id"]
            if status == "selected":
                results.append(f"  ⏸️ 《{book['title']}》選題待審核")
                kid_advanced += 1
                break
            elif status == "selected_approved":
                def _chars(b=book, bid=bid):
                    self.kidbook.create_characters(bid, llm_call)
                    return f"  🎭 《{b['title']}》角色已設定"
                result = retry_call(f"創建角色 {bid}", lambda: _chars())
                results.append(result)
                kid_advanced += 1
                break
            elif status == "characters_done":
                def _story(b=book, bid=bid):
                    self.kidbook.write_story(bid, llm_call)
                    return f"  📝 《{b['title']}》故事已撰寫"
                result = retry_call(f"撰寫故事 {bid}", lambda: _story())
                results.append(result)
                kid_advanced += 1
                break
            elif status == "story_done":
                def _compile(b=book, bid=bid):
                    return self.kidbook.compile_epub(bid)
                result = retry_call(f"編譯EPUB {bid}", lambda: _compile())
                results.append(result)
                kid_advanced += 1
                break
            elif status == "epub_done":
                gate = pipeline_supervisor.check_quality_gate(book, "kidbook")
                if gate["passed"]:
                    self.kidbook.submit_for_review(bid)
                    results.append(f"  📋 《{book['title']}》品質通過，已送審")
                else:
                    self.kidbook.submit_for_review(bid)
                    issues_str = "; ".join(gate["issues"][:2])
                    results.append(f"  📋 《{book['title']}》已送審（⚠️ 品質標記: {issues_str}）")
                kid_advanced += 1
                break
            elif status == "pending_review":
                if self._auto_publish:
                    self.kidbook.approve(bid)
                    r = self.kidbook.publish(bid)
                    results.append(f"  🚀 《{book['title']}》{r}")
                else:
                    results.append(f"  ⏸️ 《{book['title']}》待審核（/publish approve {bid}）")
                kid_advanced += 1
                break
            elif status == "rejected":
                results.append(f"  ⏸️ 《{book['title']}》已被退回，待人工處理")
                kid_advanced += 1
                break

        # ── 2.5 機械組件協作：ResourceScout 提供繪圖風格給內容生成 ──
        if kid_advanced > 0 or True:
            ill_style = resource_scout.pick_random_illustration_style()
            img_src = resource_scout.pick_random_image_source()
            results.append(f"  🎨 資源偵查提供：{ill_style} / {img_src.get('name','通用')}")

        # ── 3. 只有完全沒有進行中的書，才開新選題 ──
        if ebook_advanced == 0:
            results.append("  ℹ️ 電子書：無進行中項目，開始新選題...")
            try:
                ebook_topics = self.ebook.trend_analysis(llm_call)
                if isinstance(ebook_topics, list):
                    topic = ebook_topics[0] if isinstance(ebook_topics[0], str) else (
                        ebook_topics[0][0] if isinstance(ebook_topics[0], tuple) else str(ebook_topics[0]))
                else:
                    topic = "Python 自動化入門"
                eid = self.ebook.select_topic(topic)
                results.append(f"  📈 新選題：《{topic}》（ID: {eid}）")
            except Exception as e:
                results.append(f"  ❌ 新選題失敗: {e}")

        if kid_advanced == 0:
            results.append("  ℹ️ 童書：無進行中項目，開始新選題...")
            try:
                kid_themes = self.kidbook.trend_analysis(llm_call)
                if isinstance(kid_themes, list):
                    td = kid_themes[0]
                    if isinstance(td, (list, tuple)) and len(td) >= 3:
                        title, theme, age = td[0], td[1], td[2]
                        summary = td[3] if len(td) > 3 else ""
                    else:
                        title, theme, age, summary = "PANEY & MONEY 的收收探險：玩具回家了！", "收玩具", "3-6", "學會整理"
                else:
                    title, theme, age, summary = "PANEY & MONEY 的睡前安心：我有點怕黑", "怕黑", "3-6", "情緒安撫"
                kid = self.kidbook.select_theme(title, theme, age, summary)
                results.append(f"  📖 新選題：《{title}》（{theme}/{age}）")
            except Exception as e:
                results.append(f"  ❌ 新選題失敗: {e}")

        # 4. 銷售回饋
        sales_feedback = self.ebook.trending_topics()
        if sales_feedback:
            results.append(f"  🔄 銷售回饋：暢銷主題 → {', '.join(sales_feedback[:3])}")

        cycle_log.record("engine", "auto_cycle", "; ".join(results))
        return "\n".join(results)

    def start_auto_pilot(self, llm_call=None, interval_hours=6):
        """啟動自動循環（背景執行）"""
        if self._running:
            return "🔄 循環引擎已在運行中"

        def _loop():
            self._running = True
            while self._running:
                try:
                    result = self.auto_cycle(llm_call)
                    print(f"[PublisherEngine] 自動循環完成:\n{result}")
                except Exception as e:
                    print(f"[PublisherEngine] 循環錯誤: {e}")
                time.sleep(interval_hours * 3600)

        self._cycle_thread = threading.Thread(target=_loop, daemon=True)
        self._cycle_thread.start()
        return f"🔄 循環引擎已啟動（每 {interval_hours} 小時一次）"

    def stop_auto_pilot(self):
        self._running = False
        return "🔄 循環引擎已停止"

    def set_auto_publish(self, enabled: bool):
        self._auto_publish = enabled
        return f"自動上架：{'🟢 已開啟' if enabled else '🔴 已關閉'}"

    def status(self) -> dict:
        return {
            "ebook_published": self.ebook.total_published(),
            "kidbook_published": self.kidbook.total_published(),
            "service_active": self.service.total_active(),
            "engine_running": self._running,
            "cycle_count": len([e for e in cycle_log.log if e.get("stage") == "auto_cycle"]),
            "auto_publish": self._auto_publish,
        }

    def _book_progress_lines(self, books: list, label: str, title_key: str = "topic") -> list:
        lines = [f"  📌 {label}："]
        by_stage = {}
        for b in books:
            s = b.get("status", "unknown")
            by_stage.setdefault(s, []).append(b.get(title_key, "?")[:30])
        for stage, titles in sorted(by_stage.items()):
            emoji = {"selected": "🆕", "outline_done": "📝", "content_done": "✍️",
                     "epub_done": "📦", "pending_review": "🔍", "approved": "✅",
                     "published": "📚", "rejected": "⛔", "characters_done": "🎭",
                     "story_done": "📖"}.get(stage, "•")
            lines.append(f"    {emoji} {stage} ({len(titles)}): {', '.join(titles[:3])}")
            if len(titles) > 3:
                lines[-1] += f" 等 {len(titles)} 本"
        return lines

    def generate_report(self, detailed: bool = False) -> str:
        st = self.status()
        rs = resource_scout.status()
        sv = pipeline_supervisor.status()

        lines = []
        lines.append("🏭 出版工廠日報")
        lines.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
        lines.append("=" * 30)

        # ── 綜合統計 ──
        lines.append(f"📦 累計出版：電子書 {st['ebook_published']} 本 | 童書 {st['kidbook_published']} 本")
        lines.append(f"🌐 客服網站：{st['service_active']} 個啟用中")
        lines.append(f"🔄 循環引擎：{'🟢 運行中' if st['engine_running'] else '🔴 已停止'} | 次數 {st['cycle_count']} | 自動上架 {'🟢' if st.get('auto_publish') else '🔴'}")

        # ── 品質監督 ──
        lines.append(f"🛡️ 品質監督：完成率 {sv['completion_rate']}% | 停滯 {sv.get('stalled_count', 0)} 本 | 警報 {sv.get('alert_count', 0)}")

        # ── 資源狀態 ──
        lines.append(f"🔍 資源庫：{rs.get('catalog_entries', 0)} 項 | 風格 {rs.get('styles_available', 10)} 種")

        # ── 上架機械組件 ──
        try:
            pm = __import__("publishers", fromlist=["publisher_manager"]).publisher_manager
            ps = pm.status()
            lines.append(f"📤 上架紀錄：{ps.get('total_uploads', 0)} 次 | 忙碌: {'🟡' if ps.get('busy') else '🔴'}")
            for e in ps.get("recent_uploads", [])[-2:]:
                icon = "✅" if e.get("success") else "❌"
                lines.append(f"  {icon} {e.get('book', '?')} → {e.get('platform', '?')}")
        except:
            pass

        # ── 銷售 ──
        sales = self.ebook.get_sales_summary()
        lines.append(f"💰 {sales}")

        # ── 各書進度明細 ──
        lines.append("")
        lines.extend(self._book_progress_lines(self.ebook.ebooks, "電子工具書", "topic"))
        lines.append("")
        lines.extend(self._book_progress_lines(self.kidbook.kidbooks, "童書繪本", "title"))
        lines.append("")
        lines.extend(self._book_progress_lines(self.service.service_sites, "客服網站", "domain"))

        # ── 最近活動 ──
        recent = cycle_log.recent(5)
        if recent:
            lines.append("")
            lines.append("━━ 最近活動 ━━")
            for e in recent:
                detail = e.get("detail", "")
                d_short = f" — {detail[:40]}" if detail else ""
                lines.append(f"  [{e['ts'][11:19]}] {e['pipeline']}/{e['stage']}{d_short}")

        # ── 待辦提醒 ──
        todo = []
        pending_ebooks = [b for b in self.ebook.ebooks if b.get("status") == "pending_review"]
        pending_kids = [b for b in self.kidbook.kidbooks if b.get("status") == "pending_review"]
        if pending_ebooks and not self._auto_publish:
            todo.append(f"  ⏸️ {len(pending_ebooks)} 本電子書待審核：/publish approve <id>")
        if pending_kids and not self._auto_publish:
            todo.append(f"  ⏸️ {len(pending_kids)} 本童書待審核：/publish approve <id>")
        rejected = [b for b in self.ebook.ebooks if b.get("status") == "rejected"]
        rejected += [b for b in self.kidbook.kidbooks if b.get("status") == "rejected"]
        if rejected:
            todo.append(f"  ⛔ {len(rejected)} 本被退回需人工處理")
        if todo:
            lines.append("")
            lines.append("━━ 待辦提醒 ━━")
            lines.extend(todo)

        if detailed:
            lines.append("")
            lines.append("━━ 各產線詳細統計 ━━")
            lines.append(self.ebook.get_pipeline_status())
            lines.append("")
            lines.append(self.kidbook.get_pipeline_status())
            lines.append("")
            lines.append(self.service.get_pipeline_status())
            lines.append("")
            lines.append(f"🔎 品質監督完整報告：")
            lines.append(pipeline_supervisor.report())

        return "\n".join(lines)


engine = PublisherEngine()
