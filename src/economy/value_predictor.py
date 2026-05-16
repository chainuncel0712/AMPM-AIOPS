"""
ValuePredictor — 事前價值預測引擎
----------------------------------
在執行行動前，預測這次行動的潛在價值。
根據任務類型、過往相似行動的 ROI、成本估算，
決定該用哪層模型、該不該執行。

核心邏輯：
- 低價值任務 → cheap tier, 拒絕不必要的高成本呼叫
- 中價值任務 → normal tier
- 高價值任務 → premium tier, 允許高成本
- 未知任務 → 用 cheap tier 試探
"""
import json
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ValueEstimate:
    task_type: str
    estimated_value: float       # 0.0 ~ 1.0
    recommended_tier: str        # cheap / normal / premium
    max_cost_usd: float
    reasoning: str
    confidence: float            # 0.0 ~ 1.0


class ValuePredictor:
    """
    事前價值預測器

    使用方式：
        pred = ValuePredictor(base_dir)
        result = pred.predict("code_generation", {"language": "python"})
        if result.recommended_tier == "cheap":
            use_cheap_model()
    """

    # 任務類型預設價值
    TASK_VALUE = {
        "simple_reply":      0.1,
        "formatting":        0.05,
        "status_check":      0.15,
        "conversation":      0.3,
        "code_generation":   0.6,
        "debugging":         0.7,
        "analysis":          0.5,
        "architecture":      0.8,
        "security_audit":    0.9,
        "trading_decision":  0.85,
        "research":          0.65,
        "learning":          0.4,
        "social_post":       0.2,
        "market_analysis":   0.55,
        "evolution_decision": 0.9,
        "self_repair":       0.95,
        "emergency":         1.0,
    }

    # 每個 tier 的成本上限
    TIER_COST_CAP = {
        "cheap":   0.001,
        "normal":  0.01,
        "premium": 0.10,
    }

    def __init__(self, base_dir: Optional[Path] = None,
                 roi_analyzer=None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.history_file = self.base_dir / "data" / "economy" / "value_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.roi_analyzer = roi_analyzer
        self.prediction_history: List[Dict] = []
        self._load()

    def _load(self):
        if self.history_file.exists():
            try:
                self.prediction_history = json.loads(self.history_file.read_text())
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.history_file.write_text(
                json.dumps(self.prediction_history[-5000:], ensure_ascii=False, indent=2))

    def predict(self, task_type: str, context: Dict[str, Any] = None) -> ValueEstimate:
        """
        預測任務價值與建議 tier。
        """
        base_value = self.TASK_VALUE.get(task_type, 0.3)

        # 根據 context 調整價值
        modifier = 1.0
        context = context or {}
        reasons = []

        if context.get("urgency") == "high":
            modifier += 0.2
            reasons.append("高緊急度 +0.2")
        if context.get("user_is_admin"):
            modifier += 0.15
            reasons.append("管理員 +0.15")
        if context.get("retry_count", 0) > 2:
            modifier -= 0.1
            reasons.append("多次重試 -0.1")
        if context.get("is_critical_path"):
            modifier += 0.3
            reasons.append("關鍵路徑 +0.3")
        if task_type in ("evolution_decision", "self_repair"):
            modifier += 0.15
            reasons.append("核心生存 +0.15")

        adjusted_value = min(1.0, max(0.01, base_value * modifier))

        # 根據過往 ROI 調整
        if self.roi_analyzer:
            roi = self.roi_analyzer.get_roi_score(task_type, days=30)
            if roi.get("sample_size", 0) >= 3:
                roi_factor = roi["roi_score"]
                if roi_factor < 0.3:
                    adjusted_value *= 0.5
                    reasons.append(f"過往 ROI 低 ({roi_factor:.2f}) -50%")
                elif roi_factor > 0.7:
                    adjusted_value = min(1.0, adjusted_value * 1.2)
                    reasons.append(f"過往 ROI 高 ({roi_factor:.2f}) +20%")

        # 決定 tier
        if adjusted_value < 0.3:
            tier = "cheap"
        elif adjusted_value < 0.6:
            tier = "normal"
        else:
            tier = "premium"

        max_cost = self.TIER_COST_CAP[tier]
        confidence = 0.5 + (adjusted_value * 0.4)

        estimate = ValueEstimate(
            task_type=task_type,
            estimated_value=round(adjusted_value, 4),
            recommended_tier=tier,
            max_cost_usd=max_cost,
            reasoning="; ".join(reasons) or f"基準值 {base_value:.2f}",
            confidence=round(confidence, 4),
        )

        self.prediction_history.append({
            "task_type": task_type,
            "estimated_value": estimate.estimated_value,
            "tier": estimate.recommended_tier,
            "confidence": estimate.confidence,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

        return estimate

    def should_use_premium(self, task_type: str,
                           context: Dict[str, Any] = None) -> bool:
        est = self.predict(task_type, context)
        return est.recommended_tier == "premium"

    def get_recent_predictions(self, n: int = 20) -> List[Dict]:
        return self.prediction_history[-n:]

    def get_tier_distribution(self, days: int = 7) -> Dict[str, int]:
        cutoff = datetime.now() - timedelta(days=days)
        dist = defaultdict(int)
        for p in self.prediction_history:
            try:
                ts = datetime.fromisoformat(p["timestamp"])
            except Exception:
                continue
            if ts >= cutoff:
                dist[p.get("tier", "cheap")] += 1
        return dict(dist)

    def status(self) -> dict:
        return {
            "name": "ValuePredictor",
            "total_predictions": len(self.prediction_history),
            "tier_distribution": self.get_tier_distribution(),
        }
