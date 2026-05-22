"""
CivilizationController — AI 文明總控
=====================================
串接所有 10 層文明基礎設施，實現閉環自治：

1. economy/       — 成本意識
2. trust/         — 信任系統
3. simulation/    — 預測模擬
4. goals/         — 目標層級
5. society/       — 社會治理
6. temporal/      — 時間意識
7. dna_system/    — DNA 繼承
8. civilization_memory/ — 文明記憶
9. lifecycle/     — 器官熱插拔
10. skeleton/resource_governor — 資源治理

閉環流程：
  事件 → temporal(偵測週期) → simulation(模擬後果)
       → economy(評估成本) → goals(目標路由)
       → trust(可信度檢查) → alignment_guard(對齊檢查)
       → 執行 → trust(回報結果) → memory(記錄)
       → lifecycle(器官健康) → resource_governor(資源平衡)
"""
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.resource_governor import ResourceGovernor


class CivilizationController:

    TIERS = {
        "skeleton":  "CORE",
        "nerve":     "CORE",
        "blood":     "CORE",
        "brain":     "CORE",
        "immune":    "CORE",
        "economy":   "ESSENTIAL",
        "trust":     "ESSENTIAL",
        "goals":     "ESSENTIAL",
        "temporal":  "ESSENTIAL",
        "simulation":"ON_DEMAND",
        "society":   "ON_DEMAND",
        "dna_system":"ON_DEMAND",
        "civilization_memory": "ON_DEMAND",
        "lifecycle": "ESSENTIAL",
    }

    DEFAULT_LAYERS = [
        "economy", "trust", "simulation", "goals",
        "society", "temporal", "dna_system", "civilization_memory", "lifecycle",
    ]

    def __init__(self, base_dir: Optional[Path] = None,
                 memory=None, evolution=None, brain=None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.config_file = self.base_dir / "data" / "civilization" / "state.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        # 現有系統引用
        self.memory = memory
        self.evolution = evolution
        self.brain = brain

        # 資源總督
        self.resource_gov = ResourceGovernor(
            total_budget_mb=400, base_dir=self.base_dir)

        # 所有文明層引擎（惰性載入）
        self.engines: Dict[str, Any] = {}
        self.engine_classes: Dict[str, str] = {}
        self._discover_engines()

        # 狀態
        self.civilization_age_days: float = 0
        self.birth_time: Optional[datetime] = None
        self.cycle_count: int = 0
        self._load_state()

    def _discover_engines(self):
        """註冊各層引擎的懶載入路徑"""
        self.engine_classes = {
            "cost_engine":      "economy.cost_engine:CostEngine",
            "token_budget":     "economy.token_budget:TokenBudget",
            "roi_analyzer":     "economy.roi_analyzer:ROIAnalyzer",
            "value_predictor":  "economy.value_predictor:ValuePredictor",
            "trust_score":      "trust.trust_score:TrustScore",
            "source_validator": "trust.source_validator:SourceValidator",
            "hallucination_guard": "trust.hallucination_guard:HallucinationGuard",
            "tool_reputation":  "trust.tool_reputation:ToolReputation",
            "agent_reliability":"trust.agent_reliability:AgentReliability",
            "future_simulator": "simulation.future_simulator:FutureSimulator",
            "prime_directive":  "goals.prime_directive:PrimeDirective",
            "goal_hierarchy":   "goals.hierarchy:GoalHierarchy",
            "objective_router": "goals.objective_router:ObjectiveRouter",
            "mission_engine":   "goals.mission_engine:MissionEngine",
            "alignment_guard":  "goals.alignment_guard:AlignmentGuard",
            "governance":       "society.governance:Governance",
            "cycle_detector":   "temporal.cycle_detector:CycleDetector",
            "trend_memory":     "temporal.trend_memory:TrendMemory",
            "decay_engine":     "temporal.decay_engine:DecayEngine",
            "species_engine":   "dna_system.species_engine:SpeciesEngine",
            "episodic_memory":  "civilization_memory.episodic:EpisodicMemory",
            "failure_memory":   "civilization_memory.episodic:FailureMemory",
            "evolution_memory": "civilization_memory.episodic:EvolutionMemory",
            "organ_lifecycle":  "lifecycle.organ_lifecycle:OrganLifecycle",
        }

    def _load_state(self):
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                self.civilization_age_days = data.get("age_days", 0)
                self.cycle_count = data.get("cycles", 0)
                bt = data.get("birth_time")
                self.birth_time = datetime.fromisoformat(bt) if bt else datetime.now()
            except Exception:
                self.birth_time = datetime.now()
        else:
            self.birth_time = datetime.now()

        if self.birth_time:
            self.civilization_age_days = (datetime.now() - self.birth_time).total_seconds() / 86400

    def _save_state(self):
        with self._lock:
            self.config_file.write_text(json.dumps({
                "age_days": self.civilization_age_days,
                "cycles": self.cycle_count,
                "birth_time": self.birth_time.isoformat() if self.birth_time else "",
                "active_engines": list(self.engines.keys()),
            }, ensure_ascii=False, indent=2))

    def get_engine(self, name: str) -> Optional[Any]:
        """惰性載入引擎，搭配 ResourceGovernor 的喚醒機制"""
        if name in self.engines:
            engine = self.engines[name]
            # Auto-wake if asleep
            if hasattr(engine, 'wake') and hasattr(engine, 'is_asleep') and engine.is_asleep():
                engine.wake()
            return engine

        import_path = self.engine_classes.get(name)
        if not import_path:
            return None

        try:
            module_path, class_name = import_path.split(":")
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            # 檢查構造函數需要的參數
            kwargs = {"base_dir": self.base_dir}
            if name == "trust_score":
                kwargs["base_dir"] = self.base_dir
            elif name in ("value_predictor",):
                roi = self.get_engine("roi_analyzer")
                if roi:
                    kwargs["roi_analyzer"] = roi
            elif name in ("objective_router",):
                kwargs["goal_hierarchy"] = self.get_engine("goal_hierarchy")
                kwargs["mission_engine"] = self.get_engine("mission_engine")
            elif name == "mission_engine":
                kwargs["goal_hierarchy"] = self.get_engine("goal_hierarchy")
            elif name == "alignment_guard":
                kwargs["prime_directive"] = self.get_engine("prime_directive")
                kwargs["goal_hierarchy"] = self.get_engine("goal_hierarchy")
            elif name in ("future_simulator",):
                kwargs["memory"] = self.memory
                kwargs["trust"] = self.get_engine("trust_score")
            elif name in ("source_validator", "hallucination_guard",
                          "tool_reputation", "agent_reliability"):
                kwargs["trust_engine"] = self.get_engine("trust_score")

            engine = cls(**kwargs)
            self.engines[name] = engine

            # Register with resource governor
            layer = self._layer_for_engine(name)
            tier = self.TIERS.get(layer, "ESSENTIAL")
            self.resource_gov.register_organ(layer, name, engine)

            return engine
        except Exception:
            return None

    def _layer_for_engine(self, engine_name: str) -> str:
        mapping = {
            "cost_engine": "economy",
            "token_budget": "economy",
            "roi_analyzer": "economy",
            "value_predictor": "economy",
            "trust_score": "trust",
            "source_validator": "trust",
            "hallucination_guard": "trust",
            "tool_reputation": "trust",
            "agent_reliability": "trust",
            "future_simulator": "simulation",
            "prime_directive": "goals",
            "goal_hierarchy": "goals",
            "objective_router": "goals",
            "mission_engine": "goals",
            "alignment_guard": "goals",
            "governance": "society",
            "cycle_detector": "temporal",
            "trend_memory": "temporal",
            "decay_engine": "temporal",
            "species_engine": "dna_system",
            "episodic_memory": "civilization_memory",
            "failure_memory": "civilization_memory",
            "evolution_memory": "civilization_memory",
            "organ_lifecycle": "lifecycle",
        }
        return mapping.get(engine_name, "unknown")

    # ── 閉環操作 ──

    def pre_action_check(self, action: str, agent_id: str = "",
                         context: Dict = None) -> Dict[str, Any]:
        """
        執行任何行動前的全棧檢查。
        這是文明閉環的入口：每個 action 都經過這條 pipeline。
        """
        context = context or {}
        result = {
            "allowed": True,
            "checks": {},
            "warnings": [],
            "recommended_model_tier": "normal",
        }

        # 1. Alignment check
        guard = self.get_engine("alignment_guard")
        if guard:
            ac = guard.check_action(action, agent_id, context)
            result["checks"]["alignment"] = ac
            if not ac.get("allowed"):
                result["allowed"] = False
                result["reason"] = ac.get("reason", "alignment_blocked")
                return result

        # 2. Budget check
        budget = self.get_engine("token_budget")
        if budget:
            est_tokens = context.get("estimated_tokens", 1000)
            alloc = budget.allocate(
                context.get("task_type", "default"),
                est_tokens, agent_id)
            result["checks"]["budget"] = alloc
            if not alloc.get("allowed"):
                result["allowed"] = False
                result["reason"] = alloc.get("reason", "budget_exceeded")
                return result

        # 3. Value prediction
        predictor = self.get_engine("value_predictor")
        if predictor:
            v = predictor.predict(
                context.get("task_type", "default"), context)
            result["checks"]["value"] = {
                "estimated_value": v.estimated_value,
                "recommended_tier": v.recommended_tier,
                "max_cost": v.max_cost_usd,
            }
            result["recommended_model_tier"] = v.recommended_tier
            if v.estimated_value < 0.1:
                result["warnings"].append("low_value_task")

        # 4. Risk simulation
        sim = self.get_engine("future_simulator")
        if sim:
            s = sim.simulate(action, context)
            result["checks"]["simulation"] = {
                "risk_score": s["risk_score"],
                "recommendation": s["recommendation"],
            }
            if s["recommendation"] == "dangerous":
                result["warnings"].append("high_risk_action")

        # 5. Failure memory check
        fm = self.get_engine("failure_memory")
        if fm:
            risky = fm.is_risky(action)
            if risky.get("risky"):
                result["warnings"].append(
                    f"previously_failed_{risky['failures']}x")

        return result

    def post_action_report(self, action: str, success: bool,
                           cost_usd: float, duration_ms: float,
                           agent_id: str = ""):
        """每次行動後回報所有層。"""
        # 1. Record cost
        cost_engine = self.get_engine("cost_engine")
        if cost_engine:
            cost_engine.record_llm_call(
                "system", "", 0, 0, duration_ms, action)
            cost_engine.record_tool_exec(action, duration_ms, cost_usd)

        # 2. ROI
        roi = self.get_engine("roi_analyzer")
        if roi:
            roi.record(action, "action", cost_usd, success,
                       value_score=0.7 if success else 0.2)

        # 3. Tool reputation
        tr = self.get_engine("tool_reputation")
        if tr:
            tr.record_execution(action, success, duration_ms)

        # 4. Simulation feedback
        sim = self.get_engine("future_simulator")
        if sim:
            sim.record_outcome(action, success)

        # 5. Failure memory
        if not success:
            fm = self.get_engine("failure_memory")
            if fm:
                fm.record(action, "execution_failed", severity=0.5)

        # 6. Evolution memory
        em = self.get_engine("evolution_memory")
        if em:
            em.record_change(
                "action", f"{'OK' if success else 'FAIL'}: {action}",
                agent_id)

        # 7. Cycle detection
        cd = self.get_engine("cycle_detector")
        if cd:
            cd.record_event(action, {
                "success": success,
                "cost": cost_usd,
                "duration_ms": duration_ms,
            })

    def heartbeat(self):
        """文明週期性維護（每分鐘呼叫一次）。"""
        self.cycle_count += 1
        self.civilization_age_days = (
            datetime.now() - self.birth_time).total_seconds() / 86400 if self.birth_time else 0

        # 資源平衡
        balance = self.resource_gov.auto_balance()

        # 回收過期記憶
        decay = self.get_engine("decay_engine")
        if decay:
            decay.cleanup_expired()

        # 器官維護
        lifecycle = self.get_engine("organ_lifecycle")
        if lifecycle:
            lifecycle.auto_maintain()

        self._save_state()

    def civilization_report(self) -> str:
        """完整文明狀態報告"""
        lines = [
            "",
            "AI Civilization Report",
            "",
            f"  Age: {self.civilization_age_days:.1f} days",
            f"  Cycles: {self.cycle_count}",
            f"  Birth: {self.birth_time.isoformat() if self.birth_time else 'unknown'}",
            "",
            "--- Economy ---",
        ]

        cost = self.get_engine("cost_engine")
        if cost:
            lines.append(cost.daily_report())

        lines.append("")
        lines.append("--- Trust ---")
        trust = self.get_engine("trust_score")
        if trust:
            lines.append(f"  Entities: {trust.status().get('total_entities', 0)}")
            lines.append(f"  Avg Trust: {trust.status().get('avg_trust', 0):.2f}")

        lines.append("")
        lines.append("--- Goals ---")
        gh = self.get_engine("goal_hierarchy")
        if gh:
            lines.append(f"  Levels: {gh.status().get('levels', 0)}")
            lines.append(f"  Active: {gh.status().get('active', 'none')}")

        lines.append("")
        lines.append("--- Lifecycle ---")
        lc = self.get_engine("organ_lifecycle")
        if lc:
            lines.append(lc.cycle_report())

        lines.append("")
        lines.append("--- Resources ---")
        lines.append(self.resource_gov.get_usage_report())

        lines.append("")
        lines.append("--- Memory ---")
        em = self.get_engine("episodic_memory")
        fm = self.get_engine("failure_memory")
        evm = self.get_engine("evolution_memory")
        if em:
            lines.append(f"  Episodic: {em.status().get('episodes', 0)} events")
        if fm:
            lines.append(f"  Failures: {fm.status().get('failures', 0)}")
        if evm:
            lines.append(f"  Evolution: v{evm.status().get('version', 0)}")

        return "\n".join(lines)

    def status(self) -> dict:
        return {
            "name": "CivilizationController",
            "age_days": round(self.civilization_age_days, 1),
            "cycles": self.cycle_count,
            "active_engines": len(self.engines),
            "total_engines_available": len(self.engine_classes),
            "resource": self.resource_gov.status(),
        }
