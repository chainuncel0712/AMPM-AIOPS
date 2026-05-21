"""
監視系統 — 只偵測、不通告、不修復
====================================
Monitor 只負責監視（有沒有問題）
Immune 只負責決策（要不要修、修哪裡）
RepairOrchestrator 只負責執行（怎麼修）
"""

import time
import threading
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class Monitor:
    def __init__(self, base_dir, alert_callback=None, call_ai_func=None,
                 repair_orchestrator=None):
        self.base_dir = Path(base_dir)
        self.alert_callback = alert_callback
        self.call_ai_func = call_ai_func
        self.repair_orchestrator = repair_orchestrator
        self.running = True

        self.obsidian_status = {"alive": False, "last_heartbeat": None, "pid": None}
        self.resources = {"cpu": 0, "memory": 0, "disk": 0}
        self.alerts = []
        self.repair_log = []
        self.state_dir = self.base_dir / "data" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.repair_count = 0
        self.last_repair_time = 0

    def start(self):
        print("🔍 監視系統已啟動（偵測模式）")
        threading.Thread(target=self._watch_and_learn, daemon=True).start()
        threading.Thread(target=self._watch_resources, daemon=True).start()

    def _watch_and_learn(self):
        """監視主循環 — 發現問題就發出修復請求"""
        while self.running:
            try:
                issues = []
                for check in [self._check_heartbeat, self._check_memory,
                              self._check_tools, self._check_directories]:
                    issue = check()
                    if issue:
                        issues.append(issue)

                if issues:
                    self._dispatch_repair(issues)

            except Exception as e:
                print(f"監視錯誤: {e}")

            time.sleep(10)

    def _check_heartbeat(self) -> Optional[Dict]:
        heartbeat_file = self.state_dir / "heartbeat.json"
        if not heartbeat_file.exists():
            return {"type": "heartbeat", "severity": "high", "description": "心跳檔案不存在"}
        try:
            content = heartbeat_file.read_text().strip()
            if not content:
                return {"type": "heartbeat", "severity": "medium", "description": "心跳檔案為空"}
            data = json.loads(content)
            last_time = datetime.fromisoformat(data["time"])
            seconds_ago = (datetime.now() - last_time).seconds
            if seconds_ago > 60:
                return {"type": "heartbeat", "severity": "high",
                        "description": f"心跳停止 {seconds_ago} 秒", "seconds": seconds_ago}
            self.obsidian_status["alive"] = True
            self.obsidian_status["last_heartbeat"] = data["time"]
            self.obsidian_status["pid"] = data.get("pid")
        except (json.JSONDecodeError, ValueError):
            return {"type": "heartbeat", "severity": "high", "description": "心跳檔案損毀"}
        return None

    def _check_memory(self) -> Optional[Dict]:
        memory_file = self.base_dir / "memory" / "semantic.json"
        if not memory_file.exists():
            return {"type": "memory", "severity": "low", "description": "記憶檔案不存在"}
        try:
            if memory_file.stat().st_size > 10 * 1024 * 1024:
                return {"type": "memory", "severity": "medium", "description": "記憶檔案過大"}
        except:
            pass
        return None

    def _check_tools(self) -> Optional[Dict]:
        tools_file = self.base_dir / "tools" / "registry" / "tools.json"
        if not tools_file.exists():
            return {"type": "tools", "severity": "medium", "description": "工具註冊檔不存在"}
        return None

    def _check_directories(self) -> Optional[Dict]:
        required_dirs = [
            self.base_dir / "memory",
            self.base_dir / "tools" / "registry",
            self.base_dir / "agents",
            self.base_dir / "data" / "state",
            self.base_dir / "logs",
        ]
        missing = [str(d) for d in required_dirs if not d.exists()]
        if missing:
            return {"type": "directory", "severity": "low",
                    "description": f"缺少目錄: {missing}"}
        return None

    def _dispatch_repair(self, issues: List[Dict]):
        """將問題發送給修復執行器處理"""
        now = time.time()
        if now - self.last_repair_time < 120:
            return
        self.last_repair_time = now
        self.repair_count += 1
        self._log_alert("INFO", f"發現 {len(issues)} 個問題",
                        f"修復 #{self.repair_count}")
        if self.repair_orchestrator:
            for issue in issues:
                params = {}
                if issue["type"] == "heartbeat":
                    params["seconds"] = issue.get("seconds", 0)
                elif issue["type"] == "directory":
                    params["directories"] = issue.get("description", "").split(": ")
                self.repair_log.append(
                    self.repair_orchestrator.execute(issue["type"], params)
                )
        else:
            self.repair_log.append({
                "issues": [i["type"] for i in issues],
                "note": "無修復執行器，僅記錄"
            })

    def _watch_resources(self):
        while self.running:
            try:
                try:
                    import psutil
                    self.resources = {
                        "cpu": psutil.cpu_percent(),
                        "memory": psutil.virtual_memory().percent,
                        "disk": psutil.disk_usage(str(self.base_dir)).percent,
                        "time": datetime.now().isoformat()
                    }
                    if self.resources["cpu"] > 90:
                        self._log_alert("WARNING", f"CPU 過高: {self.resources['cpu']}%",
                                        "檢查是否有異常行程")
                    if self.resources["memory"] > 90:
                        self._log_alert("WARNING", f"記憶體過高: {self.resources['memory']}%",
                                        "建議重啟")
                except ImportError:
                    pass
            except:
                pass
            time.sleep(15)

    def _log_alert(self, level, title, message):
        alert = {
            "time": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "message": message,
        }
        self.alerts.append(alert)
        self.alerts = self.alerts[-50:]
        print(f"🔔 [{level}] {title}: {message}")
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except:
                pass

    def get_status(self) -> dict:
        return {
            "obsidian": self.obsidian_status,
            "resources": self.resources,
            "alerts": self.alerts[-10:],
            "repair_log": self.repair_log[-5:],
            "repair_count": self.repair_count,
        }

    def emergency_stop(self):
        if self.repair_orchestrator:
            result = self.repair_orchestrator.execute("emergency_stop")
            self._log_alert("CRITICAL", "緊急停止", "系統將暫停所有代理")
            return f"🛑 已執行緊急停止: {result}"
        self._log_alert("CRITICAL", "緊急停止", "無修復執行器")
        return "🛑 緊急停止 (無修復執行器)"

    def manual_repair(self):
        self._dispatch_repair([{"type": "manual", "severity": "low",
                                "description": "手動觸發"}])
        return "🔧 手動修復已執行"
