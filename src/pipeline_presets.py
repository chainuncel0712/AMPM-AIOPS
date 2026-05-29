"""
Pipeline Presets — 27 種產品類型選題設定
========================================
精簡版：只含 Stage 1 選題所需資訊。
priority 由 sales_tracker 動態調整，預設值反映市場熱度。
"""
from typing import Dict, Any

STAGE_LABELS = {
    1: "選題", 2: "研究", 3: "大綱", 4: "撰寫",
    5: "編輯", 6: "美術/插畫", 7: "排版", 8: "審核",
    9: "上架", 10: "行銷廣告"
}

HUMAN_GATES = {1, 8}

PRODUCT_TYPES: Dict[str, Dict[str, Any]] = {
    # ═══ 文字知識類 ═══
    "ebook": {
        "label": "電子書", "icon": "📚", "id_prefix": "EB",
        "description": "AI/技術/商業/自學類電子書",
        "topic_prompt_key": "ebook",
        "priority": 10,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "facebook"],
        "pricing": {"ntd": 249, "usd": 7.99},
    },
    "finance_book": {
        "label": "財經理財", "icon": "💰", "id_prefix": "FB",
        "description": "投資/理財/股票/ETF/稅務/退休規劃",
        "topic_prompt_key": "finance_book",
        "priority": 9,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "facebook", "instagram"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "crypto_book": {
        "label": "虛擬貨幣/區塊鏈", "icon": "₿", "id_prefix": "CB",
        "description": "加密貨幣/DeFi/NFT/智能合約/鏈上分析",
        "topic_prompt_key": "crypto_book",
        "priority": 8,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 349, "usd": 11.99},
    },
    "reference_book": {
        "label": "工具書", "icon": "🔧", "id_prefix": "RF",
        "description": "開發者/設計師/行銷專業參考手冊",
        "topic_prompt_key": "reference_book",
        "priority": 6,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter"],
        "pricing": {"ntd": 349, "usd": 11.99},
    },
    "edu_book": {
        "label": "學習用書", "icon": "🎓", "id_prefix": "ED",
        "description": "升學/檢定/職場技能教材",
        "topic_prompt_key": "edu_book",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter"],
        "pricing": {"ntd": 399, "usd": 12.99},
    },
    "exam_book": {
        "label": "考試用書", "icon": "📝", "id_prefix": "EX",
        "description": "公務員/多益/日檢/證照考試準備",
        "topic_prompt_key": "exam_book",
        "priority": 5,
        "platforms": ["kdp", "readmoo"],
        "ad_channels": ["telegram", "facebook"],
        "pricing": {"ntd": 499, "usd": 15.99},
    },
    "journal": {
        "label": "期刊/學報", "icon": "📓", "id_prefix": "JL",
        "description": "學術期刊/定期學報/研究報告",
        "topic_prompt_key": "journal",
        "priority": 2,
        "platforms": ["kdp", "google_scholar", "researchgate"],
        "ad_channels": ["telegram", "academia", "linkedin"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "poetry": {
        "label": "詩集/散文", "icon": "📜", "id_prefix": "PT",
        "description": "現代詩/散文/俳句/短文集",
        "topic_prompt_key": "poetry",
        "priority": 2,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },

    # ═══ 小說類 ═══
    "novel": {
        "label": "長篇小說", "icon": "📖", "id_prefix": "NV",
        "description": "5-10 萬字長篇原創小說",
        "topic_prompt_key": "novel",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "facebook"],
        "pricing": {"ntd": 249, "usd": 7.99},
    },
    "short_story": {
        "label": "短篇小說", "icon": "✏️", "id_prefix": "SS",
        "description": "3千-1萬字短篇故事集",
        "topic_prompt_key": "short_story",
        "priority": 4,
        "platforms": ["kdp", "readmoo"],
        "ad_channels": ["telegram"],
        "pricing": {"ntd": 99, "usd": 2.99},
    },
    "light_novel": {
        "label": "輕小說", "icon": "📘", "id_prefix": "LN",
        "description": "日系/台輕風格、插畫+文字混合",
        "topic_prompt_key": "light_novel",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "kobo"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 199, "usd": 6.99},
    },
    "web_novel": {
        "label": "網路小說", "icon": "💻", "id_prefix": "WN",
        "description": "玄幻/言情/原創，自有平台連載",
        "topic_prompt_key": "web_novel",
        "priority": 4,
        "platforms": ["kdp", "readmoo", "patreon"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "serialized_novel": {
        "label": "連載小說", "icon": "📅", "id_prefix": "SN",
        "description": "定期更新的章回體小說，訂閱制",
        "topic_prompt_key": "serialized_novel",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "patreon", "substack"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },

    # ═══ 漫畫類 ═══
    "comic": {
        "label": "漫畫", "icon": "🎨", "id_prefix": "CM",
        "description": "漫畫/圖像小說單行本",
        "topic_prompt_key": "comic",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "kobo"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "serialized_comic": {
        "label": "連載漫畫", "icon": "📅", "id_prefix": "SC",
        "description": "週更/月更長篇連載漫畫/webtoon",
        "topic_prompt_key": "serialized_comic",
        "priority": 6,
        "platforms": ["kdp", "readmoo", "patreon", "kobo"],
        "ad_channels": ["telegram", "twitter", "instagram", "tiktok"],
        "pricing": {"ntd": 99, "usd": 2.99},
    },

    # ═══ 生活/娛樂類 ═══
    "travel_book": {
        "label": "旅遊書籍", "icon": "✈️", "id_prefix": "TB",
        "description": "旅行指南/遊記/行程規劃/在地文化",
        "topic_prompt_key": "travel_book",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "instagram"],
        "pricing": {"ntd": 249, "usd": 7.99},
    },
    "cookbook": {
        "label": "食譜", "icon": "🍳", "id_prefix": "CK",
        "description": "烹飪食譜/烘焙/飲食文化/減醣料理",
        "topic_prompt_key": "cookbook",
        "priority": 6,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "instagram", "facebook"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "magazine": {
        "label": "雜誌", "icon": "📰", "id_prefix": "MG",
        "description": "定期刊物/專題雜誌/季刊",
        "topic_prompt_key": "magazine",
        "priority": 4,
        "platforms": ["kdp", "readmoo", "pubu"],
        "ad_channels": ["telegram", "facebook"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },

    # ═══ 視覺/設計類 ═══
    "photo_book": {
        "label": "攝影集", "icon": "📸", "id_prefix": "PH",
        "description": "主題攝影/旅行/街拍/人像攝影集",
        "topic_prompt_key": "photo_book",
        "priority": 3,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "instagram"],
        "pricing": {"ntd": 449, "usd": 14.99},
    },
    "art_book": {
        "label": "藝術畫冊", "icon": "🖼️", "id_prefix": "AB",
        "description": "繪畫/設計/插畫/創作集",
        "topic_prompt_key": "art_book",
        "priority": 3,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "instagram"],
        "pricing": {"ntd": 599, "usd": 19.99},
    },
    "coloring_book": {
        "label": "著色本", "icon": "🖍️", "id_prefix": "CL",
        "description": "成人舒壓著色/兒童教育著色本",
        "topic_prompt_key": "coloring_book",
        "priority": 4,
        "platforms": ["kdp", "readmoo", "etsy"],
        "ad_channels": ["telegram", "instagram", "pinterest"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "planner": {
        "label": "手帳/計畫本", "icon": "📒", "id_prefix": "PL",
        "description": "年度/月度/主題計畫本、可列印",
        "topic_prompt_key": "planner",
        "priority": 5,
        "platforms": ["kdp", "etsy", "gumroad"],
        "ad_channels": ["telegram", "instagram", "pinterest"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },

    # ═══ 數位商品類 ═══
    "template_pack": {
        "label": "數位模板", "icon": "📋", "id_prefix": "TP",
        "description": "Notion/Excel/Canva/GoodNotes 模板套件",
        "topic_prompt_key": "template_pack",
        "priority": 7,
        "platforms": ["gumroad", "etsy"],
        "ad_channels": ["telegram", "twitter", "instagram", "pinterest"],
        "pricing": {"ntd": 199, "usd": 6.99},
    },
    "course_material": {
        "label": "課程教材", "icon": "🎓", "id_prefix": "CM",
        "description": "線上課程講義/練習題/工作簿",
        "topic_prompt_key": "course_material",
        "priority": 4,
        "platforms": ["teachable", "gumroad"],
        "ad_channels": ["telegram", "facebook", "linkedin"],
        "pricing": {"ntd": 799, "usd": 24.99},
    },

    # ═══ 音訊/社群類 ═══
    "audiobook": {
        "label": "有聲書", "icon": "🎧", "id_prefix": "AU",
        "description": "文字轉語音有聲書/Podcast 形式",
        "topic_prompt_key": "audiobook",
        "priority": 7,
        "platforms": ["audible", "kobo_audio", "soundon"],
        "ad_channels": ["telegram", "spotify", "podcast"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "social_content": {
        "label": "社群付費內容", "icon": "📱", "id_prefix": "SC",
        "description": "YouTube/Patreon/Substack 付費內容",
        "topic_prompt_key": "social_content",
        "priority": 3,
        "platforms": ["youtube", "patreon", "substack"],
        "ad_channels": ["telegram", "twitter", "instagram", "tiktok"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },

    # ═══ 童書/系列類 ═══
    "kidbook": {
        "label": "童書繪本", "icon": "🧒", "id_prefix": "KB",
        "description": "PANEY & MONEY 3-6 歲兒童繪本",
        "topic_prompt_key": "kidbook",
        "priority": 6,
        "platforms": ["kdp", "readmoo"],
        "ad_channels": ["telegram", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "series": {
        "label": "系列套書", "icon": "📚", "id_prefix": "SR",
        "description": "多冊系到套書 (3-10 冊)",
        "topic_prompt_key": "series",
        "priority": 5,
        "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "twitter", "facebook"],
        "pricing": {"ntd": 499, "usd": 14.99},
    },

    # ═══ 新增 22 種：數位素材 / 學習 / 生活 / 專業 ═══
    "sticker_pack": {
        "label": "數位貼紙包", "icon": "🎀", "id_prefix": "SP",
        "description": "GoodNotes/Line/Telegram 貼紙 30-50 組",
        "topic_prompt_key": "sticker_pack",
        "priority": 6, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["instagram", "pinterest", "telegram"],
        "pricing": {"ntd": 99, "usd": 3.99},
    },
    "font_pack": {
        "label": "字型包", "icon": "🔤", "id_prefix": "FP",
        "description": "手寫/藝術字型商用授權",
        "topic_prompt_key": "font_pack",
        "priority": 5, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["instagram", "pinterest"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "icon_set": {
        "label": "圖示套件", "icon": "🔷", "id_prefix": "IS",
        "description": "2000+ SVG icons 商用授權",
        "topic_prompt_key": "icon_set",
        "priority": 4, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["twitter", "pinterest"],
        "pricing": {"ntd": 399, "usd": 14.99},
    },
    "preset_pack": {
        "label": "濾鏡預設包", "icon": "🎞️", "id_prefix": "PP",
        "description": "Lightroom/VSCO/PS 濾鏡預設",
        "topic_prompt_key": "preset_pack",
        "priority": 5, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["instagram", "pinterest"],
        "pricing": {"ntd": 199, "usd": 7.99},
    },
    "wallpaper_pack": {
        "label": "桌布包", "icon": "🖥️", "id_prefix": "WP",
        "description": "手機+電腦高畫質桌布 50 組",
        "topic_prompt_key": "wallpaper_pack",
        "priority": 4, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["pinterest", "instagram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "sound_pack": {
        "label": "音效包", "icon": "🔊", "id_prefix": "SDP",
        "description": "鈴聲/提示音/環境音效包",
        "topic_prompt_key": "sound_pack",
        "priority": 3, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["tiktok", "instagram"],
        "pricing": {"ntd": 149, "usd": 5.99},
    },
    "code_snippets": {
        "label": "程式碼片段", "icon": "💻", "id_prefix": "CS",
        "description": "50+ code snippets 含文件",
        "topic_prompt_key": "code_snippets",
        "priority": 6, "platforms": ["gumroad", "kdp"],
        "ad_channels": ["twitter", "telegram"],
        "pricing": {"ntd": 349, "usd": 12.99},
    },
    "language_learning": {
        "label": "語言學習", "icon": "🗣️", "id_prefix": "LL",
        "description": "單字本/文法/會話練習教材",
        "topic_prompt_key": "language_learning",
        "priority": 6, "platforms": ["kdp", "readmoo", "google_books"],
        "ad_channels": ["telegram", "facebook"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "flashcards": {
        "label": "學習字卡", "icon": "🃏", "id_prefix": "FC",
        "description": "Anki/Quizlet 匯入格式字卡",
        "topic_prompt_key": "flashcards",
        "priority": 4, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["pinterest", "telegram"],
        "pricing": {"ntd": 149, "usd": 4.99},
    },
    "cheat_sheet": {
        "label": "速查表", "icon": "📋", "id_prefix": "CHS",
        "description": "一頁式重點整理/懶人包",
        "topic_prompt_key": "cheat_sheet",
        "priority": 5, "platforms": ["gumroad", "kdp"],
        "ad_channels": ["pinterest", "twitter"],
        "pricing": {"ntd": 79, "usd": 2.99},
    },
    "quiz_bank": {
        "label": "測驗題庫", "icon": "❓", "id_prefix": "QB",
        "description": "500+ 題含詳解",
        "topic_prompt_key": "quiz_bank",
        "priority": 5, "platforms": ["kdp", "readmoo"],
        "ad_channels": ["telegram", "facebook"],
        "pricing": {"ntd": 399, "usd": 14.99},
    },
    "fitness_plan": {
        "label": "健身計畫", "icon": "💪", "id_prefix": "FP2",
        "description": "12 週課表+飲食+影片連結",
        "topic_prompt_key": "fitness_plan",
        "priority": 5, "platforms": ["kdp", "gumroad"],
        "ad_channels": ["instagram", "tiktok", "telegram"],
        "pricing": {"ntd": 349, "usd": 14.99},
    },
    "meditation_guide": {
        "label": "冥想指南", "icon": "🧘", "id_prefix": "MG2",
        "description": "音檔+文字冥想引導",
        "topic_prompt_key": "meditation_guide",
        "priority": 4, "platforms": ["kdp", "gumroad", "audible"],
        "ad_channels": ["instagram", "telegram"],
        "pricing": {"ntd": 249, "usd": 9.99},
    },
    "parenting_guide": {
        "label": "育兒指南", "icon": "👶", "id_prefix": "PG",
        "description": "0-6 歲發展+活動指南",
        "topic_prompt_key": "parenting_guide",
        "priority": 5, "platforms": ["kdp", "readmoo"],
        "ad_channels": ["facebook", "instagram", "telegram"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "pet_care": {
        "label": "寵物照護", "icon": "🐾", "id_prefix": "PC",
        "description": "狗/貓/兔飼養手冊",
        "topic_prompt_key": "pet_care",
        "priority": 4, "platforms": ["kdp", "readmoo"],
        "ad_channels": ["instagram", "facebook"],
        "pricing": {"ntd": 249, "usd": 7.99},
    },
    "gardening": {
        "label": "園藝指南", "icon": "🌱", "id_prefix": "GD",
        "description": "陽台/室內植物全攻略",
        "topic_prompt_key": "gardening",
        "priority": 3, "platforms": ["kdp", "readmoo"],
        "ad_channels": ["pinterest", "instagram"],
        "pricing": {"ntd": 249, "usd": 7.99},
    },
    "diy_crafts": {
        "label": "手作教學", "icon": "✂️", "id_prefix": "DC",
        "description": "50 個 DIY 專案圖解",
        "topic_prompt_key": "diy_crafts",
        "priority": 4, "platforms": ["kdp", "etsy"],
        "ad_channels": ["pinterest", "instagram"],
        "pricing": {"ntd": 299, "usd": 9.99},
    },
    "presentation_template": {
        "label": "簡報模板", "icon": "📊", "id_prefix": "PT",
        "description": "PPT/Keynote/Google Slides 20 組",
        "topic_prompt_key": "presentation_template",
        "priority": 6, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["linkedin", "twitter"],
        "pricing": {"ntd": 499, "usd": 19.99},
    },
    "resume_template": {
        "label": "履歷模板", "icon": "📄", "id_prefix": "RT",
        "description": "10 種風格+ATS 優化",
        "topic_prompt_key": "resume_template",
        "priority": 5, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["linkedin", "twitter"],
        "pricing": {"ntd": 249, "usd": 9.99},
    },
    "business_plan_tmpl": {
        "label": "商業計畫模板", "icon": "📈", "id_prefix": "BP",
        "description": "Lean Canvas+財務模型 Excel",
        "topic_prompt_key": "business_plan_tmpl",
        "priority": 4, "platforms": ["gumroad", "etsy"],
        "ad_channels": ["linkedin", "twitter"],
        "pricing": {"ntd": 599, "usd": 24.99},
    },
    "game_guide": {
        "label": "遊戲攻略", "icon": "🎮", "id_prefix": "GG",
        "description": "熱門遊戲圖文攻略本",
        "topic_prompt_key": "game_guide",
        "priority": 5, "platforms": ["kdp", "readmoo"],
        "ad_channels": ["twitter", "tiktok"],
        "pricing": {"ntd": 199, "usd": 7.99},
    },
    "music_sheet": {
        "label": "樂譜", "icon": "🎼", "id_prefix": "MS",
        "description": "鋼琴/吉他/烏克麗麗樂譜集",
        "topic_prompt_key": "music_sheet",
        "priority": 3, "platforms": ["kdp", "readmoo", "gumroad"],
        "ad_channels": ["pinterest", "instagram"],
        "pricing": {"ntd": 149, "usd": 5.99},
    },
}

# ═══ 選題後備清單（LLM 不可用時使用） ═══

FALLBACK_TOPICS = {
    "ebook": [
        "Python 自動化入門", "ChatGPT 提示詞大全", "Google Ads 從零開始",
        "Shopify 開店指南", "Excel 數據分析 50 招", "Linux 伺服器管理",
        "AI 繪圖提示詞寶典", "YouTube 頻道經營", "Notion 專案管理", "SEO 關鍵字策略"
    ],
    "finance_book": [
        "ETF 穩健投資術：每月 3000 開始", "股票當沖新手聖經",
        "財務自由路徑圖：25-45 歲必讀", "房地產投資實戰手冊",
        "退休金規劃：40 歲前該做的事", "台股族存股清單 2025",
        "被動收入組合：股息+版稅+房租", "省稅完全手冊：合法節稅 50 招",
        "小資族的指數投資學", "信用卡理財術：現金回饋最大化"
    ],
    "crypto_book": [
        "加密貨幣入門：從買幣到冷錢包", "DeFi 被動收入實戰",
        "NFT 創作與交易完全指南", "智能合約開發：Solidity 實戰",
        "2025 區塊鏈十大賽道分析", "空投獵人手冊：零成本賺幣術",
        "加密貨幣稅務指南：台灣篇", "冷錢包安全：護照級資產保護",
        "Web3 創業：DAO 與代幣經濟", "鏈上數據分析：追蹤聰明錢"
    ],
    "reference_book": [
        "Python 標準庫手冊", "Docker 實戰指南", "Git 指令速查",
        "AWS 服務對照表", "React Hooks 大全", "Kubernetes 維運手冊",
        "SQL 效能調校實戰", "VS Code 外掛開發", "Linux 指令百科"
    ],
    "edu_book": [
        "小學生數學入門", "英語文法速成", "程式設計基礎",
        "物理學概要", "歷史大事紀", "化學實驗手冊", "國中數學總複習"
    ],
    "exam_book": [
        "公務員考試-行政法", "多益 900 分攻略", "日檢 N3 完全攻略",
        "會計師考試總複習", "大學學測數學", "雅思 7.0 寫作範文",
        "全民英檢中高級", "不動產經紀人考試"
    ],
    "journal": [
        "AI 前沿研究月刊", "數位轉型季刊", "教育科技學報",
        "區塊鏈技術半年刊", "永續發展研究報告"
    ],
    "poetry": [
        "城市的呼吸：都市詩選", "雨夜隨筆：散文集",
        "俳句四季：日式短詩", "未寄出的信：情詩選", "山海之間：自然書寫"
    ],
    "novel": [
        "重生之 AI 帝國", "星際貿易商", "武林群俠傳",
        "末日求生指南", "穿越古代當皇帝", "都市修真高手",
        "末日廢土求生", "海賊王：新時代", "間諜遊戲：冷戰風雲"
    ],
    "short_story": [
        "最後一班地鐵", "咖啡店的貓", "雨天的約定",
        "遺失的相機", "深夜便利商店", "轉角的麵包店", "捷運站出口"
    ],
    "light_novel": [
        "異世界咖啡廳～轉生後我開了間貓咪咖啡～",
        "放學後的超能力社", "魔王大人想退休",
        "我的青梅竹馬是外星人", "圖書館的禁忌書架",
        "學園偶像班：C 位是我", "遊戲世界求生記～登出不能～"
    ],
    "web_novel": [
        "九天邪帝", "首席醫官", "大奉打更人（仿作）",
        "修真聊天群（仿作）", "斗羅之劍道獨尊",
        "最強贅婿：逆天改命", "穿越後我成了皇帝 AI",
        "帝霸天下：靈氣復甦", "絕世武神", "重生之都市修仙"
    ],
    "serialized_novel": [
        "每日更新：異世界迷宮攻略", "週末連載：偵探社事件簿",
        "雙週刊：星艦傳奇", "月更長篇：戰國風雲錄",
        "季刊小說：遠古文明之謎"
    ],
    "comic": [
        "熱血籃球少年", "奇幻冒險：龍之谷", "校園戀愛物語",
        "科幻機甲大戰", "美食獵人異世界", "推理偵探社",
        "妖怪租屋處", "電競之路：從青銅到王者"
    ],
    "serialized_comic": [
        "Webtoon：神之塔外傳", "週刊連載：忍者學園",
        "月更長篇：機甲戰記", "雙週刊：靈異事務所",
        "日更短漫：辦公室生存記", "週末漫畫：貓咪與主人的日常"
    ],
    "travel_book": [
        "東京深度旅行：在地人私房路線", "曼谷自由行：從夜市到高空酒吧",
        "台灣環島攻略：機車騎行 12 天", "京都和服散策：四季路線",
        "首爾快閃 48 小時：必吃必買", "大阪環球影城攻略",
        "北海道自駕遊：薰衣草與雪祭", "巴黎小資旅行：省錢玩遍博物館"
    ],
    "cookbook": [
        "電鍋料理 100 道：學生宿舍必備", "減醣便當：30 天瘦身計畫",
        "台灣小吃在家做：50 道經典重現", "烘焙新手入門：餅乾蛋糕一次學會",
        "舒肥料理聖經：低溫烹調完全指南", "一鍋到底：鑄鐵鍋懶人料理",
        "嬰幼兒副食品：4-12 個月食譜", "深夜食堂：15 分鐘消夜"
    ],
    "magazine": [
        "數位時代月刊", "科技前瞻雜誌", "創意生活誌",
        "創業家週刊", "設計潮流雜誌", "投資週報", "健康生活雙月刊"
    ],
    "photo_book": [
        "城市剪影：台北 24 小時", "山與海：台灣百岳攝影集",
        "街拍東京：涉谷到淺草", "極光之旅：冰島與挪威",
        "人像光影：自然光拍攝指南", "廢墟美學：被遺忘的建築"
    ],
    "art_book": [
        "水墨新繹：當代水墨畫集", "數位插畫：Procreate 創作集",
        "街頭藝術：台北塗鴉地圖", "刺青藝術：身體上的畫布",
        "浮世繪新解：江戶到現代", "陶藝之美：柴燒與釉藥"
    ],
    "coloring_book": [
        "曼陀羅舒壓著色：50 款設計", "動物花園：成人著色本",
        "台灣古蹟著色：從紅毛城到赤崁樓", "童話森林：兒童著色本",
        "禪繞畫入門：基礎 30 款", "節氣花卉：24 節氣著色"
    ],
    "planner": [
        "2026 年度計畫本：目標設定與追蹤", "月計畫手帳：極簡風格",
        "理財記帳本：每月收支追蹤", "孕期手帳：40 週紀錄",
        "健身計畫本：12 週體態改造", "讀書計畫本：考試倒數計時"
    ],
    "template_pack": [
        "Notion 專案管理模板套件", "Excel 財務報表自動化模板",
        "Canva 社群貼文模板 100 組", "GoodNotes 數位手帳模板",
        "Google Sheets 庫存管理模板", "Resume/CV 履歷模板 20 款"
    ],
    "course_material": [
        "Python 程式設計入門：講義+練習題", "數位行銷實戰：GA4 分析手冊",
        "日語 N5 學習手冊：單字+文法+練習", "投資理財基礎課：Excel 模型",
        "UI/UX 設計入門：Figma 實作工作簿", "攝影基礎：光圈快門 ISO 手冊"
    ],
    "audiobook": [
        "5 分鐘冥想引導", "睡前故事 30 則", "職場說話術",
        "投資理財入門音頻課", "英文會話 100 句", "歷史故事：三國演義",
        "心靈雞湯：每日一句正能量", "面試必備：英文自我介紹"
    ],
    "social_content": [
        "YouTube AI 教學頻道", "Patreon 獨家寫作課", "Substack 科技週報",
        "Instagram 設計靈感", "TikTok 程式教學短影音",
        "YouTube 投資理財頻道", "Patreon 插畫教學"
    ],
    "kidbook": [
        {"title": "PANEY & MONEY 的收收探險：玩具回家了！", "theme": "收玩具", "age": "3-6", "summary": "學會整理"},
        {"title": "PANEY & MONEY 的睡前安心：我有點怕黑", "theme": "怕黑", "age": "3-6", "summary": "情緒安撫"},
        {"title": "PANEY & MONEY 上學去：第一天上學", "theme": "上學", "age": "3-6", "summary": "適應新環境"},
        {"title": "PANEY & MONEY 的洗手任務：泡泡打敗細菌", "theme": "衛生", "age": "3-6", "summary": "習慣養成"},
        {"title": "PANEY & MONEY 的分享果實：一個人的快樂不如兩個", "theme": "分享", "age": "3-6", "summary": "社交學習"},
    ],
    "series": [
        "PANEY & MONEY 系列 (6 冊)", "AI 時代三部曲", "創業實戰系列",
        "歷史大冒險 (12 冊)", "程式設計從零到專業 (5 冊)",
        "投資理財全系列 (4 冊)", "兒童科學啟蒙 (8 冊)"
    ],
    # 新增 22 種
    "sticker_pack": ["手寫文字貼紙包 50 組", "貓咪日常貼紙", "GoodNotes 素材包", "Line 原創貼紙設計", "節慶貼紙大全"],
    "font_pack": ["手寫藝術字型(商用)", "復古毛筆字體", "極簡商標字型", "童趣手繪字", "科技感無襯線體"],
    "icon_set": ["電商圖示 500 枚", "醫療圖示套件", "金融理財 icons", "社群媒體 icons", "通用 UI 圖示 2000+"],
    "preset_pack": ["日系街拍 Lightroom 濾鏡", "婚禮溫暖色調預設", "美食鮮豔調色", "復古膠捲風格", "極簡黑白預設"],
    "wallpaper_pack": ["極簡山水桌布", "星空宇宙系列", "文青語錄壁紙", "日系動漫桌布", "漸層抽象藝術"],
    "sound_pack": ["手機鈴聲 50 選", "冥想環境音", "貓咪叫聲素材", "UI 提示音效", "雨聲白噪音"],
    "code_snippets": ["Python 常用函數 50 招", "JavaScript 速查", "SQL 查詢精選", "React Hook 範例集", "Git 指令速查表"],
    "language_learning": ["日語 N5 單字本", "英語會話 100 句", "韓語入門 30 天", "法語旅遊用語", "台語日常會話"],
    "flashcards": ["GRE 高頻單字卡", "醫學術語字卡", "日檢 N3 字卡", "多益必考字卡", "法條要點字卡"],
    "cheat_sheet": ["Python 語法速查", "投資財報速讀", "SEO 檢查清單", "Git 指令速查", "ChatGPT 提示詞速查"],
    "quiz_bank": ["公務員國文 500 題", "理化會考題庫", "PMP 專案管理考題", "不動產經紀人題庫", "多益閱讀 300 題"],
    "fitness_plan": ["12 週居家健身課表", "產後恢復運動計畫", "銀髮族活力操", "跑步新手訓練計畫", "瑜珈入門 30 天"],
    "meditation_guide": ["睡前放鬆冥想", "專注力提升冥想", "情緒療癒冥想", "晨間感恩冥想", "考試焦慮釋放"],
    "parenting_guide": ["0-2 歲發展里程碑", "幼小銜接準備", "幼兒飲食指南", "兒童情緒教養", "親子遊戲 100 招"],
    "pet_care": ["新手養狗手冊", "貓咪行為解密", "兔子飼養指南", "老犬照護全書", "寵物營養學入門"],
    "gardening": ["陽台小菜園", "多肉植物圖鑑", "香草種植入門", "觀葉植物養護", "城市屋頂花園"],
    "diy_crafts": ["手縫布包教學", "紙雕藝術入門", "編織初學指南", "樹脂飾品 DIY", "舊物改造 50 招"],
    "presentation_template": ["商業提案簡報 20 組", "教育培訓 PPT 模板", "產品發表會模板", "年度報告投影片", "Startup Pitch Deck"],
    "resume_template": ["外商英文履歷", "設計師作品集 CV", "新鮮人求職履歷", "高管經歷簡歷", "轉職轉行履歷"],
    "business_plan_tmpl": ["電商創業計畫", "餐飲開店計畫書", "SaaS 募資計畫", "加盟店評估表", "自媒體商業模式"],
    "game_guide": ["原神全攻略", "薩爾達王國之淚", "Minecraft 建築指南", "英雄聯盟新手入門", "FF7 重製版攻略"],
    "music_sheet": ["周杰倫經典鋼琴譜", "宮崎駿動畫配樂", "抖音熱門吉他譜", "爵士鋼琴入門", "烏克麗麗輕音樂"],
}
