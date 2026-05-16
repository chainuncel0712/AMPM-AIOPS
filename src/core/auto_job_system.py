"""
AutoJobSystemOrgan — 自主排程系統器官
輕量級 cron-like 排程器，使用 daemon 執行緒執行背景任務。
"""
import subprocess
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent

MAX_CONCURRENT_JOBS = 20


class AutoJobSystemOrgan(BrainComponent):
    """
    自主排程系統器官

    功能：
    1. 排程定期執行任務（輕量 cron）
    2. 追蹤任務執行歷史（成功/失敗/耗時）
    3. 背景 daemon 執行緒執行
    4. 最多 20 個並行任務
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._lock = threading.RLock()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []
        self._active_threads: Dict[str, threading.Timer] = {}

    # ── 公開方法 ──────────────────────────────────────────────

    def schedule_job(
        self, name: str, command: str, interval_minutes: int
    ) -> str:
        """
        排程一個定時任務。

        參數：
            name: 任務名稱（唯一識別）
            command: 要執行的指令（shell 命令）
            interval_minutes: 執行間隔（分鐘）

        回傳：
            排程確認訊息
        """
        if not name.strip():
            return "❌ 任務名稱不可為空"
        if not command.strip():
            return "❌ 指令不可為空"
        if interval_minutes < 1:
            return "❌ 間隔時間至少為 1 分鐘"

        with self._lock:
            active_count = sum(
                1 for j in self.jobs.values() if j.get("status") == "running"
            )
            if active_count >= MAX_CONCURRENT_JOBS:
                return f"❌ 已達最大並行任務數上限 ({MAX_CONCURRENT_JOBS})"

            if name in self.jobs:
                return (
                    f"⚠️ 任務「{name}」已存在，請先 remove 再重新排程\n"
                    f"  當前狀態: {self.jobs[name].get('status')}"
                )

            job_id = str(uuid.uuid4())[:8]
            now = datetime.now()

            self.jobs[name] = {
                "id": job_id,
                "name": name,
                "command": command,
                "interval_minutes": interval_minutes,
                "status": "running",
                "created_at": now.isoformat(),
                "last_run": None,
                "next_run": None,
                "success_count": 0,
                "failure_count": 0,
            }

            # 啟動背景排程執行緒
            self._start_job_loop(name)

        return (
            f"✅ 已排程任務「{name}」\n"
            f"  指令: {command[:80]}\n"
            f"  間隔: {interval_minutes} 分鐘\n"
            f"  狀態: running"
        )

    def list_jobs(self) -> str:
        """
        列出所有已排程的任務及其狀態。

        回傳：
            格式化的任務清單
        """
        with self._lock:
            if not self.jobs:
                return "📭 目前沒有排程中的任務"

            lines = ["📋 排程任務清單:"]
            for i, (name, job) in enumerate(self.jobs.items(), 1):
                status_icon = {
                    "running": "▶",
                    "paused": "⏸",
                    "completed": "✓",
                }.get(job.get("status"), "?")

                lines.append(
                    f"  {i:2d}. {status_icon} {name}\n"
                    f"       狀態: {job.get('status')} | "
                    f"間隔: {job.get('interval_minutes')}min | "
                    f"成功: {job.get('success_count')} | "
                    f"失敗: {job.get('failure_count')}\n"
                    f"       上次執行: {job.get('last_run') or '從未'}"
                )
            return "\n".join(lines)

    def get_job_history(self, name: str) -> str:
        """
        取得指定任務的執行歷史。

        參數：
            name: 任務名稱

        回傳：
            格式化的歷史紀錄
        """
        with self._lock:
            job = self.jobs.get(name)
            if not job:
                return f"❌ 找不到任務: {name}"

            job_entries = [h for h in self.history if h.get("job_name") == name]
            job_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if not job_entries:
            return f"📭 「{name}」尚未有執行紀錄"

        lines = [
            f"📜 「{name}」執行歷史 (共 {len(job_entries)} 筆):",
            f"  ─────────────────",
        ]
        for i, entry in enumerate(job_entries[:10], 1):
            icon = "✅" if entry.get("success") else "❌"
            lines.append(
                f"  {i:2d}. {icon} {entry.get('timestamp')}\n"
                f"       耗時: {entry.get('duration', 'N/A')}s | "
                f"輸出: {entry.get('output', '')[:60]}"
            )
        if len(job_entries) > 10:
            lines.append(f"  ... 還有 {len(job_entries) - 10} 筆未顯示")
        return "\n".join(lines)

    def pause_job(self, name: str) -> str:
        """
        暫停指定任務。

        參數：
            name: 任務名稱
        """
        return self._change_job_status(name, "running", "paused", "⏸ 已暫停")

    def resume_job(self, name: str) -> str:
        """
        恢復已暫停的任務。

        參數：
            name: 任務名稱
        """
        result = self._change_job_status(name, "paused", "running", "▶ 已恢復")
        if "已恢復" in result:
            # 重新啟動背景迴圈
            self._start_job_loop(name)
        return result

    def remove_job(self, name: str) -> str:
        """
        移除任務並停止其排程。

        參數：
            name: 任務名稱
        """
        with self._lock:
            if name not in self.jobs:
                return f"❌ 找不到任務: {name}"

            # 取消定時器
            timer = self._active_threads.pop(name, None)
            if timer:
                timer.cancel()

            del self.jobs[name]

        return f"🗑 已移除任務「{name}」"

    # ── 內部方法 ──────────────────────────────────────────────

    def _start_job_loop(self, name: str):
        """
        啟動任務的背景執行迴圈（daemon 執行緒）。
        """
        # 取消舊的定時器
        old_timer = self._active_threads.pop(name, None)
        if old_timer:
            old_timer.cancel()

        def _run_cycle():
            job = self.jobs.get(name)
            if not job or job.get("status") != "running":
                return

            # 執行任務
            self._execute_job(name)

            # 排程下一次執行
            interval_seconds = job.get("interval_minutes", 5) * 60
            timer = threading.Timer(interval_seconds, _run_cycle)
            timer.daemon = True
            self._active_threads[name] = timer
            next_run = datetime.now().timestamp() + interval_seconds
            with self._lock:
                if name in self.jobs:
                    self.jobs[name]["next_run"] = datetime.fromtimestamp(
                        next_run
                    ).isoformat()
            timer.start()

        # 第一次執行：等待一個間隔後執行
        interval_seconds = (
            self.jobs.get(name, {}).get("interval_minutes", 5) * 60
        )
        timer = threading.Timer(interval_seconds, _run_cycle)
        timer.daemon = True
        self._active_threads[name] = timer
        next_run = datetime.now().timestamp() + interval_seconds
        with self._lock:
            if name in self.jobs:
                self.jobs[name]["next_run"] = datetime.fromtimestamp(
                    next_run
                ).isoformat()
        timer.start()

    def _execute_job(self, name: str):
        """
        執行一個任務並記錄結果。
        """
        job = self.jobs.get(name)
        if not job:
            return

        command = job.get("command", "")
        start_time = datetime.now()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分鐘逾時
            )
            success = result.returncode == 0
            output = (result.stdout or result.stderr or "")[:200]
            duration = (datetime.now() - start_time).total_seconds()
        except subprocess.TimeoutExpired:
            success = False
            output = "執行逾時 (>5 分鐘)"
            duration = 300.0
        except Exception as e:
            success = False
            output = str(e)[:200]
            duration = (datetime.now() - start_time).total_seconds()

        now = datetime.now()
        with self._lock:
            if name in self.jobs:
                self.jobs[name]["last_run"] = now.isoformat()
                if success:
                    self.jobs[name]["success_count"] += 1
                else:
                    self.jobs[name]["failure_count"] += 1

            self.history.append(
                {
                    "job_name": name,
                    "command": command,
                    "success": success,
                    "output": output,
                    "duration": round(duration, 2),
                    "timestamp": now.isoformat(),
                }
            )

    def _change_job_status(
        self,
        name: str,
        expected_status: str,
        new_status: str,
        success_prefix: str,
    ) -> str:
        """變更任務狀態的通用輔助方法。"""
        with self._lock:
            job = self.jobs.get(name)
            if not job:
                return f"❌ 找不到任務: {name}"
            if job.get("status") != expected_status:
                return (
                    f"⚠️ 任務「{name}」目前狀態為 {job.get('status')}，"
                    f"無法從 {expected_status} 轉為 {new_status}"
                )
            job["status"] = new_status
        return f"{success_prefix} 任務「{name}」"

    # ── 器官狀態 ──────────────────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            total = len(self.jobs)
            running = sum(
                1 for j in self.jobs.values() if j.get("status") == "running"
            )
            paused = sum(
                1 for j in self.jobs.values() if j.get("status") == "paused"
            )
            total_executions = len(self.history)
        return {
            "name": "AutoJobSystemOrgan",
            "alive": True,
            "total_jobs": total,
            "running": running,
            "paused": paused,
            "total_executions": total_executions,
            "max_concurrent": MAX_CONCURRENT_JOBS,
        }
