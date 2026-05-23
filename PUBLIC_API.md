<p align="center"><img src="assets/300.png" width="180"></p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">AMPM-AIOPS Public API Contract</h1>

<h2 align="center" style="color:#58a6ff;">Principle</h2>

<p align="center" style="color:#c9d1d9;">
AMPM-AIOPS is the <strong>public framework layer</strong>. It may <strong>only</strong> interact with AMPM-KERNEL through defined interfaces.
</p>

<p align="center" style="color:#e94560; font-weight:bold;">
Direct internal import of AMPM-KERNEL is strictly prohibited.
</p>

<h2 align="center" style="color:#58a6ff;">Allowed Interfaces</h2>

<h3 style="color:#e94560;">Plugin Interface</h3>

```python
class PluginInterface:
    def register(self, name, capabilities)
    def execute(self, action, params)
    def get_capabilities()
```

<h3 style="color:#e94560;">SDK Interface</h3>

```python
class SDKInterface:
    def query(self, context)
    def submit(self, result)
    def subscribe(self, event, handler)
```

<h3 style="color:#e94560;">Event Bus</h3>

```python
class EventBus:
    def publish(self, event, data)
    def subscribe(self, event, handler)
    def unsubscribe(self, event, handler)
```

<h3 style="color:#e94560;">Lifecycle Interface</h3>

```python
class LifecycleInterface:
    def start()
    def stop()
    def health_check()
    def status()
```

<h2 align="center" style="color:#58a6ff;">Forbidden Patterns</h2>

❌ `from kernel.brain import Cortex` — direct import
❌ `from governance import gatekeeper` — bypassing interface
❌ `import runtime.context` — internal context access
❌ Any `sys.path` manipulation to import Kernel modules

<h2 align="center" style="color:#58a6ff;">Enforcement</h2>

- CI pipeline **must reject** any PR containing direct imports of Kernel modules.
- Code review **must check** for hidden routing, governance, or context logic.
- All cross-repo communication **must** go through the defined interfaces above.

<br>
<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
