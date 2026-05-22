# AMPM Repo Split Report

## Summary

The original AMPM-AIOPS monorepo has been split into:
- **AMPM-AIOPS** (public) — AI OS Public Framework
- **AMPM-KERNEL** (private) — True AI Brain

## Moved to AMPM-KERNEL

### Source Code

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

### Kernel-Only Directories (entirely private)

```
src/brain/
src/governance/
src/runtime/
src/core/
src/evolution/
src/decisions/
```

## Retained in AMPM-AIOPS

### Public Framework

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

## Forbidden in Public Repo

The following must **never** be added to AMPM-AIOPS:

- ❌ Routing logic
- ❌ Context ranking/weighting
- ❌ Governance rules/permissions
- ❌ Memory ranking
- ❌ Evolution/self-optimization logic
- ❌ Orchestration intelligence
- ❌ Provider strategy
- ❌ Decision authority

## Plugin Restrictions

All plugins loaded into AMPM-AIOPS are permanently forbidden from:
- Modifying routing
- Modifying governance
- Modifying context policy
- Modifying memory ranking
- Modifying permissions
- Modifying runtime authority

Plugins may only: provide capabilities, return results, provide context candidates (no authority).

## API Contract

AMPM-AIOPS ↔ AMPM-KERNEL communication is limited to:

```
Plugin Interface  →  register / execute / get_capabilities
SDK Interface     →  query / submit / subscribe
Event Bus         →  publish / subscribe / unsubscribe
Lifecycle         →  start / stop / health_check
```

Direct internal imports are strictly prohibited.

## Date

Split executed: 2026-05-23
