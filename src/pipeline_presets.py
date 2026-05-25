"""
Pipeline Presets — 9 種產品類型配置
====================================
每種產品類型定義其 9 階段設定。
新增產品類型只需在此加 ~15 行。
"""
from typing import List, Dict, Any

STAGE_LABELS = {
    1: "選題", 2: "研究", 3: "大綱", 4: "撰寫",
    5: "編輯", 6: "美術/插畫", 7: "排版", 8: "審核",
    9: "上架", 10: "行銷廣告"
}

HUMAN_GATES = {1, 8}  # 階段 1 和 8 需要人工審核

PRODUCT_TYPES: Dict[str, Dict[str, Any]] = {
    "ebook": {
        "label": "電子書", "icon": "📚", "id_prefix": "EB",
        "description": "AI/技術/商業/自學類電子書",
        "market_standard": "章節式 6-10 章，每章 1500-3000 字，含實例與步驟，EPUB reflowable",
        "stages": {
            1: {"auto": False, "prompt": "ebook_topic_prompt"},
            2: {"auto": True, "prompt": "ebook_research_prompt"},
            3: {"auto": True, "prompt": "ebook_outline_prompt"},
            4: {"auto": True, "prompt": "ebook_writing_prompt"},
            5: {"auto": True, "validator": "proofread"},
            6: {"auto": True, "art_mode": "cover_diagrams"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo", "google_books"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter", "facebook"]},
        }
    },
    "kidbook": {
        "label": "童書", "icon": "🧒", "id_prefix": "KB",
        "description": "PANEY & MONEY 兒童繪本",
        "stages": {
            1: {"auto": False, "prompt": "kidbook_topic_prompt"},
            2: {"auto": True, "prompt": "kidbook_research_prompt"},
            3: {"auto": True, "prompt": "kidbook_outline_prompt"},
            4: {"auto": True, "prompt": "kidbook_writing_prompt"},
            5: {"auto": True, "validator": "age_check"},
            6: {"auto": True, "art_mode": "full_illustration"},
            7: {"auto": True, "layout_mode": "fixed_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram", "instagram"]},
        }
    },
    "comic": {
        "label": "漫畫", "icon": "🎨", "id_prefix": "CM",
        "description": "漫畫/圖像小說",
        "stages": {
            1: {"auto": False, "prompt": "comic_topic_prompt"},
            2: {"auto": True, "prompt": "comic_research_prompt"},
            3: {"auto": True, "prompt": "comic_outline_prompt"},
            4: {"auto": True, "prompt": "comic_writing_prompt"},
            5: {"auto": True, "validator": "panel_check"},
            6: {"auto": True, "art_mode": "comic_panels"},
            7: {"auto": True, "layout_mode": "fixed_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter"]},
        }
    },
    "novel": {
        "label": "長篇小說", "icon": "📖", "id_prefix": "NV",
        "description": "長篇小說 (5 萬字+)",
        "stages": {
            1: {"auto": False, "prompt": "novel_topic_prompt"},
            2: {"auto": True, "prompt": "novel_research_prompt"},
            3: {"auto": True, "prompt": "novel_outline_prompt"},
            4: {"auto": True, "prompt": "novel_writing_prompt"},
            5: {"auto": True, "validator": "proofread"},
            6: {"auto": True, "art_mode": "cover_only"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo", "google_books"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter", "facebook"]},
        }
    },
    "short_story": {
        "label": "短篇小說", "icon": "✏️", "id_prefix": "SS",
        "description": "短篇小說 (3千-1萬字)",
        "stages": {
            1: {"auto": False, "prompt": "short_story_topic_prompt"},
            2: {"auto": True, "prompt": "short_story_research_prompt"},
            3: {"auto": True, "prompt": "short_story_outline_prompt"},
            4: {"auto": True, "prompt": "short_story_writing_prompt"},
            5: {"auto": True, "validator": "proofread"},
            6: {"auto": True, "art_mode": "cover_only"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram"]},
        }
    },
    "magazine": {
        "label": "雜誌", "icon": "📰", "id_prefix": "MG",
        "description": "定期雜誌/專題刊物",
        "stages": {
            1: {"auto": False, "prompt": "magazine_topic_prompt"},
            2: {"auto": True, "prompt": "magazine_research_prompt"},
            3: {"auto": True, "prompt": "magazine_outline_prompt"},
            4: {"auto": True, "prompt": "magazine_writing_prompt"},
            5: {"auto": True, "validator": "fact_check"},
            6: {"auto": True, "art_mode": "infographics"},
            7: {"auto": True, "layout_mode": "magazine_pdf"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram", "facebook"]},
        }
    },
    "edu_book": {
        "label": "學習用書", "icon": "🎓", "id_prefix": "ED",
        "description": "教材/學習指南",
        "stages": {
            1: {"auto": False, "prompt": "edu_topic_prompt"},
            2: {"auto": True, "prompt": "edu_research_prompt"},
            3: {"auto": True, "prompt": "edu_outline_prompt"},
            4: {"auto": True, "prompt": "edu_writing_prompt"},
            5: {"auto": True, "validator": "accuracy_check"},
            6: {"auto": True, "art_mode": "cover_diagrams"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter"]},
        }
    },
    "exam_book": {
        "label": "考試用書", "icon": "📝", "id_prefix": "EX",
        "description": "考試準備/題庫",
        "stages": {
            1: {"auto": False, "prompt": "exam_topic_prompt"},
            2: {"auto": True, "prompt": "exam_research_prompt"},
            3: {"auto": True, "prompt": "exam_outline_prompt"},
            4: {"auto": True, "prompt": "exam_writing_prompt"},
            5: {"auto": True, "validator": "answer_verify"},
            6: {"auto": True, "art_mode": "cover_charts"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram"]},
        }
    },
    "reference_book": {
        "label": "工具書", "icon": "🔧", "id_prefix": "RF",
        "description": "參考手冊/工具指南",
        "stages": {
            1: {"auto": False, "prompt": "reference_topic_prompt"},
            2: {"auto": True, "prompt": "reference_research_prompt"},
            3: {"auto": True, "prompt": "reference_outline_prompt"},
            4: {"auto": True, "prompt": "reference_writing_prompt"},
            5: {"auto": True, "validator": "tech_accuracy"},
            6: {"auto": True, "art_mode": "cover_screenshots"},
            7: {"auto": True, "layout_mode": "reflowable_epub"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter"]},
        }
    },
    # ── 新產品類型 ──
    "audiobook": {
        "label": "有聲書", "icon": "🎧", "id_prefix": "AB",
        "description": "文字轉語音有聲書 / Podcast 形式",
        "stages": {
            1: {"auto": False, "prompt": "audiobook_topic_prompt"},
            2: {"auto": True, "prompt": "audiobook_research_prompt"},
            3: {"auto": True, "prompt": "audiobook_outline_prompt"},
            4: {"auto": True, "prompt": "audiobook_writing_prompt"},
            5: {"auto": True, "validator": "narration_check"},
            6: {"auto": True, "art_mode": "cover_only"},
            7: {"auto": True, "layout_mode": "audio_chapters"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["audible", "kobo_audio", "soundon"]},
            10: {"auto": True, "ad_channels": ["telegram", "spotify", "podcast"]},
        }
    },
    "series": {
        "label": "系列書籍", "icon": "📚", "id_prefix": "SR",
        "description": "多冊系列套書 (3-10 冊)",
        "stages": {
            1: {"auto": False, "prompt": "series_topic_prompt"},
            2: {"auto": True, "prompt": "series_research_prompt"},
            3: {"auto": True, "prompt": "series_outline_prompt"},
            4: {"auto": True, "prompt": "series_writing_prompt"},
            5: {"auto": True, "validator": "series_consistency"},
            6: {"auto": True, "art_mode": "series_branding"},
            7: {"auto": True, "layout_mode": "series_boxset"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "readmoo", "google_books"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter", "facebook"]},
        }
    },
    "journal": {
        "label": "期刊/學報", "icon": "📓", "id_prefix": "JL",
        "description": "學術期刊 / 定期學報 / 研究報告",
        "stages": {
            1: {"auto": False, "prompt": "journal_topic_prompt"},
            2: {"auto": True, "prompt": "journal_research_prompt"},
            3: {"auto": True, "prompt": "journal_outline_prompt"},
            4: {"auto": True, "prompt": "journal_writing_prompt"},
            5: {"auto": True, "validator": "peer_review"},
            6: {"auto": True, "art_mode": "journal_format"},
            7: {"auto": True, "layout_mode": "academic_pdf"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["kdp", "google_scholar", "researchgate"]},
            10: {"auto": True, "ad_channels": ["telegram", "academia", "linkedin"]},
        }
    },
    "social_content": {
        "label": "社群付費內容", "icon": "📱", "id_prefix": "SC",
        "description": "YouTube/Patreon/Substack 等社群平台付費內容",
        "stages": {
            1: {"auto": False, "prompt": "social_topic_prompt"},
            2: {"auto": True, "prompt": "social_research_prompt"},
            3: {"auto": True, "prompt": "social_outline_prompt"},
            4: {"auto": True, "prompt": "social_writing_prompt"},
            5: {"auto": True, "validator": "engagement_check"},
            6: {"auto": True, "art_mode": "thumbnail_banner"},
            7: {"auto": True, "layout_mode": "social_format"},
            8: {"auto": False},
            9: {"auto": True, "platforms": ["youtube", "patreon", "substack"]},
            10: {"auto": True, "ad_channels": ["telegram", "twitter", "instagram", "tiktok"]},
        }
    },
}

# 選題後備清單（LLM 不可用時使用）
FALLBACK_TOPICS = {
    "ebook": [
        "Python 自動化入門", "ChatGPT 提示詞大全", "Google Ads 從零開始",
        "Shopify 開店指南", "Excel 數據分析 50 招", "Linux 伺服器管理",
        "AI 繪圖提示詞寶典", "YouTube 頻道經營", "Notion 專案管理", "SEO 關鍵字策略"
    ],
    "kidbook": [
        {"title": "PANEY & MONEY 的收收探險：玩具回家了！", "theme": "收玩具", "age": "3-6", "summary": "學會整理"},
        {"title": "PANEY & MONEY 的睡前安心：我有點怕黑", "theme": "怕黑", "age": "3-6", "summary": "情緒安撫"},
        {"title": "PANEY & MONEY 上學去：第一天上學", "theme": "上學", "age": "3-6", "summary": "適應新環境"},
    ],
    "comic": [
        "熱血籃球少年", "奇幻冒險：龍之谷", "校園戀愛物語",
        "科幻機甲大戰", "美食獵人異世界"
    ],
    "novel": [
        "重生之 AI 帝國", "星際貿易商", "武林群俠傳",
        "末日求生指南", "穿越古代當皇帝"
    ],
    "short_story": [
        "最後一班地鐵", "咖啡店的貓", "雨天的約定",
        "遺失的相機", "深夜便利商店"
    ],
    "magazine": [
        "數位時代月刊", "科技前瞻雜誌", "創意生活誌",
        "創業家週刊", "設計潮流雜誌"
    ],
    "edu_book": [
        "小學生數學入門", "英語文法速成", "程式設計基礎",
        "物理學概要", "歷史大事紀"
    ],
    "exam_book": [
        "公務員考試-行政法", "多益 900 分攻略", "日檢 N3 完全攻略",
        "會計師考試總複習", "大學學測數學"
    ],
    "reference_book": [
        "Python 標準庫手冊", "Docker 實戰指南", "Git 指令速查",
        "AWS 服務對照表", "React Hooks 大全"
    ],
    "audiobook": [
        "5 分鐘冥想引導", "睡前故事 30 則", "職場說話術",
        "投資理財入門音頻課", "英文會話 100 句"
    ],
    "series": [
        "PANEY & MONEY 系列 (6 冊)", "AI 時代三部曲", "創業實戰系列",
        "歷史大冒險 (12 冊)", "程式設計從零到專業 (5 冊)"
    ],
    "journal": [
        "AI 前沿研究月刊", "數位轉型季刊", "教育科技學報",
        "區塊鏈技術半年刊", "永續發展研究報告"
    ],
    "social_content": [
        "YouTube AI 教學頻道", "Patreon 獨家寫作課", "Substack 科技週報",
        "Instagram 設計靈感", "TikTok 程式教學短影音"
    ],
}
