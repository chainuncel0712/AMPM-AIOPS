"""
Simple Memory — 簡易記憶器官（免費版）

繼承 BaseMemory，實作 store/recall 與 save/load/clear。
"""
from organs.memory.base import BaseMemory
import re


class SimpleMemory(BaseMemory):
    def __init__(self):
        self.name = "simple_memory"
        self._store = []
        self._state = None

    def store(self, input_text: str, output: str):
        self._store.append({"input": input_text[:200], "output": str(output)[:200]})

    def recall(self, query: str, top_k: int = 3) -> str:
        if not self._store:
            return ""
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored = []
        for entry in self._store:
            text = entry.get("input", "") + " " + entry.get("output", "")
            tokens = re.findall(r"\w+", text.lower())
            score = sum(1 for t in query_tokens if t in tokens)
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        parts = [f"In: {e['input']} → Out: {e['output']}" for _, e in top if _ > 0]
        return "\n".join(parts) if parts else ""

    def save(self, state):
        self._state = state

    def load(self):
        return self._state

    def clear(self):
        self._store.clear()
        self._state = None

    def status(self) -> dict:
        return {"name": self.name, "alive": True, "entries": len(self._store)}
