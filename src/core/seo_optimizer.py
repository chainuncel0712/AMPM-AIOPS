"""SEOOptimizerOrgan — SEO 優化器官，負責關鍵字分析、頁面檢測、Meta 生成與排名追蹤。"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from skeleton.brain_component import BrainComponent

SEARCH_VOLUME_RANGES = {
    "high": (10000, 100000),
    "medium": (1000, 9999),
    "low": (100, 999),
    "very_low": (0, 99),
}


class SEOOptimizerOrgan(BrainComponent):
    """SEO 優化器官 — 分析關鍵字競爭度、搜尋量，提供頁面優化建議。"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._keyword_db: Dict[str, Dict[str, Any]] = {}
        self._page_analyses: Dict[str, Dict[str, Any]] = {}
        self._rank_tracker: Dict[str, Dict[str, Any]] = {}

    # ── 公開方法 ─────────────────────────────────────────────

    def analyze_keyword(self, keyword: str) -> dict:
        """分析單一關鍵字的搜尋量、難度與競爭情況。

        Args:
            keyword: 欲分析的關鍵字

        Returns:
            dict: 含 difficulty、search_volume、competition 等指標。
        """
        if not keyword.strip():
            raise ValueError("關鍵字不可為空")

        keyword = keyword.strip().lower()
        # 以關鍵字特徵推估難度 (1-100)
        difficulty = self._estimate_difficulty(keyword)
        volume = self._estimate_volume(keyword)
        competition = self._estimate_competition(difficulty, volume)

        result = {
            "keyword": keyword,
            "difficulty": difficulty,
            "difficulty_label": self._difficulty_label(difficulty),
            "search_volume": volume,
            "volume_tier": self._volume_tier(volume),
            "competition": competition,
            "analyzed_at": datetime.now().isoformat(),
        }
        self._keyword_db[keyword] = result
        return result

    def suggest_keywords(self, topic: str) -> dict:
        """根據主題生成建議關鍵字清單，含各自難度與搜尋量。

        Args:
            topic: 主題或種子關鍵字

        Returns:
            dict: 含 main_keyword 與 suggestions 清單。
        """
        if not topic.strip():
            raise ValueError("主題不可為空")

        topic = topic.strip().lower()
        # 基於主題衍生長尾關鍵字
        modifiers = [
            "教學", "工具", "推薦", "價格", "比較",
            "入門", "進階", "心得", "攻略", "2026",
        ]
        suggestions = []
        for mod in modifiers:
            kw = f"{topic} {mod}"
            diff = self._estimate_difficulty(kw)
            vol = self._estimate_volume(kw)
            suggestions.append({
                "keyword": kw,
                "difficulty": diff,
                "search_volume": vol,
                "volume_tier": self._volume_tier(vol),
            })
        suggestions.sort(key=lambda x: x["search_volume"], reverse=True)

        result = {
            "main_keyword": topic,
            "suggestions": suggestions,
            "count": len(suggestions),
            "generated_at": datetime.now().isoformat(),
        }
        return result

    def analyze_page(self, url: str) -> dict:
        """對指定網址進行基礎 SEO 檢測並提出改善建議。

        Args:
            url: 目標頁面網址

        Returns:
            dict: SEO 評分與改善建議清單。
        """
        if not url.strip():
            raise ValueError("URL 不可為空")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("無效的 URL，須包含 scheme 與 host")

        issues = []
        score = 100

        # 路徑深度
        path_segments = [s for s in parsed.path.split("/") if s]
        if len(path_segments) > 3:
            issues.append("URL 路徑過深，建議控製在 3 層以內")
            score -= 10

        # HTTPS
        if parsed.scheme != "https":
            issues.append("網站未使用 HTTPS，可能影響排名")
            score -= 15

        # 參數過多
        if parsed.query:
            params = parsed.query.split("&")
            if len(params) > 3:
                issues.append(f"URL 含 {len(params)} 個參數，建議簡化")
                score -= 5

        score = max(0, score)

        analysis = {
            "url": url,
            "domain": parsed.netloc,
            "seo_score": score,
            "score_label": self._score_label(score),
            "issues": issues,
            "recommendations": self._build_page_recommendations(score, issues),
            "analyzed_at": datetime.now().isoformat(),
        }
        self._page_analyses[url] = analysis
        return analysis

    def generate_meta(self, title: str, description: str, keywords: List[str]) -> dict:
        """為頁面生成最佳化的 Meta 標籤內容。

        Args:
            title: 頁面標題
            description: 頁面描述
            keywords: 目標關鍵字清單

        Returns:
            dict: 含 title、description、keywords 及其 SEO 評分。
        """
        if not title.strip():
            raise ValueError("標題不可為空")
        if not keywords:
            raise ValueError("關鍵字不可為空")

        title = title.strip()
        description = description.strip() if description else ""
        title_score = 100
        desc_score = 100

        # 標題長度檢查 (建議 30-60 字元)
        if len(title) < 20:
            title_score -= 10
        elif len(title) > 70:
            title_score -= 15

        # 描述長度檢查 (建議 120-160 字元)
        if len(description) < 80:
            desc_score -= 15
        elif len(description) > 180:
            desc_score -= 10

        # 確保關鍵字出現在標題
        primary_kw = keywords[0].lower()
        if primary_kw not in title.lower():
            title_score -= 20

        # 確保關鍵字出現在描述
        if description and primary_kw not in description.lower():
            desc_score -= 15

        kw_str = ", ".join(keywords[:10])
        return {
            "meta_title": title,
            "meta_description": description,
            "meta_keywords": kw_str,
            "title_length": len(title),
            "description_length": len(description),
            "title_score": max(0, title_score),
            "description_score": max(0, desc_score),
            "generated_at": datetime.now().isoformat(),
        }

    def check_ranking(self, keyword: str, url: str) -> dict:
        """檢查指定網址在特定關鍵字下的搜尋排名位置。

        Args:
            keyword: 搜尋關鍵字
            url: 目標網址

        Returns:
            dict: 排名位置、變動方向與建議。
        """
        if not keyword.strip():
            raise ValueError("關鍵字不可為空")
        if not url.strip():
            raise ValueError("URL 不可為空")

        # 以關鍵字與網址特徵產生模擬排名 (1-100)
        seed = abs(hash(f"{keyword}:{url}"))
        position = (seed % 50) + 1
        prev_key = f"{keyword}:{url}:prev"
        prev_position = self._rank_tracker.get(prev_key, {}).get("position", position + seed % 5)

        direction = "stable"
        if prev_position > position:
            direction = "up"
        elif prev_position < position:
            direction = "down"

        result = {
            "keyword": keyword,
            "url": url,
            "position": position,
            "previous_position": prev_position,
            "change": prev_position - position,
            "direction": direction,
            "checked_at": datetime.now().isoformat(),
        }
        self._rank_tracker[f"{keyword}:{url}"] = result
        self._rank_tracker[prev_key] = {"position": position}
        return result

    def status(self) -> dict:
        """回報器官當前狀態。"""
        return {
            "organ": "SEOOptimizerOrgan",
            "keywords_analyzed": len(self._keyword_db),
            "pages_analyzed": len(self._page_analyses),
            "rankings_tracked": len(self._rank_tracker),
        }

    # ── 內部輔助方法 ─────────────────────────────────────────

    @staticmethod
    def _estimate_difficulty(keyword: str) -> int:
        """根據關鍵字長度、詞數與競爭特徵估算難度 (1-100)。"""
        base = 35
        words = keyword.split()
        # 短關鍵字通常更競爭
        if len(words) == 1:
            base += 20
        elif len(words) >= 4:
            base -= 15
        # 單詞長度影響
        total_chars = sum(len(w) for w in words)
        if total_chars < 8:
            base += 10
        elif total_chars > 20:
            base -= 10
        # 帶有商業意圖的修飾詞
        commercial_words = {"價格", "推薦", "比較", "購買", "優惠", "方案"}
        if any(cw in keyword for cw in commercial_words):
            base += 15
        informational_words = {"教學", "入門", "是什麼", "如何", "指南"}
        if any(iw in keyword for iw in informational_words):
            base -= 5
        return max(1, min(100, base + (hash(keyword) % 10)))

    @staticmethod
    def _estimate_volume(keyword: str) -> int:
        """根據關鍵字結構估算月搜尋量。"""
        words = keyword.split()
        base = 500
        if len(words) <= 2:
            base = 5000
        elif len(words) <= 3:
            base = 2000
        elif len(words) >= 5:
            base = 300
        noise = abs(hash(keyword)) % base
        return max(50, base - noise // 2)

    @staticmethod
    def _estimate_competition(difficulty: int, volume: int) -> str:
        if difficulty >= 70:
            return "高競爭 — 建議使用長尾關鍵字切入"
        if difficulty >= 40:
            return "中競爭 — 優質內容有機會突破"
        if volume < 500:
            return "低競爭 — 容易被忽略的利基機會"
        return "低競爭 — 建議優先布局"

    @staticmethod
    def _difficulty_label(d: int) -> str:
        if d >= 70:
            return "高"
        if d >= 40:
            return "中"
        return "低"

    @staticmethod
    def _volume_tier(v: int) -> str:
        if v >= 10000:
            return "高流量"
        if v >= 1000:
            return "中流量"
        return "低流量"

    @staticmethod
    def _score_label(s: int) -> str:
        if s >= 85:
            return "優秀"
        if s >= 65:
            return "良好"
        if s >= 45:
            return "需要改善"
        return "亟需優化"

    @staticmethod
    def _build_page_recommendations(score: int, issues: List[str]) -> List[str]:
        recs = []
        if score < 85:
            recs.append("確認 Meta Title 長度在 30-60 字元之間")
            recs.append("確認 Meta Description 長度在 120-160 字元之間")
        if score < 70:
            recs.append("增加內部連結以改善爬蟲覆蓋率")
            recs.append("為所有圖片加上 alt 屬性")
        if score < 50:
            recs.append("改善頁面載入速度，目標 < 2.5 秒")
            recs.append("增加高品質外部連結提升網站權重")
        if not recs:
            recs.append("頁面 SEO 表現良好，持續監控即可")
        return recs
