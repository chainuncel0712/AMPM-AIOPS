"""
Pluggable Memory Demo — 可插拔記憶器官展示

Shows how to swap memory implementations at kernel boot.
"""
from ai_bos_core import BOSKernel, run_baseline
from organs.memory.simple_memory import SimpleMemory

bos = BOSKernel(memory=SimpleMemory())
report = run_baseline(bos)
print(f"Baseline: {report['passed']}/{report['total']} passed")

bos.memory.store("What is AI-BOS?", "A biological operating system for AI agents")
bos.memory.store("How do organs work?", "Each organ is an independent module")

ctx = bos.memory.recall("organs")
print(f"\nRecall 'organs':\n{ctx}")

bos.memory.save({"version": "1.0.0"})
print(f"\nSaved state: {bos.memory.load()}")

bos.memory.clear()
print(f"Cleared. Entries: {bos.memory.status()['entries']}")
