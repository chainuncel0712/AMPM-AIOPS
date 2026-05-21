"""
Basic Agent Example — 快速入門範例
"""
from core.bos_kernel import BOSKernel
from lifecycle.boot import boot
from lifecycle.baseline_test import run_baseline

bos = boot()
report = run_baseline(bos)
print(f"Baseline: {report['passed']}/{report['total']} passed")

response = bos.run("Hello, who are you?")
print(f"Response: {response}")
