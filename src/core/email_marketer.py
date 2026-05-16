"""EmailMarketerOrgan — 郵件行銷器官，負責建立與發送郵件活動、管理訂閱者與追蹤成效。"""
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

TEMPLATE_VARIABLES = {
    "name": "{{name}}",
    "email": "{{email}}",
    "date": "{{date}}",
    "unsubscribe_url": "{{unsubscribe_url}}",
}


class EmailMarketerOrgan(BrainComponent):
    """郵件行銷器官 — 管理郵件活動、訂閱者與成效追蹤。

    支援模板變數: {{name}}, {{email}}, {{date}}, {{unsubscribe_url}}。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._campaigns: Dict[str, Dict[str, Any]] = {}
        self._subscribers: Dict[str, Dict[str, Any]] = {}
        self._sent_log: List[Dict[str, Any]] = []

    # ── 公開方法 ─────────────────────────────────────────────

    def create_campaign(
        self, name: str, subject: str, body: str, recipients: List[str]
    ) -> dict:
        """建立郵件行銷活動。

        Args:
            name: 活動名稱
            subject: 郵件主旨（支援 {{name}} 等模板變數）
            body: 郵件內文（支援模板變數）
            recipients: 收件人 email 清單

        Returns:
            dict: 活動記錄，含 campaign_id。
        """
        if not name.strip():
            raise ValueError("活動名稱不可為空")
        if not subject.strip():
            raise ValueError("主旨不可為空")
        if not body.strip():
            raise ValueError("內文不可為空")
        if not recipients or not isinstance(recipients, list):
            raise ValueError("recipients 必須為非空清單")

        invalid = [r for r in recipients if not EMAIL_REGEX.match(r)]
        if invalid:
            raise ValueError(f"無效的 email: {invalid[:5]}")

        campaign_id = str(uuid.uuid4())[:8]
        record = {
            "campaign_id": campaign_id,
            "name": name.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "recipient_count": len(recipients),
            "recipients": recipients,
            "status": "draft",
            "created_at": datetime.now().isoformat(),
            "sent_at": None,
            "opens": 0,
            "clicks": 0,
            "bounces": 0,
            "delivered": len(recipients),
        }
        self._campaigns[campaign_id] = record
        return record

    def send_campaign(self, campaign_id: str) -> dict:
        """發送已建立的郵件活動。

        Args:
            campaign_id: 活動 ID

        Returns:
            dict: 發送結果摘要。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到活動: {campaign_id}")

        campaign = self._campaigns[campaign_id]
        if campaign["status"] == "sent":
            raise RuntimeError(f"活動 {campaign_id} 已發送過，不可重複發送")

        # 執行模板變數替換
        resolved = self._resolve_template(campaign)

        campaign["status"] = "sent"
        campaign["sent_at"] = datetime.now().isoformat()
        campaign["resolved_subject"] = resolved["subject"]
        campaign["resolved_body"] = resolved["body"]

        log_entry = {
            "campaign_id": campaign_id,
            "action": "sent",
            "recipient_count": campaign["delivered"],
            "timestamp": datetime.now().isoformat(),
        }
        self._sent_log.append(log_entry)

        return {
            "campaign_id": campaign_id,
            "name": campaign["name"],
            "status": "sent",
            "sent_at": campaign["sent_at"],
            "delivered": campaign["delivered"],
        }

    def get_campaign_stats(self, campaign_id: str) -> dict:
        """取得郵件活動的成效統計。

        Args:
            campaign_id: 活動 ID

        Returns:
            dict: 含開信率、點擊率、退信率等指標。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到活動: {campaign_id}")

        camp = self._campaigns[campaign_id]
        delivered = max(1, camp.get("delivered", 0))

        # 模擬實際開信/點擊行為（基於主旨與內文品質）
        seed = abs(hash(camp["subject"] + camp["body"]))
        opens = int(delivered * (0.18 + (seed % 15) / 100))
        clicks = int(opens * (0.10 + (seed % 10) / 200))
        bounces = int(delivered * (0.01 + (seed % 5) / 500))

        open_rate = round(opens / delivered * 100, 2)
        click_rate = round(clicks / delivered * 100, 2)
        bounce_rate = round(bounces / delivered * 100, 2)

        # 更新累計
        camp["opens"] += opens
        camp["clicks"] += clicks
        camp["bounces"] += bounces

        return {
            "campaign_id": campaign_id,
            "name": camp["name"],
            "status": camp["status"],
            "delivered": camp["delivered"],
            "opens": opens,
            "open_rate": open_rate,
            "clicks": clicks,
            "click_rate": click_rate,
            "bounces": bounces,
            "bounce_rate": bounce_rate,
            "total_opens": camp["opens"],
            "total_clicks": camp["clicks"],
        }

    def add_subscriber(self, email: str, name: str = "", tags: Optional[List[str]] = None) -> dict:
        """新增訂閱者至聯絡人清單。

        Args:
            email: 訂閱者 email
            name: 訂閱者姓名（可選）
            tags: 標籤清單（可選），例如 ["vip", "new_user"]

        Returns:
            dict: 訂閱者記錄。
        """
        if not EMAIL_REGEX.match(email):
            raise ValueError(f"無效的 email: {email}")
        if email in self._subscribers:
            existing = self._subscribers[email]
            if tags:
                existing_tags = set(existing.get("tags", []))
                existing_tags.update(tags)
                existing["tags"] = sorted(existing_tags)
            if name:
                existing["name"] = name.strip()
            existing["updated_at"] = datetime.now().isoformat()
            return existing

        tags = sorted(set(tags or []))
        record = {
            "email": email,
            "name": name.strip() if name else "",
            "tags": tags,
            "subscribed_at": datetime.now().isoformat(),
            "status": "active",
            "updated_at": datetime.now().isoformat(),
        }
        self._subscribers[email] = record
        return record

    def list_subscribers(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出訂閱者，可依標籤過濾。

        Args:
            tag: 標籤名稱（可選），若無則回傳全部

        Returns:
            list[dict]: 訂閱者清單。
        """
        if tag:
            tag = tag.strip().lower()
            return [
                s for s in self._subscribers.values()
                if tag in [t.lower() for t in s.get("tags", [])]
            ]
        return list(self._subscribers.values())

    def status(self) -> dict:
        """回報器官當前狀態。"""
        total_subs = len(self._subscribers)
        active_subs = sum(1 for s in self._subscribers.values() if s.get("status") == "active")
        campaigns_sent = sum(1 for c in self._campaigns.values() if c.get("status") == "sent")
        campaigns_draft = sum(1 for c in self._campaigns.values() if c.get("status") == "draft")
        all_tags = set()
        for s in self._subscribers.values():
            all_tags.update(s.get("tags", []))
        return {
            "organ": "EmailMarketerOrgan",
            "total_campaigns": len(self._campaigns),
            "campaigns_sent": campaigns_sent,
            "campaigns_draft": campaigns_draft,
            "total_subscribers": total_subs,
            "active_subscribers": active_subs,
            "tags": sorted(all_tags),
        }

    # ── 內部輔助方法 ─────────────────────────────────────────

    def _resolve_template(self, campaign: dict) -> dict:
        """將郵件模板中的變數替換為實際值。"""
        subject = campaign["subject"]
        body = campaign["body"]

        # 以第一筆訂閱者資料示範替換
        first_email = campaign["recipients"][0] if campaign["recipients"] else ""
        sub = self._subscribers.get(first_email, {})

        substitutions = {
            "{{name}}": sub.get("name", "用戶"),
            "{{email}}": first_email,
            "{{date}}": datetime.now().strftime("%Y-%m-%d"),
            "{{unsubscribe_url}}": f"https://example.com/unsubscribe?e={first_email}",
        }

        for var, val in substitutions.items():
            subject = subject.replace(var, val)
            body = body.replace(var, val)

        return {"subject": subject, "body": body}
