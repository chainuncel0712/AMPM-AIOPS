"""
Publisher Engine — 統一出版循環引擎
=====================================
整合 3 條產線（電子書、童書、AI 客服網站）成一個自動化循環：
  市場調查 → 選題 → 內容生成 → 審核 → 上架 → 銷售追蹤 → 回饋選題

器官協作模式：每條產線都是一個器官，由引擎統一調度
"""
import json, os, threading, time, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta

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
        cycle_log.record("ebook", "publish", book_id, str(plats))
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
        stages = {"selected": 0, "outline_done": 0, "content_done": 0,
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
        self.books_file.write_text(json.dumps(self.kidbooks, ensure_ascii=False, indent=2))
        self.themes_file.write_text(json.dumps(self.kid_themes, ensure_ascii=False, indent=2))

    def trend_analysis(self, llm_call=None) -> list:
        if llm_call:
            prompt = "分析當前繁體中文市場 TOP10 最熱門的兒童繪本主題趨勢。列出 5 個主題，每個含書名建議、核心教育價值、適合年齡層。只要清單。"
            result = llm_call(prompt)
            self.last_trend = result
            self._save()
            return result
        return random.sample([
            ("小熊學勇敢", "勇氣", "3-6"),
            ("小兔子的一天", "生活常規", "2-5"),
            ("星星不見了", "友誼", "4-7"),
            ("會說話的樹", "環保", "5-8"),
            ("彩虹下的秘密", "好奇", "3-6"),
            ("小廚師夢想", "堅持", "4-7"),
            ("月亮想回家", "歸屬", "3-6"),
            ("魔法畫筆", "創造", "5-8"),
        ], 5)

    def select_theme(self, title, theme, age_range):
        book_id = hashlib.md5(f"KB-{title}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.kidbooks.append({
            "id": book_id, "title": title, "theme": theme, "age_range": age_range,
            "status": "selected", "characters": [], "story": None, "illustrations": [],
            "created_at": datetime.now().isoformat()
        })
        self._save()
        cycle_log.record("kidbook", "select_theme", book_id, f"{title}/{theme}/{age_range}")
        return book_id

    def create_characters(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if llm_call:
            prompt = f"為童書 '{book['title']}'（主題：{book['theme']}，年齡層：{book['age_range']}）創造 2-3 個角色。包含名字、外型、性格，每個角色 50 字以內。"
            chars_text = llm_call(prompt)
        else:
            chars_text = f"角色1：主角（可愛小動物），角色2：好朋友（幫忙者），角色3：小挑戰（需要克服的困難）"
        book["characters"] = chars_text
        book["status"] = "characters_done"
        self._save()
        cycle_log.record("kidbook", "create_characters", book_id)
        return chars_text

    def write_story(self, book_id, llm_call=None):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        if llm_call:
            prompt = f"為童書 '{book['title']}'（主題：{book['theme']}，年齡層：{book['age_range']} 歲）寫一個完整故事。約 800 字，繁體中文，有教育意義，父母會想買。角色：{str(book.get('characters',''))[:200]}"
            story = llm_call(prompt)
        else:
            story = f"從前從前，{book['title']}……"
        book["story"] = story
        book["status"] = "story_done"
        self._save()
        cycle_log.record("kidbook", "write_story", book_id)
        return story

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
        cycle_log.record("kidbook", "publish", book_id, str(plats))
        return f"📚 《{book['title']}》已上架到 {len(plats)} 個平台"

    def get_pipeline_status(self):
        stages = {"selected": 0, "characters_done": 0, "story_done": 0,
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
        parts.append("")
        parts.append(f"🔄 循環引擎：{'🟢 運行中' if self._running else '🔴 已停止'}")
        recent = cycle_log.recent(5)
        if recent:
            parts.append("最近活動：")
            for e in recent:
                parts.append(f"  [{e['ts'][:19]}] {e['pipeline']}/{e['stage']} {e['book_id']}")
        return "\n".join(parts)

    def auto_cycle(self, llm_call=None):
        """執行一次完整循環：市場調查 → 選題 → 內容 → 審核 → 上架 → 追蹤"""
        results = []

        # 1. 市場調查 + 選題
        ebook_topics = self.ebook.trend_analysis(llm_call)
        if isinstance(ebook_topics, list):
            topic = ebook_topics[0] if isinstance(ebook_topics[0], str) else (ebook_topics[0][0] if isinstance(ebook_topics[0], tuple) else str(ebook_topics[0]))
            results.append(f"📈 電子書選題：{topic}")
            eid = self.ebook.select_topic(topic)
        else:
            topic = "Python 自動化入門"
            results.append(f"📈 電子書選題（模板）：{topic}")
            eid = self.ebook.select_topic(topic)

        kid_themes = self.kidbook.trend_analysis(llm_call)
        if isinstance(kid_themes, list):
            theme_data = kid_themes[0] if isinstance(kid_themes[0], tuple) else ("小故事大道理", "教育", "3-6")
            title, theme, age = theme_data
            results.append(f"📖 童書選題：{title}（{theme}/{age}）")
            kid = self.kidbook.select_theme(title, theme, age)
        else:
            results.append("📖 童書選題（模板）：小熊學勇敢")
            kid = self.kidbook.select_theme("小熊學勇敢", "勇氣", "3-6")

        # 2. 內容生成
        outline = self.ebook.generate_outline(eid, llm_call)
        results.append(f"  📝 電子書目錄已生成")
        content = self.ebook.write_content(eid, llm_call)
        results.append(f"  ✍️ 電子書內容已撰寫")

        chars = self.kidbook.create_characters(kid, llm_call)
        results.append(f"  🎭 童書角色已設定")
        story = self.kidbook.write_story(kid, llm_call)
        results.append(f"  📝 童書故事已撰寫")

        # 3. 自動送審（給人類審核閘門）
        self.ebook.submit_for_review(eid)
        self.kidbook.submit_for_review(kid)
        results.append(f"  📋 兩本已送審，等待人工批准")

        # 4. 如果已經有 sales data，回饋到下次選題
        sales_feedback = self.ebook.trending_topics()
        if sales_feedback:
            results.append(f"  🔄 銷售回饋：暢銷主題 → {', '.join(sales_feedback[:3])}")

        cycle_log.record("engine", "auto_cycle", f"{eid},{kid}", "; ".join(results))
        return "\n".join(results)

    def start_auto_pilot(self, llm_call=None, interval_hours=24):
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

    def status(self) -> dict:
        return {
            "ebook_published": self.ebook.total_published(),
            "kidbook_published": self.kidbook.total_published(),
            "service_active": self.service.total_active(),
            "engine_running": self._running,
            "cycle_count": len([e for e in cycle_log.log if e.get("stage") == "auto_cycle"]),
        }

    def generate_report(self, detailed: bool = False) -> str:
        st = self.status()
        lines = []
        lines.append("🏭 出版工廠日報")
        lines.append("=" * 30)
        lines.append(f"📚 電子書已出版：{st['ebook_published']} 本")
        lines.append(f"📖 童書已出版：{st['kidbook_published']} 本")
        lines.append(f"🌐 客服網站啟用：{st['service_active']} 個")
        lines.append(f"🔄 自動循環：{'🟢 運行中' if st['engine_running'] else '🔴 已停止'}")
        lines.append(f"🔄 累積循環次數：{st['cycle_count']}")

        sales = self.ebook.get_sales_summary()
        lines.append(f"💰 {sales}")

        recent = cycle_log.recent(3)
        if recent:
            lines.append("")
            lines.append("最近活動：")
            for e in recent:
                lines.append(f"  [{e['ts'][:19]}] {e['pipeline']}/{e['stage']}")

        if detailed:
            lines.append("")
            lines.append("── 各產線詳細 ──")
            lines.append(self.ebook.get_pipeline_status())
            lines.append("")
            lines.append(self.kidbook.get_pipeline_status())
            lines.append("")
            lines.append(self.service.get_pipeline_status())

        return "\n".join(lines)


engine = PublisherEngine()
