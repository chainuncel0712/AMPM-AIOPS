#!/usr/bin/env python3
"""
成長進化系統 — 橋接到 EvolutionCycleOrgan
evolution.py 的 Evolution 類別已合併至 core/evolution_cycle.py。
保留此檔案作為向後相容匯入點。
"""

from core.evolution_cycle import EvolutionCycleOrgan as _Evolution

class Evolution(_Evolution):
    def __init__(self, *args, **kwargs):
        kwargs.pop("agents", None)
        kwargs.pop("call_ai_func", None)
        super().__init__(*args, **kwargs)

__all__ = ["Evolution"]
