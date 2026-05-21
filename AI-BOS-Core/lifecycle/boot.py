"""
Boot — 系統啟動流程
"""
from core.bos_kernel import BOSKernel


def boot() -> BOSKernel:
    bos = BOSKernel()
    print(f"[boot] AI-BOS Core v1.0.0 — {bos.registry.health()}")
    return bos
