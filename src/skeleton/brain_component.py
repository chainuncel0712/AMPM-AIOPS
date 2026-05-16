"""BrainComponent — AI Agent 器官基底類別，提供生命週期與狀態管理。"""

from abc import ABC, abstractmethod


class BrainComponent(ABC):
    """所有 AI Agent 器官的抽象基底類別。"""

    def __init__(self, dna: dict | None = None):
        self._state: dict = {}
        self._dna: dict | None = dna

    @abstractmethod
    def status(self) -> dict:
        """回傳器官當前狀態。"""
        ...

    def on_startup(self) -> None:
        """器官啟動時的回呼。"""

    def on_shutdown(self) -> None:
        """器官關閉時的回呼。"""
