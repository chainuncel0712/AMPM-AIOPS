"""
Baseline Test — 生命週期基準測試
"""


def run_baseline(kernel) -> dict:
    results = []
    checks = [
        ("kernel_import", True),
        ("organs_count", kernel.registry.health()),
        ("brain_alive", hasattr(kernel.brain, "decide")),
        ("memory_alive", hasattr(kernel.memory, "recall")),
        ("tools_alive", hasattr(kernel.tools, "execute")),
    ]
    for name, result in checks:
        status = bool(result) if not isinstance(result, list) else len(result) > 0
        results.append({"check": name, "status": "pass" if status else "fail"})
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    return {"total": total, "passed": passed, "checks": results}
