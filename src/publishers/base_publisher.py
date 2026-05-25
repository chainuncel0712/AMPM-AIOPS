"""
PublisherBase — 上架機械組件基底類別
======================================
所有平台自動上架機械組件（Readmoo、KDP 等）的共通基礎。
"""
import os, json, time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent.parent
COOKIE_DIR = BASE / "data" / "publisher_cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class PublisherResult:
    platform: str
    success: bool
    message: str = ""
    url: str = ""
    book_id: str = ""
    status: str = "unknown"
    details: dict = field(default_factory=dict)

class PublisherBase:
    def __init__(self, platform: str, headless: bool = True):
        self.platform = platform
        self.headless = headless
        self._browser = None
        self._context = None
        self._page = None
        self._logged_in = False

    @property
    def cookie_path(self) -> Path:
        return COOKIE_DIR / f"{self.platform.lower()}_cookies.json"

    async def _launch(self):
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
            timezone_id="Asia/Taipei"
        )
        if self.cookie_path.exists():
            try:
                cookies = json.loads(self.cookie_path.read_text())
                await self._context.add_cookies(cookies)
            except:
                pass
        self._page = await self._context.new_page()
        self._page.set_default_timeout(30000)

    async def _save_cookies(self):
        if self._context:
            cookies = await self._context.cookies()
            self.cookie_path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))

    async def _screenshot(self, name: str = "debug"):
        if self._page:
            shot_dir = BASE / "output" / "publisher_screenshots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            path = shot_dir / f"{self.platform}_{name}_{int(time.time())}.png"
            await self._page.screenshot(path=str(path), full_page=True)

    async def _close(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def login(self) -> bool:
        raise NotImplementedError

    async def upload_epub(self, epub_path: str, metadata: dict) -> PublisherResult:
        raise NotImplementedError

    async def publish_book(self, epub_path: str, metadata: dict) -> PublisherResult:
        try:
            await self._launch()
            if not await self.login():
                return PublisherResult(self.platform, False, "登入失敗", details={"stage": "login"})
            result = await self.upload_epub(epub_path, metadata)
            await self._save_cookies()
            await self._close()
            return result
        except Exception as e:
            await self._screenshot(f"error_{self.platform}")
            await self._close()
            return PublisherResult(self.platform, False, f"上架異常: {str(e)[:200]}")

    def to_dict(self) -> dict:
        return {"platform": self.platform, "logged_in": self._logged_in}
