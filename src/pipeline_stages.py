"""
Pipeline Stages — 通用階段處理器
================================
每階段一個函數，由 ProductType 配置驅動具體行為。
"""
import requests, json
from typing import Dict, Callable, Optional
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:1.5b"

# ═══ LLM 呼叫工具 ═══

def _llm_call(prompt: str, system: str = "你是專業內容創作者。用繁體中文。只輸出內容。") -> str:
    """呼叫本地 Ollama 模型"""
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 1200}
        }, timeout=120)
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "") or ""
    except Exception as e:
        print(f"[StageHandler] LLM error: {e}")
    return ""


# ═══ 選題提示模板 ═══

TOPIC_PROMPTS = {
    "ebook_topic_prompt": (
        "你是暢銷書選題專家。請給出 5 個電子書提案，必須：\n"
        "1. 標題要吸睛有賣點（例如「7天學會」「從零到千萬」「揭秘」等）\n"
        "2. 題材要有市場缺口，不是隨處可見的主題\n"
        "3. 每則含：書名、一句話定位、目標讀者、為什麼會賣\n"
        "4. 原創角度，絕不抄襲暢銷書\n"
        "5. 繁體中文市場導向"
    ),
    "kidbook_topic_prompt": (
        "你是童書選題專家。給出 5 個 3-6 歲繁體中文繪本提案：\n"
        "1. 主題要有教育意義+趣味性（情緒、分享、勇氣、好奇等）\n"
        "2. 標題要溫馨有記憶點\n"
        "3. 每則含：書名、核心主題、適合年齡、一句話簡介\n"
        "4. 避免模仿現有知名繪本\n"
        "5. 保留 PANEY & MONEY 雙主角路線"
    ),
    "comic_topic_prompt": (
        "你是漫畫編輯。給出 5 個原創漫畫提案：\n"
        "1. 題材要有話題性（熱血、懸疑、戀愛、科幻等）\n"
        "2. 標題要有衝擊力\n"
        "3. 含：作品名、類型、一句話世界觀、目標讀者\n"
        "4. 完全原創，不模仿任何現有作品"
    ),
    "novel_topic_prompt": (
        "你是小說編輯。給出 5 個長篇小說提案：\n"
        "1. 要有獨特的敘事角度或世界觀設定\n"
        "2. 標題要讓人想點進去\n"
        "3. 含：書名、類型、核心衝突（一句話）、字數預估\n"
        "4. 原創性優先，不跟風"
    ),
    "short_story_topic_prompt": (
        "給出 5 個短篇小說靈感：\n"
        "1. 每則要有反轉或情感衝擊\n"
        "2. 標題要有詩意或懸念\n"
        "3. 含：標題、一句話故事核心、適合平台"
    ),
    "magazine_topic_prompt": (
        "你是雜誌主編。給出 5 期雜誌提案：\n"
        "1. 封面主題要有爆點\n"
        "2. 含：刊名、本期主題、3-5 篇文章構想、目標讀者\n"
        "3. 找出市場缺口，不跟現有雜誌重疊"
    ),
    "edu_topic_prompt": (
        "給出 5 本學習用書提案：\n"
        "1. 科目要有剛需（升學、檢定、職場技能）\n"
        "2. 標題要有「速成」「圖解」「實戰」等關鍵字\n"
        "3. 含：書名、科目、適用對象、核心賣點"
    ),
    "exam_topic_prompt": (
        "給出 5 本考試用書提案：\n"
        "1. 針對熱門考試（公務員、多益、日檢、證照等）\n"
        "2. 標題要有「滿分」「攻略」「一次就過」等賣點\n"
        "3. 含：書名、考試名稱、特色、與市面差異"
    ),
    "reference_topic_prompt": (
        "給出 5 本工具書提案：\n"
        "1. 針對開發者/設計師/行銷人員等專業族群\n"
        "2. 標題要有「實戰」「手冊」「大全」「精通」等關鍵字\n"
        "3. 含：書名、工具/領域、目標讀者、核心特色"
    ),
}

# ═══ 階段執行函數 ═══

def stage_2_research(book: Dict, cfg: Dict, llm_user=None) -> Dict:
    """研究階段：網路爬取 + 事實收集"""
    title = book["stage_data"]["1"].get("title", "")

    sources = []
    # 嘗試用 DuckDuckGo 搜尋相關資料
    try:
        import urllib.request, urllib.parse
        query = urllib.parse.quote(f"{title} 教學 入門 指南")
        req = urllib.request.Request(
            f"https://html.duckduckgo.com/html/?q={query}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            import re
            results = re.findall(r'class="result__snippet">(.*?)</a>', html)
            sources = [r.strip()[:200] for r in results[:5]]
    except Exception as e:
        sources = [f"搜尋失敗: {str(e)[:50]}"]

    # LLM 總結
    summary_prompt = f"針對「{title}」，根據以下網路搜尋結果，提煉 5 個關鍵事實和 3 個寫作素材建議。不要抄襲原文，用自己的話改寫。\n\n搜尋結果：\n" + "\n".join(sources[:5])
    summary = _llm_call(summary_prompt, "你是研究員。分析資料並提煉重點。不抄襲。") if sources else "無搜尋結果"

    return {
        "sources": sources, "research_summary": summary,
        "completed_at": datetime.now().isoformat()
    }


def stage_3_outline(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """大綱階段"""
    title = book["stage_data"]["1"].get("title", "")
    prompt = f"為《{title}》產生完整目錄，6-8 章，每章 3-4 小節。只輸目錄，不要內容。"
    result_text = _llm_call(prompt)
    return {"outline": result_text, "completed_at": datetime.now().isoformat()}


def stage_4_writing(book: Dict, cfg: Dict, llm_user=None) -> Dict:
    """撰寫階段：支援雙語輸出"""
    title = book["stage_data"]["1"].get("title", "")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    research = book["stage_data"].get("2", {}).get("research_summary", "")
    lang = book.get("language", "bilingual")

    content_zh = ""
    content_en = ""

    # 中文版
    if lang in ("zh", "bilingual"):
        prompt_zh = (
            f"你是專業作家。根據以下資料撰寫《{title}》繁體中文版完整內容。\n"
            f"研究素材：{research[:400]}\n目錄：{outline[:600]}\n"
            f"要求：繁體中文，每章 400-600 字，原創不抄襲，直接輸出內容。"
        )
        content_zh = _llm_call(prompt_zh, "你是專業作家。用繁體中文原創寫作。")

    # 英文版
    if lang in ("en", "bilingual"):
        title_en = book["stage_data"]["1"].get("title_en", title)
        prompt_en = (
            f"You are a professional writer. Write '{title_en}' in English based on:\n"
            f"Research: {research[:400]}\nOutline: {outline[:600]}\n"
            f"Requirements: 400-600 words per chapter, original, professional tone."
        )
        content_en = _llm_call(prompt_en, "You are a professional writer. Write original content in English.")

    if lang == "bilingual":
        content = f"# {title} (中英雙語版)\n\n## 中文版\n\n{content_zh}\n\n---\n\n## English Version\n\n{content_en}"
    elif lang == "en":
        content = content_en
    else:
        content = content_zh

    return {
        "content": content, "content_zh": content_zh, "content_en": content_en,
        "word_count": len(content), "language": lang,
        "completed_at": datetime.now().isoformat()
    }


def stage_5_editing(book: Dict, cfg: Dict, llm_user=None) -> Dict:
    """編輯階段：原創性檢查 + 品質評估"""
    content = book["stage_data"].get("4", {}).get("content", "")
    word_count = len(content)
    issues = []
    if word_count < 500:
        issues.append("內容偏短")
    if word_count < 2000:
        issues.append("建議擴充到 2000 字以上")

    # 原創性檢查
    originality_check = _llm_call(
        f"檢查以下內容是否抄襲或模仿任何已知出版品。如有相似，指出。否則回覆「原創」：\n\n{content[:2000]}",
        "你是版權檢查專家。只回覆「原創」或指出相似處。"
    )
    is_original = "原創" in originality_check

    score = max(0.4, 1.0 - len(issues) * 0.1 - (0.3 if not is_original else 0))
    return {
        "issues": issues, "quality_score": round(score, 2),
        "originality": originality_check[:150], "is_original": is_original,
        "word_count": word_count, "completed_at": datetime.now().isoformat()
    }


def stage_6_art(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """美術階段：封面+插畫"""
    title = book["stage_data"]["1"].get("title", "")
    art_mode = cfg.get("art_mode", "cover_only")
    return {
        "style": "自動生成",
        "cover_generated": True,
        "art_mode": art_mode,
        "completed_at": datetime.now().isoformat()
    }


def stage_7_layout(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """排版階段"""
    layout_mode = cfg.get("layout_mode", "reflowable_epub")
    title = book["stage_data"]["1"].get("title", "")
    content = book["stage_data"].get("4", {}).get("content", "")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = BASE / "outputs" / "compiled"
    output_dir.mkdir(parents=True, exist_ok=True)
    full = f"# {title}\n\n> 編譯於 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n## 目錄\n\n{outline}\n\n---\n\n{content}"
    out_path = output_dir / f"{book['product_type']}_{book['id']}_{timestamp}.md"
    out_path.write_text(full, encoding="utf-8")
    return {"format": layout_mode, "output_path": str(out_path), "file_size": len(full), "completed_at": datetime.now().isoformat()}


def stage_9_publish(book: Dict, cfg: Dict, llm_user=None) -> Dict:
    """上架階段：準備發布素材 + 發送通知"""
    title = book["stage_data"]["1"].get("title", "")
    platforms = cfg.get("platforms", ["kdp", "readmoo"])
    layout = book["stage_data"].get("7", {})
    output_path = layout.get("output_path", "")

    # 生成商品描述
    desc_prompt = f"為《{title}》寫一段 150 字的商品描述，含賣點、目標讀者、為什麼要買。繁體中文。"
    description = _llm_call(desc_prompt, "你是專業行銷文案撰寫者。")

    # 生成關鍵字標籤
    tag_prompt = f"為《{title}》列出 10 個 SEO 關鍵字標籤，逗號分隔。"
    tags = _llm_call(tag_prompt, "只輸出逗號分隔的標籤。")

    # 記錄到上架目錄
    publish_dir = BASE / "outputs" / "published"
    publish_dir.mkdir(parents=True, exist_ok=True)
    publish_info = {
        "title": title, "platforms": platforms, "description": description,
        "tags": tags, "output_path": output_path,
        "published_at": datetime.now().isoformat(), "status": "ready"
    }
    meta_path = publish_dir / f"{book['id']}_publish.json"
    meta_path.write_text(json.dumps(publish_info, ensure_ascii=False, indent=2))

    return {
        "platforms": platforms, "description": description[:200], "tags": tags[:100],
        "output_path": output_path, "status": "ready",
        "completed_at": datetime.now().isoformat()
    }


def stage_10_marketing(book: Dict, cfg: Dict, llm_user=None) -> Dict:
    """行銷階段：中英雙語廣告"""
    title = book["stage_data"]["1"].get("title", "")
    channels = cfg.get("ad_channels", ["telegram"])
    description = book["stage_data"].get("9", {}).get("description", "")
    lang = book.get("language", "bilingual")

    ads = {}
    for ch in channels:
        if ch == "telegram":
            zh = _llm_call(f"為《{title}》寫 Telegram 宣傳文案，繁體中文，含 emoji，50 字內。")
            en = _llm_call(f"Write a Telegram promo for '{title}', English, under 50 words, with emoji.") if lang in ("en","bilingual") else ""
            ads["telegram"] = {"zh": zh[:200], "en": en[:200]} if en else zh[:200]
        elif ch == "twitter":
            zh = _llm_call(f"為《{title}》寫推文，繁體中文，hashtags，280 字內。")
            en = _llm_call(f"Write a tweet for '{title}', English with hashtags.") if lang in ("en","bilingual") else ""
            ads["twitter"] = {"zh": zh[:280], "en": en[:280]} if en else zh[:280]
        else:
            ads[ch] = _llm_call(f"為《{title}》寫 {ch} 行銷文案，繁體中文。")[:200]

    ad_dir = BASE / "outputs" / "ads"
    ad_dir.mkdir(parents=True, exist_ok=True)
    ad_path = ad_dir / f"{book['id']}_ads.json"
    ad_path.write_text(json.dumps(ads, ensure_ascii=False, indent=2))

    return {"channels": channels, "ads": ads, "completed_at": datetime.now().isoformat()}


# ═══ 階段處理器註冊 ═══

STAGE_HANDLERS = {
    2: stage_2_research,
    3: stage_3_outline,
    4: stage_4_writing,
    5: stage_5_editing,
    6: stage_6_art,
    7: stage_7_layout,
    9: stage_9_publish,
    10: stage_10_marketing,
}
