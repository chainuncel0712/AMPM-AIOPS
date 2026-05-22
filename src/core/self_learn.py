"""
SelfLearnOrgan — 自我學習器官
從對話中提取可操作的洞察，建立主題化知識庫，支援知識衰減與覆查。
"""
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent


class SelfLearnOrgan(BrainComponent):
    """
    自我學習器官

    功能：
    1. 從使用者對話中提取可操作的洞察並儲存
    2. 按主題查詢已學習的教訓
    3. 自動清除超過 30 天的低信心教訓
    4. 知識覆查與摘要
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._lock = threading.RLock()
        self.lessons: List[Dict[str, Any]] = []

    # ── 公開方法 ──────────────────────────────────────────────

    def learn_from_conversation(
        self, user_msg: str, assistant_msg: str, outcome: str
    ) -> str:
        """
        從一段對話中學習，儲存洞察。

        參數：
            user_msg: 使用者訊息
            assistant_msg: AI 助理回覆
            outcome: 結果標籤（例如 'success', 'failure', 'neutral'）

        回傳：
            確認訊息與洞察 ID
        """
        if not user_msg.strip() or not assistant_msg.strip():
            return "❌ 使用者訊息與助理回覆不可為空"

        insight = self._extract_insight_from_text(user_msg, assistant_msg, outcome)
        topic = self._infer_topic(user_msg)
        lesson_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        entry: Dict[str, Any] = {
            "id": lesson_id,
            "topic": topic,
            "insight": insight,
            "user_msg": user_msg[:500],
            "assistant_msg": assistant_msg[:500],
            "outcome": outcome,
            "confidence": self._compute_confidence(outcome),
            "timestamp": now.isoformat(),
            "retrieved_count": 0,
        }

        with self._lock:
            self.lessons.append(entry)

        return (
            f"📚 已從對話中學習 (ID: {lesson_id})\n"
            f"  主題: {topic}\n"
            f"  洞察: {insight[:120]}{'...' if len(insight) > 120 else ''}\n"
            f"  信心指數: {entry['confidence']:.1%}\n"
            f"  結果: {outcome}"
        )

    def extract_insight(self, topic: str) -> str:
        """
        提取指定主題下最具價值的洞察。

        參數：
            topic: 主題關鍵字

        回傳：
            格式化的洞察摘要
        """
        matched = self._filter_by_topic(topic)
        if not matched:
            return f"📭 尚未有「{topic}」相關的學習紀錄"

        matched.sort(key=lambda x: x["confidence"], reverse=True)
        top = matched[0]

        return (
            f"💡 主題「{topic}」最佳洞察:\n"
            f"  洞察: {top['insight']}\n"
            f"  信心: {top['confidence']:.1%}\n"
            f"  來源對話: {top['user_msg'][:80]}...\n"
            f"  時間: {top['timestamp']}\n"
            f"  該主題共 {len(matched)} 筆紀錄"
        )

    def get_lessons(self, topic: Optional[str] = None) -> str:
        """
        取得指定主題的所有教訓；若不指定主題則回傳全部。

        參數：
            topic: 主題關鍵字（可選）

        回傳：
            格式化的教訓列表
        """
        with self._lock:
            lessons = self._filter_by_topic(topic) if topic else list(self.lessons)

        if not lessons:
            label = f"「{topic}」" if topic else ""
            return f"📭 尚未學習{label}相關內容"

        lessons.sort(key=lambda x: x["confidence"], reverse=True)
        lines = [f"📋 已學習{'「' + topic + '」' if topic else ''}共 {len(lessons)} 課:"]

        for i, lesson in enumerate(lessons[:20], 1):
            lines.append(
                f"  {i:2d}. [{lesson['confidence']:.0%}] "
                f"{lesson['insight'][:80]}"
            )
            # 更新取用次數
            lesson["retrieved_count"] += 1

        if len(lessons) > 20:
            lines.append(f"  ... 還有 {len(lessons) - 20} 課未顯示")
        return "\n".join(lines)

    def review_knowledge(self) -> str:
        """
        覆查所有已學習知識，提供統計摘要。

        回傳：
            知識庫統計與近期重點
        """
        with self._lock:
            total = len(self.lessons)
            if total == 0:
                return "📭 知識庫為空，尚未進行任何學習"

            topics: Dict[str, int] = {}
            total_confidence = 0.0
            outcomes: Dict[str, int] = {}

            for lesson in self.lessons:
                t = lesson.get("topic", "未分類")
                topics[t] = topics.get(t, 0) + 1
                total_confidence += lesson.get("confidence", 0.0)
                o = lesson.get("outcome", "unknown")
                outcomes[o] = outcomes.get(o, 0) + 1

            avg_conf = total_confidence / total if total > 0 else 0.0
            top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]

            lines = [
                f"🧠 知識庫覆查報告",
                f"  ─────────────────",
                f"  總課數: {total}",
                f"  平均信心: {avg_conf:.1%}",
                f"  主題分佈: ",
            ]
            for topic_name, count in top_topics:
                lines.append(f"    · {topic_name}: {count} 課")
            lines.append(f"  結果分佈: {outcomes}")

            # 自動清理過時教訓
            cleaned = self._auto_cleanup(days=30)
            if cleaned > 0:
                lines.append(f"  🧹 已自動清除 {cleaned} 筆過時低信心紀錄")

            return "\n".join(lines)

    def forget_old_lessons(self, days: int = 30) -> str:
        """
        手動清除超過指定天數且信心低於閾值的教訓。

        參數：
            days: 天數閾值，超過此天數且信心 < 0.5 的教訓將被移除

        回傳：
            清除結果
        """
        cleaned = self._auto_cleanup(days=days)
        return (
            f"🧹 已清除 {cleaned} 筆超過 {days} 天的低信心教訓\n"
            f"  剩餘教訓: {len(self.lessons)} 筆"
        )

    # ── 內部方法 ──────────────────────────────────────────────

    def _extract_insight_from_text(
        self, user_msg: str, assistant_msg: str, outcome: str
    ) -> str:
        """
        從對話中提取洞察。
        基於關鍵字與語意模式的輕量提取。
        """
        # 嘗試從使用者訊息中提取問題本質
        lower = user_msg.lower()

        if any(kw in lower for kw in ["怎麼做", "how", "如何", "步驟"]):
            prefix = "操作步驟類"
        elif any(kw in lower for kw in ["錯誤", "error", "失敗", "修復", "fix"]):
            prefix = "錯誤排除類"
        elif any(kw in lower for kw in ["最佳", "best", "推薦", "建議"]):
            prefix = "最佳實踐類"
        elif any(kw in lower for kw in ["為什麼", "why", "原因"]):
            prefix = "原因分析類"
        else:
            prefix = "一般知識類"

        # 從使用者訊息提取關鍵句
        key_sentence = user_msg[:100].strip().rstrip(".。！!？?")
        outcome_label = {"success": "✅ 成功", "failure": "❌ 失敗", "neutral": "➖ 中性"}.get(
            outcome, outcome
        )

        return f"[{prefix}] {key_sentence} → {outcome_label}"

    def _infer_topic(self, text: str) -> str:
        """
        從文字中推論主題，使用關鍵字比對。
        """
        topic_keywords = {
            "Python": ["python", "pip", "venv", "pytest", "django", "flask"],
            "部署": ["deploy", "docker", "kubernetes", "nginx", "部署", "上線"],
            "資料庫": ["sql", "mysql", "postgres", "redis", "mongo", "資料庫"],
            "系統維運": ["linux", "bash", "shell", "cron", "systemd", "監控"],
            "AI/ML": ["ai", "ml", "model", "模型", "訓練", "inference", "llm"],
            "前端": ["html", "css", "js", "react", "vue", "前端"],
            "API": ["api", "rest", "graphql", "webhook"],
            "安全性": ["security", "auth", "token", "加密", "安全性"],
            "工具": ["tool", "cli", "script", "自動化", "automation"],
        }

        lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in lower for kw in keywords):
                return topic

        return "通用"

    def _compute_confidence(self, outcome: str) -> float:
        """
        根據結果計算信心分數。
        """
        return {"success": 0.85, "failure": 0.3, "neutral": 0.6}.get(outcome, 0.5)

    def _filter_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        從 lessons 中過濾出指定主題的項目。
        """
        with self._lock:
            return [
                lesson
                for lesson in self.lessons
                if lesson.get("topic", "").lower() == topic.lower()
            ]

    def _auto_cleanup(self, days: int = 30) -> int:
        """
        自動清除超過指定天數且信心 < 0.5 的教訓。
        回傳清除筆數。
        """
        cutoff = datetime.now() - timedelta(days=days)
        with self._lock:
            before = len(self.lessons)
            self.lessons = [
                lesson
                for lesson in self.lessons
                if not (
                    lesson.get("confidence", 0.0) < 0.5
                    and datetime.fromisoformat(lesson["timestamp"]) < cutoff
                )
            ]
            return before - len(self.lessons)

    # ── 器官狀態 ──────────────────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            total = len(self.lessons)
            avg_conf = (
                sum(l.get("confidence", 0.0) for l in self.lessons) / total
                if total > 0
                else 0.0
            )
            topics = list({l.get("topic", "未分類") for l in self.lessons})
        return {
            "name": "SelfLearnOrgan",
            "alive": True,
            "total_lessons": total,
            "avg_confidence": round(avg_conf, 3),
            "topics": topics,
        }
