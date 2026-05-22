"""
Economy Layer — AI 文明經濟引擎
------------------------------
核心問題：這次行動花多少？值不值得？ROI 是多少？

定價模型：
- 動態定價表（可隨時更新，支援模型生命週期）
- GPU / CPU 估算成本
- 外部 API 調用成本
- 內部 tool 執行成本
"""
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ModelPricing:
    provider: str
    model: str
    input_per_1m: float         # USD per 1M input tokens
    output_per_1m: float        # USD per 1M output tokens
    effective_from: str         # ISO timestamp
    effective_until: str = ""   # empty = still active
    status: str = "active"      # active / deprecated / replaced
    replaced_by: str = ""
    source: str = "manual"      # manual / api_fetch / community


@dataclass
class CostRecord:
    action: str
    category: str          # llm_call / tool_exec / api_call / gpu_task
    provider: str
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: float = 0
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""


class CostEngine:
    """
    成本引擎 — 全系統統一計價，支援動態定價與模型生命週期

    使用方式：
        engine = CostEngine(base_dir)
        engine.update_pricing("DeepSeek", "deepseek-v4-pro", 0.14, 0.28)
        engine.deprecate_model("gpt-4", replaced_by="gpt-4.1")
        engine.record_llm_call("DeepSeek", "deepseek-v4-pro", 500, 200, 1200)
        print(engine.daily_report())
    """

    # ── 預設定價表（USD per 1M tokens），可隨時覆蓋 ──
    PRICING: Dict[str, Dict[str, float]] = {}
    _DEFAULT_PRICES: Dict[str, Dict[str, float]] = {
        "DeepSeek":      {"input": 0.14, "output": 0.28},
        "OpenAI":        {"input": 2.50, "output": 10.00},
        "GPT-4.1":       {"input": 2.00, "output": 8.00},
        "GPT-4o":        {"input": 2.50, "output": 10.00},
        "GPT-4o-mini":   {"input": 0.15, "output": 0.60},
        "Claude":        {"input": 3.00, "output": 15.00},
        "Gemini":        {"input": 1.25, "output": 5.00},
        "Ollama":        {"input": 0.00, "output": 0.00},
        "NV-Llama":      {"input": 0.00, "output": 0.00},
        "OR-DeepSeek":   {"input": 0.15, "output": 0.30},
        "OR-Gemini":     {"input": 0.15, "output": 0.30},
        "ATXP":          {"input": 2.00, "output": 8.00},
    }

    GPU_COST_PER_HOUR: Dict[str, float] = {}

    _DEFAULT_GPU: Dict[str, float] = {
        "T4": 0.35, "A10G": 1.00, "A100": 2.50, "H100": 4.00, "local": 0.02,
    }

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.ledger_file = self.base_dir / "data" / "economy" / "ledger.json"
        self.pricing_file = self.base_dir / "data" / "economy" / "pricing.json"
        self.gpu_file = self.base_dir / "data" / "economy" / "gpu_pricing.json"
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.total_spent: float = 0.0
        self.session_spent: float = 0.0
        self.session_id: str = datetime.now().strftime("%Y%m%d-%H%M")
        self.records: List[CostRecord] = []
        self.budget_limit: Optional[float] = None
        self.budget_alert_threshold: float = 0.8

        # 模型生命週期歷史
        self.pricing_history: List[ModelPricing] = []

        # 載入持久化資料
        self._load_pricing()
        self._load_gpu()
        self._load()
        # 補齊預設值
        self._ensure_defaults()

    def _load(self):
        if self.ledger_file.exists():
            try:
                data = json.loads(self.ledger_file.read_text())
                self.total_spent = data.get("total_spent", 0.0)
                self.records = [CostRecord(**r) for r in data.get("records", [])[-5000:]]
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {
                "total_spent": self.total_spent,
                "records": [
                    {
                        "action": r.action, "category": r.category,
                        "provider": r.provider, "model": r.model,
                        "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                        "duration_ms": r.duration_ms, "cost_usd": r.cost_usd,
                        "timestamp": r.timestamp, "session_id": r.session_id,
                    }
                    for r in self.records[-5000:]
                ],
            }
            self.ledger_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ── 動態定價系統 ──

    def _load_pricing(self):
        if self.pricing_file.exists():
            try:
                data = json.loads(self.pricing_file.read_text())
                self.PRICING = data.get("providers", {})
                for p in data.get("history", []):
                    self.pricing_history.append(ModelPricing(**p))
            except Exception:
                pass

    def _save_pricing(self):
        with self._lock:
            data = {
                "providers": {
                    k: v for k, v in self.PRICING.items()
                },
                "history": [
                    {
                        "provider": p.provider, "model": p.model,
                        "input_per_1m": p.input_per_1m,
                        "output_per_1m": p.output_per_1m,
                        "effective_from": p.effective_from,
                        "effective_until": p.effective_until,
                        "status": p.status, "replaced_by": p.replaced_by,
                        "source": p.source,
                    }
                    for p in self.pricing_history[-200:]
                ],
            }
            self.pricing_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load_gpu(self):
        if self.gpu_file.exists():
            try:
                data = json.loads(self.gpu_file.read_text())
                self.GPU_COST_PER_HOUR = data.get("gpu_types", {})
            except Exception:
                pass

    def _save_gpu(self):
        with self._lock:
            self.gpu_file.write_text(json.dumps(
                {"gpu_types": self.GPU_COST_PER_HOUR}, ensure_ascii=False, indent=2))

    def _ensure_defaults(self):
        changed = False
        for provider, prices in self._DEFAULT_PRICES.items():
            if provider not in self.PRICING:
                self.PRICING[provider] = dict(prices)
                changed = True
        for gpu_type, rate in self._DEFAULT_GPU.items():
            if gpu_type not in self.GPU_COST_PER_HOUR:
                self.GPU_COST_PER_HOUR[gpu_type] = rate
                changed = True
        if changed:
            self._save_pricing()
            self._save_gpu()

    def update_pricing(self, provider: str, model: str,
                       input_per_1m: float, output_per_1m: float,
                       source: str = "manual"):
        """更新或新增模型定價，自動記錄歷史"""
        now = datetime.now().isoformat()

        # 紀錄舊價格的變動
        old = self.PRICING.get(provider, {})
        old_input = old.get("input", -1)
        old_output = old.get("output", -1)

        if old_input >= 0 and old_output >= 0:
            if old_input != input_per_1m or old_output != output_per_1m:
                self.pricing_history.append(ModelPricing(
                    provider=provider, model=model,
                    input_per_1m=old_input, output_per_1m=old_output,
                    effective_from="historic",
                    effective_until=now, status="replaced",
                    replaced_by=f"{model}@{input_per_1m}/{output_per_1m}",
                    source="auto",
                ))

        self.PRICING[provider] = {"input": input_per_1m, "output": output_per_1m}

        # 更新模型生命週期
        for p in self.pricing_history:
            if p.provider == provider and p.model == model and p.status == "active":
                p.effective_until = now
                p.status = "replaced"

        self.pricing_history.append(ModelPricing(
            provider=provider, model=model,
            input_per_1m=input_per_1m, output_per_1m=output_per_1m,
            effective_from=now, status="active", source=source,
        ))
        self._save_pricing()

    def deprecate_model(self, provider: str, replaced_by: str = ""):
        """標記模型為已棄用，建議替代模型"""
        for p in self.pricing_history:
            if p.provider == provider and p.status == "active":
                p.status = "deprecated"
                p.effective_until = datetime.now().isoformat()
                p.replaced_by = replaced_by
                break
        if provider in self.PRICING:
            pass  # 保留定價供歷史查詢
        self._save_pricing()

    def update_gpu_pricing(self, gpu_type: str, cost_per_hour: float):
        """更新 GPU 定價"""
        self.GPU_COST_PER_HOUR[gpu_type] = cost_per_hour
        self._save_gpu()

    def get_pricing(self, provider: str) -> Dict[str, Any]:
        """取得當前定價資訊（含歷史價格變遷）"""
        prices = self.PRICING.get(provider, self.PRICING.get("DeepSeek", {"input": 0.14, "output": 0.28}))
        history = [
            {"input": p.input_per_1m, "output": p.output_per_1m,
             "from": p.effective_from[:10], "until": p.effective_until[:10] if p.effective_until else "now",
             "status": p.status, "source": p.source}
            for p in self.pricing_history
            if p.provider == provider
        ]
        return {
            "provider": provider,
            "current": {
                "input_per_1m": prices["input"],
                "output_per_1m": prices["output"],
            },
            "history": history[-20:],
            "models": [
                {
                    "model": p.model,
                    "input_per_1m": p.input_per_1m,
                    "output_per_1m": p.output_per_1m,
                    "status": p.status,
                    "replaced_by": p.replaced_by,
                    "updated": p.effective_from[:10],
                }
                for p in self.pricing_history
                if p.provider == provider
            ][-10:],
        }

    def sync_pricing_from_api(self, force: bool = False):
        """
        從 API 同步最新定價（未來可接 OpenAI pricing endpoint）
        目前先檢查 pricing_history 中超過 30 天未更新的 active model，
        標記為 stale。
        """
        now = datetime.now()
        updated = 0
        for p in self.pricing_history:
            if p.status == "active":
                try:
                    updated_at = datetime.fromisoformat(p.effective_from)
                    if (now - updated_at).days > 30:
                        p.status = "stale"
                        updated += 1
                except Exception:
                    pass
        if updated > 0:
            self._save_pricing()
        return {"synced": len(self.pricing_history), "stale_marked": updated}

    def list_active_models(self) -> List[Dict[str, Any]]:
        """列出目前活躍的模型及其價格"""
        return [
            {
                "provider": p.provider,
                "model": p.model,
                "input_per_1m": p.input_per_1m,
                "output_per_1m": p.output_per_1m,
                "status": p.status,
                "effective_from": p.effective_from[:10],
            }
            for p in self.pricing_history
            if p.status == "active"
        ]

    # ── 計費 ──

    def _llm_cost(self, provider: str, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(provider, self.PRICING["DeepSeek"])
        cost_in = (tokens_in / 1_000_000) * pricing["input"]
        cost_out = (tokens_out / 1_000_000) * pricing["output"]
        return round(cost_in + cost_out, 6)

    def record_llm_call(
        self, provider: str, model: str,
        tokens_in: int, tokens_out: int,
        duration_ms: float, action: str = "llm_call"
    ) -> float:
        cost = self._llm_cost(provider, tokens_in, tokens_out)
        record = CostRecord(
            action=action, category="llm_call",
            provider=provider, model=model,
            tokens_in=tokens_in, tokens_out=tokens_out,
            duration_ms=duration_ms, cost_usd=cost,
            session_id=self.session_id,
        )
        with self._lock:
            self.records.append(record)
            self.total_spent += cost
            self.session_spent += cost
        self._save()
        return cost

    def record_tool_exec(self, tool_name: str, duration_ms: float, cost_usd: float = 0.0):
        record = CostRecord(
            action=tool_name, category="tool_exec",
            provider="tool_system", model="",
            duration_ms=duration_ms, cost_usd=cost_usd,
            session_id=self.session_id,
        )
        with self._lock:
            self.records.append(record)
            self.total_spent += cost_usd
            self.session_spent += cost_usd
        self._save()

    def record_api_call(self, api_name: str, duration_ms: float, cost_usd: float = 0.0):
        record = CostRecord(
            action=api_name, category="api_call",
            provider="external", model="",
            duration_ms=duration_ms, cost_usd=cost_usd,
            session_id=self.session_id,
        )
        with self._lock:
            self.records.append(record)
            self.total_spent += cost_usd
            self.session_spent += cost_usd
        self._save()

    def record_gpu(self, gpu_type: str, hours: float, task: str = ""):
        rate = self.GPU_COST_PER_HOUR.get(gpu_type, 0.05)
        cost = round(rate * hours, 4)
        record = CostRecord(
            action=task or f"gpu_{gpu_type}", category="gpu_task",
            provider=gpu_type, model="",
            duration_ms=hours * 3600_000, cost_usd=cost,
            session_id=self.session_id,
        )
        with self._lock:
            self.records.append(record)
            self.total_spent += cost
            self.session_spent += cost
        self._save()

    # ── 查詢 ──

    def get_provider_cost(self, provider: str) -> float:
        with self._lock:
            return round(sum(
                r.cost_usd for r in self.records
                if r.provider == provider
            ), 6)

    def get_category_breakdown(self) -> Dict[str, float]:
        with self._lock:
            breakdown: Dict[str, float] = {}
            for r in self.records:
                breakdown[r.category] = round(breakdown.get(r.category, 0) + r.cost_usd, 6)
            return breakdown

    def daily_report(self) -> str:
        breakdown = self.get_category_breakdown()
        lines = [
            f"💰 經濟日報",
            f"  總支出: ${self.total_spent:.4f}",
            f"  本會話: ${self.session_spent:.4f}",
        ]
        for cat, cost in sorted(breakdown.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: ${cost:.4f}")
        if self.budget_limit:
            pct = self.session_spent / self.budget_limit * 100
            bar = "▓" * int(pct / 5) + "░" * (20 - int(pct / 5))
            lines.append(f"  預算: [{bar}] {pct:.1f}%")
        return "\n".join(lines)

    def estimate(self, provider: str, tokens_in: int, tokens_out: int) -> float:
        return self._llm_cost(provider, tokens_in, tokens_out)

    def cheap_provider(self, task_complexity: str = "simple") -> str:
        if task_complexity == "simple":
            return "DeepSeek" if "DeepSeek" in self.PRICING else "Ollama"
        elif task_complexity == "complex":
            return "DeepSeek"
        return "DeepSeek"

    # ── 預算 ──

    def set_budget(self, limit_usd: float):
        self.budget_limit = limit_usd

    def check_budget(self, estimated_cost: float = 0) -> Dict[str, Any]:
        if not self.budget_limit:
            return {"allowed": True, "reason": "no_budget_set"}
        remaining = self.budget_limit - self.session_spent
        if remaining < estimated_cost:
            return {
                "allowed": False,
                "reason": f"over_budget: need ${estimated_cost:.4f}, have ${remaining:.4f}",
            }
        if remaining / self.budget_limit < (1 - self.budget_alert_threshold):
            return {
                "allowed": True,
                "warning": f"budget low: ${remaining:.4f} left ({remaining/self.budget_limit*100:.1f}%)",
            }
        return {"allowed": True}

    def status(self) -> dict:
        return {
            "name": "CostEngine",
            "total_spent": self.total_spent,
            "session_spent": self.session_spent,
            "session_id": self.session_id,
            "budget_limit": self.budget_limit,
            "record_count": len(self.records),
        }
