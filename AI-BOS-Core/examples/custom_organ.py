"""
Custom Organ Example — 建立自訂器官

This example shows how to create and register a custom organ.
"""
from ai_bos_core import BOSKernel


class LoggerOrgan:
    """A custom organ that logs every interaction."""

    def __init__(self):
        self.name = "logger"
        self.log = []

    def record(self, role: str, message: str):
        self.log.append({"role": role, "message": message})

    def status(self) -> dict:
        return {"name": self.name, "alive": True, "logs": len(self.log)}


bos = BOSKernel()
logger = bos.registry.register("logger", LoggerOrgan())

for msg in ["Hello", "How are you?", "Goodbye"]:
    logger.record("user", msg)
    reply = bos.run(msg)
    logger.record("bot", reply)

print("Interaction log:")
for entry in logger.log:
    print(f"  [{entry['role']}] {entry['message']}")

report = bos.registry.health()
print(f"\nOrgan health: {report}")
