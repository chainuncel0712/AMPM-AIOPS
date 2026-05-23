"""
童書自動化生產線
選題 → 角色設定 → 故事 → 插圖 → 審核 → 上架
"""
import json, os, threading, time, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "publisher"

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

    # ── 選題 ──
    def suggest_themes(self, count=5):
        themes = [
            ("小熊學勇敢", "勇氣", "3-6"),
            ("小兔子的一天", "生活常規", "2-5"),
            ("星星不見了", "友誼", "4-7"),
            ("會說話的樹", "環保", "5-8"),
            ("彩虹下的秘密", "好奇", "3-6"),
            ("小廚師夢想", "堅持", "4-7"),
            ("月亮想回家", "歸屬", "3-6"),
            ("魔法畫筆", "創造", "5-8"),
        ]
        return random.sample(themes, min(count, len(themes)))

    def select_theme(self, title, theme, age_range):
        book_id = hashlib.md5(f"KB-{title}-{int(time.time())}".encode()).hexdigest()[:12].upper()
        self.kidbooks.append({
            "id": book_id, "title": title, "theme": theme, "age_range": age_range,
            "status": "selected", "characters": [], "story": None, "illustrations": [],
            "created_at": datetime.now().isoformat()
        })
        self._save()
        return book_id

    # ── 角色設定 ──
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
        return story

    def submit_for_review(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "pending_review"
        book["submitted_at"] = datetime.now().isoformat()
        self._save()
        return f"📖 《{book['title']}》已送審"

    def approve(self, book_id):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "approved"
        self._save()
        return f"✅ 《{book['title']}》已批准"

    def reject(self, book_id, reason):
        book = self._find(book_id)
        if not book:
            return "找不到書籍"
        book["status"] = "rejected"
        book["reject_reason"] = reason
        self._save()
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
        return f"📚 《{book['title']}》已上架到 {len(plats)} 個平台"

    def get_pipeline_status(self):
        stages = {"selected": 0, "characters_done": 0, "story_done": 0,
                  "pending_review": 0, "approved": 0, "published": 0}
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

kidbook_pipeline = KidBookPipeline()
