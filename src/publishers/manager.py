"""
PublisherManager — 上架機械組件管理器
=====================================
協調多個平台上架機械組件，以非阻塞方式執行上架作業，
並將結果回寫到 pipeline_engine 的書籍記錄。
"""
import os, json, asyncio, threading, time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable
from .base_publisher import PublisherResult
from .readmoo_publisher import ReadmooPublisher
from .kdp_publisher import KDPPublisher

BASE = Path(__file__).resolve().parent.parent.parent
PUB_LOG = BASE / "data" / "publisher_log.json"

class PublisherManager:
    def __init__(self):
        self._readmoo = None
        self._kdp = None
        self._results = {}
        self._busy = False
        self._log = []
        self._load_log()

    def _load_log(self):
        if PUB_LOG.exists():
            try:
                self._log = json.loads(PUB_LOG.read_text())
            except:
                self._log = []

    def _save_log(self):
        PUB_LOG.parent.mkdir(parents=True, exist_ok=True)
        PUB_LOG.write_text(json.dumps(self._log, ensure_ascii=False, indent=2))

    @property
    def readmoo(self) -> ReadmooPublisher:
        if not self._readmoo:
            self._readmoo = ReadmooPublisher(headless=True)
        return self._readmoo

    @property
    def kdp(self) -> KDPPublisher:
        if not self._kdp:
            self._kdp = KDPPublisher(headless=True)
        return self._kdp

    def _record(self, book_id: str, title: str, result: PublisherResult):
        entry = {
            "ts": datetime.now().isoformat(),
            "book_id": book_id,
            "title": title[:40],
            "platform": result.platform,
            "success": result.success,
            "status": result.status,
            "message": result.message[:100],
        }
        self._log.append(entry)
        if len(self._log) > 500:
            self._log = self._log[-200:]
        self._save_log()

    def is_ready(self) -> bool:
        return bool(os.getenv("READMOO_EMAIL")) and bool(os.getenv("KDP_EMAIL"))

    async def _publish_single(self, epub_path: str, metadata: dict,
                               platform: str, publisher) -> PublisherResult:
        result = await publisher.publish_book(epub_path, metadata)
        self._record(metadata.get("id", ""), metadata.get("title", ""), result)
        return result

    def publish(self, epub_path: str, metadata: dict,
                platforms: Optional[List[str]] = None,
                callback: Optional[Callable] = None) -> dict:
        if self._busy:
            return {"error": "已有上架作業進行中"}

        plats = platforms or ["readmoo", "kdp"]
        results = {}

        def _run():
            self._busy = True
            try:
                async def _async_publish():
                    tasks = []
                    if "readmoo" in plats:
                        tasks.append(self._publish_single(epub_path, metadata, "readmoo", self.readmoo))
                    if "kdp" in plats:
                        tasks.append(self._publish_single(epub_path, metadata, "kdp", self.kdp))
                    done = await asyncio.gather(*tasks, return_exceptions=True)
                    for r in done:
                        if isinstance(r, PublisherResult):
                            results[r.platform] = {"success": r.success, "message": r.message, "status": r.status}
                        elif isinstance(r, Exception):
                            results["error"] = str(r)[:200]
                    return results
                r = asyncio.run(_async_publish())
                results.update(r)
            except Exception as e:
                results["error"] = str(e)[:200]
            finally:
                self._busy = False
                if callback:
                    try:
                        callback(results)
                    except:
                        pass

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {"status": "started", "platforms": plats, "thread": True}

    def publish_sync(self, epub_path: str, metadata: dict,
                     platforms: Optional[List[str]] = None) -> dict:
        plats = platforms or ["readmoo", "kdp"]
        results = {}

        async def _run():
            if "readmoo" in plats:
                r = await self._publish_single(epub_path, metadata, "readmoo", self.readmoo)
                results["readmoo"] = {"success": r.success, "message": r.message, "status": r.status}
            if "kdp" in plats:
                r = await self._publish_single(epub_path, metadata, "kdp", self.kdp)
                results["kdp"] = {"success": r.success, "message": r.message, "status": r.status}

        try:
            asyncio.run(_run())
        except Exception as e:
            results["error"] = str(e)[:200]

        return results

    def status(self) -> dict:
        recent = self._log[-10:] if self._log else []
        platforms = {}
        if self._readmoo:
            platforms["readmoo"] = self._readmoo.to_dict()
        if self._kdp:
            platforms["kdp"] = self._kdp.to_dict()
        return {
            "busy": self._busy,
            "platforms": platforms,
            "recent_uploads": [{"ts": e["ts"][:19], "book": e["title"], "platform": e["platform"],
                                "success": e["success"]} for e in recent],
            "total_uploads": len(self._log),
        }
