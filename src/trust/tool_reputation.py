"""
ToolReputation — 工具聲譽系統
-----------------------------
追蹤每個工具的可靠性：
- 成功率、平均延遲、錯誤模式
- 自動降級不可靠工具
- 推薦替代工具
"""
import json
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ToolReputation:

    def __init__(self, trust_engine: Optional[Any] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "trust" / "tool_reputation.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.trust = trust_engine
        self.tools: Dict[str, Dict] = {}
        self.execution_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                self.tools = data.get("tools", {})
                self.execution_log = data.get("log", [])
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {"tools": self.tools, "log": self.execution_log[-5000:]}
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _init_tool(self, name: str, category: str = "general"):
        if name not in self.tools:
            self.tools[name] = {
                "name": name,
                "category": category,
                "total_exec": 0,
                "success": 0,
                "failure": 0,
                "total_latency_ms": 0,
                "last_error": "",
                "reputation": 0.5,
                "last_used": None,
                "error_patterns": defaultdict(int),
                "deprecated": False,
                "alternatives": [],
            }

    def record_execution(self, tool_name: str, success: bool,
                         duration_ms: float, error: str = "",
                         category: str = "general"):
        with self._lock:
            self._init_tool(tool_name, category)

            t = self.tools[tool_name]
            t["total_exec"] += 1
            if success:
                t["success"] += 1
            else:
                t["failure"] += 1
                t["last_error"] = error[:200]
                if error:
                    error_type = error.split(":")[0][:30]
                    t["error_patterns"][error_type] += 1

            t["total_latency_ms"] += duration_ms
            t["last_used"] = datetime.now().isoformat()

            total = t["total_exec"]
            success_rate = t["success"] / total if total > 0 else 0
            avg_latency = t["total_latency_ms"] / total if total > 0 else 0

            latency_penalty = min(0.2, max(0, (avg_latency - 5000) / 50000))
            error_penalty = sum(t["error_patterns"].values()) / max(1, total) * 0.3

            t["reputation"] = round(
                max(0.0, min(1.0, success_rate - latency_penalty - error_penalty)), 4)

        if self.trust:
            self.trust.record(f"tool_{tool_name}", success, tags=["tool_execution"])

        self.execution_log.append({
            "tool": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "error": error[:100],
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_reputation(self, tool_name: str) -> Dict[str, Any]:
        with self._lock:
            if tool_name not in self.tools:
                return {"reputation": 0.5, "reason": "unknown_tool"}
            t = self.tools[tool_name]
            total = t["total_exec"]
            return {
                "name": tool_name,
                "reputation": t["reputation"],
                "success_rate": round(t["success"] / total, 4) if total > 0 else 0,
                "total_exec": total,
                "avg_latency_ms": round(t["total_latency_ms"] / total, 1) if total > 0 else 0,
                "last_error": t["last_error"],
                "category": t["category"],
            }

    def is_usable(self, tool_name: str, min_reputation: float = 0.3) -> bool:
        return self.get_reputation(tool_name)["reputation"] >= min_reputation

    def recommend_alternative(self, tool_name: str) -> Optional[str]:
        target = self.tools.get(tool_name, {})
        category = target.get("category", "general")
        with self._lock:
            candidates = [
                (n, t) for n, t in self.tools.items()
                if n != tool_name and t.get("category") == category
                and not t.get("deprecated")
            ]
            if not candidates:
                return None
            candidates.sort(key=lambda x: -x[1]["reputation"])
            return candidates[0][0]

    def best_tools(self, category: str = None, top_n: int = 10) -> List[Dict]:
        with self._lock:
            filtered = self.tools.items()
            if category:
                filtered = ((k, v) for k, v in filtered if v.get("category") == category)
            ranked = sorted(filtered, key=lambda x: -x[1].get("reputation", 0))
            return [
                {
                    "name": k,
                    "reputation": v["reputation"],
                    "success_rate": round(v["success"] / max(1, v["total_exec"]), 4),
                    "total_exec": v["total_exec"],
                }
                for k, v in ranked[:top_n]
            ]

    def mark_deprecated(self, tool_name: str, reason: str = "",
                        alternatives: List[str] = None):
        with self._lock:
            if tool_name in self.tools:
                self.tools[tool_name]["deprecated"] = True
                self.tools[tool_name]["deprecation_reason"] = reason
                self.tools[tool_name]["alternatives"] = alternatives or []
                self._save()

    def status(self) -> dict:
        with self._lock:
            low = [
                k for k, v in self.tools.items()
                if v["reputation"] < 0.3 and not v.get("deprecated")
            ]
            return {
                "name": "ToolReputation",
                "total_tools": len(self.tools),
                "avg_reputation": round(
                    sum(t["reputation"] for t in self.tools.values()) /
                    max(1, len(self.tools)), 4),
                "low_reputation_tools": low[:10],
                "deprecated_tools": sum(1 for t in self.tools.values() if t.get("deprecated")),
            }
