"""FutureClock - predicts when events will next occur."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class FutureClock:

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self._asleep = False
        self.schedule: Dict[str, Dict] = {}

    def schedule_event(self, name: str, interval_hours: float,
                       last_occurred: Optional[str] = None) -> str:
        now = datetime.now()
        if last_occurred:
            try:
                last = datetime.fromisoformat(last_occurred)
            except Exception:
                last = now
        else:
            last = now
        next_at = last + timedelta(hours=interval_hours)
        self.schedule[name] = {
            "name": name,
            "interval_hours": interval_hours,
            "last": last.isoformat(),
            "next": next_at.isoformat(),
        }
        return next_at.isoformat()

    def is_due(self, name: str) -> bool:
        event = self.schedule.get(name)
        if not event:
            return False
        try:
            next_at = datetime.fromisoformat(event["next"])
            return datetime.now() >= next_at
        except Exception:
            return False

    def upcoming(self, within_hours: float = 24) -> List[Dict]:
        now = datetime.now()
        cutoff = now + timedelta(hours=within_hours)
        upcoming = []
        for name, event in self.schedule.items():
            try:
                next_at = datetime.fromisoformat(event["next"])
                if now <= next_at <= cutoff:
                    upcoming.append({
                        "name": name,
                        "next": event["next"],
                        "in_hours": round((next_at - now).total_seconds() / 3600, 1),
                    })
            except Exception:
                pass
        upcoming.sort(key=lambda x: x["in_hours"])
        return upcoming

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return 1
    def status(self) -> dict: return {"name": "FutureClock", "events": len(self.schedule)}
