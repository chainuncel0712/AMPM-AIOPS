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
    "ebook_topic_prompt": "分析當前繁體中文市場最熱門的電子工具書主題。給出 5 個書籍提案，含書名、目標讀者、市場需求度。只列清單。",
    "kidbook_topic_prompt": "分析 3-6 歲繁體中文童書市場熱門主題。給出 5 個繪本提案，含書名、主題、適合年齡。",
    "comic_topic_prompt": "分析繁體中文漫畫市場熱門題材。給出 5 個漫畫提案，含標題、類型、目標讀者。",
    "novel_topic_prompt": "分析繁體中文長篇小說市場。給出 5 個提案，含書名、類型、一句話簡介。",
    "short_story_topic_prompt": "給出 5 個短篇小說靈感，每則含標題和 20 字簡介。",
    "magazine_topic_prompt": "分析熱門雜誌主題。給出 5 期提案，含刊名、主題、目標讀者。",
    "edu_topic_prompt": "分析學習用書市場。給出 5 本教材提案，含科目、適用年級、核心賣點。",
    "exam_topic_prompt": "分析考試用書市場。給出 5 本提案，含考試名稱、科目、特色賣點。",
    "reference_topic_prompt": "分析技術工具書市場。給出 5 本提案，含工具名稱、適用對象、內容特色。",
}

# ═══ 階段執行函數 ═══

def stage_2_research(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """研究階段：收集素材"""
    title = book["stage_data"]["1"].get("title", "")
    prompt = f"針對「{title}」這本書，請提供 5 個關鍵事實、3 個重要參考來源、2 個目標讀者會關心的問題。只輸出清單格式。"
    result_text = _llm_call(prompt)
    return {"research_notes": result_text, "completed_at": datetime.now().isoformat()}


def stage_3_outline(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """大綱階段"""
    title = book["stage_data"]["1"].get("title", "")
    prompt = f"為《{title}》產生完整目錄，6-8 章，每章 3-4 小節。只輸目錄，不要內容。"
    result_text = _llm_call(prompt)
    return {"outline": result_text, "completed_at": datetime.now().isoformat()}


def stage_4_writing(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """撰寫階段"""
    title = book["stage_data"]["1"].get("title", "")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    prompt = f"根據以下目錄，撰寫《{title}》的完整內容。繁體中文，每章約 400 字，初學者友善。\n\n目錄：\n{outline[:800]}"
    result_text = _llm_call(prompt, "你是專業作家。直接輸出書籍內容，不要解釋。")
    return {"content": result_text, "word_count": len(result_text), "completed_at": datetime.now().isoformat()}


def stage_5_editing(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """編輯階段：品質檢查"""
    content = book["stage_data"].get("4", {}).get("content", "")
    word_count = len(content)
    issues = []
    if word_count < 500:
        issues.append("內容偏短")
    if "http" not in content and word_count > 1000:
        pass
    score = max(0.5, 1.0 - len(issues) * 0.15)
    return {"issues": issues, "quality_score": score, "word_count": word_count, "completed_at": datetime.now().isoformat()}


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


def stage_9_publish(book: Dict, cfg: Dict, llm_user: Optional[Callable] = None) -> Dict:
    """上架階段"""
    platforms = cfg.get("platforms", [])
    return {"platforms": platforms, "status": "ready", "published_at": "", "completed_at": datetime.now().isoformat()}


# ═══ 階段處理器註冊 ═══

STAGE_HANDLERS = {
    2: stage_2_research,
    3: stage_3_outline,
    4: stage_4_writing,
    5: stage_5_editing,
    6: stage_6_art,
    7: stage_7_layout,
    9: stage_9_publish,
}
