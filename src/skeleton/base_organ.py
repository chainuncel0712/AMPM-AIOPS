"""
BaseOrgan v2 — 支援資源治理的器官基底
======================================
新增：睡眠/喚醒、記憶體估算、資源預算感知
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseOrgan(ABC):
    def __init__(self, name: str):
        self.name = name
        self._alive = True
        self._asleep = False       # 是否休眠（釋放了重資源）
        self._wake_count = 0       # 喚醒次數
        self._sleep_count = 0      # 休眠次數
        self._mem_estimate_mb = 0  # 估計記憶體用量 (MB)

    def report_issue(self, issue_type: str, detail: str = ""):
        """器官自治投票：報告問題給 repair_engine。"""
        try:
            from core.repair_engine import report_issue as _ri
            _ri(self.__class__.__name__, issue_type, detail)
        except Exception:
            pass

    @abstractmethod
    def status(self) -> dict:
        pass

    def is_alive(self) -> bool:
        return self._alive

    def enable(self):
        self._alive = True

    def disable(self):
        self._alive = False

    # ── 資源治理 ──

    def sleep(self):
        """休眠：釋放可重建資源（cache、buffer、history）"""
        if not self._asleep:
            self._asleep = True
            self._sleep_count += 1
            self._on_sleep()

    def wake(self):
        """喚醒：重新載入必要資源"""
        if self._asleep:
            self._asleep = False
            self._wake_count += 1
            self._on_wake()

    def is_asleep(self) -> bool:
        return self._asleep

    def memory_estimate_mb(self) -> int:
        """估計當前記憶體用量 (MB)，子類應覆蓋"""
        return self._mem_estimate_mb

    def set_memory_estimate(self, mb: int):
        self._mem_estimate_mb = mb

    def _on_sleep(self):
        """子類覆蓋：休眠時額外清理"""
        pass

    def _on_wake(self):
        """子類覆蓋：喚醒時重新初始化"""
        pass

    def resource_status(self) -> dict:
        return {
            "name": self.name,
            "alive": self._alive,
            "asleep": self._asleep,
            "wake_count": self._wake_count,
            "sleep_count": self._sleep_count,
            "mem_estimate_mb": self.memory_estimate_mb(),
        }
