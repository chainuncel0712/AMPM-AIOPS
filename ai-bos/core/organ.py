"""
Organ 介面 — 所有器官必須實作的抽象類別
===========================================
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Organ(ABC):
    """器官基底類別 — 每個器官都是一個獨立的生命組件"""

    def __init__(self, name: str):
        self.name = name
        self._alive = True
        self._asleep = False

    @abstractmethod
    def status(self) -> Dict:
        """回傳器官當前狀態"""
        ...

    def is_alive(self) -> bool:
        return self._alive

    def enable(self):
        self._alive = True

    def disable(self):
        self._alive = False

    def sleep(self):
        self._asleep = True

    def wake(self):
        self._asleep = False

    def is_asleep(self) -> bool:
        return self._asleep
