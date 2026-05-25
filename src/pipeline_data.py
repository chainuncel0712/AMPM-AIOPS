"""
Pipeline Data Model — 統一 Book 模型
====================================
所有產品類型共用此結構，用 product_type 區分。
"""
import json, threading, hashlib, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "pipeline"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BOOKS_FILE = DATA_DIR / "books.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"
REJECTED_FILE = DATA_DIR / "rejected_topics.json"


class BookStore:
    """單一書籍儲存庫 — 所有產品的唯一真源"""

    def __init__(self):
        self._lock = threading.RLock()
        self.books: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if BOOKS_FILE.exists():
            try:
                return json.loads(BOOKS_FILE.read_text())
            except:
                return []
        return []

    def _save(self):
        with self._lock:
            BOOKS_FILE.write_text(json.dumps(self.books, ensure_ascii=False, indent=2))

    def add(self, book: Dict) -> str:
        with self._lock:
            self.books.append(book)
            self._save()
        return book["id"]

    def get(self, book_id: str) -> Optional[Dict]:
        for b in self.books:
            if b["id"] == book_id:
                return b
        return None

    def update(self, book_id: str, updates: Dict):
        with self._lock:
            book = self.get(book_id)
            if book:
                book.update(updates)
                book["updated_at"] = datetime.now().isoformat()
                self._save()

    def get_by_stage(self, stage: int) -> List[Dict]:
        return [b for b in self.books if b.get("current_stage") == stage]

    def get_by_type(self, product_type: str) -> List[Dict]:
        return [b for b in self.books if b.get("product_type") == product_type]

    def active_books(self) -> List[Dict]:
        return [b for b in self.books if b.get("current_stage", 0) not in (0, 10)]

    def stats(self) -> Dict:
        by_stage = {}
        for i in range(1, 10):
            by_stage[str(i)] = len(self.get_by_stage(i))
        return {
            "total": len(self.books),
            "by_stage": by_stage,
            "by_type": {pt: len(self.get_by_type(pt)) for pt in set(b.get("product_type", "?") for b in self.books)},
            "active": len(self.active_books()),
            "published": len([b for b in self.books if b.get("current_stage") == 9]),
        }


store = BookStore()


class ReviewStore:
    """審核狀態儲存"""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        if REVIEWS_FILE.exists():
            try:
                return json.loads(REVIEWS_FILE.read_text())
            except:
                return {}
        return {}

    def _save(self):
        REVIEWS_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))

    def set(self, key: str, status: str):
        self.data[key] = status
        self._save()

    def get(self, key: str) -> str:
        return self.data.get(key, "pending")

    def batch_set(self, prefix: str, status: str):
        for k in list(self.data.keys()):
            if k.startswith(prefix):
                self.data[k] = status
        self._save()


reviews = ReviewStore()


class RejectedStore:
    """淘汰主題記憶"""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        if REJECTED_FILE.exists():
            try:
                return json.loads(REJECTED_FILE.read_text())
            except:
                return {}
        return {}

    def _save(self):
        REJECTED_FILE.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))

    def add(self, topic: str):
        self.data[topic] = self.data.get(topic, 0) + 1
        self._save()

    def get_all(self) -> Dict:
        return dict(self.data)

    def should_filter(self, topic: str) -> bool:
        return self.data.get(topic, 0) >= 3


rejected = RejectedStore()


def create_book(product_type: str, title: str, **kwargs) -> Dict:
    """建立統一的 Book 物件"""
    ts = datetime.now().isoformat()
    book_id = hashlib.md5(f"{product_type}-{title}-{int(time.time())}".encode()).hexdigest()[:12].upper()
    return {
        "id": book_id,
        "product_type": product_type,
        "current_stage": 1,
        "stage_data": {
            "1": {"title": title, "approved": False, "approved_by": "", "approved_at": "", "reject_reason": "", **kwargs},
            "2": {}, "3": {}, "4": {}, "5": {}, "6": {}, "7": {}, "8": {}, "9": {}, "10": {}
        },
        "created_at": ts, "updated_at": ts
    }
