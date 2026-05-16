"""
Civilization Memory — 文明級六層記憶系統
=========================================
Episodic: 事件記憶（時間線上的經歷）
Semantic: 知識記憶（事實與概念）
Procedural: 技能記憶（如何做某事的步驟）
Emotional: 情緒權重記憶（哪些事危險/有價值）
Evolution: 進化歷史記憶（我如何變成現在這樣）
Failure: 失敗記憶（創傷防護，避免重蹈覆轍）

與原有 memory.py 互補：memory.py 負責短期/工作記憶，
civilization_memory 負責長期結構化記憶。
"""
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class EpisodicMemory:
    """事件記憶 — 時間線上的完整經歷片段"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_dir = self.base_dir / "data" / "civilization_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.episodes: List[Dict] = []
        self.index: Dict[str, List[int]] = defaultdict(list)
        self._load()

    def _load(self):
        f = self.data_dir / "episodic.json"
        if f.exists():
            try:
                data = json.loads(f.read_text())
                self.episodes = data.get("episodes", [])
                raw_idx = data.get("index", {})
                self.index = defaultdict(list, {k: v for k, v in raw_idx.items()})
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            (self.data_dir / "episodic.json").write_text(json.dumps({
                "episodes": self.episodes[-5000:],
                "index": {k: v[-500:] for k, v in self.index.items()},
            }, ensure_ascii=False, indent=2))

    def record(self, event_type: str, summary: str, importance: float = 0.5,
               tags: List[str] = None, context: Dict = None):
        episode = {
            "type": event_type,
            "summary": summary[:500],
            "importance": importance,
            "tags": tags or [],
            "context": {k: str(v)[:200] for k, v in (context or {}).items()},
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            idx = len(self.episodes)
            self.episodes.append(episode)
            for tag in (tags or []) + [event_type]:
                self.index[tag].append(idx)
                if len(self.index[tag]) > 500:
                    self.index[tag] = self.index[tag][-500:]
        self._save()

    def recall_by_tags(self, tags: List[str], limit: int = 20) -> List[Dict]:
        candidates = set()
        for tag in tags:
            candidates.update(self.index.get(tag, []))
        results = [
            self.episodes[i] for i in sorted(candidates, reverse=True)
            if i < len(self.episodes)
        ]
        results.sort(key=lambda e: self._score(e, tags), reverse=True)
        return results[:limit]

    def _score(self, episode: Dict, query_tags: List[str]) -> float:
        score = episode.get("importance", 0.5) * 2
        tag_overlap = len(set(episode.get("tags", [])) & set(query_tags))
        score += tag_overlap * 0.3
        try:
            age_h = (datetime.now() - datetime.fromisoformat(episode["timestamp"])).total_seconds() / 3600
            score *= max(0.1, 1.0 - age_h / (24 * 30))
        except Exception:
            pass
        return score

    def recall_by_time(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            e for e in self.episodes
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.episodes) // 500 + 5

    def status(self) -> dict:
        return {"name": "EpisodicMemory", "episodes": len(self.episodes), "index_keys": len(self.index)}


class FailureMemory:
    """失敗記憶 — 創傷防護，追蹤嚴重錯誤，防止重蹈覆轍"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_dir = self.base_dir / "data" / "civilization_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.failures: List[Dict] = []
        self.patterns: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        f = self.data_dir / "failures.json"
        if f.exists():
            try:
                data = json.loads(f.read_text())
                self.failures = data.get("failures", [])
                self.patterns = data.get("patterns", {})
            except Exception:
                pass

    def _save(self):
        with self._lock:
            (self.data_dir / "failures.json").write_text(json.dumps({
                "failures": self.failures[-2000:],
                "patterns": self.patterns,
            }, ensure_ascii=False, indent=2))

    def record(self, action: str, error: str, severity: float = 0.5,
               context: Dict = None):
        failure = {
            "action": action[:300],
            "error": error[:500],
            "severity": severity,
            "context": {k: str(v)[:100] for k, v in (context or {}).items()},
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            self.failures.append(failure)

            pattern = action.split(".")[0][:50]
            if pattern not in self.patterns:
                self.patterns[pattern] = {"count": 0, "total_severity": 0, "last_error": ""}
            self.patterns[pattern]["count"] += 1
            self.patterns[pattern]["total_severity"] += severity
            self.patterns[pattern]["last_error"] = error[:200]

        self._save()

    def is_risky(self, action: str) -> Dict[str, Any]:
        pattern = action.split(".")[0][:50]
        p = self.patterns.get(pattern, {})
        count = p.get("count", 0)
        return {
            "risky": count >= 3,
            "failures": count,
            "avg_severity": round(p.get("total_severity", 0) / max(1, count), 2),
            "last_error": p.get("last_error", ""),
        }

    def top_patterns(self, n: int = 10) -> List[Dict]:
        ranked = sorted(self.patterns.items(), key=lambda x: -x[1]["count"])
        return [
            {"pattern": k, "count": v["count"],
             "avg_severity": round(v["total_severity"] / max(1, v["count"]), 2)}
            for k, v in ranked[:n]
        ]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.failures) // 500 + 2

    def status(self) -> dict:
        return {"name": "FailureMemory", "failures": len(self.failures), "patterns": len(self.patterns)}


class EvolutionMemory:
    """進化記憶 — 追蹤 AI 如何演變到現在的版本"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_dir = self.base_dir / "data" / "civilization_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.evolution_log: List[Dict] = []
        self.version = 1
        self._load()

    def _load(self):
        f = self.data_dir / "evolution.json"
        if f.exists():
            try:
                data = json.loads(f.read_text())
                self.evolution_log = data.get("log", [])
                self.version = data.get("version", 1)
            except Exception:
                pass

    def _save(self):
        with self._lock:
            (self.data_dir / "evolution.json").write_text(json.dumps({
                "version": self.version,
                "log": self.evolution_log[-1000:],
            }, ensure_ascii=False, indent=2))

    def record_change(self, change_type: str, description: str,
                      agent_id: str = "", reasoning: str = ""):
        self.version += 1
        self.evolution_log.append({
            "version": self.version,
            "change_type": change_type,
            "description": description[:500],
            "agent_id": agent_id,
            "reasoning": reasoning[:300],
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self.evolution_log[-limit:]

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.evolution_log) // 500 + 1

    def status(self) -> dict:
        return {"name": "EvolutionMemory", "version": self.version, "changes": len(self.evolution_log)}
