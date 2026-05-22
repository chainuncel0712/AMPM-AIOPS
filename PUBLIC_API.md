# AMPM-AIOPS Public API Contract

## Principle

AMPM-AIOPS is the **public framework layer**. It may **only** interact with AMPM-KERNEL through defined interfaces.

**Direct internal import of AMPM-KERNEL is strictly prohibited.**

## Allowed Interfaces

### Plugin Interface

```python
class PluginInterface:
    def register(self, name, capabilities)
    def execute(self, action, params)
    def get_capabilities()
```

### SDK Interface

```python
class SDKInterface:
    def query(self, context)
    def submit(self, result)
    def subscribe(self, event, handler)
```

### Event Bus

```python
class EventBus:
    def publish(self, event, data)
    def subscribe(self, event, handler)
    def unsubscribe(self, event, handler)
```

### Lifecycle Interface

```python
class LifecycleInterface:
    def start()
    def stop()
    def health_check()
    def status()
```

## Forbidden Patterns

❌ `from kernel.brain import Cortex` — direct import
❌ `from governance import gatekeeper` — bypassing interface
❌ `import runtime.context` — internal context access
❌ Any `sys.path` manipulation to import Kernel modules

## Enforcement

- CI pipeline **must reject** any PR containing direct imports of Kernel modules.
- Code review **must check** for hidden routing, governance, or context logic.
- All cross-repo communication **must** go through the defined interfaces above.
