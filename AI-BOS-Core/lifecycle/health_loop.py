"""
Health Loop — 健康檢查循環
"""
import time


def start_health_loop(kernel, interval: int = 30):
    while True:
        health = kernel.health()
        print(f"[health] {health}")
        time.sleep(interval)
