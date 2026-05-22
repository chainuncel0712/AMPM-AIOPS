"""
ROIAnalyzer — 事後投資回報分析
----------------------------
每次行動後自動評估：花掉的成本值不值得？
用於判斷哪些 agent/tool/model 該保留、該降級、該砍掉。
"""
import json
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ROIEntry:
    action: str
    category: str
    cost_usd: float
    value_score: float       # 0.0 ~ 1.0 (人工 or 自動評估)
    success: bool
    outcome: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ROIAnalyzer:

    WEIGHT_SUCCESS = 0.4
    WEIGHT_VALUE = 0.3
    WEIGHT_EFFICIENCY = 0.2
    WEIGHT_CONSISTENCY = 0.1

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.history_file = self.base_dir / "data" / "economy" / "roi_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.entries: List[ROIEntry] = []
        self._load()

    def _load(self):
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text())
                self.entries = [
                    ROIEntry(**e) for e in data.get("entries", [])[-10000:]
                ]
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {
                "entries": [
                    {
                        "action": e.action, "category": e.category,
                        "cost_usd": e.cost_usd, "value_score": e.value_score,
                        "success": e.success, "outcome": e.outcome,
                        "timestamp": e.timestamp,
                    }
                    for e in self.entries[-10000:]
                ],
            }
            self.history_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ── 記錄 ──

    def record(self, action: str, category: str, cost_usd: float,
               success: bool, outcome: str = "", value_score: float = 0.5):
        entry = ROIEntry(
            action=action, category=category,
            cost_usd=cost_usd, value_score=value_score,
            success=success, outcome=outcome,
        )
        with self._lock:
            self.entries.append(entry)
        self._save()
        return entry

    # ── 分析 ──

    def _filter(self, category: str = None, action: str = None,
                days: int = 30) -> List[ROIEntry]:
        cutoff = datetime.now() - timedelta(days=days)
        result = []
        for e in self.entries:
            try:
                ts = datetime.fromisoformat(e.timestamp)
            except Exception:
                continue
            if ts < cutoff:
                continue
            if category and e.category != category:
                continue
            if action and e.action != action:
                continue
            result.append(e)
        return result

    def get_roi_score(self, category: str, days: int = 30) -> Dict[str, Any]:
        entries = self._filter(category=category, days=days)
        if not entries:
            return {"roi_score": 0, "reason": "no_data", "sample_size": 0}

        total_cost = sum(e.cost_usd for e in entries)
        success_rate = sum(1 for e in entries if e.success) / len(entries)
        avg_value = sum(e.value_score for e in entries) / len(entries)
        avg_cost = total_cost / len(entries)

        consistency = 0.0
        if len(entries) >= 3:
            successes = [1 if e.success else 0 for e in entries]
            runs = 0
            for i in range(1, len(successes)):
                if successes[i] == successes[i - 1]:
                    runs += 1
            consistency = runs / max(1, len(successes) - 1)

        roi = (
            self.WEIGHT_SUCCESS * success_rate +
            self.WEIGHT_VALUE * avg_value +
            self.WEIGHT_EFFICIENCY * (1 - min(avg_cost / 0.01, 1)) +
            self.WEIGHT_CONSISTENCY * consistency
        )

        return {
            "roi_score": round(roi, 4),
            "success_rate": round(success_rate, 4),
            "avg_value": round(avg_value, 4),
            "avg_cost": round(avg_cost, 6),
            "total_cost": round(total_cost, 6),
            "sample_size": len(entries),
            "consistency": round(consistency, 4),
        }

    def rank_actions(self, category: str = None, days: int = 30,
                     top_n: int = 10) -> List[Dict[str, Any]]:
        action_groups: Dict[str, List[ROIEntry]] = defaultdict(list)
        for e in self._filter(category=category, days=days):
            action_groups[e.action].append(e)

        ranked = []
        for action, entries in action_groups.items():
            total_cost = sum(e.cost_usd for e in entries)
            success_rate = sum(1 for e in entries if e.success) / len(entries)
            avg_value = sum(e.value_score for e in entries) / len(entries)
            roi = success_rate * 0.5 + avg_value * 0.3 + (1 - min(total_cost / 0.1, 1)) * 0.2
            ranked.append({
                "action": action,
                "roi": round(roi, 4),
                "calls": len(entries),
                "total_cost": round(total_cost, 6),
                "success_rate": round(success_rate, 4),
            })

        ranked.sort(key=lambda x: -x["roi"])
        return ranked[:top_n]

    def get_waste_report(self, days: int = 7) -> str:
        ranked = self.rank_actions(days=days)
        if not ranked:
            return "📊 ROI 報告：尚無足夠數據"

        waste = [r for r in ranked if r["roi"] < 0.3]
        stars = [r for r in ranked if r["roi"] > 0.7]

        lines = [f"📊 ROI 分析 ({days}天)"]
        if waste:
            lines.append(f"🗑 低 ROI 行動 ({len(waste)}):")
            for w in waste[:5]:
                lines.append(f"  ✗ {w['action']}: ROI={w['roi']:.2f}, cost=${w['total_cost']:.4f}")
        if stars:
            lines.append(f"⭐ 高 ROI 行動 ({len(stars)}):")
            for s in stars[:5]:
                lines.append(f"  ✓ {s['action']}: ROI={s['roi']:.2f}")

        return "\n".join(lines) if len(lines) > 1 else "📊 所有行動 ROI 正常"

    def status(self) -> dict:
        return {
            "name": "ROIAnalyzer",
            "total_entries": len(self.entries),
            "recent_summary": self.get_roi_score("llm_call", days=7),
        }
