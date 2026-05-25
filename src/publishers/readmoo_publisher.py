"""
ReadmooPublisher — Readmoo mooPub 上架機械組件
=============================================
自動登入 mooPub → 上傳 EPUB → 填寫書籍資料 → 送交審核
"""
import os, json, time
from pathlib import Path
from typing import Optional
from .base_publisher import PublisherBase, PublisherResult

BASE = Path(__file__).resolve().parent.parent.parent

class ReadmooPublisher(PublisherBase):
    def __init__(self, headless: bool = True):
        super().__init__("readmoo", headless)
        self.email = os.getenv("READMOO_EMAIL", "")
        self.password = os.getenv("READMOO_PASSWORD", "")
        self.base_url = "https://moopub.readmoo.com"

    async def login(self) -> bool:
        if not self.email or not self.password:
            return False
        try:
            page = self._page
            await page.goto(f"{self.base_url}/login", wait_until="networkidle")
            await page.wait_for_timeout(2000)

            if await page.query_selector(".user-menu"):
                self._logged_in = True
                return True

            email_input = await page.query_selector("input[type='email'], input[name='email'], input[name='account']")
            if not email_input:
                email_input = await page.query_selector("#email, #account, [placeholder*='mail']")
            if email_input:
                await email_input.fill(self.email)
            else:
                await page.wait_for_timeout(1000)

            pass_input = await page.query_selector("input[type='password'], input[name='password']")
            if pass_input:
                await pass_input.fill(self.password)

            submit_btn = await page.query_selector("button[type='submit'], .btn-login, input[type='submit']")
            if submit_btn:
                await submit_btn.click()

            await page.wait_for_timeout(5000)

            if "login" not in page.url.lower():
                self._logged_in = True
                await self._save_cookies()
                return True

            await self._screenshot("login_failed")
            return False
        except Exception as e:
            await self._screenshot("login_error")
            return False

    async def upload_epub(self, epub_path: str, metadata: dict) -> PublisherResult:
        page = self._page
        try:
            await page.goto(f"{self.base_url}/book/create", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            epub_file = Path(epub_path)
            if not epub_file.exists():
                return PublisherResult("readmoo", False, f"EPUB 不存在: {epub_path}")

            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(str(epub_file))
                await page.wait_for_timeout(5000)
            else:
                add_btn = await page.query_selector("text=新增書籍, .btn-add, [data-action='add-book']")
                if add_btn:
                    await add_btn.click()
                    await page.wait_for_timeout(3000)
                    file_input = await page.query_selector("input[type='file']")
                    if file_input:
                        await file_input.set_input_files(str(epub_file))
                        await page.wait_for_timeout(5000)

            await page.wait_for_timeout(3000)

            title_input = await page.query_selector("input[name='title'], #title, [placeholder*='書名']")
            if title_input:
                current = await title_input.input_value()
                if not current:
                    await title_input.fill(metadata.get("title", ""))

            author_input = await page.query_selector("input[name='author'], #author, [placeholder*='作者']")
            if author_input:
                current = await author_input.input_value()
                if not current:
                    await author_input.fill(metadata.get("author", "AMPM AI"))

            desc_textarea = await page.query_selector("textarea[name='description'], #description, [placeholder*='簡介']")
            if desc_textarea:
                current = await desc_textarea.input_value()
                if not current:
                    await desc_textarea.fill(metadata.get("description", "")[:500])

            price_input = await page.query_selector("input[name='price'], #price, [placeholder*='定價']")
            if price_input:
                current = await price_input.input_value()
                if not current:
                    await price_input.fill(str(metadata.get("price", 99)))

            await page.wait_for_timeout(2000)

            submit_btn = await page.query_selector("text=送交審核, .btn-submit, button[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_timeout(5000)

            current_url = page.url
            return PublisherResult(
                "readmoo", True, "已上傳至 Readmoo mooPub 並送交審核",
                url=current_url, status="pending_review"
            )
        except Exception as e:
            await self._screenshot("upload_error")
            return PublisherResult("readmoo", False, f"上傳失敗: {str(e)[:200]}")
