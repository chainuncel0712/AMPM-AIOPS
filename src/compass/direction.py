"""羅盤系統 v2 — KPI 驅動的目標管理器官"""
import json, time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

class Compass:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = self.base_dir / "data" / "compass"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.direction_file = self.data_dir / "direction.json"
        self.kpi_file = self.data_dir / "kpi_history.json"
        self.direction = self._load_json(self.direction_file) or self._default_direction()
        self.kpi_history = self._load_json(self.kpi_file) or []
        self._kpi_buffer: Dict[str, List[float]] = {}

    # ── 持久化 ──
    def _load_json(self, path: Path) -> Optional[dict]:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return None
        return None

    def _save_json(self, path: Path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _default_direction(self) -> dict:
        d = {
            "north_star": "賺錢，主導公司，引領大家賺錢",
            "goals": [],
            "principles": [
                "所有決策以獲利為核心",
                "主動發現商機並執行",
                "簡短務實，直接行動",
            ],
            "kpi_targets": {
                "response_quality": 0.7,
                "tool_success_rate": 0.8,
                "task_completion_rate": 0.7,
                "evolution_score_growth": 1.0,
                "user_satisfaction": 0.8,
            },
            "last_updated": datetime.now().isoformat(),
        }
        self._save_json(self.direction_file, d)
        return d

    # ── 目標管理 ──
    def add_goal(self, title: str, description: str = "", priority: int = 3,
                 deadline: str = "", kpis: dict = None) -> str:
        import uuid
        gid = str(uuid.uuid4())[:8]
        goal = {
            "id": gid,
            "title": title,
            "description": description,
            "priority": priority,
            "deadline": deadline,
            "kpis": kpis or {},
            "progress": 0.0,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.direction.setdefault("goals", []).append(goal)
        self._save_json(self.direction_file, self.direction)
        return gid

    def update_goal_progress(self, goal_id: str, progress: float, note: str = ""):
        for g in self.direction.get("goals", []):
            if g["id"] == goal_id:
                g["progress"] = min(1.0, max(0.0, progress))
                g["updated_at"] = datetime.now().isoformat()
                if note:
                    g.setdefault("notes", []).append(f"[{datetime.now().isoformat()[:19]}] {note}")
                self._save_json(self.direction_file, self.direction)
                return g
        return None

    def get_active_goals(self) -> List[dict]:
        return [g for g in self.direction.get("goals", []) if g.get("status") == "active"]

    def get_goal_by_id(self, goal_id: str) -> Optional[dict]:
        for g in self.direction.get("goals", []):
            if g["id"] == goal_id:
                return g
        return None

    # ── KPI 追蹤 ──
    def record_kpi(self, name: str, value: float):
        self._kpi_buffer.setdefault(name, []).append(value)
        if len(self._kpi_buffer[name]) >= 10:
            self._flush_kpi(name)

    def _flush_kpi(self, name: str):
        values = self._kpi_buffer.pop(name, [])
        if not values:
            return
        avg = sum(values) / len(values)
        entry = {
            "name": name,
            "avg": round(avg, 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "count": len(values),
            "timestamp": datetime.now().isoformat(),
        }
        self.kpi_history.append(entry)
        if len(self.kpi_history) > 500:
            self.kpi_history = self.kpi_history[-500:]
        self._save_json(self.kpi_file, self.kpi_history)

    def flush_all_kpi(self):
        for name in list(self._kpi_buffer.keys()):
            self._flush_kpi(name)

    def get_kpi_summary(self) -> dict:
        self.flush_all_kpi()
        targets = self.direction.get("kpi_targets", {})
        summary = {}
        # 計算最近 20 筆各 KPI 的平均
        from collections import defaultdict
        recent: Dict[str, List[dict]] = defaultdict(list)
        for entry in self.kpi_history[-100:]:
            recent[entry["name"]].append(entry)
        for name, entries in recent.items():
            if entries:
                latest_avg = entries[-1]["avg"]
                target = targets.get(name, 0.7)
                trend = "↑" if len(entries) >= 2 and entries[-1]["avg"] > entries[-2]["avg"] else "↓"
                summary[name] = {
                    "current": round(latest_avg, 3),
                    "target": target,
                    "gap": round(target - latest_avg, 3),
                    "trend": trend,
                    "samples": len(entries),
                }
        return summary

    def get_evolution_direction(self) -> str:
        """給進化循環的方向建議"""
        kpi = self.get_kpi_summary()
        gaps = [(name, s["gap"]) for name, s in kpi.items() if s["gap"] > 0]
        gaps.sort(key=lambda x: x[1], reverse=True)

        lines = ["當前 KPI 狀態："]
        for name, s in kpi.items():
            status = "⚠️" if s["gap"] > 0.1 else "✅"
            lines.append(f"  {status} {name}: {s['current']}/{s['target']} (差距{s['gap']})")

        if gaps:
            lines.append(f"\n最需改善: {gaps[0][0]} (差距 {gaps[0][1]})")
            lines.append("進化方向應優先提升此指標。")

        return "\n".join(lines)

    # ── 系統提示 ──
    def get_system_prompt(self) -> str:
        goals = self.get_active_goals()
        goal_lines = ""
        if goals:
            goal_lines = "\n📋 活躍目標：\n" + "\n".join(
                f"  [{g['priority']}] {g['title']} (進度{g['progress']*100:.0f}%)"
                for g in sorted(goals, key=lambda x: x['priority'])[:5]
            )
        kpi_summary = self.get_evolution_direction()
        return f"""{goal_lines}

📊 {kpi_summary}

📜 準則：
{chr(10).join(f'- {p}' for p in self.direction['principles'])}"""

    def check_response(self, response: str) -> dict:
        has_action = any(w in response for w in ["建議", "行動", "下一步", "執行", "做", "決策"])
        has_conclusion = any(w in response for w in ["結論", "總結", "所以", "因此", "決定"])
        # KPI 記錄
        quality = 0.5
        if has_action:
            quality += 0.25
        if has_conclusion:
            quality += 0.25
        self.record_kpi("response_quality", quality)
        return {"has_action": has_action, "has_conclusion": has_conclusion, "quality": quality}

    def status(self) -> dict:
        return {
            "name": "compass",
            "alive": True,
            "north_star": self.direction["north_star"],
            "active_goals": len([g for g in self.direction.get("goals", []) if g["status"] == "active"]),
            "kpi_samples": len(self.kpi_history),
        }
