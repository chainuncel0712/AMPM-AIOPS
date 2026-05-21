"""
AI‑BOS Core Demo — 一鍵啟動展示

Usage:
    python -m ai_bos_core.demo
"""
from ai_bos_core import boot, run_baseline, BOSKernel


def show_capabilities(bos):
    caps = bos.capabilities()
    print("  ┌─ Capabilities ────────────────────────────┐")
    checks = [
        ("Task Planning", caps["can_task_planning"]),
        ("Multi-Agent", caps["can_multi_agent"]),
        ("Long-Term Memory", caps["can_long_term_memory"]),
        ("Self-Heal", caps["can_self_heal"]),
        ("Governance", caps["can_governance"]),
        ("Evolution", caps["can_evolution"]),
        ("Image Generation", caps["can_image_generation"]),
        ("Image Recognition", caps["can_image_recognition"]),
    ]
    for label, ok in checks:
        icon = "✅" if ok else "❌"
        print(f"  │ {icon} {label:<20} │")
    print("  └──────────────────────────────────────────┘")
    print(f"  Organs: {caps['installed_organs']}")
    print(f"  Memory: {caps['memory_backend']}")
    print(f"  Principle: {caps['principles']}")


def main():
    import importlib.metadata
    try:
        ver = importlib.metadata.version("ai-bos-core")
    except Exception:
        ver = "1.0.0"

    print("=" * 52)
    print(f"  AI‑BOS Core v{ver} — Developer Toolkit Demo")
    print("=" * 52)

    bos = boot()

    report = run_baseline(bos)
    print(f"\n  Baseline: {report['passed']}/{report['total']} passed\n")

    inputs = [
        "Hello, what is AI-BOS?",
        "Can you remember what I just asked?",
    ]
    for text in inputs:
        print(f"  >>> {text}")
        reply = bos.run(text)
        print(f"  <<< {reply}\n")

    print(f"  Memory entries: {bos.memory.status()['entries']}")
    print()
    show_capabilities(bos)
    print()
    print("=" * 52)
    print("  ✅ Demo complete. Install: pip install ai-bos-core")
    print("  📖 docs/capabilities.md for full self-report")
    print("=" * 52)


if __name__ == "__main__":
    main()
