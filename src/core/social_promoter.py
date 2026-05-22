"""SocialPromoterOrgan — 社群推廣引擎器官，負責跨 15+ 社群平台之註冊、內容發佈、排程與成效分析。"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent
from tools import tool

PLATFORMS_CONFIG: Dict[str, Dict[str, Any]] = {
    "twitter": {
        "name": "Twitter / X",
        "char_limit": 280,
        "best_hours": [8, 9, 10, 12, 17, 18],
        "media_support": ["text", "image", "video", "link"],
        "content_style": "精簡有力，善用 emoji 與話題標籤，280 字內抓住目光",
        "setup_guide": "上傳專業大頭貼（400x400），橫幅圖片（1500x500），個人簡介須含關鍵詞與行動呼籲連結。啟用雙重驗證以保護帳號安全。",
        "hashtag_limit": 3,
    },
    "instagram": {
        "name": "Instagram",
        "char_limit": 2200,
        "best_hours": [11, 12, 13, 19, 20, 21],
        "media_support": ["image", "video", "carousel", "link"],
        "content_style": "視覺優先，高品質圖片搭配簡潔文案，善用限時動態與 Reels 提升觸及",
        "setup_guide": "切換為專業帳號以解鎖洞察報告。大頭貼需清晰品牌 Logo，精選動態封面維持品牌一致性。個人簡介加入網站連結與行動按鈕。",
        "hashtag_limit": 30,
    },
    "facebook": {
        "name": "Facebook",
        "char_limit": 63206,
        "best_hours": [9, 10, 11, 12, 13],
        "media_support": ["text", "image", "video", "carousel", "link"],
        "content_style": "社群導向，影片與連結貼文有較高觸及率，避免過度商業化語氣",
        "setup_guide": "建立粉絲專頁而非使用個人檔案。設定行動呼籲按鈕（如「瞭解更多」），完善關於頁面資訊，包含營業時間、官網與聯絡方式。",
        "hashtag_limit": 5,
    },
    "linkedin": {
        "name": "LinkedIn",
        "char_limit": 3000,
        "best_hours": [8, 9, 10, 12, 16, 17, 18],
        "media_support": ["text", "image", "video", "carousel", "link"],
        "content_style": "專業商業語氣，條列式重點、產業洞察與成功案例最受歡迎",
        "setup_guide": "完整填寫公司頁面，包含 Logo、封面圖、公司簡介與員工人數。定期發布產業趨勢與專業見解建立品牌權威。使用 LinkedIn 文章功能進行深度內容行銷。",
        "hashtag_limit": 5,
    },
    "tiktok": {
        "name": "TikTok",
        "char_limit": 4000,
        "best_hours": [7, 8, 9, 19, 20, 21, 22, 23],
        "media_support": ["video"],
        "content_style": "短影音為主，前三秒決定留存率，善用熱門音樂、特效與挑戰賽",
        "setup_guide": "使用 TikTok 企業帳號以取得分析工具。影片長度建議 15-60 秒，垂直拍攝 9:16 比例。描述欄加入號召性用語與相關話題標籤。",
        "hashtag_limit": 10,
    },
    "youtube": {
        "name": "YouTube",
        "char_limit": 5000,
        "best_hours": [12, 13, 14, 15, 16, 19, 20, 21, 22],
        "media_support": ["video"],
        "content_style": "長影片教學與產品展示，標題與縮圖是點擊率關鍵，SEO 優化描述",
        "setup_guide": "自訂頻道橫幅（2560x1440）與品牌浮水印。每部影片撰寫含關鍵詞的描述欄，加入時間戳記與相關播放清單。定期上傳提升演算法推薦權重。",
        "hashtag_limit": 15,
    },
    "pinterest": {
        "name": "Pinterest",
        "char_limit": 500,
        "best_hours": [20, 21, 22, 23, 2, 3, 4],
        "media_support": ["image", "video"],
        "content_style": "垂直圖片為主（2:3 比例），搜尋引擎導向，關鍵詞豐富的描述決定曝光",
        "setup_guide": "申請企業帳號並啟用 Rich Pins（豐富圖釘）以顯示即時價格與庫存資訊。建立主題看板分類內容，每張圖釘描述需含 SEO 關鍵詞。",
        "hashtag_limit": 5,
    },
    "reddit": {
        "name": "Reddit",
        "char_limit": 40000,
        "best_hours": [6, 7, 8, 9],
        "media_support": ["text", "image", "video", "link"],
        "content_style": "社群為王，真誠分享價值而非推銷，遵守各 subreddit 規則，參與討論建立聲譽",
        "setup_guide": "選擇相關 subreddit 並先以真誠互動建立聲譽再發布內容。遵守各看板發文規則，避免含短網址與過度自我宣傳。以文字貼文搭配外部連結最有效。",
        "hashtag_limit": 0,
    },
    "discord": {
        "name": "Discord",
        "char_limit": 2000,
        "best_hours": [9, 10, 11, 12, 13, 14, 15],
        "media_support": ["text", "image", "video", "link"],
        "content_style": "即時對話風格，善用頻道分類、機器人自動化推播與角色標記通知",
        "setup_guide": "建立伺服器並設定頻道分類（公告、討論、客服等）。加入社群機器人自動排程公告。設定角色權限與歡迎訊息，定期舉辦活動凝聚社群。",
        "hashtag_limit": 0,
    },
    "telegram": {
        "name": "Telegram",
        "char_limit": 4096,
        "best_hours": [7, 12, 18, 21],
        "media_support": ["text", "image", "video", "link"],
        "content_style": "簡潔行動導向，善用頻道廣播與群組互動雙軌經營",
        "setup_guide": "建立公開頻道並自訂連結（t.me/品牌名稱）。使用機器人自動發佈、排程與互動回覆。置頂重要訊息，善用投票功能收集用戶意見。",
        "hashtag_limit": 5,
    },
    "threads": {
        "name": "Threads",
        "char_limit": 500,
        "best_hours": [8, 9, 10, 18, 19, 20, 21],
        "media_support": ["text", "image", "video", "link", "carousel"],
        "content_style": "輕鬆對話式文字為主，500 字內真誠交流，情境分享與即時互動",
        "setup_guide": "以 Instagram 帳號一鍵登入建立。個人簡介簡潔有力，表達品牌個性。每日多次發布短文互動，善用回覆串建立社群對話。",
        "hashtag_limit": 3,
    },
    "medium": {
        "name": "Medium",
        "char_limit": 100000,
        "best_hours": [8, 9, 10],
        "media_support": ["text", "image", "link"],
        "content_style": "長文深度寫作，故事驅動與專業知識分享，段落分明、可讀性高",
        "setup_guide": "建立品牌 Publication（出版品）以匯集所有文章。每篇文章加入 5 個主題標籤以增加分發觸及。在文章底部加入行動呼籲與電子報訂閱連結。",
        "hashtag_limit": 5,
    },
    "quora": {
        "name": "Quora",
        "char_limit": 100000,
        "best_hours": [8, 9, 10, 17, 18, 19, 20],
        "media_support": ["text", "image", "link"],
        "content_style": "專業問答格式，詳細且有深度的回答獲得最多曝光，附上來源與數據加強可信度",
        "setup_guide": "個人檔案完整填入專業領域與經歷，建立主題追蹤清單。選擇高追蹤數問題回答，回答結構需有開頭、主文與結論，適時引用產品為解決方案。",
        "hashtag_limit": 0,
    },
    "producthunt": {
        "name": "ProductHunt",
        "char_limit": 260,
        "best_hours": [0, 1, 2, 3],
        "media_support": ["text", "image", "video", "link"],
        "content_style": "產品上架日當天全力衝刺，標語一句到位，Maker 留言真誠述說開發故事",
        "setup_guide": "提前一週準備所有素材：Logo（240x240）、標語（260 字）、圖庫至少五張截圖與一部示範影片。邀請知名 Hunter 協助上架。Maker 留言需分享開發故事與未來藍圖。",
        "hashtag_limit": 0,
    },
    "indiehackers": {
        "name": "IndieHackers",
        "char_limit": 50000,
        "best_hours": [8, 9, 10, 12, 13, 14],
        "media_support": ["text", "image", "link"],
        "content_style": "透明分享營收數據與創業歷程，真誠的 Build-in-Public 風格，技術與商業並重",
        "setup_guide": "建立產品頁面，填上營收模式與里程碑。定期發布營收報告與開發進度更新。積極參與社群討論，分享失敗經驗與學到的教訓。",
        "hashtag_limit": 0,
    },
}

MEDIA_TYPE_GUIDELINES: Dict[str, str] = {
    "image": "靜態圖片：PNG/JPG 格式，Instagram/Pinterest 建議 1080x1080 或 1080x1350，Twitter/Facebook 建議 1200x630",
    "video": "影片內容：MP4 格式，TikTok/Reels 建議 9:16 垂直（1080x1920），YouTube 建議 16:9 水平（1920x1080），時長 15 秒至 3 分鐘",
    "text": "純文字貼文：適用 Twitter、LinkedIn、Threads、Reddit、Telegram，強調文案結構與清晰傳達",
    "carousel": "多圖輪播：2-10 張圖片，適用 Instagram、LinkedIn、Facebook，適合教學步驟、產品展示與前後對比",
    "link": "連結預覽貼文：附帶 Open Graph 標籤優化的連結頁面，顯示縮圖、標題與描述，適用 Facebook、LinkedIn",
}


class SocialPromoterOrgan(BrainComponent):
    """社群推廣引擎器官 — 管理 15+ 社群平台註冊、跨平台行銷活動建立、排程貼文與成效追蹤。

    支援平台：Twitter/X、Instagram、Facebook、LinkedIn、TikTok、
    YouTube、Pinterest、Reddit、Discord、Telegram、Threads、
    Medium、Quora、ProductHunt、IndieHackers。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._accounts: Dict[str, Dict[str, Any]] = {}
        self._campaigns: Dict[str, Dict[str, Any]] = {}
        self._scheduled_posts: Dict[str, Dict[str, Any]] = {}
        self._products: List[str] = []

    # ── 公開方法 ─────────────────────────────────────────────

    @tool(name="register_platform", description="在指定社群平台註冊帳號，儲存憑證並回傳該平台的設定指引與個人檔案優化建議")
    def register_platform(self, platform: str, username: str, bio: str) -> dict:
        """在指定社群平台模擬註冊，儲存帳號資訊並回傳該平台的設定指引與個人檔案最佳化建議。

        Args:
            platform: 平台代碼（twitter / instagram / facebook / linkedin / tiktok /
                      youtube / pinterest / reddit / discord / telegram / threads /
                      medium / quora / producthunt / indiehackers）
            username: 帳號使用者名稱或顯示名稱
            bio: 個人簡介或品牌描述

        Returns:
            dict: 含註冊狀態、平台設定指引與個人檔案優化建議的字典。
        """
        if platform not in PLATFORMS_CONFIG:
            raise ValueError(f"不支援的平台: {platform}，支援: {list(PLATFORMS_CONFIG)}")
        if not username.strip():
            raise ValueError("使用者名稱不可為空")
        if not bio.strip():
            raise ValueError("個人簡介不可為空")

        cfg = PLATFORMS_CONFIG[platform]
        account_id = str(uuid.uuid4())[:8]
        record = {
            "account_id": account_id,
            "platform": platform,
            "platform_name": cfg["name"],
            "username": username.strip(),
            "bio": bio.strip(),
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "char_limit": cfg["char_limit"],
            "media_support": cfg["media_support"],
            "best_hours_utc": cfg["best_hours"],
        }
        self._accounts[platform] = record

        return {
            "account_id": account_id,
            "platform": platform,
            "platform_name": cfg["name"],
            "username": username.strip(),
            "registered_at": record["registered_at"],
            "status": "active",
            "setup_guide": cfg["setup_guide"],
            "profile_tips": {
                "大頭貼建議": "使用高解析度品牌 Logo（至少 400x400 px），避免過多文字",
                "個人簡介優化": f"當前簡介字數 {len(bio)} 字，{'符合' if len(bio) <= cfg['char_limit'] else '超出'}平台限制 {cfg['char_limit']} 字",
                "內容風格指引": cfg["content_style"],
                "最佳發文時段_UTC": cfg["best_hours"],
                "支援媒體類型": cfg["media_support"],
                "話題標籤上限": cfg["hashtag_limit"],
            },
        }

    @tool(name="create_campaign", description="建立跨平台行銷活動，產生各平台最佳化的貼文模板")
    def create_campaign(
        self,
        product_name: str,
        description: str,
        platforms: List[str],
        media_type: str = "text",
    ) -> dict:
        """建立一個跨平台行銷活動，為每個指定平台產生最佳化的貼文模板。

        針對各平台特性自動調整文案風格、字數限制與內容格式：
        - Twitter：280 字以內，精簡有力
        - Instagram：視覺優先搭配豐富話題標籤
        - LinkedIn：專業商業語氣，條列重點
        - TikTok：短影音導向，前三秒吸睛
        - YouTube：SEO 優化標題與描述
        - Pinterest：關鍵詞豐富的垂直圖文
        - Reddit：社群真誠分享風格
        - Discord：即時對話通知
        - Telegram：行動導向簡潔推播
        - Threads：輕鬆對話式文字
        - Medium：長文深度寫作
        - Quora：詳細專業問答
        - ProductHunt：產品標語與 Maker 故事
        - IndieHackers：Build-in-Public 透明風格

        Args:
            product_name: 產品名稱
            description: 產品描述（核心賣點與特色）
            platforms: 目標平台代碼清單
            media_type: 媒體類型（text / image / video / carousel / link）

        Returns:
            dict: 含 campaign_id 與各平台貼文模板的活動記錄。
        """
        if not product_name.strip():
            raise ValueError("產品名稱不可為空")
        if not description.strip():
            raise ValueError("產品描述不可為空")
        if not platforms or not isinstance(platforms, list):
            raise ValueError("platforms 必須為非空清單")
        invalid = [p for p in platforms if p not in PLATFORMS_CONFIG]
        if invalid:
            raise ValueError(f"不支援的平台: {invalid}")
        if media_type not in MEDIA_TYPE_GUIDELINES:
            raise ValueError(f"不支援的媒體類型: {media_type}，支援: {list(MEDIA_TYPE_GUIDELINES)}")

        campaign_id = str(uuid.uuid4())[:8]
        templates: Dict[str, Dict[str, str]] = {}

        for plat in platforms:
            cfg = PLATFORMS_CONFIG[plat]
            plat_name = cfg["name"]
            char_limit = cfg["char_limit"]
            hashtag_limit = cfg["hashtag_limit"]

            head, body, htags = self._build_platform_post(
                product_name, description, plat, media_type, char_limit, hashtag_limit
            )
            templates[plat] = {
                "platform_name": plat_name,
                "headline": head,
                "body": body,
                "hashtags": htags,
                "full_post": (head + "\n\n" + body + "\n\n" + htags).strip(),
                "char_count": len(head) + len(body) + len(htags),
                "char_limit": char_limit,
                "media_type": media_type,
                "media_guidelines": MEDIA_TYPE_GUIDELINES.get(media_type, ""),
            }

        record = {
            "campaign_id": campaign_id,
            "product_name": product_name.strip(),
            "description": description.strip(),
            "media_type": media_type,
            "platforms": platforms,
            "templates": templates,
            "created_at": datetime.now().isoformat(),
            "status": "draft",
        }
        self._campaigns[campaign_id] = record
        if product_name.strip() not in self._products:
            self._products.append(product_name.strip())

        return {
            "campaign_id": campaign_id,
            "product_name": product_name.strip(),
            "media_type": media_type,
            "platform_count": len(platforms),
            "templates": templates,
            "status": "draft",
            "created_at": record["created_at"],
        }

    @tool(name="schedule_posts", description="為指定行銷活動排程各平台貼文，依據最佳發文時段自動建議排程時間")
    def schedule_posts(self, campaign_id: str, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """為指定行銷活動排程貼文，根據各平台最佳發文時段進行排程。

        schedule 清單中每項須包含：
        - platform: 平台代碼
        - scheduled_time: ISO 8601 格式字串，例如 "2026-05-20T09:00:00"

        Args:
            campaign_id: 行銷活動 ID
            schedule: 發文排程清單，每項含 platform 與 scheduled_time

        Returns:
            dict: 含排程結果與最佳時段建議的彙總。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到行銷活動: {campaign_id}")
        if not isinstance(schedule, list) or not schedule:
            raise ValueError("排程清單不可為空")

        campaign = self._campaigns[campaign_id]
        results: List[Dict[str, Any]] = []
        scheduling_advice: Dict[str, List[int]] = {}

        for entry in schedule:
            plat = entry.get("platform", "")
            if plat not in PLATFORMS_CONFIG:
                raise ValueError(f"不支援的平台: {plat}")
            if plat not in campaign["platforms"]:
                raise ValueError(f"平台 {plat} 不在活動 {campaign_id} 的目標平台清單中")

            try:
                scheduled_time = datetime.fromisoformat(entry["scheduled_time"])
            except (ValueError, KeyError):
                raise ValueError(f"scheduled_time 必須為有效的 ISO 8601 格式")

            if scheduled_time <= datetime.now():
                raise ValueError(f"排程時間必須在未來，當前: {entry['scheduled_time']}")

            schedule_id = str(uuid.uuid4())[:8]
            cfg = PLATFORMS_CONFIG[plat]
            post_record = {
                "schedule_id": schedule_id,
                "campaign_id": campaign_id,
                "platform": plat,
                "platform_name": cfg["name"],
                "scheduled_at": scheduled_time.isoformat(),
                "scheduled_hour": scheduled_time.hour,
                "best_hours_match": scheduled_time.hour in cfg["best_hours"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
            self._scheduled_posts[schedule_id] = post_record
            results.append(post_record)
            scheduling_advice.setdefault(plat, cfg["best_hours"])

        campaign["status"] = "scheduled"

        return {
            "campaign_id": campaign_id,
            "product_name": campaign["product_name"],
            "scheduled_count": len(results),
            "posts": results,
            "optimal_hours_by_platform": scheduling_advice,
            "tip": "將排程時間設定於各平台最佳發文時段（optimal_hours_by_platform）可最大化觸及與互動率",
        }

    @tool(name="get_analytics", description="取得指定行銷活動的模擬互動成效數據，含曝光、點擊、分享、轉換與各平台比較")
    def get_analytics(self, campaign_id: str) -> dict:
        """取得指定行銷活動的跨平台互動成效分析報告。

        根據活動內容與平台特性，產生包含曝光數、點擊數、分享數、
        轉換數及互動率的綜合數據報表。

        Args:
            campaign_id: 行銷活動 ID

        Returns:
            dict: 含各平台成效指標與排名比較的完整分析報告。
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"找不到行銷活動: {campaign_id}")

        campaign = self._campaigns[campaign_id]
        product_name = campaign["product_name"]
        description = campaign["description"]
        platform_metrics: Dict[str, Dict[str, Any]] = []
        total_impressions = 0
        total_clicks = 0
        total_shares = 0
        total_conversions = 0
        keyword_seed = abs(hash(product_name + description))

        for plat in campaign["platforms"]:
            cfg = PLATFORMS_CONFIG[plat]
            plat_seed = abs(hash(plat + product_name))
            post_template = campaign.get("templates", {}).get(plat, {})

            reach_multiplier = {
                "twitter": 1.0, "instagram": 1.3, "facebook": 1.2, "linkedin": 0.8,
                "tiktok": 1.5, "youtube": 1.1, "pinterest": 0.9, "reddit": 0.7,
                "discord": 0.5, "telegram": 0.6, "threads": 0.8, "medium": 0.6,
                "quora": 0.7, "producthunt": 0.4, "indiehackers": 0.5,
            }.get(plat, 1.0)

            impressions = int((keyword_seed % 5000 + 2000) * reach_multiplier)
            clicks = int(impressions * (0.025 + (plat_seed % 15) / 200))
            shares = int(impressions * (0.008 + (plat_seed % 8) / 300))
            conversions = max(1, int(clicks * (0.02 + (plat_seed % 10) / 500)))
            engagement_rate = round(
                (clicks + shares) / max(1, impressions) * 100, 2
            )

            total_impressions += impressions
            total_clicks += clicks
            total_shares += shares
            total_conversions += conversions

            platform_metrics.append({
                "platform": plat,
                "platform_name": cfg["name"],
                "impressions": impressions,
                "clicks": clicks,
                "shares": shares,
                "conversions": conversions,
                "engagement_rate": engagement_rate,
                "click_through_rate": round(clicks / max(1, impressions) * 100, 2),
                "conversion_rate": round(conversions / max(1, clicks) * 100, 2),
            })

        platform_metrics.sort(key=lambda x: x["engagement_rate"], reverse=True)

        return {
            "campaign_id": campaign_id,
            "product_name": product_name,
            "status": campaign["status"],
            "aggregate_metrics": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_shares": total_shares,
                "total_conversions": total_conversions,
                "overall_engagement_rate": round(
                    (total_clicks + total_shares) / max(1, total_impressions) * 100, 2
                ),
                "overall_conversion_rate": round(
                    total_conversions / max(1, total_clicks) * 100, 2
                ),
            },
            "platform_breakdown": platform_metrics,
            "top_performing_platform": platform_metrics[0]["platform_name"] if platform_metrics else None,
            "analyzed_at": datetime.now().isoformat(),
        }

    @tool(name="list_platforms", description="列出所有 15 個支援社群平台及其註冊狀態與最佳發文時段")
    def list_platforms(self) -> dict:
        """列出所有 15 個支援的社群平台，包含註冊狀態、平台特性與最佳發文時段。

        Returns:
            dict: 含各平台完整資訊與當前註冊概況。
        """
        platforms_status: List[Dict[str, Any]] = []
        registered_count = 0

        for key, cfg in PLATFORMS_CONFIG.items():
            registered = key in self._accounts
            if registered:
                registered_count += 1
            platforms_status.append({
                "platform_key": key,
                "platform_name": cfg["name"],
                "registered": registered,
                "username": self._accounts[key]["username"] if registered else None,
                "char_limit": cfg["char_limit"],
                "best_hours_utc": cfg["best_hours"],
                "media_support": cfg["media_support"],
            })

        return {
            "total_platforms": len(PLATFORMS_CONFIG),
            "registered_platforms": registered_count,
            "platforms": platforms_status,
        }

    @tool(name="cross_promote", description="提供從來源平台到目標平台的跨平台推廣策略建議")
    def cross_promote(self, source_platform: str, target_platforms: List[str]) -> dict:
        """針對來源平台至目標平台的跨平台推廣，提供具體策略建議。

        根據平台使用者重疊度、內容格式相容性與觸及差異，
        產生具體可行的跨平台引流方案。

        Args:
            source_platform: 來源平台代碼（主要社群陣地）
            target_platforms: 欲拓展的目標平台代碼清單

        Returns:
            dict: 含跨平台策略建議的完整方案。
        """
        if source_platform not in PLATFORMS_CONFIG:
            raise ValueError(f"不支援的來源平台: {source_platform}")
        if not target_platforms or not isinstance(target_platforms, list):
            raise ValueError("目標平台清單不可為空")
        invalid = [p for p in target_platforms if p not in PLATFORMS_CONFIG]
        if invalid:
            raise ValueError(f"不支援的目標平台: {invalid}")

        source_cfg = PLATFORMS_CONFIG[source_platform]
        strategies: List[Dict[str, str]] = []

        for target in target_platforms:
            target_cfg = PLATFORMS_CONFIG[target]

            strategy_map = {
                ("twitter", "threads"): "在 Twitter 貼文末尾加上 Threads 連結，將即時討論延伸至 Threads 進行深度對話",
                ("twitter", "medium"): "將 Twitter 精華推文擴寫為 Medium 長文，並在 Twitter 個人簡介置入 Medium 連結",
                ("twitter", "reddit"): "挑選 Twitter 上引發最多討論的主題，到 Reddit 相關看板發起深度討論並附上原始推文連結",
                ("instagram", "pinterest"): "將 Instagram 精選圖片重新排版為 2:3 垂直圖釘發布至 Pinterest，並在 IG 限動宣傳 Pinterest 看板",
                ("instagram", "tiktok"): "將 Instagram Reels 重新剪輯發至 TikTok，並在 IG 個人簡介加入 TikTok 連結",
                ("instagram", "facebook"): "直接使用 Instagram 的 Facebook 連動發布功能，一鍵同步貼文至粉絲專頁",
                ("youtube", "tiktok"): "從 YouTube 長片剪輯 15-60 秒精華片段發布至 TikTok，並在影片描述置入完整版 YouTube 連結",
                ("youtube", "medium"): "將 YouTube 教學影片轉寫為 Medium 深度文章，嵌入原始影片提升雙向流量",
                ("linkedin", "medium"): "將 LinkedIn 專業文章同步發布至 Medium，並在 LinkedIn 貼文中加入 Medium 完整版連結",
                ("linkedin", "twitter"): "將 LinkedIn 產業洞察濃縮為 Twitter 執行緒（Thread），以簡潔要點吸引追蹤",
                ("discord", "telegram"): "使用 Discord-Telegram 雙向橋接機器人，自動同步公告到兩個社群",
                ("telegram", "discord"): "在 Telegram 頻道置頂訊息中宣傳 Discord 伺服器，提供獨家內容引導用戶加入",
                ("producthunt", "twitter"): "在 ProductHunt 上線當天，於 Twitter 密集發布進度更新，引導追隨者前往投票與留言",
                ("producthunt", "indiehackers"): "在 IndieHackers 發布 ProductHunt 上線戰報，詳細分享策略、數據與心得",
            }

            specific = strategy_map.get((source_platform, target))
            if specific:
                strategies.append({
                    "target_platform": target,
                    "target_name": target_cfg["name"],
                    "strategy": specific,
                    "difficulty": "低",
                })
            else:
                strategies.append({
                    "target_platform": target,
                    "target_name": target_cfg["name"],
                    "strategy": f"將 {source_cfg['name']} 的優質內容重新包裝為 {target_cfg['name']} 格式發布，並在 {source_cfg['name']} 個人簡介中加入 {target_cfg['name']} 連結導流",
                    "difficulty": "中",
                })

        return {
            "source_platform": source_platform,
            "source_name": source_cfg["name"],
            "target_platforms": target_platforms,
            "cross_promotion_strategies": strategies,
            "general_tips": [
                "確保各平台的品牌識別一致（Logo、色調、語氣）",
                "每平台內容需原生調整，避免直接複製貼上",
                "追蹤 UTM 參數來源，量化跨平台導流成效",
                "定期分析各平台受眾重疊度，優化資源配置",
            ],
        }

    def status(self) -> dict:
        """回報器官當前狀態。

        Returns:
            dict: 含註冊平台數、進行中活動數、已排程貼文數與推廣產品清單。
        """
        active_campaigns = sum(
            1 for c in self._campaigns.values() if c["status"] in ("draft", "scheduled")
        )
        pending_scheduled = sum(
            1 for s in self._scheduled_posts.values() if s["status"] == "pending"
        )
        return {
            "name": "SocialPromoterOrgan",
            "alive": True,
            "registered_platforms": list(self._accounts.keys()),
            "registered_count": len(self._accounts),
            "active_campaigns": active_campaigns,
            "total_campaigns": len(self._campaigns),
            "scheduled_posts": len(self._scheduled_posts),
            "pending_posts": pending_scheduled,
            "products_promoted": self._products,
            "supported_platforms": list(PLATFORMS_CONFIG.keys()),
        }

    # ── 內部輔助方法 ─────────────────────────────────────────

    @staticmethod
    def _build_platform_post(
        product_name: str,
        description: str,
        platform: str,
        media_type: str,
        char_limit: int,
        hashtag_limit: int,
    ) -> tuple:
        """根據平台特性建立最佳化的貼文標題、內文與話題標籤。"""
        head_builders = {
            "twitter": f"🚀 {product_name} 正式推出！",
            "instagram": f"✨ 隆重介紹 {product_name}",
            "facebook": f"🎉 {product_name} — 解決你困擾已久的問題",
            "linkedin": f"我們推出了 {product_name}：為專業人士打造的解決方案",
            "tiktok": f"你絕對不能錯過的 {product_name} 🔥",
            "youtube": f"完整解析 {product_name}：功能、優勢與實戰教學",
            "pinterest": f"{product_name} — 你的下一個必備工具",
            "reddit": f"[分享] 我們開發了 {product_name}，想聽聽大家的意見",
            "discord": f"📢 新消息！{product_name} 已上線",
            "telegram": f"🔥 {product_name} 正式推出，立即體驗",
            "threads": f"跟大家分享一個令人興奮的消息：{product_name} 誕生了",
            "medium": f"深入解析 {product_name}：從概念到實現的完整歷程",
            "quora": f"關於 {product_name} 的完整解答",
            "producthunt": f"{product_name} — 一句話解決一個痛點",
            "indiehackers": f"我打造了 {product_name}，以下是目前為止的數據與心得",
        }
        head = head_builders.get(platform, f"介紹 {product_name}")

        body_builders = {
            "twitter": f"{description[:200]} 立即體驗 👇",
            "instagram": f"{description[:200]}\n\n點擊個人簡介連結了解更多 ✨",
            "facebook": f"{description}\n\n你怎麼看？在下方留言告訴我們！",
            "linkedin": f"痛點分析：\n• {description[:80]}\n\n解決方案：\n• {product_name} 提供完整解方\n\n立即造訪官網瞭解更多",
            "tiktok": f"{description[:120]} #fyp",
            "youtube": f"本集重點：\n1. {product_name} 核心功能展示\n2. 實際操作教學\n3. 效果比較與心得\n\n🔗 完整資源在下方描述欄",
            "pinterest": f"{description[:300]} 點擊圖片探索更多靈感",
            "reddit": f"大家好，我們團隊花了好幾個月打造 {product_name}。\n\n它解決的是：{description[:200]}\n\n想聽聽各位的真實回饋，任何建議都歡迎！",
            "discord": f"@everyone {product_name} 上線了！\n{description[:200]}\n\n立刻到 #公告 頻道查看詳情",
            "telegram": f"{description[:300]}\n\n👉 立即體驗：點擊下方連結",
            "threads": f"開發 {product_name} 的過程中我們學到很多。{description[:300]}\n\n分享給正在考慮類似專案的朋友。",
            "medium": f"{product_name} 解決了一個長期存在的問題。\n\n{description}\n\n以下是我們的開發歷程、技術決策與市場回饋…",
            "quora": f"針對這個問題，{product_name} 是目前最具效率的解決方案。\n\n{description}\n\n根據我們的實際測試數據，使用者回饋如下…",
            "producthunt": f"嗨 ProductHunt 社群！我們團隊打造了 {product_name}\n\n{description[:200]}\n\n歡迎試用並給我們回饋！",
            "indiehackers": f"MRR: $0 → 目標 $1,000\n\n{product_name} 簡介：{description[:200]}\n\n目前進度與下一步計劃…",
        }
        body = body_builders.get(platform, description)

        tag_pool = [
            product_name.replace(" ", ""),
            "新品上市", "科技", "AI", "新創", "產品發表",
            "AMPM", "AIOPS",
        ]
        if hashtag_limit <= 0:
            htags = ""
        elif platform == "instagram":
            htags = " ".join(f"#{t}" for t in tag_pool[:hashtag_limit])
        elif platform in ("twitter", "threads"):
            htags = " ".join(f"#{t}" for t in tag_pool[:hashtag_limit])
        else:
            htags = " ".join(f"#{t}" for t in tag_pool[:hashtag_limit])

        return head, body, htags
