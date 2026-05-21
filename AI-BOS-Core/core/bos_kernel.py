"""
AI‑BOS Core Kernel — 核心啟動器
"""
from organs.registry.organ_registry import OrganRegistry
from organs.brain.brain import Brain
from organs.memory.memory_manager import MemoryManager
from organs.memory.base import BaseMemory
from organs.tools.tool_manager import ToolManager


class BOSKernel:
    def __init__(self, memory: BaseMemory = None):
        self.registry = OrganRegistry()
        self.brain = self.registry.register("brain", Brain())
        if memory is not None:
            self.memory = self.registry.register("memory", memory)
        else:
            self.memory = self.registry.register("memory", MemoryManager())
        self.tools = self.registry.register("tools", ToolManager())

    def run(self, input_text: str) -> str:
        context = self.memory.recall(input_text)
        decision = self.brain.decide(input_text, context)
        result = self.tools.execute(decision)
        self.memory.store(input_text, result)
        return result

    def health(self) -> dict:
        return {"organs": self.registry.health(), "alive": True}

    def capabilities(self) -> dict:
        organ_names = [o["name"] for o in self.registry.health()]
        memory_type = type(self.memory).__name__
        return {
            "can_task_planning": True,
            "can_multi_agent": True,
            "can_long_term_memory": "SimpleMemory" in memory_type or "MemoryManager" in memory_type,
            "can_self_heal": False,
            "can_governance": False,
            "can_evolution": False,
            "can_image_generation": False,
            "can_image_recognition": False,
            "installed_organs": organ_names,
            "memory_backend": memory_type,
            "principles": "I do what my organs and tools allow. I don't fake capability.",
        }
