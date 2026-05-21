"""
Base Memory — 記憶抽象介面
"""


class BaseMemory:
    """所有記憶器官的基底類別。實作自訂記憶器官時請繼承此類。"""

    def save(self, state):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def store(self, input_text: str, output: str):
        raise NotImplementedError

    def recall(self, query: str) -> str:
        raise NotImplementedError

    def status(self) -> dict:
        return {"name": "base_memory", "alive": True}
