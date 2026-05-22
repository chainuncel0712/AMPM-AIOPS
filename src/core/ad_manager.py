"""AdManagerOrgan — 廣告管理器器官，負責廣告活動建立、預算優化、A/B 測試與成效追蹤。"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

AD_PLATFORMS = ["google", "facebook", "linkedin", "twitter", "tiktok"]

PLATFORM_CPC_ESTIMATES = {
    "google": 1.50,
    "facebook": 0.80,
    "linkedin": 5.00,
    "twitter": 1.20,
    "tiktok": 0.60,
}


class AdManagerOrgan(BrainComponent):
    """廣告管理器器官 — 管理付費廣告活動、追蹤花費與轉換成效、提供預算分配建議。"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._campaigns: Dict[str, Dict[str, Any]] = {}
        self._ab_tests: Dict[str, Dict[str, Any]] = {}
        self._spend_log: List[Dict[str, Any]] = []

    # ── 公開方法 ─────────────────────────────────────────────

    def create_campaign(
        self,
        platform: str,
        budget: float,
        targeting: dict,
        creative: dict,
    ) -> dict:
        """建立新的廣告活動。

        Args:
            platform: 廣告平台 (google / facebook / linkedin / twitter / tiktok)
            budget: 總預算（美元）
            targeting: 目標受眾設定，例如 {"age_range": [25, 45], "interests": ["tech"]}
            creative: 廣告素材設定，例如 {"headline": "...", "body": "...", "cta": "..."}

        Returns:
            dict: 活動記錄，含 campaign_id。
        """
        if platform not in AD_PLATFORMS:
            raise ValueError(f"不支援的廣告平台: {platform}，支援: {AD_PLATFORMS}")
        if budget <= 0:
            raise ValueError("預算必須大於 0")
        if not isinstance(targeting, dict):
            raise ValueError("targeting 必須為字典")
        if not isinstance(creative, dict):
            raise ValueError("creative 必須為字典")

        campaign_id = str(uuid.uuid4())[:8]
        cpc_est = PLATFORM_CPC_ESTIMATES.get(platform, 1.0)
        record = {
            "campaign_id": campaign_id,
            "platform": platform,
            "budget": budget,
            "remaining_budget": budget,
            "targeting": targeting,
            "creative": creative,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "spend": 0.0,
            "cpa": 0.0,
            "paused_at": None,
        }
        self._campaigns[campaign_id] = record
        return record

    def get_campaign_stats(self, campaign_id: str) -> dict:
        """取得廣告活動的即時成效統計。

        Args:
            campaign_id: 活動 ID

        Returns:
            dict: 含曝光、點擊、轉換、CPA、ROAS 等指標。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到廣告活動: {campaign_id}")

        camp = self._campaigns[campaign_id]
        cpc = PLATFORM_CPC_ESTIMATES.get(camp["platform"], 1.0)
        seed = abs(hash(campaign_id + camp["platform"]))

        # 模擬累計數據（基於剩餘預算）
        spent_ratio = min(1.0, (camp["budget"] - camp["remaining_budget"]) / max(1, camp["budget"]))
        base_impressions = int(camp["budget"] / cpc * 100) + seed % 500
        impressions = int(base_impressions * spent_ratio)
        clicks = int(impressions * (0.02 + (seed % 10) / 300))
        conv_rate = 0.01 + (seed % 8) / 500
        conversions = max(1, int(clicks * conv_rate))
        spend = round(clicks * cpc, 2)
        cpa = round(spend / max(1, conversions), 2)
        roas = round((conversions * 25) / max(0.01, spend), 1)

        # 更新記錄
        camp["impressions"] = max(camp["impressions"], impressions)
        camp["clicks"] = max(camp["clicks"], clicks)
        camp["conversions"] = max(camp["conversions"], conversions)
        camp["spend"] = max(camp["spend"], spend)
        camp["cpa"] = cpa

        return {
            "campaign_id": campaign_id,
            "platform": camp["platform"],
            "status": camp["status"],
            "budget": camp["budget"],
            "spend": spend,
            "remaining_budget": round(camp["remaining_budget"], 2),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(clicks / max(1, impressions) * 100, 2),
            "conversions": conversions,
            "conversion_rate": round(conversions / max(1, clicks) * 100, 2),
            "cpa": cpa,
            "roas": roas,
        }

    def optimize_budget(self, campaign_id: str) -> dict:
        """根據成效數據提供預算調整建議。

        Args:
            campaign_id: 活動 ID

        Returns:
            dict: 含預算建議與理由。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到廣告活動: {campaign_id}")

        stats = self.get_campaign_stats(campaign_id)
        camp = self._campaigns[campaign_id]
        cpa = stats["cpa"]
        roas = stats["roas"]
        platform_cpc = PLATFORM_CPC_ESTIMATES.get(camp["platform"], 1.0)

        suggestions = []
        action = "maintain"

        if roas >= 3.0:
            suggestions.append("ROAS 表現優異，建議增加 20%-50% 預算以放大成效")
            action = "scale_up"
        elif roas >= 1.5:
            suggestions.append("ROAS 尚可，建議小幅增加 10% 預算觀察數據")
            action = "scale_up"
        elif roas < 1.0:
            suggestions.append("ROAS 低於 1.0，建議暫停或調整目標受眾")
            action = "reduce"

        if cpa > camp["budget"] * 0.3:
            suggestions.append("CPA 過高，建議優化廣告素材與到達頁以提高轉換率")

        # 跨平台建議
        if camp["platform"] == "linkedin" and camp["budget"] > 500:
            suggestions.append("LinkedIn CPM 偏高，可考慮將部分預算移至 Facebook 獲取較低 CPM")

        return {
            "campaign_id": campaign_id,
            "current_budget": camp["budget"],
            "recommended_action": action,
            "suggestions": suggestions,
            "projected_cpa": cpa,
            "projected_roas": roas,
        }

    def pause_campaign(self, campaign_id: str) -> dict:
        """暫停進行中的廣告活動。

        Args:
            campaign_id: 活動 ID

        Returns:
            dict: 更新後的活動狀態。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到廣告活動: {campaign_id}")

        camp = self._campaigns[campaign_id]
        if camp["status"] == "paused":
            return {"campaign_id": campaign_id, "status": "paused", "message": "活動已處於暫停狀態"}

        camp["status"] = "paused"
        camp["paused_at"] = datetime.now().isoformat()
        return {
            "campaign_id": campaign_id,
            "status": "paused",
            "paused_at": camp["paused_at"],
            "remaining_budget": round(camp["remaining_budget"], 2),
        }

    def status(self) -> dict:
        """回報器官當前狀態。"""
        active = sum(1 for c in self._campaigns.values() if c["status"] == "active")
        paused = sum(1 for c in self._campaigns.values() if c["status"] == "paused")
        total_spend = sum(c.get("spend", 0) for c in self._campaigns.values())
        total_conversions = sum(c.get("conversions", 0) for c in self._campaigns.values())
        return {
            "organ": "AdManagerOrgan",
            "total_campaigns": len(self._campaigns),
            "active_campaigns": active,
            "paused_campaigns": paused,
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "ab_tests_running": len(self._ab_tests),
            "supported_platforms": AD_PLATFORMS,
        }
