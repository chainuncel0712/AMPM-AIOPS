<p align="center"><img src="assets/300.png" width="180"></p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">AMPM Repo Split Report</h1>

<h2 align="center" style="color:#58a6ff;">Summary</h2>

<p align="center" style="color:#c9d1d9;">
The original AMPM-AIOPS monorepo has been split into:
</p>

- **AMPM-AIOPS** (public) — AI OS Public Framework
- **AMPM-KERNEL** (private) — True AI Brain

<h2 align="center" style="color:#58a6ff;">Moved to AMPM-KERNEL</h2>

<h3 style="color:#e94560;">Source Code</h3>

| Path | Reason |
|------|--------|
| `src/brain/` | Decision hub: Cortex, Thalamus, Hypothalamus, Insula, etc. |
| `src/governance/` | Permission engine, firewall, execution policies, authority control |
| `src/runtime/` | Execution environment, context assembly, decision authority |
| `src/core/` | Agent intelligence, auto learning, feedback loops |
| `src/agents.py` | Multi-agent system control |
| `src/llm.py` | Multi-layer LLM routing (Ollama/OpenRouter/DeepSeek) |
| `src/memory.py` | Memory system |
| `src/memory_vector.py` | Vector memory |
| `src/models.py` | Data model definitions |
| `src/executor.py` | Execution engine |
| `src/handler.py` | Event handler |
| `src/breath.py` | Throttle/regulator |
| `src/nose.py` | Input filter |
| `src/decisions/` | Decision flow, priority, orchestration |
| `src/evolution/` | Adaptive logic, self optimization |
| `src/civilization_controller.py` | Multi-agent coordination, orchestration |
| `src/evolution_module.py` | Growth/optimization logic |
| `src/config.py` (private parts) | Provider priorities, routing config, fallback config |

<h3 style="color:#e94560;">Kernel-Only Directories (entirely private)</h3>

```
src/brain/
src/governance/
src/runtime/
src/core/
src/evolution/
src/decisions/
```

<h2 align="center" style="color:#58a6ff;">Retained in AMPM-AIOPS</h2>

<h3 style="color:#2ea043;">Public Framework</h3>

| Path | Purpose |
|------|---------|
| `src/dashboard/` | Lite monitoring UI |
| `src/monitor.py` | Lite monitoring (no decision logic) |
| `src/config.py` (public parts) | Basic UI config, public settings |
| `src/tools.py` (interface only) | Tool interface & public decorators |
| `src/tool_decorators/` | Public tool decorators |
| `src/skeleton/` | Framework scaffold (public) |
| `assets/` | Static resources |
| `scripts/` | Install/setup scripts |
| `docs/` | Public documentation |
| `*.md` | Public documentation |
| `bot.py` | Bot interface (public) |

<h2 align="center" style="color:#58a6ff;">Forbidden in Public Repo</h2>

<p style="color:#c9d1d9;">
The following must <strong>never</strong> be added to AMPM-AIOPS:
</p>

- ❌ Routing logic
- ❌ Context ranking/weighting
- ❌ Governance rules/permissions
- ❌ Memory ranking
- ❌ Evolution/self-optimization logic
- ❌ Orchestration intelligence
- ❌ Provider strategy
- ❌ Decision authority

<h2 align="center" style="color:#58a6ff;">Plugin Restrictions</h2>

<p style="color:#c9d1d9;">
All plugins loaded into AMPM-AIOPS are permanently forbidden from:
</p>

- Modifying routing
- Modifying governance
- Modifying context policy
- Modifying memory ranking
- Modifying permissions
- Modifying runtime authority

<p style="color:#c9d1d9;">
Plugins may only: provide capabilities, return results, provide context candidates (no authority).
</p>

<h2 align="center" style="color:#58a6ff;">API Contract</h2>

<p style="color:#c9d1d9;">
AMPM-AIOPS ↔ AMPM-KERNEL communication is limited to:
</p>

```
Plugin Interface  →  register / execute / get_capabilities
SDK Interface     →  query / submit / subscribe
Event Bus         →  publish / subscribe / unsubscribe
Lifecycle         →  start / stop / health_check
```

<p align="center" style="color:#e94560; font-weight:bold;">
Direct internal imports are strictly prohibited.
</p>

<h2 align="center" style="color:#58a6ff;">Date</h2>

<p align="center" style="color:#c9d1d9;">
Split executed: 2026-05-23
</p>

<br>
<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
