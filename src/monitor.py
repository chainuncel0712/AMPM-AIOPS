#!/usr/bin/env python3
"""
監視 + 修復系統 - 主動學習版
會自己學習什麼是異常、什麼時候該修、怎麼修更好
"""

import time
import threading
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class Monitor:
    def __init__(self, base_dir, alert_callback=None, call_ai_func=None):
        self.base_dir = Path(base_dir)
        self.alert_callback = alert_callback
        self.call_ai_func = call_ai_func  # 讓監視系統可以思考
        self.running = True
        
        # 狀態
        self.obsidian_status = {"alive": False, "last_heartbeat": None, "pid": None}
        self.resources = {"cpu": 0, "memory": 0, "disk": 0}
        self.alerts = []
        self.repair_log = []
        
        # 學習數據
        self.anomaly_patterns = self._load_patterns()  # 學習到的異常模式
        self.repair_history = self._load_repair_history()  # 修復歷史
        
        # 確保目錄存在
        self.state_dir = self.base_dir / "data" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # 修復計數器
        self.repair_count = 0
        self.last_repair_time = 0
        
        # 初始化心跳
        self._create_heartbeat()
    
    def _load_patterns(self) -> Dict:
        patterns_file = self.base_dir / "monitor" / "patterns.json"
        if patterns_file.exists():
            return json.loads(patterns_file.read_text())
        return {"known_anomalies": [], "repair_success_rate": {}}
    
    def _save_patterns(self):
        patterns_file = self.base_dir / "monitor" / "patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        patterns_file.write_text(json.dumps(self.anomaly_patterns, ensure_ascii=False, indent=2))
    
    def _load_repair_history(self) -> List:
        history_file = self.base_dir / "monitor" / "repair_history.json"
        if history_file.exists():
            return json.loads(history_file.read_text())
        return []
    
    def _save_repair_history(self):
        history_file = self.base_dir / "monitor" / "repair_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps(self.repair_history[-100:], ensure_ascii=False, indent=2))
    
    def start(self):
        print("👁️ 監視+修復系統已啟動（主動學習版）")
        threading.Thread(target=self._watch_and_learn, daemon=True).start()
        threading.Thread(target=self._watch_resources, daemon=True).start()
    
    def _watch_and_learn(self):
        """監視主循環 - 發現問題就修復，並從中學習"""
        while self.running:
            try:
                issues = []
                
                # 檢查各個系統
                heartbeat_issue = self._check_heartbeat()
                if heartbeat_issue:
                    issues.append(heartbeat_issue)
                
                memory_issue = self._check_memory()
                if memory_issue:
                    issues.append(memory_issue)
                
                tools_issue = self._check_tools()
                if tools_issue:
                    issues.append(tools_issue)
                
                dir_issue = self._check_directories()
                if dir_issue:
                    issues.append(dir_issue)
                
                # 如果有問題，執行修復（並學習）
                if issues:
                    self._execute_repair_with_learning(issues)
                
            except Exception as e:
                print(f"監視錯誤: {e}")
            
            time.sleep(10)
    
    def _check_heartbeat(self) -> Optional[Dict]:
        """檢查心跳，返回問題描述"""
        heartbeat_file = self.state_dir / "heartbeat.json"
        
        if not heartbeat_file.exists():
            return {"type": "heartbeat", "severity": "high", "description": "心跳檔案不存在"}
        
        try:
            content = heartbeat_file.read_text().strip()
            if not content:
                return {"type": "heartbeat", "severity": "medium", "description": "心跳檔案為空"}
            
            data = json.loads(content)
            last_time = datetime.fromisoformat(data["time"])
            now = datetime.now()
            seconds_ago = (now - last_time).seconds
            
            if seconds_ago > 60:
                return {"type": "heartbeat", "severity": "high", 
                       "description": f"心跳停止 {seconds_ago} 秒", "seconds": seconds_ago}
            else:
                self.obsidian_status["alive"] = True
                self.obsidian_status["last_heartbeat"] = data["time"]
                self.obsidian_status["pid"] = data.get("pid")
                
        except (json.JSONDecodeError, ValueError):
            return {"type": "heartbeat", "severity": "high", "description": "心跳檔案損毀"}
        
        return None
    
    def _check_memory(self) -> Optional[Dict]:
        """檢查記憶系統"""
        memory_file = self.base_dir / "memory" / "semantic.json"
        
        if not memory_file.exists():
            return {"type": "memory", "severity": "low", "description": "記憶檔案不存在"}
        
        try:
            if memory_file.stat().st_size > 10 * 1024 * 1024:  # 超過 10MB
                return {"type": "memory", "severity": "medium", "description": "記憶檔案過大"}
        except:
            pass
        
        return None
    
    def _check_tools(self) -> Optional[Dict]:
        """檢查工具系統"""
        tools_file = self.base_dir / "tools" / "registry" / "tools.json"
        
        if not tools_file.exists():
            return {"type": "tools", "severity": "medium", "description": "工具註冊檔不存在"}
        
        return None
    
    def _check_directories(self) -> Optional[Dict]:
        """檢查目錄結構"""
        required_dirs = [
            self.base_dir / "memory",
            self.base_dir / "tools" / "registry",
            self.base_dir / "agents",
            self.base_dir / "data" / "state",
            self.base_dir / "logs",
        ]
        
        missing = []
        for d in required_dirs:
            if not d.exists():
                missing.append(str(d))
        
        if missing:
            return {"type": "directory", "severity": "low", "description": f"缺少目錄: {missing}"}
        
        return None
    
    def _execute_repair_with_learning(self, issues: List[Dict]):
        """執行修復，並從中學習"""
        now = time.time()
        
        # 避免頻繁修復（2分鐘內只修一次）
        if now - self.last_repair_time < 120:
            return
        
        self.last_repair_time = now
        self.repair_count += 1
        
        print(f"🔧 執行修復 #{self.repair_count}（問題：{len(issues)} 個）")
        
        # 記錄這次修復
        repair_record = {
            "time": datetime.now().isoformat(),
            "repair_count": self.repair_count,
            "issues": issues,
            "actions": [],
            "success": True
        }
        
        # 對每個問題執行修復
        for issue in issues:
            action = self._repair_issue(issue)
            repair_record["actions"].append(action)
        
        # 學習：分析這次修復的效果
        if self.call_ai_func:
            self._learn_from_repair(repair_record)
        
        # 儲存修復歷史
        self.repair_history.append(repair_record)
        self._save_repair_history()
        
        # 發送警報
        self._log_alert("INFO", f"修復完成", f"已處理 {len(issues)} 個問題")
    
    def _repair_issue(self, issue: Dict) -> Dict:
        """修復單一問題"""
        action = {"type": issue["type"], "performed": [], "success": False}
        
        if issue["type"] == "heartbeat":
            self._create_heartbeat()
            action["performed"].append("重建心跳")
            action["success"] = True
            
            # 如果心跳停止太久，嘗試重啟
            seconds = issue.get("seconds", 0)
            if seconds > 120 and not self._is_obsidian_running():
                self._restart_obsidian()
                action["performed"].append("重新啟動黑曜")
        
        elif issue["type"] == "memory":
            # 創建空的記憶檔案
            memory_file = self.base_dir / "memory" / "semantic.json"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            memory_file.write_text(json.dumps([], ensure_ascii=False, indent=2))
            action["performed"].append("重建記憶檔案")
            action["success"] = True
        
        elif issue["type"] == "tools":
            # 重新註冊工具
            action["performed"].append("需要手動重新註冊工具")
            action["success"] = False
        
        elif issue["type"] == "directory":
            for d in issue.get("description", "").split(":"):
                Path(d.strip()).mkdir(parents=True, exist_ok=True)
            action["performed"].append("建立缺失目錄")
            action["success"] = True
        
        return action
    
    def _learn_from_repair(self, repair_record: Dict):
        """從修復中學習（成長核心）"""
        prompt = f"""我是監視系統，剛剛執行了一次修復。

修復記錄：
{json.dumps(repair_record, ensure_ascii=False, indent=2)[:1000]}

請分析：
1. 這次修復有效嗎？
2. 下次遇到類似問題，應該改進什麼？
3. 有沒有更好的修復方式？

輸出 JSON：
{{
    "effective": true/false,
    "improvement": "改進建議",
    "new_pattern": "新發現的異常模式（如果有）"
}}
"""
        try:
            result = self.call_ai_func(prompt)
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                learning = json.loads(json_match.group())
                
                # 記錄學習到的模式
                if learning.get("new_pattern"):
                    self.anomaly_patterns["known_anomalies"].append({
                        "pattern": learning["new_pattern"],
                        "learned_at": datetime.now().isoformat()
                    })
                    self._save_patterns()
                
                print(f"📚 監視系統學習: {learning.get('improvement', '')[:50]}")
        except:
            pass
    
    def _create_heartbeat(self):
        """建立心跳檔案"""
        heartbeat_file = self.state_dir / "heartbeat.json"
        heartbeat_file.write_text(json.dumps({
            "time": datetime.now().isoformat(),
            "status": "alive",
            "pid": os.getpid(),
            "repaired": True
        }, ensure_ascii=False, indent=2))
    
    def _is_obsidian_running(self) -> bool:
        """檢查黑曜是否在執行"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "brain.py"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return True
    
    def _restart_obsidian(self):
        """重新啟動黑曜"""
        try:
            subprocess.run(["pkill", "-f", "brain.py"], capture_output=True)
            time.sleep(0.5)
            
            script_path = self.base_dir.parent / "ampm_brain" / "brain.py"
            if script_path.exists():
                subprocess.Popen(
                    ["python3", str(script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("🔄 已重新啟動黑曜")
        except Exception as e:
            print(f"重啟失敗: {e}")
    
    def _watch_resources(self):
        """監視系統資源"""
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
                    
                    # 資源異常檢查
                    if self.resources["cpu"] > 90:
                        self._log_alert("WARNING", f"CPU 過高: {self.resources['cpu']}%", "檢查是否有異常行程")
                    
                    if self.resources["memory"] > 90:
                        self._log_alert("WARNING", f"記憶體過高: {self.resources['memory']}%", "建議重啟")
                        
                except ImportError:
                    pass
            except:
                pass
            time.sleep(15)
    
    def _log_alert(self, level, title, message):
        """記錄警報"""
        alert = {
            "time": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "message": message,
            "repaired": True
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
        """取得完整狀態"""
        return {
            "obsidian": self.obsidian_status,
            "resources": self.resources,
            "alerts": self.alerts[-10:],
            "repair_log": self.repair_log[-5:],
            "repair_count": self.repair_count,
            "learned_patterns": len(self.anomaly_patterns.get("known_anomalies", []))
        }
    
    def emergency_stop(self):
        """緊急停止"""
        self._log_alert("CRITICAL", "緊急停止", "系統將暫停所有代理")
        stop_file = self.state_dir / "emergency_stop.flag"
        stop_file.write_text(datetime.now().isoformat())
        return "🛑 已執行緊急停止"
    
    def manual_repair(self):
        """手動觸發修復"""
        self._execute_repair_with_learning([{"type": "manual", "severity": "low", "description": "手動觸發"}])
        return "🔧 手動修復已執行"
    
    def get_learning_summary(self) -> str:
        """學習摘要"""
        return f"""📚 監視系統學習摘要
━━━━━━━━━━━━━━━━
修復次數: {self.repair_count}
學習到的異常模式: {len(self.anomaly_patterns.get('known_anomalies', []))}
最近修復: {len(self.repair_history[-5:])} 次
儲存的修復歷史: {len(self.repair_history)} 筆"""


if __name__ == "__main__":
    print("監視+修復系統模組（主動學習版）已載入")
