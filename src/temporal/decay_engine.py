"""
DecayEngine — 衰減引擎
=======================
所有資訊都有半衰期。舊知識價值遞減。
管理記憶、信任、資源的「過期」機制。

時間衰減公式：value = initial * 0.5^(age / half_life)
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DecayEngine:

    PRESETS = {
        "urgent_alert":   300,       # 5 minutes
        "market_price":   60,        # 1 minute
        "news_headline":  3600,      # 1 hour
        "tool_result":    86400,     # 1 day
        "user_fact":      604800,    # 1 week
        "learned_skill":  2592000,   # 30 days
        "core_knowledge": 7776000,   # 90 days
        "identity":       31536000,  # 1 year
    }

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "temporal" / "decay.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.decay_items: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                self.decay_items = json.loads(self.data_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.data_file.write_text(
                json.dumps(self.decay_items, ensure_ascii=False, indent=2))

    def register(self, item_id: str, item_type: str,
                 initial_value: float = 1.0, custom_half_life: int = None):
        """Register an item with a decay schedule."""
        half_life = custom_half_life or self.PRESETS.get(item_type, 86400)
        with self._lock:
            self.decay_items[item_id] = {
                "id": item_id,
                "type": item_type,
                "initial_value": initial_value,
                "half_life_seconds": half_life,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
            }
            self._save()

    def get_value(self, item_id: str) -> float:
        """Get current decayed value of an item."""
        item = self.decay_items.get(item_id)
        if not item:
            return 0.0

        try:
            created = datetime.fromisoformat(item["created_at"])
            age = (datetime.now() - created).total_seconds()
            half_life = item["half_life_seconds"]
            if half_life <= 0:
                return item["initial_value"]
            value = item["initial_value"] * (0.5 ** (age / half_life))
            return round(max(0.0, value), 6)
        except Exception:
            return item.get("initial_value", 0.0)

    def is_expired(self, item_id: str, threshold: float = 0.1) -> bool:
        return self.get_value(item_id) < threshold

    def touch(self, item_id: str):
        """Refresh last_accessed time."""
        with self._lock:
            if item_id in self.decay_items:
                self.decay_items[item_id]["last_accessed"] = datetime.now().isoformat()
                self._save()

    def cleanup_expired(self, threshold: float = 0.05) -> int:
        """Remove fully decayed items. Returns count removed."""
        expired = [iid for iid in self.decay_items if self.is_expired(iid, threshold)]
        with self._lock:
            for iid in expired:
                del self.decay_items[iid]
            self._save()
        return len(expired)

    def get_half_life(self, item_type: str) -> int:
        return self.PRESETS.get(item_type, 86400)

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.decay_items) // 200 + 2

    def status(self) -> dict:
        return {
            "name": "DecayEngine",
            "items_tracked": len(self.decay_items),
            "expired": sum(1 for i in self.decay_items if self.is_expired(i)),
        }
