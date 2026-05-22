# AMPM-KERNEL Architecture

## Kernel Boundary

AMPM-KERNEL is the **private AI Brain repository**. It contains all core decision intelligence that must never be exposed in public repositories.

### What Kernel Owns

| Domain | Contents |
|--------|----------|
| **Routing** | Router, Model Selector, Provider Balancing, Fallback Logic, Priority Logic, Lock Manager |
| **Context Authority** | Context Assembler, Memory Ranking, Memory Weighting, Persona Merge, Prompt Composition, Context Compression |
| **Governance** | Permission Engine, Capability Firewall, Execution Policies, Authority Control, Sandbox Rules |
| **Evolution** | Self Reflection, Adaptive Routing, Optimization Logic, Scoring Engine, Runtime Learning |
| **Runtime Intelligence** | Internal Orchestration, Retry Intelligence, Runtime Policies, Decision Authority, Provider Strategy |

### Source Directories (moved from AMPM-AIOPS)

```
src/brain/          — Cortex, Thalamus, Insula, Memory Engine (decision hub)
src/governance/     — Permission control, firewall, execution policies
src/runtime/        — Execution environment, decision authority, provider strategy
src/core/           — Agent intelligence, auto learning, feedback learning
src/agents.py       — Multi-agent system control
src/llm.py          — Multi-layer LLM routing (Ollama/OpenRouter/DeepSeek)
src/memory.py       — Memory system
src/memory_vector.py — Vector memory
src/models.py       — Data model definitions
src/executor.py     — Execution engine
src/handler.py      — Event handler
src/breath.py       — Throttle regulator
src/nose.py         — Input filter
src/decisions/      — Decision flow, priority, orchestration
src/evolution/      — Adaptive logic, self optimization, runtime learning
top-level OPS       — Operations scripts (private)
```

## Authority Rules

1. **Only AMPM-KERNEL** holds routing, context, governance, and evolution authority.
2. **Plugins, SDK, Dashboard must never** hold decision authority.
3. **No direct internal import** from public repos into Kernel.
4. All cross-repo communication goes through defined **Public API interfaces**.

## Public API Contract

AMPM-AIOPS (public) interacts with AMPM-KERNEL (private) strictly through:

| Interface | Description |
|-----------|-------------|
| `Plugin Interface` | Plugin registration, capability exposure, result return |
| `SDK Interface` | Public SDK methods for ecosystem developers |
| `Event Bus` | Async event publishing/subscription |
| `Lifecycle Interface` | Start/stop/health check |

Direct internal imports of AMPM-KERNEL components are **strictly prohibited**.
