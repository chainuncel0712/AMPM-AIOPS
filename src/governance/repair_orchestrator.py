"""
修復執行器 — 統一執行所有修復動作
====================================
Immune 只負責決策（要不要修、修哪裡）
RepairOrchestrator 只負責執行（怎麼修）
Monitor 只負責監視（有沒有問題）

所有修復動作：
- 寫入 event_log
- 回傳成功/失敗結果
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class RepairOrchestrator:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.repair_count = 0

    def execute(self, repair_type: str, params: dict = None) -> dict:
        """執行修復，回傳結果"""
        self.repair_count += 1
        params = params or {}

        method = {
            "heartbeat": self._repair_heartbeat,
            "memory": self._repair_memory_file,
            "directory": self._repair_directory,
            "restart_service": self._restart_service,
            "emergency_stop": self._emergency_stop,
        }.get(repair_type)

        if not method:
            return {"success": False, "error": f"未知修復類型: {repair_type}"}

        try:
            result = method(params)
            self._log(repair_type, result)
            return result
        except Exception as e:
            result = {"success": False, "error": str(e)}
            self._log(repair_type, result)
            return result

    def _repair_heartbeat(self, params: dict) -> dict:
        """重建心跳檔案"""
        state_dir = Path(params.get("state_dir", self.base_dir / "data" / "state"))
        state_dir.mkdir(parents=True, exist_ok=True)
        heartbeat_file = state_dir / "heartbeat.json"
        heartbeat_file.write_text(json.dumps({
            "time": datetime.now().isoformat(),
            "status": "alive",
            "pid": os.getpid(),
            "repaired": True
        }, ensure_ascii=False, indent=2))
        return {"success": True, "action": "重建心跳檔案"}

    def _repair_memory_file(self, params: dict) -> dict:
        """重建記憶檔案"""
        memory_file = Path(params.get("memory_file", self.base_dir / "memory" / "semantic.json"))
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        memory_file.write_text(json.dumps([], ensure_ascii=False, indent=2))
        return {"success": True, "action": "重建記憶檔案"}

    def _repair_directory(self, params: dict) -> dict:
        """建立缺失目錄"""
        directories = params.get("directories", [])
        for d in directories:
            Path(d).mkdir(parents=True, exist_ok=True)
        return {"success": True, "action": f"建立 {len(directories)} 個目錄"}

    def _restart_service(self, params: dict) -> dict:
        """重啟服務"""
        service = params.get("service", "ampm-brain.service")
        try:
            subprocess.run(["sudo", "systemctl", "restart", service],
                           capture_output=True, timeout=30)
            return {"success": True, "action": f"重啟服務 {service}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _emergency_stop(self, params: dict) -> dict:
        """緊急停止 — 寫入停止標誌"""
        state_dir = Path(params.get("state_dir", self.base_dir / "data" / "state"))
        state_dir.mkdir(parents=True, exist_ok=True)
        stop_file = state_dir / "emergency_stop.flag"
        stop_file.write_text(datetime.now().isoformat())
        return {"success": True, "action": "緊急停止標誌已寫入"}

    def _log(self, repair_type: str, result: dict):
        """記錄到 event_log"""
        try:
            from governance.event_log import EventLog
            EventLog().record(
                source="repair_orchestrator",
                action=f"repair:{repair_type}",
                input={"type": repair_type},
                output=result,
            )
        except Exception:
            pass
