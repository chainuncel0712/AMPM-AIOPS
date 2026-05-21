#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑曜大腦 — 中央處理單元
========================
Re-export layer for refactored modules:
  - Obsidian        → brain/obsidian.py
  - OrganRegistry   → brain/organ_registry.py
  - run_agent_executor → brain/agent_executor.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain.obsidian import Obsidian
from brain.organ_registry import OrganRegistry
from brain.agent_executor import run_agent_executor
