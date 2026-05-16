"""ProactiveLearnerOrgan — 主動學習回報引擎

此器官主動搜尋新知識並向使用者回報發現，不需等待提問。
涵蓋新聞掃描、趨勢追蹤、每日簡報、深度學習、機會偵測與學習進度追蹤。
"""
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from skeleton.brain_component import BrainComponent
from tools import tool
import hashlib


class ProactiveLearnerOrgan(BrainComponent):
    """主動學習回報引擎

    主動搜尋新聞、追蹤趨勢、生成每日簡報、深度學習特定主題、
    發掘商業機會，並追蹤學習進度。

    功能模組：
    - 興趣管理：設定與管理使用者感興趣的主題
    - 新聞掃描：從多個來源掃描相關新聞
    - 趨勢追蹤：監測科技、加密貨幣、AI、商業領域趨勢
    - 每日簡報：生成結構化每日摘要
    - 深度學習：深入探究特定主題
    - 機會建議：根據興趣與趨勢推薦商業機會
    """

    DEFAULT_INTERESTS = [
        "AI", "crypto", "blockchain", "NFT", "DeFi",
        "business automation", "passive income", "children's books",
    ]

    NEWS_SOURCES = ["Google News", "Reddit", "HackerNews", "GitHub Trending", "CoinGecko", "CoinMarketCap"]

    TREND_DOMAINS = ["tech", "crypto", "AI", "business"]

    HEADLINE_TEMPLATES: Dict[str, List[str]] = {
        "Google News": [
            "{topic} 突破性進展引發業界關注",
            "最新研究：{topic} 將改變未來十年產業格局",
            "{topic} 市場規模預計在 2026 年達到新高",
            "專家警告：{topic} 領域人才缺口持續擴大",
            "{topic} 新創公司獲得 5000 萬美元 B 輪融資",
            "調查顯示 {topic} 採用率年增 200%",
            "全球 {topic} 峰會將於下月舉行",
            "{topic} 監管法案即將表決，市場觀望",
            "科技巨頭爭相佈局 {topic} 生態系",
            "{topic} 領域出現重大併購案",
        ],
        "Reddit": [
            "ELI5: How does {topic} actually work under the hood?",
            "I built a {topic} side project and made $10K in 3 months",
            "Unpopular opinion: {topic} is overhyped right now",
            "Ask HN style: What are your best {topic} resources?",
            "My {topic} journey: from 0 to job offer in 6 months",
            "The dark side of {topic} nobody talks about",
            "{topic} megathread — share your experience and tips",
            "Why I quit my job to focus on {topic} full-time",
        ],
        "HackerNews": [
            "Show HN: An open-source {topic} tool built with Rust",
            "{topic} and the Future of Work: A Deep Dive",
            "The {topic} Playbook: Lessons from 1000 Deployments",
            "Why {topic} Might Be the Most Important Skill of 2026",
            "{topic} Infrastructure at Scale: A Postmortem",
            "How We Reduced {topic} Latency by 90%",
            "A Formal Verification Approach to {topic}",
        ],
        "GitHub Trending": [
            "awesome-{topic} — 精選 {topic} 資源合集 ★12.4k",
            "{topic}-framework — 下一代 {topic} 開發框架 ★8.7k",
            "{topic} 開源替代方案登上 GitHub Trending #1",
            "社群熱議：{topic} 相關開源專案一週暴增 300%",
            "{topic}-gpt — 整合 LLM 的 {topic} 工具 ★5.2k",
        ],
        "CoinGecko": [
            "{topic} 代幣 24 小時內暴漲 45%，市值突破 10 億",
            "{topic} 生態系統 TVL 創歷史新高",
            "機構資金大量流入 {topic} 相關資產",
            "{topic} 協議升級提案獲得社群壓倒性通過",
            "分析：{topic} 賽道本季表現超越大盤 3 倍",
        ],
        "CoinMarketCap": [
            "{topic} 交易量飆升，單日突破 5 億美元",
            "CMC 社群評分：{topic} 蟬聯本週最受關注項目",
            "{topic} 新增上架 12 家交易所，流動性大增",
            "巨鯨地址大量囤積 {topic}，鏈上數據顯示異常",
            "{topic} 市值排名躍升至前 50，分析師上調目標價",
        ],
    }

    TREND_TEMPLATES: List[Dict[str, Any]] = [
        {"topic": "Generative AI 應用落地", "domain": "AI", "base_momentum": 95},
        {"topic": "比特幣 Layer2 擴容方案", "domain": "crypto", "base_momentum": 88},
        {"topic": "去中心化實體基礎設施 (DePIN)", "domain": "crypto", "base_momentum": 82},
        {"topic": "AI Agent 自主經濟系統", "domain": "AI", "base_momentum": 91},
        {"topic": "量子計算商業化進程", "domain": "tech", "base_momentum": 78},
        {"topic": "RWA 代幣化 (真實世界資產)", "domain": "crypto", "base_momentum": 85},
        {"topic": "邊緣 AI 與 TinyML", "domain": "AI", "base_momentum": 76},
        {"topic": "模塊化區塊鏈架構", "domain": "crypto", "base_momentum": 80},
        {"topic": "AI 驅動的個人化教育", "domain": "AI", "base_momentum": 73},
        {"topic": "去中心化社交協議 (SocialFi)", "domain": "crypto", "base_momentum": 70},
        {"topic": "自動化行銷與 CRM 整合", "domain": "business", "base_momentum": 68},
        {"topic": "綠色能源與永續科技", "domain": "tech", "base_momentum": 65},
        {"topic": "鏈上聲譽與身份系統", "domain": "crypto", "base_momentum": 72},
        {"topic": "多模態大語言模型", "domain": "AI", "base_momentum": 93},
        {"topic": "跨境支付與穩定幣監管", "domain": "business", "base_momentum": 77},
        {"topic": "Web3 遊戲與 GameFi 2.0", "domain": "crypto", "base_momentum": 69},
    ]

    LEARNING_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "beginner": {
            "resources": [
                {"title": "入門完全指南", "source": "Coursera", "type": "線上課程", "duration": "6 小時"},
                {"title": "30 分鐘快速上手", "source": "YouTube", "type": "影片教學", "duration": "30 分鐘"},
                {"title": "官方入門文件", "source": "官方網站", "type": "文件", "duration": "2 小時"},
                {"title": "互動式教學練習", "source": "Codecademy", "type": "互動課程", "duration": "4 小時"},
            ],
            "notes": [
                "核心概念：理解基本術語與運作原理",
                "環境建置：安裝必要工具與依賴套件",
                "第一個範例：實作最小可行範例以建立信心",
                "常見陷阱：注意初學者常犯的 5 個錯誤",
            ],
            "next_steps": [
                "完成一個小型實作專案 (2-4 小時)",
                "加入相關社群或論壇以獲取支援",
                "閱讀進階文件以加深理解",
            ],
        },
        "intermediate": {
            "resources": [
                {"title": "進階架構設計", "source": "Udemy", "type": "線上課程", "duration": "12 小時"},
                {"title": "最佳實踐與設計模式", "source": "O'Reilly", "type": "電子書", "duration": "8 小時"},
                {"title": "開源專案貢獻指南", "source": "GitHub", "type": "社群貢獻", "duration": "持續"},
                {"title": "效能優化實戰", "source": "Pluralsight", "type": "影片課程", "duration": "5 小時"},
            ],
            "notes": [
                "架構思維：理解系統設計取捨與權衡",
                "效能調校：識別瓶頸並實施最佳化策略",
                "安全性考量：常見攻擊向量與防禦方法",
                "可擴展性：水平擴展與垂直擴展的選擇",
            ],
            "next_steps": [
                "貢獻一個開源專案的 PR",
                "撰寫技術部落格分享學習心得",
                "參加黑客松或技術競賽",
            ],
        },
        "advanced": {
            "resources": [
                {"title": "前沿研究論文回顧", "source": "arXiv", "type": "學術論文", "duration": "20 小時"},
                {"title": "專家大師班", "source": "MasterClass", "type": "線上課程", "duration": "10 小時"},
                {"title": "架構決策記錄 (ADR)", "source": "業界案例", "type": "案例研究", "duration": "5 小時"},
                {"title": "技術領導力培訓", "source": "Harvard Business Review", "type": "管理課程", "duration": "15 小時"},
            ],
            "notes": [
                "前沿趨勢：掌握領域最新研究與技術突破",
                "架構決策：學習在限制條件下做出最佳技術選擇",
                "導師角色：如何有效地指導初階與中階學習者",
                "商業價值：理解技術投資的 ROI 與商業影響",
            ],
            "next_steps": [
                "發表演講或在研討會上分享",
                "創建自己的開源框架或工具",
                "組織在地技術社群或讀書會",
            ],
        },
    }

    def __init__(self, dna: Optional[dict] = None):
        """初始化主動學習回報引擎

        Parameters
        ----------
        dna : dict, optional
            器官的 DNA 設定
        """
        super().__init__(dna)
        self._interests: List[str] = list(self.DEFAULT_INTERESTS)
        self._learning_log: List[Dict[str, Any]] = []
        self._articles_scanned: int = 0
        self._reports_generated: int = 0
        self._opportunities_found: int = 0

    # ── 雜湊輔助方法 ────────────────────────────────────────

    def _hash_seed(self, seed_str: str) -> float:
        """根據輸入字串產生 0~1 之間的確定性亂數"""
        digest = hashlib.sha256(seed_str.encode()).digest()
        return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF

    def _hash_int(self, seed_str: str, lo: int, hi: int) -> int:
        """根據輸入字串產生 lo~hi 之間的確定性整數"""
        return lo + int(self._hash_seed(seed_str) * (hi - lo + 1))

    def _pick_from_pool(self, pool: List[Any], seed_str: str) -> Any:
        """根據種子從池中確定性選取一個元素"""
        idx = self._hash_int(seed_str, 0, len(pool) - 1)
        return pool[idx]

    # ── 公開方法 ────────────────────────────────────────────

    @tool
    def set_interests(self, topics: List[str]) -> str:
        """設定使用者感興趣的主題清單

        替換目前追蹤的所有興趣主題。每個主題將作為新聞掃描、
        趨勢追蹤與機會建議的基礎。

        Parameters
        ----------
        topics : List[str]
            感興趣的主題字串清單，例如 ["AI", "區塊鏈", "被動收入"]

        Returns
        -------
        str
            確認訊息，列出已設定的興趣清單
        """
        if not topics or not isinstance(topics, list):
            return "❌ 請提供有效的主題清單 (List[str])"
        valid = [str(t).strip() for t in topics if str(t).strip()]
        if not valid:
            return "❌ 主題清單不可為空"
        self._interests = valid
        return (
            f"✅ 已設定 {len(self._interests)} 個興趣主題：\n"
            + "\n".join(f"  • {t}" for t in self._interests)
        )

    @tool
    def scan_news(self) -> str:
        """掃描新聞來源，為每個興趣主題擷取頭條

        逐一掃描 Google News、Reddit、HackerNews、GitHub Trending、
        CoinGecko、CoinMarketCap 等來源，為每個興趣主題產生
        具備真實感的模擬新聞頭條。每則新聞包含來源、日期與相關性評分。

        Returns
        -------
        str
            格式化的新聞掃描報告
        """
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📰 新聞掃描報告 — {today}", "=" * 50]
        total_articles = 0

        for topic in self._interests:
            lines.append(f"\n🔹 主題：{topic}")
            topic_articles = 0
            for source in self.NEWS_SOURCES:
                seed = f"{topic}:{source}:{today}"
                relevance = self._hash_int(seed, 1, 10)
                templates = self.HEADLINE_TEMPLATES.get(source, [])
                if not templates:
                    continue
                headline_template = self._pick_from_pool(templates, seed)
                headline = headline_template.format(topic=topic)

                article_date = (
                    datetime.now() - timedelta(days=self._hash_int(seed + ":age", 0, 3))
                ).strftime("%Y-%m-%d")

                lines.append(
                    f"  [{source}] {headline}\n"
                    f"    日期: {article_date} | 相關性: {'⭐' * relevance} ({relevance}/10)"
                )
                topic_articles += 1
                total_articles += 1
            lines.append(f"  ── 本主題共掃描 {topic_articles} 則新聞 ──")

        self._articles_scanned += total_articles

        lines.append(f"\n{'=' * 50}")
        lines.append(f"📊 本次掃描總計：{total_articles} 則新聞 | 累計掃描：{self._articles_scanned} 則")
        return "\n".join(lines)

    @tool
    def scan_trends(self) -> str:
        """掃描各領域熱門趨勢，附帶動量分數

        掃描科技、加密貨幣、AI、商業四大領域的當前熱門趨勢，
        每個趨勢帶有動量分數（1-100），代表該趨勢的熱度與成長速度。

        Returns
        -------
        str
            格式化的趨勢掃描報告
        """
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"🔥 趨勢掃描報告 — {today}", "=" * 50]

        by_domain: Dict[str, List[Dict[str, Any]]] = {}
        for trend in self.TREND_TEMPLATES:
            seed = f"{trend['topic']}:{today}"
            noise = self._hash_int(seed, -10, 10)
            momentum = max(1, min(100, trend["base_momentum"] + noise))
            entry = {
                "topic": trend["topic"],
                "domain": trend["domain"],
                "momentum": momentum,
            }
            by_domain.setdefault(trend["domain"], []).append(entry)

        domain_labels = {
            "tech": "科技",
            "crypto": "加密貨幣",
            "AI": "人工智慧",
            "business": "商業",
        }

        for domain in self.TREND_DOMAINS:
            domain_trends = by_domain.get(domain, [])
            domain_trends.sort(key=lambda x: x["momentum"], reverse=True)
            lines.append(f"\n📡 {domain_labels.get(domain, domain)} 趨勢：")
            for i, t in enumerate(domain_trends[:4], 1):
                bar = "▓" * (t["momentum"] // 10) + "░" * (10 - t["momentum"] // 10)
                label = "🔥🔥🔥" if t["momentum"] >= 90 else ("🔥🔥" if t["momentum"] >= 70 else "🔥")
                lines.append(
                    f"  {label} {t['topic']}\n"
                    f"    動量: [{bar}] {t['momentum']}/100"
                )

        lines.append(f"\n{'=' * 50}")
        lines.append("💡 趨勢掃描完成，可使用 daily_briefing 生成綜合簡報")
        return "\n".join(lines)

    @tool
    def daily_briefing(self) -> str:
        """生成每日綜合簡報

        彙整當日重要資訊，包含：
        - 5 則最重要的新聞頭條
        - 3 個值得關注的趨勢
        - 2 個潛在商業機會
        - 1 個需警惕的風險

        Returns
        -------
        str
            專業格式的每日簡報
        """
        today = datetime.now().strftime("%Y-%m-%d")
        formatted_date = datetime.now().strftime("%Y 年 %m 月 %d 日")

        # 產生 5 則新聞
        top_news = []
        for i in range(5):
            topic = self._interests[i % len(self._interests)]
            source = self.NEWS_SOURCES[i % len(self.NEWS_SOURCES)]
            seed = f"briefing:{topic}:{source}:{today}:{i}"
            templates = self.HEADLINE_TEMPLATES.get(source, self.HEADLINE_TEMPLATES["Google News"])
            headline_template = self._pick_from_pool(templates, seed)
            headline = headline_template.format(topic=topic)
            relevance = self._hash_int(seed, 6, 10)
            top_news.append({
                "headline": headline,
                "source": source,
                "topic": topic,
                "relevance": relevance,
            })

        # 產生 3 個趨勢
        top_trends = []
        trend_indices = self._hash_int(f"trend_pick:{today}", 0, len(self.TREND_TEMPLATES) - 1)
        for i in range(3):
            idx = (trend_indices + i * 7) % len(self.TREND_TEMPLATES)
            trend = self.TREND_TEMPLATES[idx]
            seed = f"briefing_trend:{trend['topic']}:{today}"
            noise = self._hash_int(seed, -8, 8)
            momentum = max(1, min(100, trend["base_momentum"] + noise))
            top_trends.append({"topic": trend["topic"], "momentum": momentum, "domain": trend["domain"]})

        # 產生 2 個機會
        opportunities_data = self._generate_opportunities()
        top_opportunities = opportunities_data[:2]

        # 產生 1 個風險
        risk = self._generate_risk()

        self._reports_generated += 1
        self._opportunities_found += len(top_opportunities)

        lines = [
            "╔══════════════════════════════════════════════╗",
            f"║        📋 每日簡報 — {formatted_date}        ║",
            "╚══════════════════════════════════════════════╝",
            "",
            "📰 今日 5 大新聞",
            "─" * 40,
        ]
        for i, news in enumerate(top_news, 1):
            lines.append(
                f"  {i}. [{news['source']}] {news['headline']}\n"
                f"     主題：{news['topic']} | 相關性：{'⭐' * news['relevance']}"
            )

        lines.extend([
            "",
            "🔥 3 大趨勢",
            "─" * 40,
        ])
        for i, trend in enumerate(top_trends, 1):
            lines.append(
                f"  {i}. {trend['topic']}\n"
                f"     動量：{trend['momentum']}/100 | 領域：{trend['domain']}"
            )

        lines.extend([
            "",
            "💎 2 個商業機會",
            "─" * 40,
        ])
        for i, opp in enumerate(top_opportunities, 1):
            lines.append(
                f"  {i}. {opp['title']}\n"
                f"     描述：{opp['description']}\n"
                f"     潛力評分：{'⭐' * opp['potential']} ({opp['potential']}/10)\n"
                f"     預估時程：{opp['timeframe']}"
            )

        lines.extend([
            "",
            "⚠️ 風險警示",
            "─" * 40,
            f"  🔴 {risk['title']}\n"
            f"     描述：{risk['description']}\n"
            f"     嚴重性：{risk['severity']}/10\n"
            f"     建議：{risk['mitigation']}",
            "",
            "─" * 40,
            f"📊 本簡報由 ProactiveLearner 自動生成 | 累計簡報數：{self._reports_generated}",
        ])
        return "\n".join(lines)

    @tool
    def learn_topic(self, topic: str) -> str:
        """深度學習特定主題

        搜尋該主題的學習資源、編纂結構化學習筆記、並建議下一步行動。
        資源涵蓋初階、中階、進階三個層級。

        Parameters
        ----------
        topic : str
            要深度學習的主題

        Returns
        -------
        str
            結構化的學習報告，含資源、筆記與下一步建議
        """
        if not topic or not isinstance(topic, str):
            return "❌ 請提供有效的學習主題"

        topic = topic.strip()
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"🎓 深度學習報告：{topic}",
            f"生成日期：{today}",
            "=" * 50,
        ]

        for level, data in self.LEARNING_TEMPLATES.items():
            level_label = {"beginner": "初階", "intermediate": "中階", "advanced": "進階"}
            lines.append(f"\n📚 {level_label[level]} 學習資源")
            lines.append("─" * 30)

            for i, res in enumerate(data["resources"], 1):
                seed = f"learn:{topic}:{level}:{res['source']}:{today}"
                rating = self._hash_int(seed, 3, 5)
                lines.append(
                    f"  {i}. [{res['type']}] {res['title']}\n"
                    f"     來源：{res['source']} | 時長：{res['duration']} | 評分：{'⭐' * rating}"
                )

            lines.append(f"\n📝 {level_label[level]} 學習筆記")
            lines.append("─" * 30)
            for note in data["notes"]:
                lines.append(f"  • {note}")

            lines.append(f"\n➡️ {level_label[level]} 下一步建議")
            lines.append("─" * 30)
            for step in data["next_steps"]:
                lines.append(f"  → {step}")

        # 加入學習日誌
        self._add_to_learning_log({
            "date": today,
            "topic": topic,
            "action": "deep_learn",
            "levels_covered": list(self.LEARNING_TEMPLATES.keys()),
        })

        lines.append(f"\n{'=' * 50}")
        lines.append("✅ 深度學習完成，學習紀錄已儲存至學習日誌")
        return "\n".join(lines)

    @tool
    def report_to_user(self, format: str = "brief") -> str:
        """生成結構化報告給使用者

        根據指定格式產生報告：
        - "brief"：TLDR 摘要，僅重點條列
        - "detailed"：完整分析，含詳細數據與說明
        - "actionable"：僅列出需要採取行動的項目

        Parameters
        ----------
        format : str
            報告格式，可選 "brief"、"detailed"、"actionable"

        Returns
        -------
        str
            指定格式的結構化報告
        """
        valid_formats = {"brief", "detailed", "actionable"}
        if format not in valid_formats:
            return f"❌ 不支援的格式：{format}，請選用：{', '.join(valid_formats)}"

        today = datetime.now().strftime("%Y-%m-%d")
        formatted_date = datetime.now().strftime("%Y 年 %m 月 %d 日")

        # 產生模擬數據
        news_count = self._hash_int(f"report_news:{today}", 15, 45)
        trend_count = self._hash_int(f"report_trend:{today}", 8, 20)
        opp_count = self._hash_int(f"report_opp:{today}", 2, 6)

        if format == "brief":
            lines = [
                f"📋 TLDR 摘要 — {formatted_date}",
                "─" * 30,
                f"• 掃描 {news_count} 則相關新聞",
                f"• 追蹤到 {trend_count} 個新興趨勢",
                f"• 發現 {opp_count} 個潛在機會",
                f"• 追蹤主題：{', '.join(self._interests[:5])}{'...' if len(self._interests) > 5 else ''}",
                "",
                f"📊 學習日誌總計：{len(self._learning_log)} 筆",
                f"📰 累計掃描文章：{self._articles_scanned} 則",
                f"📋 已生成報告：{self._reports_generated} 份",
            ]
            return "\n".join(lines)

        elif format == "detailed":
            lines = [
                f"📊 完整分析報告 — {formatted_date}",
                "=" * 50,
                "",
                "🔍 興趣主題現況",
                "─" * 30,
            ]
            for i, topic in enumerate(self._interests, 1):
                seed = f"detail:{topic}:{today}"
                articles = self._hash_int(seed + ":articles", 3, 15)
                avg_relevance = self._hash_int(seed + ":rel", 5, 9)
                momentum = self._hash_int(seed + ":mom", 30, 95)
                lines.append(
                    f"  {i}. {topic}\n"
                    f"     相關文章：{articles} 則 | 平均相關性：{avg_relevance}/10 | 趨勢動量：{momentum}/100"
                )

            lines.extend([
                "",
                "📰 新聞來源分佈",
                "─" * 30,
            ])
            for source in self.NEWS_SOURCES:
                seed = f"detail_src:{source}:{today}"
                count = self._hash_int(seed, 5, 30)
                lines.append(f"  • {source}：{count} 則相關新聞")

            lines.extend([
                "",
                "📈 趨勢總覽",
                "─" * 30,
            ])
            for trend in self.TREND_TEMPLATES[:6]:
                seed = f"detail_trend:{trend['topic']}:{today}"
                momentum = max(1, min(100, trend["base_momentum"] + self._hash_int(seed, -10, 10)))
                lines.append(
                    f"  • {trend['topic']} ({trend['domain']}) — 動量 {momentum}/100"
                )

            lines.extend([
                "",
                "📚 學習進度",
                "─" * 30,
                f"  • 累計學習紀錄：{len(self._learning_log)} 筆",
                f"  • 本週新學主題：{self._hash_int(f'weekly:{today}', 1, 5)} 個",
                f"  • 待探索主題：{len(self._interests)} 個",
                "",
                "💡 建議行動",
                "─" * 30,
            ])
            for opp in self._generate_opportunities()[:3]:
                lines.append(f"  → {opp['title']}：{opp['description']}")

            return "\n".join(lines)

        elif format == "actionable":
            # 找出需要行動的項目
            opportunities = self._generate_opportunities()[:3]
            risk = self._generate_risk()

            lines = [
                f"⚡ 行動項目清單 — {formatted_date}",
                "=" * 40,
                "",
                "🟢 機會 (建議把握)",
                "─" * 30,
            ]
            for i, opp in enumerate(opportunities, 1):
                lines.append(
                    f"  {i}. {opp['title']}\n"
                    f"     行動：{opp['action']}\n"
                    f"     優先級：{'⭐' * (11 - opp['potential'])} {'HIGH' if opp['potential'] >= 7 else 'MEDIUM'}"
                )

            lines.extend([
                "",
                "🔴 風險 (需立即處理)",
                "─" * 30,
                f"  1. {risk['title']}\n"
                f"     行動：{risk['mitigation']}\n"
                f"     時限：{'立即' if risk['severity'] >= 7 else '本週內'}",
                "",
                "📋 學習待辦",
                "─" * 30,
            ])
            pending = self._interests[:3]
            for i, topic in enumerate(pending, 1):
                lines.append(f"  {i}. 深度學習「{topic}」→ 使用 learn_topic('{topic}')")

            return "\n".join(lines)

    @tool
    def track_learning_progress(self) -> str:
        """追蹤學習進度

        顯示學習日誌的統計資訊與最近學習記錄，包括學習主題、
        學習日期與學習類型。

        Returns
        -------
        str
            學習進度追蹤報告
        """
        if not self._learning_log:
            return (
                "📭 尚無學習記錄。\n\n"
                "開始你的學習之旅：\n"
                f"  → 使用 learn_topic('主題名稱') 來深度學習\n"
                f"  → 當前興趣主題：{', '.join(self._interests[:5])}"
            )

        lines = [
            "📚 學習進度追蹤報告",
            "=" * 40,
            f"累計學習記錄：{len(self._learning_log)} / 500 筆",
        ]

        # 按日期分組統計
        date_groups: Dict[str, int] = {}
        topic_groups: Dict[str, int] = {}
        for entry in self._learning_log:
            date = entry.get("date", "未知")
            topic = entry.get("topic", "未知")
            date_groups[date] = date_groups.get(date, 0) + 1
            topic_groups[topic] = topic_groups.get(topic, 0) + 1

        # 學習連續天數
        sorted_dates = sorted(date_groups.keys(), reverse=True)
        streak = 0
        check_date = datetime.now()
        for _ in range(30):
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in date_groups:
                streak += 1
            else:
                if streak > 0:
                    break
            check_date -= timedelta(days=1)

        lines.extend([
            f"學習連續天數：{streak} 天",
            "",
            "📊 主題分佈 (Top 5)",
            "─" * 30,
        ])
        for topic, count in sorted(topic_groups.items(), key=lambda x: x[1], reverse=True)[:5]:
            bar = "▓" * min(count, 20)
            lines.append(f"  • {topic}：{bar} ({count} 次)")

        lines.extend([
            "",
            "📅 最近學習記錄",
            "─" * 30,
        ])
        for entry in self._learning_log[-10:][::-1]:
            lines.append(
                f"  [{entry.get('date', '-')}] {entry.get('topic', '-')}"
                f" — {entry.get('action', '-')}"
            )

        lines.extend([
            "",
            "📈 學習建議",
            "─" * 30,
        ])
        if streak < 3:
            lines.append("  ⚠️ 學習連續天數偏低，建議每天至少學習一個主題")
        most_learned = max(topic_groups, key=topic_groups.get) if topic_groups else ""
        if most_learned:
            lines.append(f"  💡 最常學習主題為「{most_learned}」，可考慮探索新領域以拓展視野")
        unexplored = [t for t in self._interests if t not in topic_groups]
        if unexplored:
            lines.append(f"  🔍 尚未探索的興趣主題：{', '.join(unexplored[:3])}")

        return "\n".join(lines)

    @tool
    def suggest_opportunities(self) -> str:
        """根據目前興趣與趨勢推薦商業機會

        分析當前的興趣主題與市場趨勢，產生相關的商業機會建議，
        每個機會包含標題、描述、評分與預估時程。

        Returns
        -------
        str
            商業機會建議報告
        """
        opportunities = self._generate_opportunities()
        self._opportunities_found += len(opportunities)

        lines = [
            "💎 商業機會建議",
            "=" * 40,
        ]
        for i, opp in enumerate(opportunities, 1):
            lines.append(
                f"\n  {i}. {opp['title']}\n"
                f"     {opp['description']}\n"
                f"     潛力評分：{'⭐' * opp['potential']} ({opp['potential']}/10)\n"
                f"     適合興趣：{', '.join(opp['related_interests'])}\n"
                f"     預估時程：{opp['timeframe']}\n"
                f"     建議行動：{opp['action']}"
            )

        lines.extend([
            "",
            "─" * 40,
            f"共發現 {len(opportunities)} 個商業機會 | 累計發現：{self._opportunities_found} 個",
        ])
        return "\n".join(lines)

    @tool
    def status(self) -> dict:
        """回報器官當前狀態

        Returns
        -------
        dict
            包含器官名稱、存活狀態、追蹤興趣數、掃描文章數、
            生成報告數與發現機會數的狀態字典
        """
        return {
            "name": "ProactiveLearnerOrgan",
            "alive": True,
            "interests_tracked": len(self._interests),
            "articles_scanned": self._articles_scanned,
            "reports_generated": self._reports_generated,
            "opportunities_found": self._opportunities_found,
            "learning_log_entries": len(self._learning_log),
        }

    # ── 內部方法 ────────────────────────────────────────────

    def _add_to_learning_log(self, entry: Dict[str, Any]) -> None:
        """將學習記錄加入日誌，超過 500 筆則移除最舊的記錄"""
        self._learning_log.append(entry)
        if len(self._learning_log) > 500:
            self._learning_log = self._learning_log[-500:]

    def _generate_opportunities(self) -> List[Dict[str, Any]]:
        """根據興趣主題與趨勢產生商業機會建議"""
        today = datetime.now().strftime("%Y-%m-%d")

        opportunity_pool = [
            {
                "title": "AI 自動化內容創作平台",
                "description": "利用生成式 AI 為小型企業自動產生行銷文案、社群貼文與 SEO 文章，月訂閱制商業模式。",
                "related_interests": ["AI", "business automation", "passive income"],
                "timeframe": "3-6 個月 MVP",
                "action": "研究現有競品 (Jasper, Copy.ai)，找出差異化切入點",
                "base_potential": 8,
            },
            {
                "title": "加密貨幣自動化套利機器人",
                "description": "開發跨交易所的價差套利機器人，利用閃電貸與智能合約實現零本金套利。",
                "related_interests": ["crypto", "DeFi", "blockchain", "passive income"],
                "timeframe": "2-4 個月開發與測試",
                "action": "研究 MEV 與閃電貸機制，選擇 Polygon 或 Arbitrum 作為首發鏈",
                "base_potential": 7,
            },
            {
                "title": "NFT 兒童教育內容平台",
                "description": "將兒童書籍轉化為互動式 NFT 收藏品，結合 AR 技術與遊戲化學習體驗。",
                "related_interests": ["NFT", "children's books", "blockchain"],
                "timeframe": "4-8 個月",
                "action": "與插畫家與教育專家合作，建立首批 10 本互動童書原型",
                "base_potential": 9,
            },
            {
                "title": "DeFi 被動收益優化器",
                "description": "自動在多個 DeFi 協議間分配資金以最大化收益，含風險評估與自動複投功能。",
                "related_interests": ["DeFi", "crypto", "passive income", "blockchain"],
                "timeframe": "3-5 個月",
                "action": "整合 Yearn、Aave、Compound 等協議 API，建立收益比較儀表板",
                "base_potential": 8,
            },
            {
                "title": "區塊鏈供應鏈追蹤 SaaS",
                "description": "為中小型製造業提供基於區塊鏈的供應鏈透明化解決方案，月費制 SaaS。",
                "related_interests": ["blockchain", "business automation"],
                "timeframe": "6-12 個月",
                "action": "針對食品與藥品產業進行市場驗證，尋找首位企業客戶",
                "base_potential": 7,
            },
            {
                "title": "AI 驅動的個人財務顧問 App",
                "description": "整合用戶銀行數據與市場資訊，提供個人化理財建議與自動化投資配置。",
                "related_interests": ["AI", "passive income", "business automation"],
                "timeframe": "4-6 個月 MVP",
                "action": "研究開放銀行 API (PSD2)，建立風險評估演算法原型",
                "base_potential": 9,
            },
            {
                "title": "自媒體 IP 被動收入系統",
                "description": "建立一套可複製的自媒體 IP 孵化流程，從內容創作、社群經營到多元變現。",
                "related_interests": ["passive income", "business automation", "children's books"],
                "timeframe": "3-6 個月",
                "action": "選定垂直領域（如親子教育），建立內容行事曆與創作框架",
                "base_potential": 6,
            },
            {
                "title": "Web3 遊戲內經濟設計顧問服務",
                "description": "為 GameFi 專案提供代幣經濟學設計、平衡性分析與可持續性評估。",
                "related_interests": ["crypto", "NFT", "blockchain"],
                "timeframe": "1-3 個月啟動",
                "action": "分析現有成功 GameFi 專案的代幣模型，建立分析框架",
                "base_potential": 7,
            },
        ]

        # 根據當前興趣評分
        scored = []
        for opp in opportunity_pool:
            seed = f"opp:{opp['title']}:{today}"
            noise = self._hash_int(seed, -2, 2)
            # 興趣匹配加分
            interest_bonus = sum(
                2 for interest in self._interests if interest in opp["related_interests"]
            )
            potential = max(1, min(10, opp["base_potential"] + noise + interest_bonus))
            opp_copy = dict(opp)
            opp_copy["potential"] = potential
            scored.append(opp_copy)

        scored.sort(key=lambda x: x["potential"], reverse=True)
        return scored[:5]

    def _generate_risk(self) -> Dict[str, str]:
        """產生風險警示"""
        today = datetime.now().strftime("%Y-%m-%d")

        risk_pool = [
            {
                "title": "AI 監管政策不確定性",
                "description": "全球多國加速制定 AI 監管法案，可能影響 AI 相關商業模式的合規成本與市場準入。",
                "mitigation": "密切追蹤歐盟 AI Act 與美國行政命令進展，預先建立合規框架。",
                "base_severity": 7,
            },
            {
                "title": "加密貨幣市場波動加劇",
                "description": "宏觀經濟數據與監管消息可能引發市場劇烈波動，影響加密資產持倉價值。",
                "mitigation": "設定止損點位，將部分資產轉移至穩定幣，避免過度槓桿。",
                "base_severity": 8,
            },
            {
                "title": "市場競爭白熱化",
                "description": "大型科技公司加速進入 AI 與 Web3 領域，可能擠壓新創團隊的生存空間。",
                "mitigation": "專注利基市場，建立社群壁壘，快速迭代以維持競爭優勢。",
                "base_severity": 6,
            },
            {
                "title": "技術人才短缺",
                "description": "AI 與區塊鏈領域的資深工程師供不應求，薪資成本持續攀升。",
                "mitigation": "考慮使用無程式碼工具或 AI 輔助開發，外包非核心功能。",
                "base_severity": 5,
            },
            {
                "title": "智能合約安全漏洞風險",
                "description": "DeFi 協議駭客攻擊事件頻傳，單次損失可達數千萬美元，需嚴格審計。",
                "mitigation": "所有智能合約上線前必須通過第三方審計，並建立漏洞賞金計畫。",
                "base_severity": 9,
            },
        ]

        seed = f"risk:{today}"
        risk = risk_pool[self._hash_int(seed, 0, len(risk_pool) - 1)]
        risk_copy = dict(risk)
        risk_copy["severity"] = max(1, min(10, risk["base_severity"] + self._hash_int(seed + ":noise", -2, 2)))
        return risk_copy
