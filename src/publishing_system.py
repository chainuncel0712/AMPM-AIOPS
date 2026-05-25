"""
Publishing System — 完整上架系統
=================================
多平台發布、元數據管理、狀態追蹤。
"""
import json, hashlib, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

BASE = Path(__file__).resolve().parent.parent
PUB_DIR = BASE / "outputs" / "published"
PUB_DIR.mkdir(parents=True, exist_ok=True)

# 平台規格
PLATFORM_SPECS = {
    "kdp": {
        "name": "Amazon Kindle Direct Publishing",
        "icon": "📦",
        "formats": ["epub", "pdf"],
        "max_size_mb": 50,
        "supported_langs": ["zh", "en"],
        "requirements": ["封面 2560x1600", "EPUB 3.0", "目錄完整"],
        "royalty": "35%-70%",
        "status": "ready" if True else "need_creds",
    },
    "readmoo": {
        "name": "Readmoo 讀墨",
        "icon": "📱",
        "formats": ["epub", "pdf"],
        "max_size_mb": 100,
        "supported_langs": ["zh"],
        "requirements": ["EPUB 2.0/3.0", "ISBN 可選", "繁體中文"],
        "royalty": "50%-60%",
        "status": "ready" if True else "need_creds",
    },
    "google_books": {
        "name": "Google Play Books",
        "icon": "📗",
        "formats": ["epub", "pdf"],
        "max_size_mb": 100,
        "supported_langs": ["zh", "en"],
        "requirements": ["EPUB 2.0/3.0", "封面", "ISBN 可選"],
        "royalty": "52%-70%",
        "status": "need_setup",
    },
    "pubu": {
        "name": "Pubu 書城",
        "icon": "📘",
        "formats": ["epub", "pdf"],
        "max_size_mb": 200,
        "supported_langs": ["zh"],
        "requirements": ["EPUB", "封面", "ISBN 可選"],
        "royalty": "60%",
        "status": "need_setup",
    },
    "kobo": {
        "name": "Kobo 樂天",
        "icon": "📙",
        "formats": ["epub"],
        "max_size_mb": 50,
        "supported_langs": ["zh", "en"],
        "requirements": ["EPUB 3.0", "封面", "目錄"],
        "royalty": "45%-70%",
        "status": "need_setup",
    },
    # ── 新平台 ──
    "audible": {
        "name": "Audible (Amazon 有聲書)",
        "icon": "🎧",
        "formats": ["mp3", "aax"],
        "max_size_mb": 500,
        "supported_langs": ["zh", "en"],
        "requirements": ["無損音檔", "章節分段", "旁白專業"],
        "royalty": "25%-40%",
        "status": "need_setup",
    },
    "kobo_audio": {
        "name": "Kobo 有聲書",
        "icon": "🎧",
        "formats": ["mp3"],
        "max_size_mb": 500,
        "supported_langs": ["zh", "en"],
        "requirements": ["MP3 128kbps+", "章節標記"],
        "royalty": "45%",
        "status": "need_setup",
    },
    "soundon": {
        "name": "SoundOn (Podcast 平台)",
        "icon": "🎙️",
        "formats": ["mp3", "rss"],
        "max_size_mb": 200,
        "supported_langs": ["zh", "en"],
        "requirements": ["RSS Feed", "封面 1400x1400"],
        "royalty": "廣告/sponsor 收入",
        "status": "need_setup",
    },
    "youtube": {
        "name": "YouTube (會員頻道)",
        "icon": "▶️",
        "formats": ["mp4", "webm"],
        "max_size_mb": 1000,
        "supported_langs": ["zh", "en"],
        "requirements": ["1080p+", "縮圖", "CC字幕"],
        "royalty": "會員費 + 廣告分潤",
        "status": "need_setup",
    },
    "patreon": {
        "name": "Patreon (訂閱制)",
        "icon": "💎",
        "formats": ["text", "image", "video"],
        "max_size_mb": 200,
        "supported_langs": ["zh", "en"],
        "requirements": ["定期更新", "會員分級內容"],
        "royalty": "月費制 (自訂)",
        "status": "need_setup",
    },
    "substack": {
        "name": "Substack (電子報)",
        "icon": "📧",
        "formats": ["html", "email"],
        "max_size_mb": 10,
        "supported_langs": ["zh", "en"],
        "requirements": ["郵件格式", "訂閱管理"],
        "royalty": "月費/年費 (自訂)",
        "status": "need_setup",
    },
    "google_scholar": {
        "name": "Google Scholar",
        "icon": "🎓",
        "formats": ["pdf"],
        "max_size_mb": 20,
        "supported_langs": ["zh", "en"],
        "requirements": ["學術格式", "引用完整", "摘要"],
        "royalty": "開放存取/付費",
        "status": "need_setup",
    },
    "researchgate": {
        "name": "ResearchGate",
        "icon": "🔬",
        "formats": ["pdf"],
        "max_size_mb": 50,
        "supported_langs": ["zh", "en"],
        "requirements": ["研究格式", "DOI 可選"],
        "royalty": "免費/付費請求",
        "status": "need_setup",
    },
}

class PublishingManager:
    """上架管理器 — 完整發布生命週期"""

    def __init__(self):
        self.log: List[Dict] = []
        self._load_log()

    def _load_log(self):
        p = PUB_DIR / "publish_log.json"
        if p.exists():
            try: self.log = json.loads(p.read_text())
            except: self.log = []

    def _save_log(self):
        (PUB_DIR / "publish_log.json").write_text(json.dumps(self.log, ensure_ascii=False, indent=2))

    # ── 發布準備 ──

    def prepare_book(self, book: Dict) -> Dict:
        """為一本書準備所有平台的上架素材"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        book_id = book["id"]
        product_type = book.get("product_type", "ebook")
        word_count = len(book.get("stage_data", {}).get("4", {}).get("content", ""))

        # 生成元數據
        metadata = {
            "title": title,
            "title_en": title,  # TODO: translate
            "author": "AMPM-AIOPS",
            "language": book.get("language", "bilingual"),
            "description": book.get("stage_data", {}).get("9", {}).get("description", ""),
            "word_count": word_count,
            "category": product_type,
            "keywords": self._extract_keywords(title),
            "age_range": book.get("stage_data", {}).get("1", {}).get("age_range", ""),
            "isbn": "",
            "price": self._suggest_price(product_type, word_count),
            "created_at": book.get("created_at", ""),
        }

        # 檢查格式產出
        layout = book.get("stage_data", {}).get("7", {})
        output_path = layout.get("output", "")
        has_output = bool(output_path and Path(output_path).exists())

        # 決定可上架平台
        suitable_platforms = self._get_suitable_platforms(product_type, book.get("language", "zh"))

        publish_item = {
            "book_id": book_id,
            "title": title,
            "metadata": metadata,
            "platforms": suitable_platforms,
            "output_path": output_path,
            "has_output": has_output,
            "status": "ready" if has_output else "missing_output",
            "prepared_at": datetime.now().isoformat(),
            "publish_history": [],
        }

        # 儲存
        item_path = PUB_DIR / f"{book_id}.json"
        item_path.write_text(json.dumps(publish_item, ensure_ascii=False, indent=2))

        # 記錄
        self.log.append({"ts": datetime.now().isoformat(), "book_id": book_id, "action": "prepare", "title": title[:40]})
        self._save_log()

        return publish_item

    def get_prepared_books(self) -> List[Dict]:
        items = []
        for f in sorted(PUB_DIR.glob("*.json"), reverse=True):
            if f.name in ("publish_log.json",): continue
            try: items.append(json.loads(f.read_text()))
            except: pass
        return items

    def get_platform_status(self) -> Dict:
        return {
            name: {"name": spec["name"], "icon": spec["icon"], "status": spec["status"],
                    "formats": spec["formats"], "royalty": spec["royalty"]}
            for name, spec in PLATFORM_SPECS.items()
        }

    # ── 輔助 ──

    def _extract_keywords(self, title: str) -> List[str]:
        kw = [w for w in title.replace("："," ").replace("《","").replace("》","").replace("的","").split() if len(w) >= 2]
        return kw[:10] if kw else [title[:20]]

    def _suggest_price(self, product_type: str, word_count: int) -> Dict:
        prices = {
            "ebook": {"ntd": 199, "usd": 6.99},
            "kidbook": {"ntd": 149, "usd": 4.99},
            "comic": {"ntd": 129, "usd": 4.49},
            "novel": {"ntd": 299, "usd": 9.99},
            "short_story": {"ntd": 79, "usd": 2.99},
            "magazine": {"ntd": 149, "usd": 4.99},
            "edu_book": {"ntd": 349, "usd": 11.99},
            "exam_book": {"ntd": 499, "usd": 15.99},
            "reference_book": {"ntd": 299, "usd": 9.99},
        }
        return prices.get(product_type, {"ntd": 199, "usd": 6.99})

    def _get_suitable_platforms(self, product_type: str, lang: str) -> List[str]:
        suitable = ["readmoo"]  # Readmoo always suitable for zh
        if lang in ("en", "bilingual"):
            suitable.append("kdp")
        if product_type in ("ebook", "novel", "reference_book"):
            suitable.append("google_books")
            suitable.append("pubu")
        if product_type in ("comic",):
            suitable.append("kobo")
        return suitable

    def record_publish(self, book_id: str, platform: str, success: bool, msg: str = ""):
        item_path = PUB_DIR / f"{book_id}.json"
        if item_path.exists():
            data = json.loads(item_path.read_text())
            data["publish_history"].append({
                "platform": platform, "success": success, "message": msg[:100],
                "ts": datetime.now().isoformat()
            })
            item_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        self.log.append({
            "ts": datetime.now().isoformat(), "book_id": book_id,
            "action": "publish", "platform": platform, "success": success, "message": msg[:100]
        })
        self._save_log()


publisher = PublishingManager()
