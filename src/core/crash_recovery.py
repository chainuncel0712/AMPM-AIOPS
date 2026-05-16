"""
崩潰恢復器官 — 優雅關機保護
攔截 SIGTERM/SIGINT，在關機前儲存所有器官狀態、記憶、快照。
"""
import atexit
import json
import signal
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from skeleton.base_organ import BaseOrgan


class CrashRecovery(BaseOrgan):
    """
    崩潰恢復 — 最後一道防線

    職責：
    1. 攔截 SIGTERM / SIGINT 信號
    2. 關機前自動儲存所有狀態
    3. 下次啟動時載入上次崩潰原因
    4. 通知重生器官恢復
    """

    def __init__(self, base_dir: Path, organ_refs: dict = None):
        super().__init__("crash_recovery")
        self.base_dir = base_dir
        self.organ_refs = organ_refs or {}
        self.recovery_dir = base_dir / "data" / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

        self.crash_log_file = self.recovery_dir / "crash_log.json"
        self.recovery_state_file = self.recovery_dir / "last_state.json"
        self._clean_shutdown = False
        self._original_handlers = {}

        # 掛載信號處理
        self._setup_signal_handlers()

        # 註冊 atexit 最後一道防線
        atexit.register(self._atexit_handler)

        # 載入上次崩潰資訊
        self.last_crash = self._load_crash_log()

    # =========================================
    # 信號處理
    # =========================================

    def _setup_signal_handlers(self):
        """掛載 OS 信號攔截"""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            try:
                old = signal.signal(sig, self._signal_handler)
                self._original_handlers[sig] = old
            except Exception:
                pass  # 非主線程無法設 signal

    def _signal_handler(self, signum, frame):
        """攔截到關機信號"""
        sig_name = signal.Signals(signum).name
        print(f"\n🛑 [崩潰恢復] 收到 {sig_name} 信號，開始優雅關機...")
        self._emergency_save()
        self._clean_shutdown = True
        sys.exit(0)

    def _atexit_handler(self):
        """atexit 最後防線（即使沒有收到 signal 也會觸發）"""
        if self._clean_shutdown:
            return
        try:
            self._emergency_save()
        except Exception:
            pass

    # =========================================
    # 緊急儲存
    # =========================================

    def _emergency_save(self):
        """緊急儲存所有器官狀態"""
        saved = []
        failed = []

        for name, organ in self.organ_refs.items():
            try:
                if hasattr(organ, "save"):
                    organ.save()
                    saved.append(name)
            except Exception as e:
                failed.append({"name": name, "error": str(e)[:100]})

        # 記錄關機狀態
        state = {
            "shutdown_at": datetime.now().isoformat(),
            "saved_organs": saved,
            "failed_organs": failed,
            "total_organs": len(self.organ_refs),
        }
        try:
            self.recovery_state_file.write_text(
                json.dumps(state, ensure_ascii=False, indent=2))
        except Exception:
            pass

        print(f"💾 [崩潰恢復] 已儲存 {len(saved)}/{len(self.organ_refs)} 個器官狀態")

    # =========================================
    # 崩潰分析
    # =========================================

    def record_crash(self, exception: Exception, traceback_str: str = ""):
        """記錄崩潰事件"""
        crash = {
            "ts": datetime.now().isoformat(),
            "type": type(exception).__name__,
            "message": str(exception)[:200],
            "traceback": traceback_str[:500] if traceback_str else "",
        }
        crashes = self._load_crash_log_list()
        crashes.append(crash)
        if len(crashes) > 50:
            crashes = crashes[-50:]
        self.crash_log_file.write_text(
            json.dumps(crashes, ensure_ascii=False, indent=2))

    def _load_crash_log(self) -> Optional[dict]:
        """載入上次崩潰記錄"""
        crashes = self._load_crash_log_list()
        return crashes[-1] if crashes else None

    def _load_crash_log_list(self) -> list:
        if self.crash_log_file.exists():
            try:
                return json.loads(self.crash_log_file.read_text())
            except Exception:
                return []
        return []

    def get_last_crash_info(self) -> str:
        """取得上次崩潰摘要"""
        if not self.last_crash:
            return "✅ 無崩潰記錄"
        c = self.last_crash
        return f"⚠️ 上次崩潰: {c['type']} — {c['message'][:100]} ({c['ts'][:19]})"

    # =========================================
    # 恢復
    # =========================================

    def try_recover(self, rebirth=None) -> bool:
        """嘗試恢復上次崩潰前的狀態"""
        if not self.recovery_state_file.exists():
            return False

        try:
            state = json.loads(self.recovery_state_file.read_text())
        except Exception:
            return False

        if rebirth and hasattr(rebirth, "restore_from_snapshot"):
            return rebirth.restore_from_snapshot()
        return False

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "last_crash": self.last_crash["ts"][:19] if self.last_crash else None,
            "clean_shutdown": self._clean_shutdown,
        }
