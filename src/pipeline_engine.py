"""
Publisher Engine — 統一出版管線引擎
====================================
支援 9 種產品類型，9 階段流水線。
每小時自動循環，逐步推進所有書籍。
"""
import random, time, threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict, List

from pipeline_presets import PRODUCT_TYPES, FALLBACK_TOPICS, STAGE_LABELS, HUMAN_GATES
from pipeline_data import store, create_book
from pipeline_stages import STAGE_HANDLERS, TOPIC_PROMPTS

from resource_scout import scout as resource_scout
from pipeline_supervisor import supervisor as pipeline_supervisor

BASE = Path(__file__).resolve().parent.parent


class _PipelineProxy:
    """Dispatch pipeline commands to the engine, filtering by product type."""

    def __init__(self, engine, product_type: str):
        self._engine = engine
        self._type = product_type

    def trend_analysis(self):
        return self._engine.create_topic(self._type)

    def select_topic(self, topic: str):
        return self._engine.create_topic(self._type, topic)

    def select_theme(self, title: str, theme: str, age: str, summary: str):
        return self._engine.create_topic(
            self._type, title,
            theme=theme, age=age, summary=summary,
        )

    def approve(self, book_id: str):
        return self._engine.approve_topic(self._type, book_id)

    def reject(self, book_id: str, reason: str = ""):
        return self._engine.reject_topic(book_id)

    def publish(self, book_id: str):
        return self._engine.approve_topic(self._type, book_id)


class PublisherEngine:
    """統一管線引擎（全身器官整合版）"""

    def __init__(self):
        self._running = False
        self._cycle_thread = None
        self._auto_publish = False
        self._orchestrator = None
        self.ebook = _PipelineProxy(self, "ebook")
        self.kidbook = _PipelineProxy(self, "kidbook")

    @property
    def orchestrator(self):
        if self._orchestrator is None:
            from pipeline_orchestrator import orchestrator
            self._orchestrator = orchestrator
        return self._orchestrator

    # ── 選題 ──

    def create_topic(self, product_type: str, title: str = "", **kwargs) -> str:
        """Stage 1: 建立選題 (自動去重)"""
        preset = PRODUCT_TYPES[product_type]
        if not title:
            fallback = FALLBACK_TOPICS.get(product_type, ["未命名"])
            if isinstance(fallback[0], dict):
                f = random.choice(fallback)
                title = f.pop("title", "未命名")
                kwargs.update({k: v for k, v in f.items() if k != "title"})
            else:
                title = random.choice(fallback)

        # 去重檢查
        existing = [b for b in store.books if b.get("product_type") == product_type
                    and b.get("stage_data", {}).get("1", {}).get("title") == title]
        if existing:
            return f"⏭️ 《{title}》已存在，跳過"

        book = create_book(product_type, title, **kwargs)
        book_id = store.add(book)
        return f"{preset['icon']} 《{title}》選題已建立 (ID: {book_id})，待審核"

    def approve_topic(self, pipeline: str, book_id: str) -> str:
        """人工通過選題閘門"""
        book = store.get(book_id)
        if not book:
            return "找不到書籍"
        if book["current_stage"] != 1:
            return f"書籍已在階段 {book['current_stage']}，無需審核選題"
        store.update(book_id, {
            "stage_data": {**book["stage_data"], "1": {**book["stage_data"]["1"], "approved": True, "approved_at": datetime.now().isoformat()}}
        })
        preset = PRODUCT_TYPES.get(book.get("product_type", "ebook"), {})
        return f"✅ {preset.get('icon','')} 《{book['stage_data']['1'].get('title','?')}》選題已通過，進入流水線"

    # ── 推進 ──

    def advance(self, book_id: str, llm_call: Optional[Callable] = None) -> Dict:
        """推進一本書到下一個階段"""
        book = store.get(book_id)
        if not book:
            return {"ok": False, "error": "not_found"}

        stage = book["current_stage"]
        product_type = book.get("product_type", "ebook")
        preset = PRODUCT_TYPES.get(product_type, PRODUCT_TYPES["ebook"])
        stage_cfg = preset["stages"].get(stage, {})

        title = book["stage_data"]["1"].get("title", "?")

        # 人工閘門
        if stage in HUMAN_GATES:
            if stage == 1 and not book["stage_data"]["1"].get("approved"):
                return {"ok": False, "stage": stage, "status": "human_gate", "reason": f"《{title}》選題待審核"}
            if stage == 8:
                return {"ok": False, "stage": stage, "status": "human_gate", "reason": f"《{title}》最終審核待處理"}

        # 自動階段 — 使用器官協調器
        try:
            result_data = self.orchestrator.execute_stage(stage, book)
            book_copy = store.get(book_id)
            if book_copy:
                sd = dict(book_copy.get("stage_data", {}))
                sd[str(stage)] = result_data
                store.update(book_id, {"stage_data": sd, "current_stage": stage + 1})
            return {
                "ok": True, "stage": stage, "status": "advanced",
                "reason": f"{preset['icon']} 《{title}》→ {STAGE_LABELS.get(stage+1, stage+1)}"
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "stage": stage}

    def auto_cycle(self, llm_call: Optional[Callable] = None) -> str:
        """一輪循環：推進所有非阻塞書籍一步"""
        results = []

        # 資源偵查
        try:
            sr = resource_scout.scout_all()
            avail = sum(v["available"] for v in sr.values())
            total = sum(v["total"] for v in sr.values())
            results.append(f"🔍 資源偵查：{avail}/{total} 項可用")
        except:
            pass

        advanced = 0
        for book in store.books:
            if book.get("current_stage", 0) in (0, 10):
                continue
            r = self.advance(book["id"], llm_call)
            if r.get("ok"):
                results.append(f"  {r['reason']}")
                advanced += 1

        # 無活躍書 → 自動選題
        active = store.active_books()
        if not active:
            n = 0
            for pt in random.sample(list(PRODUCT_TYPES.keys()), min(3, len(PRODUCT_TYPES))):
                if n >= 2: break
                try:
                    msg = self.create_topic(pt)
                    results.append(f"  📈 {msg}")
                    n += 1
                except: pass

        if advanced == 0 and active:
            results.append("  ℹ️ 所有書籍在人工閘門等待審核")

        return "\n".join(results)

    # ── 自動循環控制 ──

    def start_auto_pilot(self, llm_call: Optional[Callable] = None, interval_hours: int = 1):
        if self._running: return "已運行中"
        def _loop():
            self._running = True
            while self._running:
                try:
                    result = self.auto_cycle(llm_call)
                    print(f"[PublisherEngine] 循環完成\n{result}")
                except Exception as e:
                    print(f"[PublisherEngine] 循環錯誤: {e}")
                time.sleep(interval_hours * 3600)
        self._cycle_thread = threading.Thread(target=_loop, daemon=True, name="pipeline-cycle")
        self._cycle_thread.start()
        return "🔄 已啟動"

    def stop_auto_pilot(self):
        self._running = False

    def reject_topic(self, book_id: str) -> str:
        """淘汰選題 → 記憶此類主題"""
        book = store.get(book_id)
        if not book: return "找不到書籍"
        title = book["stage_data"]["1"].get("title", "?")
        store.update(book_id, {
            "current_stage": 0,
            "stage_data": {**book.get("stage_data", {}), "1": {**book.get("stage_data", {}).get("1", {}), "approved": False, "reject_reason": "淘汰"}}
        })
        from pipeline_data import rejected
        rejected.add(title)
        preset = PRODUCT_TYPES.get(book.get("product_type", "ebook"), {})
        return f"❌ {preset.get('icon','')} 《{title}》已淘汰，記憶中"

    def retry_topic(self, book_id: str, new_title: str = "") -> str:
        """敗部復活：換個標題重新選題"""
        book = store.get(book_id)
        if not book: return "找不到書籍"
        old_title = book["stage_data"]["1"].get("title", "?")
        pt = book.get("product_type", "ebook")
        title = new_title or f"{old_title}（修訂版）"
        store.update(book_id, {
            "current_stage": 1,
            "stage_data": {**book.get("stage_data", {}), "1": {**book.get("stage_data", {}).get("1", {}), "title": title, "approved": False, "reject_reason": ""}}
        })
        preset = PRODUCT_TYPES.get(pt, {})
        return f"🔄 {preset.get('icon','')} 《{old_title}》→ 《{title}》重新進入選題"

    def set_auto_publish(self, enabled: bool):
        self._auto_publish = enabled

    def status(self) -> Dict:
        return store.stats()

    def generate_report(self, detailed: bool = False) -> str:
        stats = store.stats()
        from publishing_system import publisher as pub_mgr
        pub_items = pub_mgr.get_prepared_books()
        platforms = pub_mgr.get_platform_status()

        lines = ["🏭 出版工廠日報", "=============================="]
        by_type = stats.get("by_type", {})
        for pt, count in sorted(by_type.items()):
            preset = PRODUCT_TYPES.get(pt, {})
            lines.append(f"{preset.get('icon','?')} {preset.get('label',pt)}：{count} 本")
        lines.append("")
        lines.append(f"📊 總書籍：{stats['total']} | 活躍：{stats['active']} | 已出版：{stats['published']}")

        # 上架狀態
        lines.append("")
        lines.append("📤 上架平台狀態：")
        for name, p in platforms.items():
            icon = p["icon"]
            status = "✅" if p["status"] == "ready" else "🔧"
            lines.append(f"  {icon} {p['name']}: {status}")

        lines.append(f"📦 待上架：{len(pub_items)} 本")
        if pub_items:
            for item in pub_items[:5]:
                lines.append(f"  📗 {item['title'][:35]} — {item['status']}")

        lines.append(f"🔄 自動循環：{'🟢 運行中' if self._running else '🔴 已停止'}")
        return "\n".join(lines)


engine = PublisherEngine()
