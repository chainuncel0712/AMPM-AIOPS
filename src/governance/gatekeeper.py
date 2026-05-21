"""
Gatekeeper — 系統唯一授權入口
================================
所有模組啟動前必須經過 Gatekeeper.check()。

規則：
1. 只能從 main.py 的 main() 函數內部啟動
2. 禁止模組自行 import 後另開 thread / process
3. 所有 thread 啟動必須註冊到 Gatekeeper
4. 違反者拋 GatekeeperViolation，系統強製中止
"""
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Set


class GatekeeperViolation(Exception):
    """違反閘門規則時拋出"""
    pass


class Gatekeeper:
    _instance = None
    _lock = threading.Lock()

    # 允許啟動的模組白名單（module_path → allowed）
    WHITELIST: Dict[str, bool] = {}

    # 已註冊的執行緒
    _registered_threads: Dict[str, threading.Thread] = {}

    # 是否已通過入口檢查
    _entry_passed = False
    _entry_caller = ""  # 記錄誰通過了入口

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # ── 入口檢查 ──────────────────────────────────────

    @classmethod
    def check_entry(cls, caller_name: str = "main"):
        """
        唯一入口檢查：只能在 main.py 的 main() 中被呼叫。
        caller_name: 預設 "main"，其他名稱會觸發警告。
        """
        if caller_name != "main":
            print(f"⚠️ [Gatekeeper] 非 main 入口嘗試啟動: {caller_name}")
            if not os.getenv("AMPM_ALLOW_NON_MAIN_ENTRY"):
                raise GatekeeperViolation(
                    f"不允許從 {caller_name} 啟動系統。"
                    f"請使用 python main.py"
                )

        # 檢查呼叫堆疊，確保源自 main.py
        stack = traceback.extract_stack()
        caller_frame = stack[-3] if len(stack) >= 3 else stack[-1]
        caller_file = Path(caller_frame.filename).resolve()

        if caller_name == "main":
            expected_main = Path(__file__).parent.parent.parent / "main.py"
            if caller_file != expected_main:
                print(f"⚠️ [Gatekeeper] 入口呼叫來源非 main.py: {caller_file.name}")
                if not os.getenv("AMPM_ALLOW_NON_MAIN_ENTRY"):
                    raise GatekeeperViolation(
                        f"入口必須從 main.py 呼叫，實際來源: {caller_file.name}"
                    )

        cls._entry_passed = True
        cls._entry_caller = caller_name
        return True

    @classmethod
    def is_entry_passed(cls) -> bool:
        return cls._entry_passed

    # ── 執行緒管理 ──────────────────────────────────────

    @classmethod
    def register_thread(cls, name: str, thread: threading.Thread) -> bool:
        """註冊一個背景執行緒。"""
        if not cls._entry_passed:
            raise GatekeeperViolation(
                f"執行緒 {name} 未經入口檢查，拒絕註冊。"
                f"所有 thread 必須在 main() 內部啟動。"
            )
        with cls._lock:
            cls._registered_threads[name] = thread
        return True

    @classmethod
    def unregister_thread(cls, name: str):
        with cls._lock:
            cls._registered_threads.pop(name, None)

    @classmethod
    def get_registered_threads(cls) -> Dict[str, threading.Thread]:
        with cls._lock:
            return dict(cls._registered_threads)

    @classmethod
    def check_module_permission(cls, module_name: str, action: str) -> bool:
        """
        檢查模組是否有權限執行某動作。
        回傳 False = 無權限（僅記錄，不強製中止 — 初期階段）。
        """
        import json
        perm_file = Path(__file__).parent / "permissions.json"
        if not perm_file.exists():
            return True  # 還沒有權限檔案時，全部允許

        try:
            perms = json.loads(perm_file.read_text())
            module_perms = perms.get(module_name, {})
            allowed_list = module_perms.get("allowed", [])
            denied_list = module_perms.get("denied", [])
            if action in denied_list:
                print(f"🔒 [Gatekeeper] {module_name} 不允許執行 {action}（拒絕清單）")
                return False
            if action in allowed_list:
                return True
            print(f"🔒 [Gatekeeper] {module_name} 無權限執行 {action}（不在允許清單）")
            return False
        except Exception:
            return True


# 單例快捷
gatekeeper = Gatekeeper()
