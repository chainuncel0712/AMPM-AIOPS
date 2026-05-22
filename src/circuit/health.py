"""
健康檢查
"""

import time
from datetime import datetime
from typing import Dict, List

class HealthChecker:
    def __init__(self):
        self.start_time = time.time()
        self.health_log = []
    
    def check_system(self) -> Dict:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        uptime_seconds = time.time() - self.start_time
        
        issues = []
        if cpu_percent > 80:
            issues.append(f"CPU過高 ({cpu_percent:.0f}%)")
        if memory.percent > 80:
            issues.append(f"記憶體過高 ({memory.percent:.0f}%)")
        
        health = {
            "status": "UNHEALTHY" if issues else "HEALTHY",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "uptime_hours": uptime_seconds / 3600,
            "issues": issues,
            "checked_at": datetime.now().isoformat()
        }
        self.health_log.append(health)
        self.health_log = self.health_log[-100:]
        return health
    
    def suggest_recovery(self) -> List[str]:
        if not self.health_log:
            return []
        last = self.health_log[-1]
        suggestions = []
        if "CPU" in str(last.get("issues", [])):
            suggestions.append("減少並行任務")
        if "記憶體" in str(last.get("issues", [])):
            suggestions.append("重啟服務釋放記憶體")
        return suggestions
