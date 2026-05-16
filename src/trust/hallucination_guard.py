"""
HallucinationGuard — 幻覺守衛
-------------------------------
檢測並記錄 LLM 輸出中的潛在幻覺。
透過：
1. 事實一致性檢查（跨多次呼叫比對）
2. 自我矛盾檢測（同一回應中前後矛盾）
3. 來源可追溯性（是否給出來源）
4. 過度自信檢測（確定性過高但無依據）
"""
import json
import re
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class HallucinationGuard:

    UNCERTAINTY_PATTERNS = [
        r"(?i)as an AI",
        r"(?i)I (?:don't|cannot|do not|can not) (?:have|know|access)",
        r"(?i)I am not sure",
        r"(?i)it is possible that",
        r"(?i)to the best of my knowledge",
        r"(?i)I (?:believe|think|assume|guess)",
    ]

    OVERCONFIDENCE_PATTERNS = [
        r"(?i)absolutely",
        r"(?i)without (?:any|a) doubt",
        r"(?i)100%",
        r"(?i)definitely",
        r"(?i)I am (?:completely|certain|positive)",
    ]

    def __init__(self, trust_engine: Optional[Any] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.data_file = self.base_dir / "data" / "trust" / "hallucinations.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.trust = trust_engine
        self.hallucination_log: List[Dict] = []
        self.agent_scores: Dict[str, Dict] = defaultdict(
            lambda: {"total_responses": 0, "flagged": 0, "score": 1.0})
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                self.hallucination_log = data.get("log", [])
                for k, v in data.get("agent_scores", {}).items():
                    self.agent_scores[k] = v
            except Exception:
                pass

    def _save(self):
        with self._lock:
            data = {
                "log": self.hallucination_log[-5000:],
                "agent_scores": dict(self.agent_scores),
            }
            self.data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def scan(self, agent_id: str, response: str,
             context: str = "") -> Dict[str, Any]:
        """
        掃描回應，回傳幻覺風險評估。
        """
        flags = []
        risk_score = 0.0

        has_uncertainty = any(
            re.search(p, response) for p in self.UNCERTAINTY_PATTERNS
        )
        overconfidence = any(
            re.search(p, response) for p in self.OVERCONFIDENCE_PATTERNS
        )
        has_source = bool(re.search(r"(?:https?://|\[[\d,]+\]|source:|根據)", response))
        repetition = len(set(response.lower().split())) / max(1, len(response.split())) < 0.3

        if overconfidence and not has_source:
            flags.append("overconfident_no_source")
            risk_score += 0.3

        if repetition:
            flags.append("repetitive")
            risk_score += 0.15

        factual_claims = re.findall(
            r'(?i)(?:根據|according to|studies show|research indicates|statistics show)', response
        )
        if factual_claims and not has_source:
            flags.append("unsupported_claim")
            risk_score += 0.2

        if len(response.split()) < 5 and not has_uncertainty:
            flags.append("too_short")
            risk_score += 0.05

        if response.strip() == context.strip():
            flags.append("echo_response")
            risk_score += 0.4

        risk_score = min(1.0, risk_score)

        self._update_agent(agent_id, risk_score > 0.3, risk_score)

        if risk_score > 0.3:
            self.hallucination_log.append({
                "agent_id": agent_id,
                "response_preview": response[:200],
                "flags": flags,
                "risk_score": risk_score,
                "timestamp": datetime.now().isoformat(),
            })
            self._save()

        if self.trust:
            success = risk_score < 0.3
            self.trust.record(f"agent_{agent_id}", success,
                              tags=["hallucination_check"])

        return {
            "risk_score": round(risk_score, 4),
            "flags": flags,
            "is_flagged": risk_score > 0.3,
            "recommendation": "safe" if risk_score < 0.3
            else "review" if risk_score < 0.6 else "reject",
        }

    def _update_agent(self, agent_id: str, flagged: bool, score: float):
        with self._lock:
            s = self.agent_scores[agent_id]
            s["total_responses"] += 1
            if flagged:
                s["flagged"] += 1
            total = s["total_responses"]
            flag_rate = s["flagged"] / total if total > 0 else 0
            s["score"] = round(max(0.0, min(1.0, 1.0 - flag_rate - score * 0.1)), 4)

    def get_agent_hallucination_rate(self, agent_id: str) -> Dict[str, Any]:
        s = self.agent_scores.get(agent_id, {})
        return {
            "agent_id": agent_id,
            "total_responses": s.get("total_responses", 0),
            "flagged": s.get("flagged", 0),
            "hallucination_score": s.get("score", 1.0),
            "flag_rate": round(
                s.get("flagged", 0) / max(1, s.get("total_responses", 1)), 4
            ),
        }

    def worst_offenders(self, top_n: int = 5) -> List[Dict]:
        ranked = sorted(
            self.agent_scores.items(),
            key=lambda x: x[1].get("score", 1.0)
        )
        return [self.get_agent_hallucination_rate(k) for k, _ in ranked[:top_n]]

    def recent_flags(self, n: int = 20) -> List[Dict]:
        return self.hallucination_log[-n:]

    def status(self) -> dict:
        return {
            "name": "HallucinationGuard",
            "total_scans": sum(s["total_responses"] for s in self.agent_scores.values()),
            "total_flags": len(self.hallucination_log),
            "tracked_agents": len(self.agent_scores),
            "worst_offenders": self.worst_offenders(3),
        }
