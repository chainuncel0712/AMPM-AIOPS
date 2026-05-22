# AMPM-AIOPS Public Framework / AMPM-AIOPS 公開框架

## English

This repository serves as the public-facing framework and ecosystem hub for the AMPM AI Operating System.

### 📍 Positioning

AMPM-AIOPS is the **public framework** layer, responsible for:
- SDKs and plugin interfaces
- Public APIs and documentation
- Example agents and dashboards
- Ecosystem growth and community contributions

### 🔒 Core Intelligence Location

The true AI decision intelligence (routing, context control, governance, evolution, orchestration intelligence) resides in the private kernel repository:
**AMPM-KEL**

This separation ensures that the core intellectual property remains protected while enabling open ecosystem development.

### 📁 Directory Structure

- `assets/` - Public static resources (icons, banners, etc.)
- `scripts/` - Public utility scripts (installation, setup, etc.)
- `docs/` - Public documentation and guides
- `examples/` - Example agents and workflows
- `dashboard/` - Lite monitoring and runtime UI (public-facing)
- `OPS` - Public operations scripts

### 🔗 Integration with AMPM-KEL

Public components interact with the private kernel strictly through well-defined interfaces:
- Plugin Interface
- SDK Interface
- Event Bus Interface
- Lifecycle Interface

Direct internal imports of AMPM-KEL components are strictly prohibited.

### 🛡️ Security Boundary

To maintain the integrity of the AI brain:
- Plugins cannot modify routing, governance, context policies, or memory ranking
- SDKs provide only public-facing capabilities
- Dashboard components are read-only monitoring tools
- All decision-making authority remains within AMPM-KEL

---

## 中文

此倉庫作為 AMPM AI 作業系統的公開框架和生態系統中心。

### 📍 定位

AMPM-AIOPS 是 **公開框架** 層，負責：
- SDK 和插件介面
- 公開 API 和文件
- 範例代理和儀表板
- 生態系統成長和社群貢獻

### 🔒 核心智慧位置

真正的 AI 決策智慧（路由、上下文控制、治理、演化、協調智慧）位於私有內核倉庫：
**AMPM-KEL**

這種分離確保了核心智慧財產受到保護，同時實現開放的生態系統開發。

### 📁 目錄結構

- `assets/` - 公開靜態資源（圖標、橫幅等）
- `scripts/` - 公開工具腳本（安裝、設置等）
- `docs/` - 公開文件和指南
- `examples/` - 範例代理和工作流程
- `dashboard/` - 輕量監控和運行時 UI（公開面向）
- `OPS` - 公開運維腳本

### 🔗 與 AMPM-KEL 的整合

公開組件嚴格通過明確定義的介面與私有內核互動：
- 插件介面
- SDK 介面
- 事件總線介面
- 生命週期介面

嚴格禁止直接導入 AMPM-KEL 內部組件。

### 🛡️ 安全邊界

為維護 AI 大腦的完整性：
- 插件不能修改路由、治理、上下文政策或記憶排名
- SDK 僅提供面向公眾的能力
- 儀表板組件是唯讀監控工具
- 所有決策權限都保留在 AMPM-KEL 內

---
*Last updated: $(date +%Y-%m-%d) / 最近更新：$(date +%Y-%m-%d)*
