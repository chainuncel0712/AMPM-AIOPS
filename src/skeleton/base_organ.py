"""所有器官的祖宗 - 每个器官都继承这个"""
from abc import ABC, abstractmethod

class BaseOrgan(ABC):
    def __init__(self, name: str):
        self.name = name
        self._alive = True

    @abstractmethod
    def status(self) -> dict:
        """回报器官状态 - 每个器官必须实作"""
        pass

    def is_alive(self) -> bool:
        return self._alive

    def enable(self): self._alive = True
    def disable(self): self._alive = False
