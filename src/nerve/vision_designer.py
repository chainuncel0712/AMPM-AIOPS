"""
視覺設計器官 — 圖片編輯建議、版面編排、商業設計
不直接修改圖片，而是提供專業的設計建議和佈局方案。
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class VisionDesigner(BaseOrgan):
    """
    視覺設計引擎

    能力：
    1. 版面編排建議 — 分析圖片佈局並提供改進方案
    2. 編輯建議 — 裁切、調整、濾鏡建議
    3. 商業設計 — logo、名片、海報、社群圖
    4. 設計規範檢查 — 品牌一致性和設計原則
    5. 風格轉換建議 — 從參考圖提取風格特徵
    """

    # 設計規範資料庫
    PLATFORM_SPECS = {
        "instagram_post": {"size": "1080x1080", "ratio": "1:1", "max_file": "30MB"},
        "instagram_story": {"size": "1080x1920", "ratio": "9:16", "max_file": "30MB"},
        "facebook_post": {"size": "1200x630", "ratio": "1.91:1", "max_file": "30MB"},
        "twitter_post": {"size": "1200x675", "ratio": "16:9", "max_file": "5MB"},
        "linkedin_post": {"size": "1200x627", "ratio": "1.91:1", "max_file": "5MB"},
        "youtube_thumbnail": {"size": "1280x720", "ratio": "16:9", "max_file": "2MB"},
        "telegram_post": {"size": "1280x720", "ratio": "16:9", "max_file": "10MB"},
        "logo": {"size": "500x500", "ratio": "1:1", "max_file": "5MB"},
        "business_card": {"size": "1050x600", "ratio": "1.75:1", "max_file": "5MB"},
        "banner": {"size": "1200x400", "ratio": "3:1", "max_file": "5MB"},
    }

    # 設計原則
    DESIGN_PRINCIPLES = {
        "contrast": "確保文字和背景有足夠對比",
        "alignment": "元素對齊創造秩序感",
        "repetition": "重複元素強化品牌一致性",
        "proximity": "相關元素靠近放置",
        "white_space": "留白讓設計呼吸",
        "hierarchy": "重要元素要突出",
        "balance": "視覺重量要平衡分佈",
    }

    def __init__(self, analyzer=None):
        super().__init__("vision_designer")
        self.analyzer = analyzer  # VisionAnalyzer 實例（可選）
        self.design_history: List[Dict] = []
        self.total_designs = 0

    # =========================================
    # 版面編排分析
    # =========================================

    def layout_analysis(self, image_path: str) -> Dict:
        """分析圖片版面編排並提供改進建議"""
        result = {
            "image": image_path,
            "layout": {},
            "composition": {},
            "suggestions": [],
            "analyzed_at": datetime.now().isoformat(),
        }

        # 基本檔案檢查
        try:
            size = os.path.getsize(image_path)
            result["file_size_kb"] = size // 1024
        except Exception:
            result["error"] = "無法讀取圖片"
            return result

        # 如果有 VisionAnalyzer 則用 AI 分析
        if self.analyzer:
            ai_result = self.analyzer.analyze(image_path, [
                "分析這張圖片的版面編排：1) 元素位置 (rule of thirds) 2) 留白空間 3) 視覺層級 4) 平衡性",
                "以 JSON 回覆: {grid_analysis, white_space_ratio, visual_hierarchy, balance_score, improvements[]}"
            ])
            result["ai_analysis"] = ai_result.get("analysis", "")

        # 版面建議（無論有無 AI）
        result["suggestions"] = [
            "📐 使用格線系統對齊元素",
            "📏 保持邊距一致 (建議 20-40px)",
            "👁️ 視覺焦點應放在畫面 1/3 處 (rule of thirds)",
            "⬜ 保留 30-40% 留白空間",
            "📝 文字層級不超過 3 級 (標題/副標/內文)",
        ]

        result["composition"] = {
            "rule_of_thirds": "將主體放在交叉點上",
            "leading_lines": "使用引導線將視線帶向主體",
            "framing": "用邊框元素框住主體",
            "symmetry": "對稱構圖創造穩定感",
        }

        self.design_history.append(result)
        self.total_designs += 1
        return result

    # =========================================
    # 編輯建議
    # =========================================

    def edit_suggestions(self, image_path: str, purpose: str = "general") -> Dict:
        """針對特定用途提供圖片編輯建議"""
        suggestions = {
            "general": [
                "🖼️ 裁切多餘邊緣，聚焦主體",
                "🎨 調整亮度和對比度 (+10%)",
                "✨ 輕微銳化 (radius 1.0)",
                "🌈 飽和度微調 (+5%)",
            ],
            "product": [
                "📷 去背 (移除背景)",
                "💡 均勻打光，消除陰影",
                "🔍 產品放大至佔畫面 70%",
                "🎨 色溫調至 5500K (自然光)",
            ],
            "portrait": [
                "👤 柔膚效果 (輕微)",
                "👁️ 眼睛銳化",
                "🎨 膚色校正",
                "🌫️ 背景模糊 (bokeh)",
            ],
            "food": [
                "🍽️ 提高飽和度 (+15%)",
                "💡 暖色調增強食慾",
                "🔍 細節銳化 (質感)",
                "🎨 色彩分級 (warm tone)",
            ],
            "landscape": [
                "🌅 動態範圍調整 (HDR)",
                "🎨 天空增強",
                "🔍 遠景銳化",
                "📐 水平校正",
            ],
        }

        result = {
            "image": image_path,
            "purpose": purpose,
            "suggestions": suggestions.get(purpose, suggestions["general"]),
            "generated_at": datetime.now().isoformat(),
        }

        # AI 輔助
        if self.analyzer:
            ai_result = self.analyzer.analyze(image_path, [
                f"針對 {purpose} 用途，這張圖片需要哪些編輯？請提供具體建議"
            ])
            result["ai_suggestions"] = ai_result.get("analysis", "")

        return result

    # =========================================
    # 平台規範檢查
    # =========================================

    def platform_check(self, image_path: str, platform: str) -> Dict:
        """檢查圖片是否符合社群平台規範"""
        specs = self.PLATFORM_SPECS.get(platform, {})
        if not specs:
            return {"error": f"未知平台: {platform}", "known": list(self.PLATFORM_SPECS.keys())}

        result = {
            "image": image_path,
            "platform": platform,
            "required": specs,
            "status": "unknown",
            "issues": [],
        }

        # 檢查檔案大小
        try:
            size_kb = os.path.getsize(image_path) // 1024
            max_kb = int(specs.get("max_file", "0").replace("MB", "")) * 1024
            if size_kb > max_kb:
                result["issues"].append(f"檔案過大: {size_kb}KB > {max_kb}KB")
        except Exception:
            pass

        if not result["issues"]:
            result["status"] = "ok"
        else:
            result["status"] = "issues_found"

        return result

    # =========================================
    # 商業設計方案生成
    # =========================================

    def generate_brief(self, project_type: str, brand_name: str, industry: str = "") -> Dict:
        """生成設計簡報 — 提供完整的設計方向指南"""
        project_types = {
            "logo": {
                "description": "品牌標誌設計",
                "deliverables": ["主 logo", "單色版", "favicon", "社群頭像"],
                "key_questions": [
                    "品牌核心價值是什麼？",
                    "目標受眾是誰？",
                    "競爭對手的 logo 風格？",
                ],
                "style_suggestions": [
                    "簡約 — 少即是多，蘋果風格",
                    "幾何 — 使用基本形狀建構",
                    "手繪 — 溫暖有人味",
                    "文字標誌 — 字體本身就是 logo",
                ],
            },
            "social_media": {
                "description": "社群媒體貼文設計",
                "deliverables": ["主視覺", "文字排版", "CTA 按鈕", "品牌浮水印"],
                "key_questions": [
                    "貼文目的是什麼？ (曝光/互動/轉換)",
                    "主要平台是？",
                    "有參考素材嗎？",
                ],
                "style_suggestions": [
                    "大膽配色 — 在資訊流中脫穎而出",
                    "簡潔文字 — 3 秒內傳達訊息",
                    "品牌色一致 — 強化品牌識別",
                ],
            },
            "banner": {
                "description": "橫幅廣告設計",
                "deliverables": ["主視覺", "標題文字", "副標", "CTA"],
                "key_questions": [
                    "廣告目標？ (點擊/曝光/轉換)",
                    "投放平台和尺寸？",
                    "A/B 測試需求？",
                ],
                "style_suggestions": [
                    "對比強烈 — CTA 按鈕要突出",
                    "少文字 — 不超過 10 個字",
                    "情感連結 — 使用人物照片效果更好",
                ],
            },
        }

        info = project_types.get(project_type, project_types["social_media"])

        return {
            "project_type": project_type,
            "brand_name": brand_name,
            "industry": industry or "general",
            "brief": info,
            "design_principles": list(self.DESIGN_PRINCIPLES.values())[:5],
            "generated_at": datetime.now().isoformat(),
        }

    # =========================================
    # 設計原則檢查
    # =========================================

    def design_audit(self, image_path: str) -> Dict:
        """設計審計 — 檢查是否符合設計原則"""
        result = {
            "image": image_path,
            "principles_check": {},
            "overall_score": 0,
            "audited_at": datetime.now().isoformat(),
        }

        for principle, description in self.DESIGN_PRINCIPLES.items():
            result["principles_check"][principle] = {
                "description": description,
                "score": 5,  # 預設中等
                "status": "需 AI 驗證",
            }

        if self.analyzer:
            ai_result = self.analyzer.analyze(image_path, [
                "檢查這張圖片是否符合以下設計原則，每個 1-10 分：" +
                " ".join(f"{k}({v})" for k, v in self.DESIGN_PRINCIPLES.items()),
                "回傳 JSON: {contrast: N, alignment: N, repetition: N, proximity: N, white_space: N, hierarchy: N, balance: N, overall: N}"
            ])
            result["ai_audit"] = ai_result.get("analysis", "")

        return result

    # =========================================
    # 吸收新知 — 從圖片學習設計知識
    # =========================================

    def learn_from_image(self, image_path: str, topic: str = "design") -> Dict:
        """從圖片中吸收設計新知"""
        result = self.analyze(image_path, [
            f"從這張圖片中，我能學到什麼關於 {topic} 的知識？請列出 3-5 個具體可學習的點。",
            f"這些知識如何應用到未來的設計中？"
        ]) if self.analyzer else {"analysis": "需要 VisionAnalyzer 支援"}

        learning = {
            "source": image_path,
            "topic": topic,
            "learned_at": datetime.now().isoformat(),
            "insights": result.get("analysis", ""),
        }

        self.design_history.append(learning)
        return learning

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_designs": self.total_designs,
            "has_analyzer": self.analyzer is not None,
            "platform_specs": len(self.PLATFORM_SPECS),
            "design_principles": len(self.DESIGN_PRINCIPLES),
        }
