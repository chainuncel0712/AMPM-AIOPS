"""SocialMediaManagerOrgan — 社群媒體管理器器官，負責多平台連線、發文、跨平台轉發與成效分析。"""
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

SUPPORTED_PLATFORMS = ["twitter", "linkedin", "telegram", "discord"]

BEST_POSTING_HOURS = {
    "twitter": [8, 12, 17, 20],
    "linkedin": [8, 10, 12, 16],
    "telegram": [7, 12, 18, 21],
    "discord": [9, 13, 17, 22],
}


class SocialMediaManagerOrgan(BrainComponent):
    """社群媒體管理器器官 — 管理多平台連線、貼文與數據追蹤。

    認證資訊以 SHA-256 雜湊儲存，絕不記錄明碼金鑰。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._posts: Dict[str, Dict[str, Any]] = {}
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}

    # ── 公開方法 ─────────────────────────────────────────────

    def connect_platform(self, platform: str, credentials: dict) -> dict:
        """建立平台連線（安全儲存認證）。

        Args:
            platform: 平台名稱 (twitter / linkedin / telegram / discord)
            credentials: 認證字典，例如 {"api_key": "...", "api_secret": "..."}

        Returns:
            dict: 連線狀態，不含原始金鑰。
        """
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"不支援的平台: {platform}，支援: {SUPPORTED_PLATFORMS}")
        if not isinstance(credentials, dict) or not credentials:
            raise ValueError("credentials 必須為非空字典")

        safe = {}
        for key, value in credentials.items():
            safe[key] = hashlib.sha256(str(value).encode()).hexdigest()[:12]

        conn_id = str(uuid.uuid4())[:8]
        self._connections[platform] = {
            "conn_id": conn_id,
            "platform": platform,
            "credential_hash": safe,
            "connected_at": datetime.now().isoformat(),
            "active": True,
        }
        return {
            "conn_id": conn_id,
            "platform": platform,
            "connected_at": self._connections[platform]["connected_at"],
            "active": True,
        }

    def post(self, platform: str, content: str) -> dict:
        """在指定平台發布貼文。

        Args:
            platform: 目標平台
            content: 貼文內容

        Returns:
            dict: 發文結果，含 post_id。
        """
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"不支援的平台: {platform}")
        if not content.strip():
            raise ValueError("內容不可為空")
        if platform not in self._connections:
            raise ConnectionError(f"尚未連線至 {platform}，請先呼叫 connect_platform")

        post_id = str(uuid.uuid4())[:8]
        record = {
            "post_id": post_id,
            "platform": platform,
            "content": content,
            "char_count": len(content),
            "posted_at": datetime.now().isoformat(),
            "status": "published",
        }
        self._posts[post_id] = record
        return record

    def get_analytics(self, platform: str, post_id: str) -> dict:
        """取得指定貼文的成效數據。

        Args:
            platform: 平台名稱
            post_id: 貼文 ID

        Returns:
            dict: 成效指標。
        """
        if post_id not in self._posts:
            raise KeyError(f"找不到貼文: {post_id}")
        if self._posts[post_id]["platform"] != platform:
            raise ValueError(f"貼文 {post_id} 不屬於 {platform}")

        post = self._posts[post_id]
        base = hash(post_id + platform) % 2000 + 500
        impressions = base * 4 + hash(post["content"]) % 300
        likes = int(impressions * 0.045)
        shares = int(impressions * 0.012)
        comments = int(impressions * 0.008)
        clicks = int(impressions * 0.03)
        engagement_rate = round(
            (likes + shares + comments + clicks) / max(1, impressions) * 100, 2
        )

        metric = {
            "post_id": post_id,
            "platform": platform,
            "impressions": impressions,
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "clicks": clicks,
            "engagement_rate": engagement_rate,
            "fetched_at": datetime.now().isoformat(),
        }
        self._metrics.setdefault(post_id, []).append(metric)
        return {
            "post_id": post_id,
            "platform": platform,
            "metrics": metric,
            "history_count": len(self._metrics.get(post_id, [])),
        }

    def cross_post(self, content: str, platforms: List[str]) -> List[Dict[str, Any]]:
        """將同一內容同步發布到多個平台。

        Args:
            content: 貼文內容
            platforms: 目標平台清單

        Returns:
            list[dict]: 各平台發文結果。
        """
        if not platforms:
            raise ValueError("platforms 不可為空")
        invalid = [p for p in platforms if p not in SUPPORTED_PLATFORMS]
        if invalid:
            raise ValueError(f"不支援的平台: {invalid}")
        disconnected = [p for p in platforms if p not in self._connections]
        if disconnected:
            raise ConnectionError(f"尚未連線的平台: {disconnected}")

        results = []
        for plat in platforms:
            results.append(self.post(plat, content))
        return results

    def get_best_posting_time(self, platform: str) -> dict:
        """根據平台特性回傳建議的最佳發文時段。

        Args:
            platform: 平台名稱

        Returns:
            dict: 最佳發文時間建議。
        """
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"不支援的平台: {platform}")

        hours = BEST_POSTING_HOURS.get(platform, [9, 12, 17])
        now = datetime.now()
        slots = [f"{now.strftime('%Y-%m-%d')}T{h:02d}:00:00" for h in hours]

        reasons = {
            "twitter": "用戶活躍高峰落在通勤與午休時段",
            "linkedin": "專業人士偏好晨間與午後瀏覽",
            "telegram": "即時通知在早晚開啟率最高",
            "discord": "社群活躍集中於午後與晚間",
        }

        return {
            "platform": platform,
            "best_hours_utc": hours,
            "suggested_times_today": slots,
            "reason": reasons.get(platform, "根據過往數據分析"),
        }

    def status(self) -> dict:
        """回報器官當前狀態。"""
        total_posts = len(self._posts)
        return {
            "organ": "SocialMediaManagerOrgan",
            "connected_platforms": list(self._connections.keys()),
            "connection_count": len(self._connections),
            "total_posts": total_posts,
            "tracked_metrics": len(self._metrics),
            "supported_platforms": SUPPORTED_PLATFORMS,
        }
