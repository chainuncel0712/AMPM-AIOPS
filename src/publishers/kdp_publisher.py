"""
KDPPublisher — Amazon KDP 上架機械組件
=====================================
自動登入 KDP → 建立 Kindle 電子書 → 上傳 EPUB → 設定資訊 → 送審
"""
import os, json, time
from pathlib import Path
from typing import Optional
from .base_publisher import PublisherBase, PublisherResult

BASE = Path(__file__).resolve().parent.parent.parent

class KDPPublisher(PublisherBase):
    def __init__(self, headless: bool = True):
        super().__init__("kdp", headless)
        self.email = os.getenv("KDP_EMAIL", "")
        self.password = os.getenv("KDP_PASSWORD", "")
        self.base_url = "https://kdp.amazon.com"

    async def login(self) -> bool:
        if not self.email or not self.password:
            return False
        try:
            page = self._page
            await page.goto(self.base_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            if "kdp.amazon.com" in page.url and "signin" not in page.url.lower():
                self._logged_in = True
                return True

            email_input = await page.query_selector("input[type='email'], #ap_email, [name='email']")
            if email_input:
                await email_input.fill(self.email)
                continue_btn = await page.query_selector("#continue, input[type='submit']")
                if continue_btn:
                    await continue_btn.click()
                    await page.wait_for_timeout(2000)

            pass_input = await page.query_selector("input[type='password'], #ap_password")
            if pass_input:
                await pass_input.fill(self.password)
                signin_btn = await page.query_selector("#signInSubmit, input[type='submit']")
                if signin_btn:
                    await signin_btn.click()

            await page.wait_for_timeout(5000)

            if "kdp.amazon.com" in page.url or "author.amazon" in page.url:
                self._logged_in = True
                await self._save_cookies()
                return True

            if await page.query_selector("#auth-mfa-otp"):
                return False

            await self._screenshot("login_failed")
            return False
        except Exception as e:
            await self._screenshot("login_error")
            return False

    async def _select_ebook_option(self):
        page = self._page
        try:
            create_btn = await page.query_selector("text=Create a new title, a[href*='create'], .create-title-btn")
            if create_btn:
                await create_btn.click()
                await page.wait_for_timeout(2000)

            ebook_btn = await page.query_selector("text=Kindle eBook, [data-value='KINDLE_EBOOK'], .ebook-option")
            if ebook_btn:
                await ebook_btn.click()
                await page.wait_for_timeout(3000)
        except:
            pass

    async def upload_epub(self, epub_path: str, metadata: dict) -> PublisherResult:
        page = self._page
        try:
            await page.goto(f"{self.base_url}/books", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            await self._select_ebook_option()

            title_input = await page.query_selector("#title, input[name='title'], [data-testid='title-input']")
            if title_input:
                await title_input.fill(metadata.get("title", ""))

            author_input = await page.query_selector("#author, input[name='author'], [data-testid='author-input']")
            if author_input:
                await author_input.fill(metadata.get("author", "AMPM AI"))

            desc_iframe = await page.query_selector("iframe[title*='description'], #description_ifr")
            if desc_iframe:
                frame = await desc_iframe.content_frame()
                if frame:
                    body = await frame.query_selector("body")
                    if body:
                        await body.fill(metadata.get("description", "")[:500])

            epub_file = Path(epub_path)
            if epub_file.exists():
                file_input = await page.query_selector("input[type='file'], #manuscript-upload-input")
                if file_input:
                    await file_input.set_input_files(str(epub_file))
                    await page.wait_for_timeout(10000)
                    try:
                        await page.wait_for_selector("[data-testid='processing-complete'], text=COMPLETED", timeout=60000)
                    except:
                        pass

            await page.wait_for_timeout(3000)

            submit_btn = await page.query_selector("text=Submit, text=Publish, button[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_timeout(5000)

            current_url = page.url
            return PublisherResult(
                "kdp", True,
                "已上傳至 Amazon KDP（Kindle 電子書）並送交審核",
                url=current_url, status="pending_review"
            )
        except Exception as e:
            await self._screenshot("upload_error")
            return PublisherResult("kdp", False, f"上傳失敗: {str(e)[:200]}")
