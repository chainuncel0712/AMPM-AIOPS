"""AutoContentCreatorOrgan — 自動內容建立器官，負責生成多平台行銷內容、排程發布與互動分析。"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

CONTENT_TYPES = ["announcement", "educational", "promotional", "engagement"]
PLATFORM_LIMITS = {
    "twitter": 280,
    "linkedin": 3000,
    "blog": 10000,
    "telegram": 4096,
}

TEMPLATES = {
    "twitter": {
        "announcement": "🚀 {headline}\n\n{body}\n\n{hashtags}",
        "educational": "📚 {headline}\n\n{body}\n\n{hashtags}",
        "promotional": "🔥 {headline}\n\n{body}\n\n{hashtags}",
        "engagement": "💬 {headline}\n\n{body}\n\n{hashtags}",
    },
    "linkedin": {
        "announcement": "{headline}\n\n{body}\n\n{hashtags}",
        "educational": "📖 {headline}\n\n{body}\n\n{hashtags}",
        "promotional": "💼 {headline}\n\n{body}\n\n{hashtags}",
        "engagement": "🗣️ {headline}\n\n{body}\n\n{hashtags}",
    },
    "blog": {
        "announcement": "標題：{headline}\n\n{body}\n\n標籤：{hashtags}",
        "educational": "標題：{headline}\n\n{body}\n\n標籤：{hashtags}",
        "promotional": "標題：{headline}\n\n{body}\n\n標籤：{hashtags}",
        "engagement": "標題：{headline}\n\n{body}\n\n標籤：{hashtags}",
    },
    "telegram": {
        "announcement": "{headline}\n\n{body}",
        "educational": "📘 {headline}\n\n{body}",
        "promotional": "🎯 {headline}\n\n{body}",
        "engagement": "❓ {headline}\n\n{body}",
    },
}

NICHE_IDEAS = {
    "tech": ["AI 工具評測", "開發者效率秘訣", "開源專案推薦", "雲端成本優化"],
    "finance": ["投資組合策略", "被動收入藍圖", "稅務節省技巧", "加密貨幣入門"],
    "health": ["居家運動菜單", "營養補充指南", "冥想入門教學", "睡眠品質提升"],
    "business": ["新創募資攻略", "遠端團隊管理", "客戶留存策略", "定價心理學"],
    "education": ["線上課程設計", "學習效率方法", "知識管理系統", "證照考試備戰"],
}


class AutoContentCreatorOrgan(BrainComponent):
    """自動內容建立器官 — 產生、排程並追蹤各平台行銷內容。"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._contents: Dict[str, Dict[str, Any]] = {}
        self._scheduled: Dict[str, Dict[str, Any]] = {}
        self._engagement_log: Dict[str, List[Dict[str, Any]]] = {}

    # ── 公開方法 ─────────────────────────────────────────────

    def generate_post(self, topic: str, platform: str, tone: str = "professional") -> dict:
        """為指定平台生成一則內容貼文。

        Args:
            topic: 貼文主題，例如「新產品上市」
            platform: 目標平台 (twitter / linkedin / blog / telegram)
            tone: 語調風格 (professional / casual / enthusiastic / formal)

        Returns:
            dict: 包含 content_id、平台、內容、字數等資訊。
        """
        if platform not in PLATFORM_LIMITS:
            raise ValueError(f"不支援的平台: {platform}，支援: {list(PLATFORM_LIMITS)}")
        if not topic.strip():
            raise ValueError("主題不可為空")

        content_type = self._pick_content_type(tone)
        template = TEMPLATES.get(platform, {}).get(content_type, "{headline}\n{body}")

        headline = f"{topic} — {self._tone_label(tone)}"
        body = self._build_body(topic, platform, content_type, tone)
        hashtags = self._generate_hashtags(topic, platform)

        rendered = template.format(headline=headline, body=body, hashtags=hashtags)
        rendered = rendered[: PLATFORM_LIMITS[platform]]

        content_id = str(uuid.uuid4())[:8]
        record = {
            "content_id": content_id,
            "topic": topic,
            "platform": platform,
            "tone": tone,
            "content_type": content_type,
            "content": rendered,
            "char_count": len(rendered),
            "hashtags": hashtags,
            "created_at": datetime.now().isoformat(),
        }
        self._contents[content_id] = record
        return record

    def schedule_post(self, content: dict, platform: str, time: str) -> dict:
        """排程一則內容至指定時間發布。

        Args:
            content: generate_post 回傳的內容字典，或自訂內容 dict (須含 "content" 鍵)
            platform: 目標平台
            time: 發布時間，ISO 8601 格式字串 (例如 "2026-05-20T09:00:00")

        Returns:
            dict: 排程記錄，含 schedule_id 與狀態。
        """
        if not isinstance(content, dict) or "content" not in content:
            raise ValueError("content 必須是包含 'content' 鍵的字典")

        try:
            scheduled_time = datetime.fromisoformat(time)
        except (ValueError, TypeError):
            raise ValueError("time 必須為 ISO 8601 格式，例如 '2026-05-20T09:00:00'")

        if scheduled_time <= datetime.now():
            raise ValueError("排程時間必須在未來")

        schedule_id = str(uuid.uuid4())[:8]
        record = {
            "schedule_id": schedule_id,
            "content_id": content.get("content_id", "manual"),
            "platform": platform,
            "content": content["content"],
            "scheduled_at": scheduled_time.isoformat(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self._scheduled[schedule_id] = record
        return record

    def list_scheduled_posts(self) -> List[Dict[str, Any]]:
        """列出所有已排程的貼文，按發布時間排序。

        Returns:
            list[dict]: 排程貼文清單。
        """
        items = list(self._scheduled.values())
        items.sort(key=lambda x: x.get("scheduled_at", ""))
        return items

    def get_content_ideas(self, niche: str) -> dict:
        """根據利基市場返回內容靈感清單。

        Args:
            niche: 利基領域 (tech / finance / health / business / education)

        Returns:
            dict: 含 niche 與 ideas 清單。
        """
        niche_lower = niche.lower().strip()
        ideas = NICHE_IDEAS.get(niche_lower, NICHE_IDEAS["tech"])
        return {"niche": niche_lower, "ideas": ideas, "count": len(ideas)}

    def analyze_engagement(self, post_id: str) -> dict:
        """分析指定貼文的互動數據。

        Args:
            post_id: 貼文 content_id

        Returns:
            dict: 互動分析結果。
        """
        if post_id not in self._contents:
            raise KeyError(f"找不到貼文: {post_id}")

        post = self._contents[post_id]
        # 模擬互動指標：以內容長度、類型與平台為基礎產生合理假數據
        base = len(post["content"])
        likes = int(base * 0.12) + hash(post_id) % 50
        shares = int(likes * 0.15)
        comments = int(likes * 0.08)
        reach = likes * 25 + shares * 80 + comments * 40
        engagement_rate = round((likes + shares + comments) / max(1, reach) * 100, 2)

        log_entry = {
            "post_id": post_id,
            "timestamp": datetime.now().isoformat(),
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "reach": reach,
            "engagement_rate": engagement_rate,
        }
        self._engagement_log.setdefault(post_id, []).append(log_entry)

        return {
            "post_id": post_id,
            "platform": post["platform"],
            "content_type": post["content_type"],
            "metrics": {
                "likes": likes,
                "shares": shares,
                "comments": comments,
                "reach": reach,
                "engagement_rate": engagement_rate,
            },
            "history": self._engagement_log[post_id],
        }

    def status(self) -> dict:
        """回報器官當前狀態。"""
        pending = sum(1 for s in self._scheduled.values() if s["status"] == "pending")
        published = sum(1 for s in self._scheduled.values() if s["status"] == "published")
        failed = sum(1 for s in self._scheduled.values() if s["status"] == "failed")
        return {
            "organ": "AutoContentCreatorOrgan",
            "total_contents": len(self._contents),
            "scheduled_pending": pending,
            "scheduled_published": published,
            "scheduled_failed": failed,
            "tracked_posts": len(self._engagement_log),
            "platforms": list(PLATFORM_LIMITS),
        }

    # ── 內部輔助方法 ─────────────────────────────────────────

    @staticmethod
    def _pick_content_type(tone: str) -> str:
        mapping = {
            "professional": "educational",
            "casual": "engagement",
            "enthusiastic": "promotional",
            "formal": "announcement",
        }
        return mapping.get(tone, "educational")

    @staticmethod
    def _tone_label(tone: str) -> str:
        labels = {
            "professional": "專業觀點",
            "casual": "輕鬆聊聊",
            "enthusiastic": "熱烈推薦",
            "formal": "正式公告",
        }
        return labels.get(tone, "專業觀點")

    @staticmethod
    def _build_body(topic: str, platform: str, content_type: str, tone: str) -> str:
        """根據主題與類型建立內文段落。"""
        intros = {
            "announcement": f"我們很榮幸宣布：{topic} 正式登場。這是一個重要的里程碑。",
            "educational": f"關於 {topic}，許多人常有以下誤解。今天我們逐一拆解，讓你徹底搞懂。",
            "promotional": f"限時方案來了！{topic} 提供你無法拒絕的價值，錯過不再。",
            "engagement": f"你怎麼看 {topic}？我們很好奇你的想法，歡迎留言交流。",
        }
        body = intros.get(content_type, intros["educational"])
        detail = (
            f"\n\n核心要點：\n"
            f"1. 背景：{topic} 在當前市場的重要性持續上升。\n"
            f"2. 優勢：採用正確策略可大幅提升成效。\n"
            f"3. 行動：立即評估並付諸實行。"
        )
        if platform != "twitter":
            body += detail
        return body

    @staticmethod
    def _generate_hashtags(topic: str, platform: str) -> str:
        base_tags = [topic.replace(" ", ""), "AMPM", "AIOPS"]
        if platform == "twitter":
            base_tags.append("行銷自動化")
        elif platform == "linkedin":
            base_tags.append("商業策略")
        elif platform == "telegram":
            base_tags.append("即時通知")
        return " ".join(f"#{t}" for t in base_tags)
