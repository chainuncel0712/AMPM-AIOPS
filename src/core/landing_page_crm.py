"""LandingPageCRMOrgan — 著陸頁 CRM 器官，負責頁面管理、訪客追蹤、潛在客戶管理與轉換漏斗分析。"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

LEAD_STATUSES = ["new", "contacted", "qualified", "converted"]
LEAD_SCORE_TIERS = {
    "hot": (70, 100),
    "warm": (40, 69),
    "cold": (0, 39),
}

PAGE_TEMPLATES = {
    "default": {"sections": ["hero", "features", "cta"]},
    "webinar": {"sections": ["hero", "speaker", "agenda", "registration"]},
    "product": {"sections": ["hero", "benefits", "testimonials", "pricing"]},
    "lead_magnet": {"sections": ["hero", "value_prop", "form", "social_proof"]},
}


class LandingPageCRMOrgan(BrainComponent):
    """著陸頁 CRM 器官 — 管理著陸頁、追蹤訪客行為、潛在客戶評分與轉換管線。

    潛在客戶狀態管線: new → contacted → qualified → converted。
    潛在客戶評分: cold (0-39) / warm (40-69) / hot (70-100)。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._pages: Dict[str, Dict[str, Any]] = {}
        self._visitors: Dict[str, List[Dict[str, Any]]] = {}
        self._leads: Dict[str, Dict[str, Any]] = {}
        self._conversions: Dict[str, List[Dict[str, Any]]] = {}

    # ── 公開方法 ─────────────────────────────────────────────

    def create_page(self, template: str, content: dict) -> dict:
        """建立著陸頁。

        Args:
            template: 頁面模板名稱 (default / webinar / product / lead_magnet)
            content: 頁面內容字典，例如 {"hero_title": "...", "cta_text": "..."}

        Returns:
            dict: 頁面記錄，含 page_id。
        """
        if template not in PAGE_TEMPLATES:
            raise ValueError(f"不支援的模板: {template}，支援: {list(PAGE_TEMPLATES)}")
        if not isinstance(content, dict):
            raise ValueError("content 必須為字典")

        page_id = str(uuid.uuid4())[:8]
        record = {
            "page_id": page_id,
            "template": template,
            "sections": PAGE_TEMPLATES[template]["sections"],
            "content": content,
            "created_at": datetime.now().isoformat(),
            "visitor_count": 0,
            "conversion_count": 0,
            "bounce_count": 0,
        }
        self._pages[page_id] = record
        self._visitors[page_id] = []
        self._conversions[page_id] = []
        return record

    def track_visitor(self, page_id: str, data: dict) -> dict:
        """追蹤單一訪客進入著陸頁的事件。

        Args:
            page_id: 著陸頁 ID
            data: 訪客資料，例如 {"source": "google", "device": "mobile", "session_duration": 45}

        Returns:
            dict: 訪客記錄。
        """
        if page_id not in self._pages:
            raise KeyError(f"找不到頁面: {page_id}")
        if not isinstance(data, dict):
            raise ValueError("data 必須為字典")

        visitor_id = str(uuid.uuid4())[:8]
        entry = {
            "visitor_id": visitor_id,
            "page_id": page_id,
            "data": data,
            "visited_at": datetime.now().isoformat(),
        }
        self._visitors[page_id].append(entry)
        self._pages[page_id]["visitor_count"] += 1
        return entry

    def get_conversion_stats(self, page_id: str) -> dict:
        """取得著陸頁的轉換統計。

        Args:
            page_id: 著陸頁 ID

        Returns:
            dict: 含訪客數、轉換率、跳出率等指標。
        """
        if page_id not in self._pages:
            raise KeyError(f"找不到頁面: {page_id}")

        page = self._pages[page_id]
        visitors = len(self._visitors.get(page_id, []))
        conversions = len(self._conversions.get(page_id, []))
        bounce_count = page.get("bounce_count", 0)

        conversion_rate = round(conversions / max(1, visitors) * 100, 2)
        bounce_rate = round(bounce_count / max(1, visitors) * 100, 2)

        # 平均停留時間（模擬）
        durations = [
            v.get("data", {}).get("session_duration", 0)
            for v in self._visitors.get(page_id, [])
        ]
        avg_duration = round(sum(durations) / max(1, len(durations)), 1)

        return {
            "page_id": page_id,
            "template": page["template"],
            "visitors": visitors,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "bounce_rate": bounce_rate,
            "avg_session_duration_sec": avg_duration,
            "total_bounces": bounce_count,
        }

    def add_lead(self, lead_data: dict) -> dict:
        """新增潛在客戶至名單。

        Args:
            lead_data: 客戶資料，至少含 "email" 欄位，可選 "name", "phone", "source", "notes"

        Returns:
            dict: 潛在客戶記錄，含 lead_id、狀態與評分。
        """
        if not isinstance(lead_data, dict) or "email" not in lead_data:
            raise ValueError("lead_data 必須為字典且含 'email' 欄位")

        email = lead_data["email"].strip().lower()
        if email in self._leads:
            existing = self._leads[email]
            existing["data"].update(lead_data)
            existing["updated_at"] = datetime.now().isoformat()
            return existing

        lead_id = str(uuid.uuid4())[:8]
        score = self._calculate_lead_score(lead_data)
        tier = self._score_tier(score)
        now = datetime.now().isoformat()

        record = {
            "lead_id": lead_id,
            "email": email,
            "data": lead_data,
            "status": "new",
            "score": score,
            "tier": tier,
            "created_at": now,
            "updated_at": now,
            "status_history": [{"status": "new", "timestamp": now}],
        }
        self._leads[email] = record
        return record

    def get_leads(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出潛在客戶，可依狀態過濾。

        Args:
            status: 狀態過濾 (new / contacted / qualified / converted)，若無則回傳全部

        Returns:
            list[dict]: 潛在客戶清單。
        """
        if status:
            if status not in LEAD_STATUSES:
                raise ValueError(f"無效的狀態: {status}，有效值: {LEAD_STATUSES}")
            return [l for l in self._leads.values() if l["status"] == status]
        return sorted(
            self._leads.values(), key=lambda x: x["score"], reverse=True
        )

    def update_lead_status(self, email: str, new_status: str) -> dict:
        """更新潛在客戶的管線狀態。

        Args:
            email: 客戶 email
            new_status: 目標狀態 (new / contacted / qualified / converted)

        Returns:
            dict: 更新後的客戶記錄。
        """
        email = email.strip().lower()
        if email not in self._leads:
            raise KeyError(f"找不到客戶: {email}")
        if new_status not in LEAD_STATUSES:
            raise ValueError(f"無效的狀態: {new_status}，有效值: {LEAD_STATUSES}")

        lead = self._leads[email]
        current_idx = LEAD_STATUSES.index(lead["status"])
        target_idx = LEAD_STATUSES.index(new_status)
        if target_idx < current_idx:
            raise ValueError(f"狀態不可回溯: {lead['status']} → {new_status}")

        lead["status"] = new_status
        lead["updated_at"] = datetime.now().isoformat()
        lead["status_history"].append({
            "status": new_status,
            "timestamp": lead["updated_at"],
        })

        # 若轉換為 converted，記錄轉換事件
        if new_status == "converted":
            for page_id in self._pages:
                self._pages[page_id]["conversion_count"] += 1
                self._conversions[page_id].append({
                    "lead_email": email,
                    "converted_at": datetime.now().isoformat(),
                })
                break

        return lead

    def status(self) -> dict:
        """回報器官當前狀態。"""
        status_counts = {s: 0 for s in LEAD_STATUSES}
        for lead in self._leads.values():
            s = lead["status"]
            if s in status_counts:
                status_counts[s] += 1

        return {
            "organ": "LandingPageCRMOrgan",
            "total_pages": len(self._pages),
            "total_leads": len(self._leads),
            "leads_by_status": status_counts,
            "total_visitors": sum(p.get("visitor_count", 0) for p in self._pages.values()),
            "templates_available": list(PAGE_TEMPLATES),
        }

    # ── 內部輔助方法 ─────────────────────────────────────────

    @staticmethod
    def _calculate_lead_score(data: dict) -> int:
        """根據客戶資料計算潛在客戶評分 (0-100)。"""
        score = 30

        name = data.get("name", "")
        if name and len(name.strip()) > 1:
            score += 10

        phone = data.get("phone", "")
        if phone and len(phone.strip()) >= 6:
            score += 15

        source = data.get("source", "").lower()
        if source in ("paid_ad", "廣告"):
            score += 15
        elif source in ("referral", "推薦"):
            score += 20
        elif source in ("organic", "自然搜尋"):
            score += 10
        else:
            score += 5

        company = data.get("company", "")
        if company:
            score += 10

        notes = data.get("notes", "")
        if notes and len(notes) > 20:
            score += 15

        budget = data.get("budget", "")
        if budget:
            score += 10

        return min(100, score)

    @staticmethod
    def _score_tier(score: int) -> str:
        for tier, (lo, hi) in LEAD_SCORE_TIERS.items():
            if lo <= score <= hi:
                return tier
        return "cold"
