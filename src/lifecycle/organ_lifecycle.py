"""
OrganLifecycle -- organ birth, growth, maturity, retirement, renewal cycle.
Each organ has a lifecycle: embryo -> growing -> mature -> retiring -> asleep -> recycled.
New organs can hot-swap old ones with gradual traffic cutover.

This implements the "Ship of Theseus + Four Seasons" pattern:
every part can be replaced, but the system identity persists.
"""
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class OrganRecord:
    organ_id: str
    name: str
    version: str
    category: str
    status: str            # embryo/growing/mature/retiring/asleep/recycled
    created_at: str
    last_healthy: str
    replacement_of: str = ""
    replaced_by: str = ""
    traffic_pct: float = 100.0
    health_score: float = 1.0
    deprecation_reason: str = ""
    generation: int = 0


class OrganLifecycle:

    STATUS_ORDER = {
        "embryo": 0, "growing": 1, "mature": 2,
        "retiring": 3, "asleep": 4, "recycled": 5,
    }

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.registry_file = self.base_dir / "data" / "lifecycle" / "organs.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.organs: Dict[str, OrganRecord] = {}
        self._gen_counter: int = 0
        self._load()

    def _load(self):
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text())
                self._gen_counter = data.get("generation", 0)
                for r in data.get("organs", []):
                    self.organs[r["organ_id"]] = OrganRecord(**r)
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {
                "generation": self._gen_counter,
                "organs": [
                    {
                        "organ_id": o.organ_id, "name": o.name,
                        "version": o.version, "category": o.category,
                        "status": o.status, "created_at": o.created_at,
                        "last_healthy": o.last_healthy,
                        "replacement_of": o.replacement_of,
                        "replaced_by": o.replaced_by,
                        "traffic_pct": o.traffic_pct,
                        "health_score": o.health_score,
                        "deprecation_reason": o.deprecation_reason,
                        "generation": o.generation,
                    }
                    for o in self.organs.values()
                ],
            }
            self.registry_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _gen_id(self, name: str) -> str:
        self._gen_counter += 1
        ts = datetime.now().strftime("%Y%m%d%H%M")
        return f"{name}-{ts}-{self._gen_counter:04d}"

    def birth(self, name: str, category: str, version: str = "1.0.0",
              replaces: str = "") -> str:
        """Create a new organ in embryo state. If replacing, mark old organ retiring."""
        organ_id = self._gen_id(name)
        now = datetime.now().isoformat()
        generation = self._gen_counter

        with self._lock:
            record = OrganRecord(
                organ_id=organ_id, name=name, version=version,
                category=category, status="embryo",
                created_at=now, last_healthy=now,
                replacement_of=replaces, traffic_pct=0.0,
                generation=generation,
            )
            self.organs[organ_id] = record

            if replaces:
                for oid, o in self.organs.items():
                    if o.name == replaces and o.status in ("mature", "growing", "embryo"):
                        o.status = "retiring"
                        o.replaced_by = organ_id
                        o.deprecation_reason = f"replaced by {name} v{version}"

            self._save()
        return organ_id

    def promote(self, organ_id: str) -> bool:
        """embryo -> growing -> mature. Returns True if promoted."""
        with self._lock:
            o = self.organs.get(organ_id)
            if not o:
                return False
            if o.status == "embryo":
                o.status = "growing"
                o.traffic_pct = 10.0
            elif o.status == "growing":
                o.status = "mature"
                o.traffic_pct = 100.0
            else:
                return False
            o.last_healthy = datetime.now().isoformat()
            self._save()
            return True

    def report_health(self, organ_id: str, health: float):
        """Report organ health (0.0-1.0). Auto-retire if consistently < 0.3."""
        with self._lock:
            o = self.organs.get(organ_id)
            if not o:
                return
            o.health_score = max(0.0, min(1.0, health))
            o.last_healthy = datetime.now().isoformat()
            if o.health_score < 0.3 and o.status == "mature":
                o.status = "retiring"
                o.deprecation_reason = f"low health: {o.health_score:.2f}"
            self._save()

    def gradual_cutover(self, new_id: str, old_id: str, step_pct: float = 20.0):
        """Gradually shift traffic from old to new organ."""
        with self._lock:
            new_o = self.organs.get(new_id)
            old_o = self.organs.get(old_id)
            if not new_o or not old_o:
                return
            new_pct = min(100.0, new_o.traffic_pct + step_pct)
            old_pct = max(0.0, 100.0 - new_pct)
            new_o.traffic_pct = new_pct
            old_o.traffic_pct = old_pct
            if new_pct >= 100.0:
                if new_o.status == "growing":
                    self.promote(new_id)
                old_o.status = "asleep"
            self._save()

    def retire(self, organ_id: str, reason: str = ""):
        """Manually retire an organ."""
        with self._lock:
            o = self.organs.get(organ_id)
            if not o:
                return
            o.status = "retiring"
            o.deprecation_reason = reason or "manual retirement"
            self._save()

    def recycle(self, organ_id: str):
        """Recycle a retired/asleep organ - free resources."""
        with self._lock:
            o = self.organs.get(organ_id)
            if not o:
                return
            o.status = "recycled"
            o.traffic_pct = 0.0
            self._save()

    def get_active(self, name: str) -> Optional[OrganRecord]:
        """Get the currently active (mature or growing) instance of an organ by name."""
        best = None
        best_status = 99
        for o in self.organs.values():
            if o.name == name and o.status in ("mature", "growing"):
                s = self.STATUS_ORDER.get(o.status, 99)
                if s < best_status:
                    best = o
                    best_status = s
        return best

    def get_lineage(self, name: str) -> List[Dict[str, Any]]:
        """Get the full replacement lineage of an organ."""
        lineage = []
        for o in sorted(self.organs.values(), key=lambda x: x.created_at):
            if o.name == name:
                lineage.append({
                    "organ_id": o.organ_id, "version": o.version,
                    "status": o.status, "generation": o.generation,
                    "replaced_by": o.replaced_by,
                    "created_at": o.created_at[:10],
                })
        return lineage

    def cycle_report(self) -> str:
        """Generate a renewal cycle report."""
        with self._lock:
            by_category: Dict[str, List[OrganRecord]] = {}
            for o in self.organs.values():
                by_category.setdefault(o.category, []).append(o)

            lines = ["Renewal Cycle Report"]
            for cat, organs in sorted(by_category.items()):
                active = [o for o in organs if o.status in ("mature", "growing")]
                replacing = [o for o in organs if o.status == "retiring"]
                embryos = [o for o in organs if o.status == "embryo"]
                recycled = len([o for o in organs if o.status == "recycled"])
                lines.append(
                    f"  {cat}: {len(active)} active, {len(embryos)} embryo, "
                    f"{len(replacing)} retiring, {recycled} recycled"
                )
            lines.append(
                f"  All organs: {len(self.organs)}, generations: {self._gen_counter}"
            )
            return "\n".join(lines)

    def auto_maintain(self):
        """Auto maintenance: recycle organs asleep > 7 days, check for stale versions."""
        now = datetime.now()
        with self._lock:
            for oid, o in list(self.organs.items()):
                if o.status == "asleep":
                    try:
                        last = datetime.fromisoformat(o.last_healthy)
                        if (now - last).days > 7:
                            o.status = "recycled"
                            o.traffic_pct = 0.0
                    except Exception:
                        pass
            self._save()

    def sleep(self): pass
    def wake(self): pass
    def is_asleep(self) -> bool: return False
    def memory_estimate_mb(self) -> int: return 2

    def status(self) -> dict:
        active_count = sum(
            1 for o in self.organs.values() if o.status in ("mature", "growing", "embryo"))
        return {
            "name": "OrganLifecycle",
            "total_organs": len(self.organs),
            "active": active_count,
            "generations": self._gen_counter,
            "categories": len(set(o.category for o in self.organs.values())),
        }
