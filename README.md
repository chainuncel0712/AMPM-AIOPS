# AMPM-AIOPS Public Framework

This repository serves as the public-facing framework and ecosystem hub for the AMPM AI Operating System.

## 📍 Positioning

AMPM-AIOPS is the **public framework** layer, responsible for:
- SDKs and plugin interfaces
- Public APIs and documentation
- Example agents and dashboards
- Ecosystem growth and community contributions

## 🔒 Core Intelligence Location

The true AI decision intelligence (routing, context control, governance, evolution, orchestration intelligence) resides in the private kernel repository:
**AMPM-KEL**

This separation ensures that the core intellectual property remains protected while enabling open ecosystem development.

## 📁 Directory Structure

- `assets/` - Public static resources (icons, banners, etc.)
- `scripts/` - Public utility scripts (installation, setup, etc.)
- `docs/` - Public documentation and guides
- `examples/` - Example agents and workflows
- `dashboard/` - Lite monitoring and runtime UI (public-facing)
- `OPS` - Public operations scripts

## 🔗 Integration with AMPM-KEL

Public components interact with the private kernel strictly through well-defined interfaces:
- Plugin Interface
- SDK Interface
- Event Bus Interface
- Lifecycle Interface

Direct internal imports of AMPM-KEL components are strictly prohibited.

## 🛡️ Security Boundary

To maintain the integrity of the AI brain:
- Plugins cannot modify routing, governance, context policies, or memory ranking
- SDKs provide only public-facing capabilities
- Dashboard components are read-only monitoring tools
- All decision-making authority remains within AMPM-KEL

---
*Last updated: $(date +%Y-%m-%d)*
