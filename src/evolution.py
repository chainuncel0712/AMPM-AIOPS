#!/usr/bin/env python3
"""
成長進化系統 — 橋接到 EvolutionCycleOrgan
evolution.py 的 Evolution 類別已合併至 core/evolution_cycle.py。
保留此檔案作為向後相容匯入點。
"""

from core.evolution_cycle import EvolutionCycleOrgan as Evolution

__all__ = ["Evolution"]
