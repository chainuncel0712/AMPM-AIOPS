"""
Executor 基底類別
====================
"""
from abc import ABC, abstractmethod


class Executor(ABC):
    @abstractmethod
    def execute(self, task: str) -> str:
        ...
