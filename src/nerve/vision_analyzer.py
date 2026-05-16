"""
視覺分析器官 — 圖片辨識、美感評分、內容提取
支援 GPT-4V / Gemini Vision / 本地分析
"""
import base64
import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from skeleton.base_organ import BaseOrgan


class VisionAnalyzer(BaseOrgan):
    """
    視覺分析引擎

    能力：
    1. 圖片辨識 — 描述圖片內容
    2. 物件偵測 — 找出圖片中的關鍵元素
    3. 美感評分 — 評估視覺品質
    4. 色彩分析 — 提取主色調、配色建議
    5. 文字擷取 — 圖片中的文字 OCR 辨識
    6. 商業分析 — 廣告、商標、產品圖評估
    """

    def __init__(self):
        super().__init__("vision_analyzer")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.analysis_history: List[Dict] = []
        self.total_analyzed = 0
        self._cache: Dict[str, Dict] = {}

    # =========================================
    # 圖片讀取
    # =========================================

    def _read_image_b64(self, image_path: str) -> str:
        """讀取圖片並轉 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def _get_image_type(self, image_path: str) -> str:
        ext = Path(image_path).suffix.lower()
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "bmp": "bmp"}
        return mime.get(ext, "jpeg")

    def _call_vision_llm(self, image_b64: str, questions: List[str], mime: str = "jpeg") -> str:
        """呼叫視覺 LLM"""
        content = []
        for q in questions:
            content.append({"type": "text", "text": q})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{image_b64}"}})

        # 優先 GPT-4V
        if self.api_key:
            try:
                r = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": "gpt-4o", "messages": [{"role": "user", "content": content}], "max_tokens": 1500},
                    timeout=45
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

        # 備援 Gemini
        if self.gemini_key:
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}",
                    json={
                        "contents": [{"parts": [
                            {"text": "\n".join(questions)},
                            {"inlineData": {"mimeType": f"image/{mime}", "data": image_b64}}
                        ]}]
                    },
                    timeout=45
                )
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                pass

        # 無可用 API 時的本地分析
        return self._local_analysis(image_b64, questions)

    def _local_analysis(self, image_b64: str, questions: List[str]) -> str:
        """本地圖片分析（無 API 時）"""
        qs = " ".join(questions)
        if "描述" in qs or "describe" in qs.lower():
            return (
                "📷 本地圖片分析 (無視覺 API):\n"
                f"  檔案大小: {len(image_b64) // 1024} KB\n"
                "  ⚠️ 需設定 OPENAI_API_KEY 或 GEMINI_API_KEY 以啟用 AI 視覺辨識\n"
                "  目前只能提供基本檔案資訊"
            )
        if "顏色" in qs or "color" in qs.lower():
            return "🎨 色彩分析需要視覺 API 支援"
        if "美感" in qs or "aesthetic" in qs.lower():
            return "🎨 美感評分需要視覺 API 支援"
        return "需設定視覺 API 金鑰"

    # =========================================
    # 核心能力
    # =========================================

    def analyze(self, image_path: str, questions: List[str] = None) -> Dict:
        """完整圖片分析"""
        if not os.path.exists(image_path):
            return {"error": f"找不到圖片: {image_path}"}

        cache_key = hashlib.md5(f"{image_path}:{str(questions)}".encode()).hexdigest()[:12]
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            img_b64 = self._read_image_b64(image_path)
            mime = self._get_image_type(image_path)
        except Exception as e:
            return {"error": f"讀取失敗: {e}"}

        if questions is None:
            questions = ["請詳細描述這張圖片的內容，包括主題、物件、色彩、構圖"]

        result_text = self._call_vision_llm(img_b64, questions, mime)

        result = {
            "image_path": image_path,
            "size_kb": len(img_b64) // 1024,
            "type": mime,
            "analysis": result_text,
            "analyzed_at": datetime.now().isoformat(),
        }

        self.analysis_history.append(result)
        if len(self.analysis_history) > 100:
            self.analysis_history = self.analysis_history[-100:]
        self.total_analyzed += 1

        self._cache[cache_key] = result
        if len(self._cache) > 50:
            self._cache = dict(list(self._cache.items())[-50:])

        return result

    # =========================================
    # 美感評分
    # =========================================

    def aesthetic_score(self, image_path: str) -> Dict:
        """美感評分 (1-10)"""
        result = self.analyze(image_path, [
            "請為這張圖片的美感評分 1-10，並說明理由。評估標準：構圖平衡、色彩和諧、視覺焦點、專業度。請回傳 JSON: {score, reasoning, strengths[], weaknesses[]}"
        ])

        text = result.get("analysis", "")
        import re, json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                score_data = json.loads(match.group())
                result["aesthetic"] = score_data
            except Exception:
                result["aesthetic"] = {"score": 5, "reasoning": "無法解析", "strengths": [], "weaknesses": []}
        else:
            result["aesthetic"] = {"score": 5, "reasoning": "無法解析", "strengths": [], "weaknesses": []}

        return result

    # =========================================
    # 色彩分析
    # =========================================

    def color_analysis(self, image_path: str) -> Dict:
        """色彩分析 — 主色調、配色建議"""
        result = self.analyze(image_path, [
            "請分析這張圖片的色彩：1) 主色調 (3-5 色，含 hex 色碼) 2) 色彩風格 3) 配色建議。請回傳 JSON: {palette: [{name, hex}], style, suggestions[]}"
        ])

        text = result.get("analysis", "")
        import re, json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                result["color"] = json.loads(match.group())
            except Exception:
                result["color"] = {"palette": [], "style": "未知", "suggestions": []}

        return result

    # =========================================
    # 商業設計分析
    # =========================================

    def commercial_design_analysis(self, image_path: str, industry: str = "general") -> Dict:
        """商業設計分析 — 廣告、商標、產品圖評估"""
        result = self.analyze(image_path, [
            f"請以{industry}行業的角度分析這張商業設計圖：1) 整體設計評價 2) 品牌傳遞效果 3) 目標受眾吸引力 4) 改進建議。回傳 JSON: {{rating, brand_impact, audience_appeal, improvements[]}}"
        ])

        text = result.get("analysis", "")
        import re, json
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                result["commercial"] = json.loads(match.group())
            except Exception:
                result["commercial"] = {"rating": 5, "brand_impact": "未知", "audience_appeal": "未知", "improvements": []}

        return result

    # =========================================
    # 文字擷取 (OCR)
    # =========================================

    def extract_text(self, image_path: str) -> Dict:
        """從圖片中擷取文字"""
        return self.analyze(image_path, [
            "請擷取這張圖片中的所有文字內容，保持原有順序和格式"
        ])

    # =========================================
    # 查詢
    # =========================================

    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        return self.analysis_history[-limit:]

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_analyzed": self.total_analyzed,
            "has_openai_vision": bool(self.api_key),
            "has_gemini_vision": bool(self.gemini_key),
        }
