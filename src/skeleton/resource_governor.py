"""
ResourceGovernor — 資源總督
===========================
管理所有文明層的記憶體預算、自動休眠/喚醒。

層級分類：
- CORE:   永遠活著（skeleton, blood, nerve, brain）
- ESSENTIAL: 預設活著（economy, trust, goals, temporal）
- ON_DEMAND: 需要才載入（simulation, society, dna_system）
- ARCHIVE:  休眠中（civilization_memory 舊資料）

記憶體預算 (預設)：
- CORE:       50 MB
- ESSENTIAL: 100 MB
- ON_DEMAND: 200 MB（單次最多同時 3 個）
- ARCHIVE:    50 MB
- TOTAL:     400 MB

自動休眠策略：
- 超過 5 分鐘未使用 → 休眠
- 記憶體超過預算 → 強製休眠最低優先級的層
"""
import gc
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class LayerInfo:
    name: str
    tier: str          # CORE / ESSENTIAL / ON_DEMAND / ARCHIVE
    priority: int      # 0=highest
    organs: Dict[str, Any] = field(default_factory=dict)
    mem_budget_mb: int = 50
    mem_current_mb: int = 0
    last_active: Optional[datetime] = None
    sleep_after_idle_s: int = 300


class ResourceGovernor:
    """
    資源總督 — 全系統記憶體管家

    使用方式：
        gov = ResourceGovernor(total_budget_mb=400)
        gov.register_layer("economy", tier="ESSENTIAL", organs={"cost_engine": engine})
        gov.wake("economy")  # 手動喚醒
        gov.auto_balance()   # 自動平衡
    """

    TIER_ORDER = {"CORE": 0, "ESSENTIAL": 1, "ON_DEMAND": 2, "ARCHIVE": 3}

    DEFAULT_BUDGETS = {
        "CORE": 80,
        "ESSENTIAL": 120,
        "ON_DEMAND": 150,
        "ARCHIVE": 50,
    }

    def __init__(self, total_budget_mb: int = 400,
                 base_dir: Optional[Path] = None):
        self.total_budget_mb = total_budget_mb
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.config_file = self.base_dir / "data" / "governor" / "resource.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.layers: Dict[str, LayerInfo] = {}
        self.current_usage_mb: int = 0
        self.budget_per_tier: Dict[str, int] = dict(self.DEFAULT_BUDGETS)
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = False

        self._load_config()

    def _load_config(self):
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                self.total_budget_mb = data.get("total_budget_mb", self.total_budget_mb)
                self.budget_per_tier = data.get("budget_per_tier", self.DEFAULT_BUDGETS)
            except Exception:
                pass

    def _save_config(self):
        with self._lock:
            self.config_file.write_text(json.dumps({
                "total_budget_mb": self.total_budget_mb,
                "budget_per_tier": self.budget_per_tier,
                "layers": {
                    name: {"tier": info.tier, "mem_budget_mb": info.mem_budget_mb,
                           "organ_count": len(info.organs)}
                    for name, info in self.layers.items()
                },
            }, ensure_ascii=False, indent=2))

    # ── 註冊 ──

    def register_layer(self, name: str, tier: str = "ESSENTIAL",
                       organs: Dict[str, Any] = None,
                       mem_budget_mb: int = None,
                       sleep_after_idle_s: int = 300):
        with self._lock:
            if name in self.layers:
                self.layers[name].organs.update(organs or {})
                return

            budget = mem_budget_mb or self.budget_per_tier.get(tier, 50)
            self.layers[name] = LayerInfo(
                name=name, tier=tier,
                priority=self.TIER_ORDER.get(tier, 2),
                organs=organs or {},
                mem_budget_mb=budget,
                last_active=datetime.now(),
                sleep_after_idle_s=sleep_after_idle_s,
            )
            self._save_config()

    def register_organ(self, layer_name: str, organ_name: str, organ: Any):
        with self._lock:
            if layer_name not in self.layers:
                self.register_layer(layer_name)
            self.layers[layer_name].organs[organ_name] = organ
            self.layers[layer_name].last_active = datetime.now()

    # ── 休眠/喚醒 ──

    def sleep_layer(self, layer_name: str) -> int:
        """休眠一整層，回傳釋放的 MB 數"""
        with self._lock:
            info = self.layers.get(layer_name)
            if not info or info.tier == "CORE":
                return 0

            freed = 0
            for name, organ in info.organs.items():
                if hasattr(organ, 'sleep'):
                    before = organ.memory_estimate_mb() if hasattr(organ, 'memory_estimate_mb') else 0
                    organ.sleep()
                    after = organ.memory_estimate_mb() if hasattr(organ, 'memory_estimate_mb') else 0
                    freed += max(0, before - after)
                elif hasattr(organ, 'is_asleep') and not organ.is_asleep():
                    if hasattr(organ, 'memory_estimate_mb'):
                        freed += organ.memory_estimate_mb()
                    organ.sleep()

            info.mem_current_mb = max(0, info.mem_current_mb - freed)
            self.current_usage_mb -= freed
            gc.collect()
            return freed

    def wake_layer(self, layer_name: str):
        """喚醒一整層"""
        with self._lock:
            info = self.layers.get(layer_name)
            if not info:
                return
            for name, organ in info.organs.items():
                if hasattr(organ, 'wake'):
                    organ.wake()
            info.last_active = datetime.now()

    def wake_organ(self, layer_name: str, organ_name: str) -> Any:
        """喚醒單一器官（惰性載入）"""
        with self._lock:
            info = self.layers.get(layer_name)
            if not info:
                return None
            organ = info.organs.get(organ_name)
            if organ is None:
                return None
            if hasattr(organ, 'wake'):
                organ.wake()
            info.last_active = datetime.now()
            return organ

    # ── 記憶體估算 ──

    def _estimate_layer_memory(self, info: LayerInfo) -> int:
        total = 0
        for organ in info.organs.values():
            if hasattr(organ, 'memory_estimate_mb'):
                total += organ.memory_estimate_mb()
            elif hasattr(organ, 'is_asleep') and not organ.is_asleep():
                total += 5  # 保守估計
        return total

    def recalc_usage(self):
        with self._lock:
            total = 0
            for info in self.layers.values():
                info.mem_current_mb = self._estimate_layer_memory(info)
                total += info.mem_current_mb
            self.current_usage_mb = total

    # ── 自動平衡 ──

    def auto_balance(self) -> Dict[str, Any]:
        """
        自動平衡記憶體使用量。
        1. 檢查閒置層 → 休眠
        2. 若仍超過總預算 → 強製休眠最低優先級的非 CORE 層
        """
        with self._lock:
            self.recalc_usage()
            now = datetime.now()
            freed_total = 0
            actions = []

            # Step 1: 休眠閒置層
            for name, info in sorted(self.layers.items(), key=lambda x: x[1].priority):
                if info.tier == "CORE":
                    continue
                if info.last_active is None:
                    continue
                idle_s = (now - info.last_active).total_seconds()
                if idle_s > info.sleep_after_idle_s:
                    freed = self.sleep_layer(name)
                    if freed > 0:
                        actions.append(f"sleep_idle:{name} (idle {int(idle_s)}s, freed {freed}MB)")
                        freed_total += freed

            # Step 2: 若仍超標，強製休眠
            self.recalc_usage()
            if self.current_usage_mb > self.total_budget_mb:
                over = self.current_usage_mb - self.total_budget_mb
                for name, info in sorted(self.layers.items(),
                                         key=lambda x: (x[1].priority, -x[1].mem_current_mb)):
                    if info.tier == "CORE" or info.tier == "ARCHIVE":
                        continue
                    if self.current_usage_mb <= self.total_budget_mb:
                        break
                    freed = self.sleep_layer(name)
                    if freed > 0:
                        actions.append(f"force_sleep:{name} (over budget, freed {freed}MB)")
                        freed_total += freed
                        self.recalc_usage()

            self._save_config()
            return {
                "before_mb": self.current_usage_mb + freed_total,
                "after_mb": self.current_usage_mb,
                "freed_mb": freed_total,
                "budget_mb": self.total_budget_mb,
                "actions": actions,
                "within_budget": self.current_usage_mb <= self.total_budget_mb,
            }

    # ── 背景監控 ──

    def start_monitor(self, interval_s: int = 60):
        """啟動背景執行緒，定時自動平衡"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        def _loop():
            while not self._stop_monitor:
                time.sleep(interval_s)
                try:
                    self.auto_balance()
                except Exception:
                    pass

        self._monitor_thread = threading.Thread(target=_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitor(self):
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)

    # ── 查詢 ──

    def get_usage_report(self) -> str:
        self.recalc_usage()
        tiers_usage: Dict[str, int] = {}
        for info in self.layers.values():
            tiers_usage[info.tier] = tiers_usage.get(info.tier, 0) + info.mem_current_mb

        bar_len = 30
        filled = int(bar_len * self.current_usage_mb / max(1, self.total_budget_mb))
        bar = "▓" * filled + "░" * (bar_len - filled)

        lines = [
            f"📊 資源報告",
            f"  [{bar}] {self.current_usage_mb}/{self.total_budget_mb} MB",
        ]
        for tier in ["CORE", "ESSENTIAL", "ON_DEMAND", "ARCHIVE"]:
            used = tiers_usage.get(tier, 0)
            budget = self.budget_per_tier.get(tier, 50)
            lines.append(f"  {tier}: {used}/{budget} MB")

        asleep_layers = [n for n, i in self.layers.items()
                         if all(o.is_asleep() if hasattr(o, 'is_asleep') else False
                                for o in i.organs.values())]
        if asleep_layers:
            lines.append(f"  😴 休眠層: {', '.join(asleep_layers)}")

        return "\n".join(lines)

    def status(self) -> dict:
        self.recalc_usage()
        return {
            "name": "ResourceGovernor",
            "total_budget_mb": self.total_budget_mb,
            "current_usage_mb": self.current_usage_mb,
            "layer_count": len(self.layers),
            "tiers": {
                tier: sum(1 for i in self.layers.values() if i.tier == tier)
                for tier in ["CORE", "ESSENTIAL", "ON_DEMAND", "ARCHIVE"]
            },
            "within_budget": self.current_usage_mb <= self.total_budget_mb,
        }
