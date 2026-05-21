# AI‑BOS Core

**AI Biological Operating System — Developer Toolkit**

A biologically‑inspired framework for building modular AI agents.

## Quick Start

```bash
pip install ai-bos-core
```

```python
from ai_bos_core import BOSKernel

bos = BOSKernel()
response = bos.run("Hello!")
print(response)
```

## One‑Command Demo

```bash
python -m ai_bos_core
```

## Architecture

```
core/       — Kernel, Config, Context
organs/     — Brain, Memory, Tools, Registry
lifecycle/  — Boot, Baseline Test, Health Loop
executor/   — Orchestrator, Reflect, Repair, Evolve
```

## Pluggable Memory

Swap memory implementations at boot:

```python
from ai_bos_core import BOSKernel, SimpleMemory

bos = BOSKernel(memory=SimpleMemory())
bos.run("Hello")
```

Create your own:

```python
from ai_bos_core import BaseMemory

class VectorMemory(BaseMemory):
    def store(self, text, output):
        ...
    def recall(self, query):
        ...
    def save(self, state):
        ...
    def load(self):
        ...
    def clear(self):
        ...
```

See `examples/pluggable_memory.py` for a full demo.

## Creating a Custom Organ

```python
from ai_bos_core import BOSKernel

class MyOrgan:
    def __init__(self):
        self.name = "my_organ"
    def status(self):
        return {"name": self.name, "alive": True}

bos = BOSKernel()
bos.registry.register("my_organ", MyOrgan())
```

## For Developers

```bash
git clone https://github.com/chainuncel0712/AI-BOS-Core.git
cd AI-BOS-Core
pip install -e .
pytest -v
```

## License

AGPL‑3.0 + Additional Restrictions. Commercial use requires a license.

## Commercial Edition

Immune System · Governance Layer · Evolution Engine · Civilization Memory
→ chainuncel0712@gmail.com
