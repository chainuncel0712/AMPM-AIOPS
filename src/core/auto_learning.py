"""
AutoLearningOrgan — 自動學習進修器官
搜尋學習資源、策展內容、建立學習路徑、追蹤進度、推薦下一步。
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent


class AutoLearningOrgan(BrainComponent):
    """
    自動學習進修器官

    功能：
    1. 模擬搜尋免費線上學習資源
    2. 根據主題策展資源
    3. 建立結構化學習路徑（含里程碑）
    4. 追蹤學習完成百分比
    5. 根據知識缺口推薦下一個主題
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._resources: List[Dict[str, Any]] = []
        self._learning_paths: Dict[str, Dict[str, Any]] = {}
        self._completed_topics: List[str] = []

    # ── 公開方法 ──────────────────────────────────────────────

    def search_tutorial(self, topic: str, level: str = "beginner") -> str:
        """
        模擬搜尋免費教學資源。

        參數：
            topic: 學習主題
            level: 難度等級（beginner / intermediate / advanced）

        回傳：
            格式化的搜尋結果
        """
        valid_levels = {"beginner", "intermediate", "advanced"}
        if level not in valid_levels:
            return f"❌ level 必須為: {', '.join(valid_levels)}"

        level_label = {"beginner": "初學者", "intermediate": "中級", "advanced": "進階"}
        results = self._simulate_web_search(topic, level)

        self._resources.extend(results)

        lines = [
            f"🔍 「{topic}」({level_label[level]}) 教學資源搜尋結果:",
            f"  ─────────────────",
        ]
        for i, res in enumerate(results, 1):
            lines.append(
                f"  {i}. [{res['type']}] {res['title']}\n"
                f"     來源: {res['source']}\n"
                f"     時長: {res['duration']}\n"
                f"     評分: {'⭐' * res['rating']}"
            )
        return "\n".join(lines)

    def curate_resources(self, topic: str) -> str:
        """
        為指定主題策展已找到的資源，依品質排序。

        參數：
            topic: 主題關鍵字

        回傳：
            策展後的資源清單
        """
        matched = [
            r for r in self._resources if topic.lower() in r.get("title", "").lower()
        ]
        if not matched:
            return f"📭 尚未有「{topic}」相關的學習資源，請先使用 search_tutorial"

        matched.sort(key=lambda r: r.get("rating", 0), reverse=True)

        lines = [f"📚 「{topic}」資源策展 (共 {len(matched)} 項):"]
        for i, res in enumerate(matched, 1):
            lines.append(
                f"  {i:2d}. {'⭐' * res['rating']:6s} {res['title']}\n"
                f"       來源: {res['source']} | 時長: {res['duration']} | "
                f"類型: {res['type']}"
            )
        return "\n".join(lines)

    def create_learning_path(self, topic: str) -> str:
        """
        建立結構化學習路徑，包含里程碑與預估時間。

        參數：
            topic: 學習主題

        回傳：
            學習路徑詳情（含路徑 ID）
        """
        path_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        milestones = self._generate_milestones(topic)
        total_hours = sum(m["estimated_hours"] for m in milestones)

        self._learning_paths[path_id] = {
            "topic": topic,
            "milestones": milestones,
            "total_hours": total_hours,
            "created_at": now.isoformat(),
            "completed_milestones": [],
            "started_at": None,
        }

        lines = [
            f"🗺️ 學習路徑已建立 (ID: {path_id})",
            f"  主題: {topic}",
            f"  總預估時數: {total_hours} 小時",
            f"  ─────────────────",
            f"  里程碑:",
        ]
        for i, ms in enumerate(milestones, 1):
            lines.append(
                f"    {i}. {ms['title']}\n"
                f"       描述: {ms['description']}\n"
                f"       預估時數: {ms['estimated_hours']}h\n"
                f"       建議資源: {ms['suggested_resource']}"
            )
        return "\n".join(lines)

    def track_progress(self, path_id: str) -> str:
        """
        追蹤指定學習路徑的進度。

        參數：
            path_id: 學習路徑 ID

        回傳：
            進度報告（含完成百分比）
        """
        path = self._learning_paths.get(path_id)
        if not path:
            return f"❌ 找不到學習路徑: {path_id}"

        total = len(path["milestones"])
        completed = len(path["completed_milestones"])
        pct = round(completed / total * 100, 1) if total > 0 else 0.0

        pending = [
            ms
            for ms in path["milestones"]
            if ms["title"] not in path["completed_milestones"]
        ]

        bar_len = 20
        filled = int(bar_len * pct / 100)
        bar = "▓" * filled + "░" * (bar_len - filled)

        lines = [
            f"📊 學習進度: {path['topic']}",
            f"  [{bar}] {pct}%",
            f"  已完成: {completed}/{total} 里程碑",
            f"  總時數: {path['total_hours']}h",
        ]
        if completed == total:
            lines.append("  🎉 全部完成！")
        elif pending:
            lines.append(f"  下一步: {pending[0]['title']}")
        return "\n".join(lines)

    def get_recommendations(self) -> str:
        """
        根據已完成主題與知識缺口推薦下一個學習目標。

        回傳：
            推薦主題清單
        """
        all_topics = {
            "Python 基礎",
            "Python 進階",
            "版本控制 Git",
            "Linux 系統管理",
            "Docker 容器化",
            "CI/CD 自動化",
            "資料庫 SQL",
            "API 設計",
            "測試驅動開發",
            "雲端部署 AWS",
            "機器學習入門",
            "網路安全基礎",
            "監控與日誌",
            "微服務架構",
        }

        completed_set = set(self._completed_topics)
        gaps = all_topics - completed_set

        if not gaps:
            return "🎉 所有已知主題皆已完成，建議探索進階領域或貢獻開源專案"

        # 根據學習路徑中的主題，給予優先推薦
        in_progress_topics = {
            p["topic"] for p in self._learning_paths.values()
            if len(p["completed_milestones"]) < len(p["milestones"])
        }
        priority = list(gaps & in_progress_topics)
        remaining = list(gaps - in_progress_topics)

        lines = [f"🎯 學習推薦:"]
        if priority:
            lines.append(f"  ▶ 優先（進行中路徑相關）:")
            for t in priority[:3]:
                lines.append(f"    · {t}")
        if remaining:
            lines.append(f"  ○ 待探索:")
            for t in remaining[:5]:
                lines.append(f"    · {t}")
        return "\n".join(lines)

    # ── 內部方法 ──────────────────────────────────────────────

    def _simulate_web_search(
        self, topic: str, level: str
    ) -> List[Dict[str, Any]]:
        """
        模擬網路搜尋結果，回傳結構化資源清單。
        """
        resource_pool = {
            "beginner": [
                {
                    "type": "免費課程",
                    "title": f"{topic} 入門教學",
                    "source": "freeCodeCamp",
                    "duration": "4 小時",
                    "rating": 4,
                },
                {
                    "type": "影片教學",
                    "title": f"30 分鐘搞懂 {topic}",
                    "source": "YouTube",
                    "duration": "30 分鐘",
                    "rating": 5,
                },
                {
                    "type": "互動練習",
                    "title": f"{topic} 實作練習",
                    "source": "Codecademy",
                    "duration": "2 小時",
                    "rating": 4,
                },
            ],
            "intermediate": [
                {
                    "type": "專案實戰",
                    "title": f"{topic} 專案實戰",
                    "source": "Udemy",
                    "duration": "8 小時",
                    "rating": 4,
                },
                {
                    "type": "文件導讀",
                    "title": f"{topic} 進階指南",
                    "source": "官方文件",
                    "duration": "3 小時",
                    "rating": 5,
                },
                {
                    "type": "社群討論",
                    "title": f"{topic} 最佳實踐",
                    "source": "Stack Overflow Blog",
                    "duration": "1 小時",
                    "rating": 3,
                },
            ],
            "advanced": [
                {
                    "type": "論文研讀",
                    "title": f"深入 {topic} 架構設計",
                    "source": "arXiv",
                    "duration": "10 小時",
                    "rating": 5,
                },
                {
                    "type": "開源貢獻",
                    "title": f"{topic} 開源專案貢獻指南",
                    "source": "GitHub",
                    "duration": "持續",
                    "rating": 4,
                },
                {
                    "type": "研討會錄影",
                    "title": f"{topic} 技術高峰會",
                    "source": "Confreaks",
                    "duration": "5 小時",
                    "rating": 4,
                },
            ],
        }

        return resource_pool.get(level, resource_pool["beginner"])

    def _generate_milestones(self, topic: str) -> List[Dict[str, Any]]:
        """
        根據主題產生結構化里程碑。
        """
        return [
            {
                "title": f"{topic} 概念理解",
                "description": f"閱讀 {topic} 基本概念與術語",
                "estimated_hours": 2,
                "suggested_resource": f"{topic} 入門教學 (freeCodeCamp)",
            },
            {
                "title": "環境設定",
                "description": "安裝必要工具與設定開發環境",
                "estimated_hours": 1,
                "suggested_resource": "官方安裝文件",
            },
            {
                "title": "基礎實作",
                "description": "完成第一個練習專案",
                "estimated_hours": 3,
                "suggested_resource": f"{topic} 實作練習 (Codecademy)",
            },
            {
                "title": "中級應用",
                "description": "實作較複雜的功能或整合",
                "estimated_hours": 4,
                "suggested_resource": f"{topic} 專案實戰 (Udemy)",
            },
            {
                "title": "最佳實踐與測試",
                "description": "學習單元測試、程式碼品質工具",
                "estimated_hours": 2,
                "suggested_resource": f"{topic} 進階指南 (官方文件)",
            },
        ]

    # ── 器官狀態 ──────────────────────────────────────────────

    def status(self) -> dict:
        total_paths = len(self._learning_paths)
        total_resources = len(self._resources)
        in_progress = sum(
            1
            for p in self._learning_paths.values()
            if 0 < len(p.get("completed_milestones", [])) < len(p.get("milestones", []))
        )
        return {
            "name": "AutoLearningOrgan",
            "alive": True,
            "total_paths": total_paths,
            "in_progress": in_progress,
            "total_resources": total_resources,
            "completed_topics": len(self._completed_topics),
        }
