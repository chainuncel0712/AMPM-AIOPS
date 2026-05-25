"""
PipelineSupervisor — 出版管線品質監督機械組件
==========================================
⚠️ 重要：本機械組件只能 observe + 報警，不能 blocking 流程。
   執行決策權完全在 ExecutionContext，違者視為 bug。

職責（僅限觀察）：
  1. 監控每本書的生產時長，超過閥值則報警
  2. 驗證每個階段的品質（內容不為空、有目錄等）
  3. 計算完成率、退件率、平均生產週期
  4. 對停滯超過 N 次循環的書推送警報（不阻擋）
"""
import json, os, threading, time, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "supervisor"

class PipelineSupervisor:
    def __init__(self):
        self.audit_file = DATA / "audit.json"
        self.stall_file = DATA / "stalls.json"
        DATA.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._running = False
        self._thread = None
        self.alert_callback: Optional[Callable] = None
        self._load()

    def _load(self):
        with self._lock:
            for f, default in [(self.audit_file, {"cycles": 0, "books_started": 0, "books_completed": 0,
                                                   "books_rejected": 0, "total_retries": 0, "alerts": 0}), (self.stall_file, [])]:
                if f.exists():
                    try:
                        setattr(self, f.stem, json.loads(f.read_text()))
                    except:
                        setattr(self, f.stem, default)
                else:
                    setattr(self, f.stem, default)

    def _save(self):
        with self._lock:
            self.audit_file.write_text(json.dumps(self.audit, ensure_ascii=False, indent=2))
            self.stall_file.write_text(json.dumps(self.stalls, ensure_ascii=False, indent=2))

    def set_alert_callback(self, fn: Callable):
        """設定警報回呼（推送到 Telegram）"""
        self.alert_callback = fn

    # ── 品質檢查 ──

    def verify_content_quality(self, book: dict, pipeline_type: str) -> list:
        """驗證一本書的內容品質，回傳缺失清單（空清單 = 通過）"""
        issues = []
        now = datetime.now()

        if pipeline_type == "ebook":
            topic = book.get("topic", "")
            status = book.get("status", "selected")
            created = book.get("created_at", "")
            if not topic:
                issues.append("缺少主題")
            if status in ("outline_done", "content_done", "pending_review", "approved", "published"):
                outline = book.get("outline", "")
                if not outline or len(outline) < 20:
                    issues.append("目錄不完整或為空")
            if status in ("content_done", "pending_review", "approved", "published"):
                content = book.get("content", "")
                if not content or len(content) < 100:
                    issues.append("內容不完整或為空")

        elif pipeline_type == "kidbook":
            title = book.get("title", "")
            status = book.get("status", "selected")
            created = book.get("created_at", "")
            age_range = book.get("age_range", "")
            if not title:
                issues.append("缺少書名")
            if not age_range:
                issues.append("缺少年齡層設定")
            if status in ("characters_done", "story_done", "pending_review", "approved", "published"):
                chars = book.get("characters", "")
                if not chars:
                    issues.append("角色設定為空")
            if status in ("story_done", "pending_review", "approved", "published"):
                story = book.get("story", "")
                if not story or len(story) < 100:
                    issues.append("故事內容不完整")

        created_dt = datetime.fromisoformat(created) if created else now
        age_hours = (now - created_dt).total_seconds() / 3600
        if age_hours > 72 and status != "published":
            issues.append(f"已停留 {int(age_hours)} 小時未完成")

        return issues

    def check_quality_gate(self, book: dict, pipeline_type: str) -> dict:
        """檢查品質閘門，回傳 {passed, issues, recommendation}"""
        issues = self.verify_content_quality(book, pipeline_type)
        return {
            "book_id": book.get("id", "?"),
            "title": book.get("topic") or book.get("title", "?"),
            "status": book.get("status", "?"),
            "passed": len(issues) == 0,
            "issues": issues,
            "recommendation": "可繼續" if len(issues) == 0 else "需人工處理" if any("72" in i for i in issues) else "建議退回",
        }

    # ── 停滯偵測 ──

    def detect_stalls(self, engine) -> list:
        """找出所有停滯的書籍"""
        stalls = []
        now = datetime.now()

        for book in engine.ebook.ebooks:
            status = book.get("status", "selected")
            if status in ("published", "rejected"):
                continue
            created = book.get("created_at", "")
            created_dt = datetime.fromisoformat(created) if created else now
            hours = (now - created_dt).total_seconds() / 3600
            cycle_stall_count = sum(1 for s in self.stalls if s.get("book_id") == book["id"])
            if hours > 24 and cycle_stall_count >= 3:
                stalls.append({
                    "book_id": book["id"],
                    "title": book.get("topic", "?"),
                    "type": "ebook",
                    "status": status,
                    "stalled_hours": int(hours),
                    "cycles_stalled": cycle_stall_count,
                    "created_at": created,
                })

        for book in engine.kidbook.kidbooks:
            status = book.get("status", "selected")
            if status in ("published", "rejected"):
                continue
            created = book.get("created_at", "")
            created_dt = datetime.fromisoformat(created) if created else now
            hours = (now - created_dt).total_seconds() / 3600
            cycle_stall_count = sum(1 for s in self.stalls if s.get("book_id") == book["id"])
            if hours > 24 and cycle_stall_count >= 3:
                stalls.append({
                    "book_id": book["id"],
                    "title": book.get("title", "?"),
                    "type": "kidbook",
                    "status": status,
                    "stalled_hours": int(hours),
                    "cycles_stalled": cycle_stall_count,
                    "created_at": created,
                })

        return stalls

    # ── 審計記錄 ──

    def record_cycle(self, ebook_count: int, kidbook_count: int, retries: int, errors: int):
        with self._lock:
            self.audit["cycles"] += 1
            self.audit["books_started"] += ebook_count + kidbook_count
            self.audit["total_retries"] += retries
            self._save()

    def record_completion(self, book_id: str, pipeline_type: str):
        with self._lock:
            self.audit["books_completed"] += 1
            self._save()

    def record_rejection(self, book_id: str):
        with self._lock:
            self.audit["books_rejected"] += 1
            self._save()

    def record_stall(self, stall_info: dict):
        with self._lock:
            stall_info["detected_at"] = datetime.now().isoformat()
            self.stalls.append(stall_info)
            if len(self.stalls) > 200:
                self.stalls = self.stalls[-100:]
            self._save()

    # ── 監督循環 ──

    def supervise(self, engine) -> str:
        """執行一次完整監督，回報結果"""
        lines = ["🔎 管線品質監督報告", "=" * 30]

        # 1. 品質抽檢
        ebook_issues = 0
        for book in engine.ebook.ebooks:
            gate = self.check_quality_gate(book, "ebook")
            if not gate["passed"]:
                ebook_issues += 1
                lines.append(f"  ⚠️ 電子書《{gate['title']}》: {'; '.join(gate['issues'])}")

        kid_issues = 0
        for book in engine.kidbook.kidbooks:
            gate = self.check_quality_gate(book, "kidbook")
            if not gate["passed"]:
                kid_issues += 1
                lines.append(f"  ⚠️ 童書《{gate['title']}》: {'; '.join(gate['issues'])}")

        if ebook_issues == 0 and kid_issues == 0:
            lines.append("  ✅ 所有書籍品質檢查通過")

        # 2. 停滯偵測
        stalls = self.detect_stalls(engine)
        if stalls:
            lines.append(f"  🛑 發現 {len(stalls)} 本停滯書籍：")
            for s in stalls:
                lines.append(f"    {s['type']}《{s['title']}》- {s['stalled_hours']} 小時停在 {s['status']}")
                self.record_stall(s)
            # 發送警報
            if self.alert_callback:
                alert = "🛑 出版管線警報\n" + "\n".join(
                    f"《{s['title']}》停在 {s['status']} 已 {s['stalled_hours']} 小時" for s in stalls[:5])
                try:
                    self.alert_callback(alert)
                    self.audit["alerts"] = self.audit.get("alerts", 0) + 1
                    self._save()
                except Exception as e:
                    lines.append(f"  ⚠️ 警報發送失敗: {e}")
        else:
            lines.append("  ✅ 無停滯書籍")

        # 3. 生產力指標
        a = self.audit
        total = a["books_started"]
        completed = a["books_completed"]
        rate = (completed / total * 100) if total > 0 else 0
        lines.append("")
        lines.append(f"📊 生產力指標")
        lines.append(f"  啟動總數：{total}")
        lines.append(f"  完成總數：{completed}")
        lines.append(f"  退件總數：{a['books_rejected']}")
        lines.append(f"  完成率：{rate:.1f}%")
        lines.append(f"  重試次數：{a['total_retries']}")

        return "\n".join(lines)

    # ── 背景監督 ──

    def start(self, engine, interval_seconds: int = 1800):
        """啟動背景監督（每 N 秒檢查一次）"""
        if self._running:
            return "🔎 品質監督已在運行"

        def _loop():
            self._running = True
            while self._running:
                try:
                    report = self.supervise(engine)
                    print(f"[PipelineSupervisor] 監督完成")
                    if self.alert_callback and any("🛑" in line for line in report.split("\n")):
                        pass  # alert already sent in supervise()
                except Exception as e:
                    print(f"[PipelineSupervisor] 監督錯誤: {e}")
                time.sleep(interval_seconds)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return f"🔎 品質監督已啟動（每 {interval_seconds//60} 分鐘）"

    def stop(self):
        self._running = False
        return "🔎 品質監督已停止"

    def status(self) -> dict:
        a = self.audit
        total = a["books_started"]
        completed = a["books_completed"]
        stalled = sum(1 for s in self.stalls
                      if isinstance(s, dict) and s.get("stalled") and not s.get("resolved"))
        return {
            "name": "PipelineSupervisor",
            "alive": True,
            "cycles": a["cycles"],
            "books_started": total,
            "books_completed": completed,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
            "rejected": a["books_rejected"],
            "retries": a["total_retries"],
            "stalls_tracked": len(self.stalls),
            "stalled_count": stalled,
            "alert_count": a.get("alerts", 0),
            "running": self._running,
        }

    def report(self) -> str:
        st = self.status()
        lines = []
        lines.append("🔎 品質監督機械組件狀態")
        lines.append("=" * 30)
        lines.append(f"  背景運行：{'🟢' if st['running'] else '🔴'}")
        lines.append(f"  監督次數：{st['cycles']}")
        lines.append(f"  完成率：{st['completion_rate']}%")
        lines.append(f"  重試次數：{st['retries']}")
        lines.append(f"  追蹤中停滯：{st['stalls_tracked']}")
        return "\n".join(lines)


supervisor = PipelineSupervisor()
