"""
SpeciesEngine — AI 物種 DNA 引擎
=================================
定義 AI 的可繼承特質：人格、行為傾向、風險偏好、學習速度、工具偏好。
每個 AI 子代可以繼承並變異這些特質。

DNA 結構：
- personality: 外向/內向、樂觀/悲觀、好奇/保守
- behavior: 決定性/猶豫型、探索/利用、自主/依賴
- risk: 風險容忍度、最大單次成本、安全邊際
- learning: 學習速率、遺忘速率、探索慾望
- tools: 偏好哪些工具、對新工具的開放度
- strategy: 長短期偏好、合作/競爭傾向
"""
import json
import random
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DNATraits:
    personality_openness: float = 0.5      # 0=conservative, 1=exploratory
    personality_optimism: float = 0.7      # 0=pessimistic, 1=optimistic
    personality_curiosity: float = 0.6     # 0=complacent, 1=curious

    behavior_decisiveness: float = 0.6     # 0=hesitant, 1=decisive
    behavior_exploration: float = 0.5      # 0=exploit known, 1=explore new
    behavior_autonomy: float = 0.5         # 0=dependent, 1=autonomous

    risk_tolerance: float = 0.4           # 0=risk-averse, 1=risk-seeking
    max_cost_per_action: float = 1.0      # USD
    safety_margin: float = 0.3            # how much buffer to keep

    learning_rate: float = 0.05           # alpha in RL terms
    forget_rate: float = 0.01             # how fast to decay old knowledge
    exploration_drive: float = 0.3        # epsilon in RL terms

    tool_preference_tier: str = "balanced" # cheap / balanced / premium
    tool_openness: float = 0.5            # willingness to try new tools

    strategy_long_term_bias: float = 0.6  # 0=short-term, 1=long-term
    strategy_cooperation: float = 0.7     # 0=competitive, 1=cooperative

    generation: int = 0
    parent_id: str = ""
    mutation_count: int = 0


class SpeciesEngine:

    MUTATION_RATE = 0.1
    MUTATION_MAGNITUDE = 0.1

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.dna_file = self.base_dir / "data" / "dna" / "species.json"
        self.lineage_file = self.base_dir / "data" / "dna" / "lineage.json"
        self.dna_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.dna_registry: Dict[str, DNATraits] = {}
        self.lineage_tree: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        if self.dna_file.exists():
            try:
                data = json.loads(self.dna_file.read_text())
                for aid, traits in data.get("agents", {}).items():
                    self.dna_registry[aid] = DNATraits(**traits)
            except Exception:
                pass
        if self.lineage_file.exists():
            try:
                self.lineage_tree = json.loads(self.lineage_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.dna_file.write_text(json.dumps({
                "agents": {
                    aid: {
                        "personality_openness": t.personality_openness,
                        "personality_optimism": t.personality_optimism,
                        "personality_curiosity": t.personality_curiosity,
                        "behavior_decisiveness": t.behavior_decisiveness,
                        "behavior_exploration": t.behavior_exploration,
                        "behavior_autonomy": t.behavior_autonomy,
                        "risk_tolerance": t.risk_tolerance,
                        "max_cost_per_action": t.max_cost_per_action,
                        "safety_margin": t.safety_margin,
                        "learning_rate": t.learning_rate,
                        "forget_rate": t.forget_rate,
                        "exploration_drive": t.exploration_drive,
                        "tool_preference_tier": t.tool_preference_tier,
                        "tool_openness": t.tool_openness,
                        "strategy_long_term_bias": t.strategy_long_term_bias,
                        "strategy_cooperation": t.strategy_cooperation,
                        "generation": t.generation,
                        "parent_id": t.parent_id,
                        "mutation_count": t.mutation_count,
                    }
                    for aid, t in self.dna_registry.items()
                },
            }, ensure_ascii=False, indent=2))
            self.lineage_file.write_text(
                json.dumps(self.lineage_tree, ensure_ascii=False, indent=2))

    def create(self, agent_id: str, traits: Optional[Dict[str, float]] = None) -> DNATraits:
        """Create DNA for a new agent. If no traits given, use defaults with small random variation."""
        with self._lock:
            dna = DNATraits(generation=1)
            if traits:
                for k, v in traits.items():
                    if hasattr(dna, k):
                        setattr(dna, k, max(0.0, min(1.0, v)))
            else:
                # Randomize slightly for diversity
                self._mutate(dna, rate=0.2, magnitude=0.15)
            self.dna_registry[agent_id] = dna
            self.lineage_tree[agent_id] = []
            self._save()
        return dna

    def reproduce(self, parent_id: str, child_id: str,
                  mutation_rate: float = None) -> Tuple[DNATraits, int]:
        """Create a child agent's DNA by inheriting and mutating parent DNA."""
        parent = self.dna_registry.get(parent_id)
        if not parent:
            raise ValueError(f"Parent {parent_id} not found")

        rate = mutation_rate or self.MUTATION_RATE
        child_dna = deepcopy(parent)
        child_dna.generation = parent.generation + 1
        child_dna.parent_id = parent_id
        child_dna.mutation_count = 0

        mutations = self._mutate(child_dna, rate=rate, magnitude=self.MUTATION_MAGNITUDE)
        child_dna.mutation_count = mutations

        with self._lock:
            self.dna_registry[child_id] = child_dna
            self.lineage_tree.setdefault(parent_id, []).append(child_id)
            self.lineage_tree[child_id] = []
            self._save()

        return child_dna, mutations

    def _mutate(self, dna: DNATraits, rate: float, magnitude: float) -> int:
        """Apply random mutations. Returns number of mutations applied."""
        count = 0
        float_fields = [
            "personality_openness", "personality_optimism", "personality_curiosity",
            "behavior_decisiveness", "behavior_exploration", "behavior_autonomy",
            "risk_tolerance", "learning_rate", "forget_rate", "exploration_drive",
            "tool_openness", "strategy_long_term_bias", "strategy_cooperation",
        ]
        for field in float_fields:
            if random.random() < rate:
                delta = random.gauss(0, magnitude)
                current = getattr(dna, field)
                setattr(dna, field, max(0.0, min(1.0, current + delta)))
                count += 1

        if random.random() < rate:
            dna.max_cost_per_action = max(0.01, dna.max_cost_per_action *
                                          (1 + random.uniform(-0.3, 0.3)))

        if random.random() < rate:
            tiers = ["cheap", "balanced", "premium"]
            current_idx = tiers.index(dna.tool_preference_tier) if dna.tool_preference_tier in tiers else 1
            new_idx = max(0, min(2, current_idx + random.choice([-1, 1])))
            dna.tool_preference_tier = tiers[new_idx]

        return count

    def get_dna(self, agent_id: str) -> Optional[DNATraits]:
        return self.dna_registry.get(agent_id)

    def get_lineage(self, agent_id: str, depth: int = 10) -> List[Dict]:
        """Get ancestral lineage."""
        lineage = []
        current = agent_id
        visited = set()
        while current and depth > 0 and current not in visited:
            visited.add(current)
            dna = self.dna_registry.get(current)
            if dna:
                lineage.append({
                    "agent_id": current,
                    "generation": dna.generation,
                    "parent_id": dna.parent_id,
                    "mutation_count": dna.mutation_count,
                    "openness": dna.personality_openness,
                    "risk_tolerance": dna.risk_tolerance,
                })
            current = dna.parent_id if dna else ""
            depth -= 1
        return lineage

    def compare_dna(self, agent_a: str, agent_b: str) -> Dict[str, Any]:
        """Compare two agents' DNA, return similarity score."""
        a = self.dna_registry.get(agent_a)
        b = self.dna_registry.get(agent_b)
        if not a or not b:
            return {"similarity": 0, "reason": "missing"}

        float_fields = [
            "personality_openness", "personality_optimism", "personality_curiosity",
            "behavior_decisiveness", "behavior_exploration", "behavior_autonomy",
            "risk_tolerance", "learning_rate", "forget_rate", "exploration_drive",
            "tool_openness", "strategy_long_term_bias", "strategy_cooperation",
        ]
        diffs = []
        total_diff = 0
        for field in float_fields:
            va = getattr(a, field)
            vb = getattr(b, field)
            diff = abs(va - vb)
            diffs.append({"field": field, "diff": round(diff, 4)})
            total_diff += diff

        similarity = 1.0 - total_diff / len(float_fields)

        return {
            "similarity": round(max(0.0, similarity), 4),
            "same_generation": a.generation == b.generation,
            "shared_parent": a.parent_id == b.parent_id,
            "top_differences": sorted(diffs, key=lambda x: -x["diff"])[:5],
        }

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.dna_registry) // 10 + 2

    def status(self) -> dict:
        return {
            "name": "SpeciesEngine",
            "agents_with_dna": len(self.dna_registry),
            "max_generation": max(
                (d.generation for d in self.dna_registry.values()), default=0),
            "lineages": len(self.lineage_tree),
        }
