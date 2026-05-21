# AI‑BOS Organ System

## Registered Organs

| Organ | File | Function |
|-------|------|----------|
| Brain | `organs/brain/brain.py` | Decision making |
| Memory | `organs/memory/memory_manager.py` | Recall and store |
| Tools | `organs/tools/tool_manager.py` | External actions |
| Registry | `organs/registry/organ_registry.py` | Dynamic loading |

## Creating a New Organ

```python
class MyOrgan:
    def __init__(self):
        self.name = "my_organ"

    def status(self) -> dict:
        return {"name": self.name, "alive": True}
```

Register it:

```python
kernel.registry.register("my_organ", MyOrgan())
```
