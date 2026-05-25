"""
Resource Scout — 資源偵查器官
================================
自動外出尋找免費優質資源，確保出版管線永不枯竭。

偵查範圍：
  - 圖片/插畫（Unsplash, Pexels, Pixabay, Openverse）
  - 字型（Google Fonts, 開源字型）
  - 圖示/SVG（FreeSVG, Tabler Icons）
  - API（免費 LLM、圖片生成、翻譯）
  - 趨勢內容（網路爬蟲熱門主題）
  - 開源工具

運作方式：
  每 N 小時自動外出偵查 → 存入資源庫 → 管線取用
"""
import json, os, threading, time, hashlib, random, re
from pathlib import Path
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "resources"

class ResourceScout:
    def __init__(self):
        self.resources_file = DATA / "catalog.json"
        self.cache_file = DATA / "cache.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._running = False
        self._thread = None
        self.last_scout_time = None
        self._load()

    def _load(self):
        with self._lock:
            for f, default in [(self.resources_file, {}), (self.cache_file, {})]:
                if f.exists():
                    try:
                        setattr(self, f.stem, json.loads(f.read_text()))
                    except:
                        setattr(self, f.stem, default)
                else:
                    setattr(self, f.stem, default)

    def _save(self):
        with self._lock:
            self.resources_file.write_text(json.dumps(self.catalog, ensure_ascii=False, indent=2))
            self.cache_file.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2))

    # ── 資源類別定義 ──
    RESOURCE_SOURCES = {
        "images": {
            "label": "免費圖片",
            "sources": [
                {"name": "Unsplash", "url": "https://api.unsplash.com/search/photos", "free": True, "key_required": True, "note": "精選高品質攝影"},
                {"name": "Pexels", "url": "https://api.pexels.com/v1/search", "free": True, "key_required": True, "note": "大量免費圖庫"},
                {"name": "Pixabay", "url": "https://pixabay.com/api/", "free": True, "key_required": True, "note": "圖片+插畫+向量圖"},
                {"name": "Openverse", "url": "https://api.openverse.engineering/v1/images/", "free": True, "key_required": False, "note": "CC 授權開放圖庫"},
                {"name": "Stable Diffusion", "url": "local", "free": True, "key_required": False, "note": "本機 AI 生成（需 GPU）"},
            ]
        },
        "illustrations": {
            "label": "插畫/向量圖",
            "sources": [
                {"name": "Humaaans", "url": "https://humaaans.com", "free": True, "key_required": False, "note": "可混搭人物插畫"},
                {"name": "unDraw", "url": "https://undraw.co", "free": True, "key_required": False, "note": "開源插畫，可改色"},
                {"name": "ManyPixels", "url": "https://www.manypixels.co/gallery", "free": True, "key_required": False, "note": "ISO 風格插畫"},
                {"name": "OpenDoodles", "url": "https://www.opendoodles.com", "free": True, "key_required": False, "note": "塗鴉風格插畫"},
                {"name": "FreeSVG", "url": "https://freesvg.org", "free": True, "key_required": False, "note": "向量圖庫"},
            ]
        },
        "fonts": {
            "label": "免費字型",
            "sources": [
                {"name": "Google Fonts", "url": "https://fonts.google.com", "free": True, "key_required": False, "note": "開源網頁字型"},
                {"name": "Noto Sans TC", "url": "https://fonts.google.com/noto", "free": True, "key_required": False, "note": "Google 繁體中文"},
                {"name": "LXGW WenKai", "url": "https://github.com/lxgw/LxgwWenKai", "free": True, "key_required": False, "note": "開源中文楷體"},
                {"name": "思源字型", "url": "https://github.com/adobe-fonts/source-han-serif", "free": True, "key_required": False, "note": "Adobe 開源繁體"},
            ]
        },
        "icons": {
            "label": "圖示/SVG",
            "sources": [
                {"name": "Tabler Icons", "url": "https://tabler-icons.io", "free": True, "key_required": False, "note": "4,900+ 開源圖示"},
                {"name": "Feather Icons", "url": "https://feathericons.com", "free": True, "key_required": False, "note": "簡約開源圖示"},
                {"name": "Lucide", "url": "https://lucide.dev", "free": True, "key_required": False, "note": "Feather 分支，持續更新"},
                {"name": "SVG Repo", "url": "https://www.svgrepo.com", "free": True, "key_required": False, "note": "50 萬+ SVG"},
            ]
        },
        "apis": {
            "label": "免費 API",
            "sources": [
                {"name": "DeepSeek API", "url": "https://platform.deepseek.com", "free": False, "key_required": True, "note": "GPT-4 級別，超低價格"},
                {"name": "NVIDIA NIM", "url": "https://build.nvidia.com", "free": True, "key_required": True, "note": "免費額度，多模型"},
                {"name": "OpenRouter", "url": "https://openrouter.ai", "free": False, "key_required": True, "note": "多供應商聚合"},
                {"name": "HuggingFace Inference", "url": "https://huggingface.co/inference", "free": True, "key_required": True, "note": "開源模型免費推論"},
                {"name": "Replicate", "url": "https://replicate.com", "free": False, "key_required": True, "note": "雲端開源模型"},
                {"name": "Stability AI", "url": "https://platform.stability.ai", "free": True, "key_required": True, "note": "圖片生成免費額度"},
                {"name": "Google Gemini", "url": "https://makersuite.google.com", "free": True, "key_required": True, "note": "免費 API 額度"},
            ]
        },
        "trends": {
            "label": "趨勢來源",
            "sources": [
                {"name": "Google Trends", "url": "https://trends.google.com", "free": True, "key_required": False, "note": "搜尋趨勢"},
                {"name": "Amazon Bestsellers", "url": "https://www.amazon.com/gp/bestsellers/books", "free": True, "key_required": False, "note": "暢銷書排行"},
                {"name": "Readmoo 暢銷", "url": "https://readmoo.com/books/bestsellers", "free": True, "key_required": False, "note": "繁體中文電子書排行"},
                {"name": "Kobo 暢銷", "url": "https://www.kobo.com/tw/ebooks/bestsellers", "free": True, "key_required": False, "note": "國際電子書排行"},
                {"name": "博客來暢銷", "url": "https://www.books.com.tw/web/books_best_50", "free": True, "key_required": False, "note": "台灣實體書排行"},
            ]
        },
        "tools": {
            "label": "開源工具",
            "sources": [
                {"name": "GitHub Trending", "url": "https://github.com/trending/python", "free": True, "key_required": False, "note": "Python 開源趨勢"},
                {"name": "Calibre", "url": "https://calibre-ebook.com", "free": True, "key_required": False, "note": "電子書轉檔工具"},
                {"name": "EPUBCheck", "url": "https://github.com/w3c/epubcheck", "free": True, "key_required": False, "note": "EPUB 驗證工具"},
                {"name": "Kindle Previewer", "url": "https://www.amazon.com/Kindle-Previewer/b?ie=UTF8&node=21381691011", "free": True, "key_required": False, "note": "Kindle 預覽工具"},
                {"name": "Inkscape", "url": "https://inkscape.org", "free": True, "key_required": False, "note": "向量繪圖編輯"},
                {"name": "GIMP", "url": "https://www.gimp.org", "free": True, "key_required": False, "note": "點陣繪圖編輯"},
                {"name": "Krita", "url": "https://krita.org", "free": True, "key_required": False, "note": "數位繪畫軟體"},
            ]
        },
    }

    # ── 核心功能 ──

    def scout_all(self, use_web=False) -> dict:
        """執行一次完整偵查，回報所有資源狀態"""
        results = {}
        for category, info in self.RESOURCE_SOURCES.items():
            results[category] = self._check_category(category, info, use_web)
        self.last_scout_time = datetime.now().isoformat()
        self._save()
        return results

    def _check_category(self, category: str, info: dict, use_web: bool) -> dict:
        """檢查單一類別的資源可用性"""
        available = []
        dead = []
        for src in info["sources"]:
            status = "unknown"
            if use_web and src["url"] != "local":
                status = self._ping_url(src["url"])
            else:
                status = "listed"
            entry = {
                "name": src["name"],
                "url": src["url"],
                "free": src["free"],
                "key_required": src["key_required"],
                "note": src["note"],
                "status": status,
                "checked_at": datetime.now().isoformat(),
            }
            if status in ("alive", "listed"):
                available.append(entry)
            else:
                dead.append(entry)
            self._add_to_catalog(category, entry)
        return {
            "label": info["label"],
            "total": len(info["sources"]),
            "available": len(available),
            "dead": len(dead),
            "sources": available + dead,
        }

    def _ping_url(self, url: str) -> str:
        """測試 URL 是否可達（輕量 HEAD 請求）"""
        try:
            req = Request(url, method="HEAD")
            req.add_header("User-Agent", "AMPM-ResourceScout/1.0")
            resp = urlopen(req, timeout=5)
            return "alive" if resp.status < 500 else "dead"
        except Exception:
            return "dead"

    def _add_to_catalog(self, category: str, entry: dict):
        with self._lock:
            if category not in self.catalog:
                self.catalog[category] = []
            existing = [e for e in self.catalog[category] if e["name"] == entry["name"]]
            if existing:
                existing[0].update(entry)
            else:
                self.catalog[category].append(entry)

    # ── 管線取用介面 ──

    def get_resource(self, category: str, query: str = "") -> list:
        """從資源庫取得指定類別的資源"""
        with self._lock:
            resources = self.catalog.get(category, [])
            if not resources:
                return self.RESOURCE_SOURCES.get(category, {}).get("sources", [])
            if query:
                q = query.lower()
                resources = [r for r in resources if q in r["name"].lower() or q in r.get("note", "").lower()]
            return resources

    def get_image_sources(self) -> list:
        return self.get_resource("images")

    def get_font_sources(self) -> list:
        return self.get_resource("fonts")

    def get_illustration_sources(self) -> list:
        return self.get_resource("illustrations")

    def get_trend_sources(self) -> list:
        return self.get_resource("trends")

    def get_api_sources(self) -> list:
        return self.get_resource("apis")

    def get_tool_sources(self) -> list:
        return self.get_resource("tools")

    def pick_random_image_source(self) -> dict:
        sources = self.get_image_sources()
        return random.choice(sources) if sources else {}

    def pick_random_illustration_style(self) -> str:
        styles = [
            "水彩手繪風格", "扁平向量插畫", "日系動漫風格",
            "鉛筆素描風格", "幾何抽象風格", "童趣塗鴉風格",
            "寫實油畫風格", "剪紙拼貼風格", "像素藝術風格",
            "線條藝術風格", "復古木刻風格", "水墨畫風格",
        ]
        return random.choice(styles)

    # ── 背景自動偵查 ──

    def start(self, interval_seconds: int = 3600):
        """啟動背景偵查（每 N 秒自動外出找資源）"""
        if self._running:
            return "🔍 資源偵查已在運行中"

        def _loop():
            self._running = True
            while self._running:
                try:
                    print(f"[ResourceScout] 外出偵查資源...")
                    result = self.scout_all()
                    total = sum(v["total"] for v in result.values())
                    avail = sum(v["available"] for v in result.values())
                    print(f"[ResourceScout] 完成：{avail}/{total} 資源可用")
                except Exception as e:
                    print(f"[ResourceScout] 偵查錯誤: {e}")
                time.sleep(interval_seconds)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return f"🔍 資源偵查已啟動（每 {interval_seconds//60} 分鐘）"

    def stop(self):
        self._running = False
        return "🔍 資源偵查已停止"

    # ── 狀態報告 ──

    def status(self) -> dict:
        with self._lock:
            total = sum(len(v) for v in self.catalog.values()) if self.catalog else 0
            return {
                "name": "ResourceScout",
                "alive": True,
                "catalog_entries": total,
                "categories": list(self.catalog.keys()) if self.catalog else [],
                "running": self._running,
                "last_scout": self.last_scout_time or "從未",
            }

    def report(self) -> str:
        """人類可讀的狀態報告"""
        lines = ["🔍 資源偵查器官狀態", "=" * 30]
        lines.append(f"  背景運行：{'🟢' if self._running else '🔴'}")
        lines.append(f"  上次偵查：{self.last_scout_time or '從未'}")
        lines.append("")
        for category, info in self.RESOURCE_SOURCES.items():
            catalog_items = self.catalog.get(category, [])
            alive_count = len(catalog_items)
            lines.append(f"  {info['label']}: {alive_count}/{len(info['sources'])} 個來源")
        return "\n".join(lines)

scout = ResourceScout()
