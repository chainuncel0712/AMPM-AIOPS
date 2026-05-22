"""
SourceValidator — 資料源可信度驗證器
------------------------------------
每個資訊來源（URL、API、agent output）都有可信度分數。
自動追蹤：哪個來源最準？哪個常給錯誤資訊？
"""
import hashlib
import json
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class SourceValidator:

    VALIDATION_HISTORY_LIMIT = 1000

    def __init__(self, trust_engine: Optional[Any] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "trust" / "sources.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.trust = trust_engine
        self.sources: Dict[str, Dict] = {}
        self.validation_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                self.sources = data.get("sources", {})
                self.validation_log = data.get("log", [])
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {"sources": self.sources, "log": self.validation_log[-2000:]}
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _normalize(self, source: str) -> str:
        try:
            parsed = urlparse(source)
            return parsed.netloc or source.lower().strip()
        except Exception:
            return source.lower().strip()

    def _source_id(self, source: str) -> str:
        return hashlib.md5(self._normalize(source).encode()).hexdigest()[:12]

    def register(self, source: str, source_type: str = "unknown",
                 initial_reliability: float = 0.5):
        sid = self._source_id(source)
        with self._lock:
            if sid not in self.sources:
                self.sources[sid] = {
                    "source": self._normalize(source),
                    "type": source_type,
                    "reliability": initial_reliability,
                    "total_validations": 0,
                    "accurate_count": 0,
                    "inaccurate_count": 0,
                    "last_validated": None,
                    "tags": [],
                }
            if self.trust:
                self.trust.register(sid, "source", initial_reliability)
            self._save()

    def validate(self, source: str, claim: str, is_accurate: bool,
                 actual_value: str = ""):
        sid = self._source_id(source)
        if sid not in self.sources:
            self.register(source, "api" if "api" in source.lower() else "web")

        with self._lock:
            s = self.sources[sid]
            s["total_validations"] += 1
            if is_accurate:
                s["accurate_count"] += 1
            else:
                s["inaccurate_count"] += 1
            s["last_validated"] = datetime.now().isoformat()

            total = s["total_validations"]
            s["reliability"] = round(s["accurate_count"] / total, 4) if total > 0 else 0.5

        if self.trust:
            self.trust.record(sid, is_accurate, weight=1.0)

        self.validation_log.append({
            "source": self._normalize(source),
            "claim": claim[:200],
            "accurate": is_accurate,
            "actual": actual_value[:200],
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.validation_log) > self.VALIDATION_HISTORY_LIMIT:
            self.validation_log = self.validation_log[-self.VALIDATION_HISTORY_LIMIT:]
        self._save()

    def is_reliable(self, source: str, threshold: float = 0.5) -> bool:
        sid = self._source_id(source)
        return self.sources.get(sid, {}).get("reliability", 0.5) >= threshold

    def get_reliability(self, source: str) -> float:
        sid = self._source_id(source)
        return self.sources.get(sid, {}).get("reliability", 0.5)

    def most_reliable(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            ranked = sorted(
                self.sources.items(),
                key=lambda x: (-x[1]["reliability"], -x[1]["total_validations"])
            )
            return [
                {"source": v["source"], "reliability": v["reliability"],
                 "validations": v["total_validations"]}
                for _, v in ranked[:top_n]
            ]

    def least_reliable(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            ranked = sorted(
                self.sources.items(),
                key=lambda x: (x[1]["reliability"], -x[1]["total_validations"])
            )
            return [
                {"source": v["source"], "reliability": v["reliability"],
                 "validations": v["total_validations"]}
                for _, v in ranked[:top_n]
            ]

    def status(self) -> dict:
        return {
            "name": "SourceValidator",
            "total_sources": len(self.sources),
            "avg_reliability": round(
                sum(s["reliability"] for s in self.sources.values()) /
                max(1, len(self.sources)), 4),
            "most_reliable": self.most_reliable(3),
            "least_reliable": self.least_reliable(3),
        }
