<p align="center"><img src="assets/300.png" width="180"></p>

<p align="center">
  <img src="assets/0066.png" alt="AMPM Architecture Diagram" width="720">
</p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">
AMPM AI Operating System<br>
<span style="color:#58a6ff; font-size:0.6em;">Architecture Direction & Repository Refactor</span>
</h1>
<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px; margin-top:-10px;">
AMPM AI 作業系統<br>
<span style="color:#58a6ff; font-size:0.6em;">架構方向與倉庫重構規範</span>
</h1>

<br>

---

<h2 align="center" style="color:#58a6ff;">1. Project Positioning · 專案定位</h2>

<p align="center" style="color:#c9d1d9;">
AMPM is no longer a standard bot framework or automation project.<br>
The system has evolved into an experimental <strong style="color:#e94560;">AI Operating System</strong> architecture.
</p>
<p align="center" style="color:#c9d1d9;">
AMPM 不再是標準的機器人框架或自動化專案。<br>
系統已進化為實驗性的 <strong style="color:#e94560;">AI 作業系統</strong>架構。
</p>

<br>

<p align="center" style="color:#c9d1d9;">
<strong>Focused on · 專注於：</strong><br>
Orchestration · Runtime Intelligence · Governance · Memory Systems<br>
Multi-Agent Coordination · Autonomous Infrastructure
</p>

<br>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">The objective is not to build another chatbot.</strong><br>
The objective is to build an AI runtime environment capable of coordinating:<br>
models · memory · tools · execution · permissions · lifecycle · adaptive behavior<br>
under a unified orchestration system.
</p>
<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">目標不是建立另一個聊天機器人。</strong><br>
目標是建立一個 AI 執行環境，能夠在統一協調系統下<br>
協調模型、記憶、工具、執行、權限、生命週期、自適應行為。
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">2. Core Philosophy · 核心哲學</h2>

<p align="center" style="color:#c9d1d9;">
Modern AI systems are fragmented.<br>
Models, memory, tools, agents, and execution layers typically operate independently<br>
with minimal governance or orchestration.
</p>
<p align="center" style="color:#c9d1d9;">
現代 AI 系統是破碎的。<br>
模型、記憶、工具、代理和執行層通常各自獨立運作，<br>
幾乎沒有治理或協調。
</p>

<br>

<p align="center" style="color:#c9d1d9;">
AMPM explores a different architecture:<br>
<strong style="color:#e94560;">An AI Operating System</strong> where:
</p>
<p align="center" style="color:#c9d1d9;">
AMPM 探索不同的架構：<br>
<strong style="color:#e94560;">AI 作業系統</strong>，其中：
</p>

<p align="center" style="color:#c9d1d9;">
✅ Orchestration is centralized · 協調集中化<br>
✅ Authority is controlled · 權限受控<br>
✅ Execution is sandboxed · 執行沙箱化<br>
✅ Memory is structured · 記憶結構化<br>
✅ Runtime behavior is governed · 執行行為受治理<br>
✅ Plugins remain isolated from kernel authority · 插件隔離於核心權限之外
</p>

<br>

<p align="center" style="color:#c9d1d9;">
<strong>The system must be designed as infrastructure, not as a monolithic chatbot.</strong>
</p>
<p align="center" style="color:#c9d1d9;">
<strong>系統必須設計為基礎設施，而不是單體聊天機器人。</strong>
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">3. Repository Segmentation · 倉庫分割</h2>

<p align="center" style="color:#c9d1d9;">
The project must now be separated into:<br>
Public Ecosystem Layer · Private Kernel Layer · Modular Public Subsystems
</p>
<p align="center" style="color:#c9d1d9;">
專案現在必須拆分為：<br>
公開生態層 · 私有核心層 · 模組化公開子系統
</p>

<br>

<h3 align="center" style="color:#2ea043;">Mandatory for · 必須拆分以確保：</h3>

<p align="center" style="color:#c9d1d9;">
Maintainability · 可維護性<br>
Authority Isolation · 權限隔離<br>
IP Protection · 智慧財產保護<br>
Ecosystem Scalability · 生態系統可擴展性<br>
Governance Enforcement · 治理執行
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">4. Public Ecosystem · 公開生態</h2>

<h3 align="center" style="color:#e94560;">Repository · 倉庫</h3>
<p align="center" style="color:#c9d1d9; font-size:1.1em;">
<code style="background:#1a1a2e; color:#e94560; padding:4px 16px; border-radius:4px;">AMPM-AIOPS</code>
</p>

<h3 align="center" style="color:#2ea043;">Purpose · 目的</h3>
<p align="center" style="color:#c9d1d9;">Public AI OS ecosystem framework · 公開 AI 作業系統生態框架</p>

<br>

<h3 align="center" style="color:#2ea043;">Responsibilities · 職責</h3>

<h4 align="center" style="color:#58a6ff;">Framework Layer · 框架層</h4>
<p align="center" style="color:#c9d1d9;">
SDK interfaces · SDK 介面<br>
Plugin interfaces · 插件介面<br>
Lifecycle system · 生命週期系統<br>
Event bus · 事件總線<br>
Callback flow · 回呼流程<br>
Logging · 日誌<br>
Monitoring lite · 輕量監控
</p>

<h4 align="center" style="color:#58a6ff;">Ecosystem Layer · 生態層</h4>
<p align="center" style="color:#c9d1d9;">
Plugins · 插件<br>
Adapters · 適配器<br>
Integrations · 整合<br>
Public tools · 公開工具<br>
Example agents · 範例代理<br>
Templates · 模板
</p>

<h4 align="center" style="color:#58a6ff;">Documentation Layer · 文件層</h4>
<p align="center" style="color:#c9d1d9;">
Architecture docs · 架構文件<br>
Tutorials · 教學<br>
Onboarding · 入門引導<br>
Diagrams · 圖表<br>
Public API contracts · 公開 API 合約
</p>

<h4 align="center" style="color:#58a6ff;">UI Layer · UI 層</h4>
<p align="center" style="color:#c9d1d9;">
Dashboard lite · 輕量儀表板<br>
Runtime visualization · 執行視覺化<br>
Monitoring UI · 監控介面
</p>

<br>

<h3 align="center" style="color:#e94560;">Public Repository Restrictions · 公開倉庫限制</h3>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">The public repository must never contain:</strong><br>
<strong style="color:#e94560;">公開倉庫永遠不能包含：</strong>
</p>

<p align="center" style="color:#c9d1d9;">
❌ Routing intelligence · 路由智慧<br>
❌ Orchestration logic · 協調邏輯<br>
❌ Governance rules · 治理規則<br>
❌ Capability enforcement · 能力執行<br>
❌ Memory weighting · 記憶權重<br>
❌ Provider strategy · 提供商策略<br>
❌ Adaptive optimization · 自適應優化<br>
❌ Runtime authority · 執行權限<br>
❌ Hidden orchestration hooks · 隱藏協調鉤子<br>
❌ Internal scoring systems · 內部評分系統
</p>

<br>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">The public repository is a framework layer only.</strong><br>
It must not contain the actual AI brain.
</p>
<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">公開倉庫僅是框架層。</strong><br>
它不得包含真正的 AI 大腦。
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">5. Private Kernel · 私有核心</h2>

<h3 align="center" style="color:#e94560;">Repository · 倉庫</h3>
<p align="center" style="color:#c9d1d9; font-size:1.1em;">
<code style="background:#1a1a2e; color:#e94560; padding:4px 16px; border-radius:4px;">AMPM-KEL</code>
</p>

<h3 align="center" style="color:#2ea043;">Purpose · 目的</h3>
<p align="center" style="color:#c9d1d9;">
Private orchestration kernel and runtime intelligence layer.<br>
私有協調核心與執行智慧層。
</p>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">This repository contains all authority-bearing systems.</strong><br>
Only core maintainers may access this repository.
</p>
<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">此倉庫包含所有具權限的系統。</strong><br>
僅核心維護者可以存取此倉庫。
</p>

<br>

<h3 align="center" style="color:#2ea043;">Kernel Authority Systems · 核心權限系統</h3>

<h4 align="center" style="color:#e94560;">Routing Authority · 路由權限</h4>
<p align="center" style="color:#c9d1d9;">
Responsible for · 負責：<br>
Model selection · 模型選擇<br>
Provider balancing · 提供商平衡<br>
Fallback strategy · 備援策略<br>
Execution priority · 執行優先級<br>
Orchestration routing · 協調路由<br>
Lock management · 鎖定管理
</p>
<p align="center" style="color:#8b949e;">
Examples: Thalamus, Router, Provider Selector, Priority Engine<br>
範例：視丘、路由器、提供商選擇器、優先級引擎
</p>

<br>

<h4 align="center" style="color:#e94560;">Context Authority · 上下文權限</h4>
<p align="center" style="color:#c9d1d9;">
Responsible for · 負責：<br>
Context assembly · 上下文組裝<br>
Memory ranking · 記憶排名<br>
Persona merge · 人格合併<br>
Prompt composition · 提示組合<br>
Context compression · 上下文壓縮<br>
Context filtering · 上下文過濾
</p>

<p align="center" style="color:#e94560; font-weight:bold;">
🔑 Who controls context controls the AI.<br>
誰控制上下文，誰就控制了 AI。
</p>

<br>

<h4 align="center" style="color:#e94560;">Governance Authority · 治理權限</h4>
<p align="center" style="color:#c9d1d9;">
Responsible for · 負責：<br>
Permission enforcement · 權限執行<br>
Capability firewall · 能力防火牆<br>
Sandbox policies · 沙箱策略<br>
Authority validation · 權限驗證<br>
Execution restrictions · 執行限制<br>
Runtime policies · 執行政策
</p>

<br>

<h4 align="center" style="color:#e94560;">Evolution Authority · 演化權限</h4>
<p align="center" style="color:#c9d1d9;">
Responsible for · 負責：<br>
Adaptive optimization · 自適應優化<br>
Runtime learning · 執行學習<br>
Self reflection · 自我反思<br>
Scoring systems · 評分系統<br>
Evolutionary planning · 演化規劃
</p>

<br>

<h4 align="center" style="color:#e94560;">Runtime Intelligence · 執行智慧</h4>
<p align="center" style="color:#c9d1d9;">
Responsible for · 負責：<br>
Orchestration policies · 協調政策<br>
Retry intelligence · 重試智慧<br>
Provider balancing · 提供商平衡<br>
Execution heuristics · 執行啟發式<br>
Internal coordination · 內部協調<br>
Runtime optimization · 執行優化
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">6. Migration Mandate · 遷移命令</h2>

<h3 align="center" style="color:#e94560;">Move Immediately · 立即搬移</h3>

<p align="center" style="color:#c9d1d9;">
The following must not remain inside the public repository:<br>
以下不得留在公開倉庫中：
</p>

<p align="center" style="color:#c9d1d9;">
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/brain/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/governance/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/runtime/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/core/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/compass/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/decisions/</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/agents.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/llm.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/memory.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/memory_vector.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/models.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/executor.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/handler.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/breath.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/nose.py</code><br>
<code style="background:#1a1a2e; color:#e94560; padding:2px 10px; border-radius:3px;">src/civilization_controller.py</code>
</p>

<br>

<h3 align="center" style="color:#d29922;">Conditional Audit · 有條件審查</h3>

<p align="center" style="color:#c9d1d9;">
The following files must be reviewed and moved if they contain authority-bearing logic:<br>
以下文件必須審查，若包含權限邏輯則搬移：
</p>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#58a6ff;">decisions.py</strong><br>
Move if contains: routing, orchestration, agent selection, priority logic, execution flow<br>
包含路由、協調、代理選擇、優先級邏輯、執行流程則搬移
</p>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#58a6ff;">evolution_module.py</strong><br>
Move if contains: adaptive logic, optimization, runtime learning, self-modification, growth systems<br>
包含自適應邏輯、優化、執行學習、自我修改、成長系統則搬移
</p>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#58a6ff;">civilization_controller.py</strong><br>
Move if contains: multi-agent orchestration, civilization memory, strategic coordination, governance logic<br>
包含多代理協調、文明記憶、戰略協調、治理邏輯則搬移
</p>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#58a6ff;">config.py</strong><br>
Must be split into: public configuration + kernel configuration<br>
必須拆分為：公開配置 + 核心配置
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">7. Plugin Security · 插件安全</h2>

<p align="center" style="color:#e94560; font-weight:bold;">
Plugins are capability providers only.<br>
Plugins must never possess authority.
</p>
<p align="center" style="color:#e94560; font-weight:bold;">
插件僅是能力提供者。插件永遠不能擁有權限。
</p>

<br>

<h3 align="center" style="color:#2ea043;">Plugins MAY · 插件可以</h3>
<p align="center" style="color:#c9d1d9;">
✅ Execute tools · 執行工具<br>
✅ Return structured outputs · 回傳結構化輸出<br>
✅ Provide context candidates · 提供上下文候選<br>
✅ Expose external integrations · 暴露外部整合
</p>

<h3 align="center" style="color:#e94560;">Plugins MUST NOT · 插件不能</h3>
<p align="center" style="color:#c9d1d9;">
❌ Modify routing · 修改路由<br>
❌ Modify governance · 修改治理<br>
❌ Modify permissions · 修改權限<br>
❌ Modify memory ranking · 修改記憶排名<br>
❌ Modify orchestration flow · 修改協調流程<br>
❌ Inject hidden prompts · 注入隱藏提示<br>
❌ Alter runtime authority · 改變執行權限
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">8. Required Documentation · 必要文件</h2>

<p align="center" style="color:#c9d1d9;">

| Document | Purpose |
|:---|:---|
| <strong>ARCHITECTURE_KERNEL.md</strong> | Kernel boundaries, authority ownership, orchestration hierarchy |
| <strong>PUBLIC_API.md</strong> | Public interfaces, SDK contracts, plugin contracts |
| <strong>PLUGIN_SECURITY.md</strong> | Plugin sandbox rules, capability restrictions, authority limits |
| <strong>SPLIT_REPORT.md</strong> | Migrated systems, public systems, restricted systems |

</p>

<p align="center" style="color:#c9d1d9;">
<em>Direct internal imports are prohibited. · 直接內部導入是被禁止的。</em>
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">9. Runtime Enforcement · 執行強制</h2>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">The following are prohibited outside the kernel:</strong><br>
<strong style="color:#e94560;">以下禁止在核心外部執行：</strong>
</p>

<p align="center" style="color:#c9d1d9;">
❌ Self-modifying runtime · 自我修改執行環境<br>
❌ Autonomous routing rewrites · 自主路由重寫<br>
❌ Unrestricted memory mutation · 無限制記憶變異<br>
❌ Plugin-based authority escalation · 基於插件的權限提升<br>
❌ Hidden orchestration hooks · 隱藏協調鉤子<br>
❌ Circular authority control · 循環權限控制
</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">10. Strategic Goal · 戰略目標</h2>

<p align="center" style="color:#c9d1d9; font-size:1.1em;">

| Repository · 倉庫 | Role · 角色 |
|:---|---:|
| <strong style="color:#2ea043;">AMPM-AIOPS</strong> | Public ecosystem framework · 公開生態框架 |
| <strong style="color:#e94560;">AMPM-KEL</strong> | Private orchestration kernel · 私有協調核心 |

</p>

<br>

---

<h2 align="center" style="color:#58a6ff;">11. Final Principle · 最終原則</h2>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#8b949e;">The primary intellectual property is not:</strong><br>
<strong style="color:#8b949e;">主要智慧財產不是：</strong>
</p>

<p align="center" style="color:#8b949e;">
bots · dashboards · plugins · tools<br>
機器人 · 儀表板 · 插件 · 工具
</p>

<br>

<p align="center" style="color:#c9d1d9;">
<strong style="color:#e94560;">The true system value is:</strong><br>
<strong style="color:#e94560;">系統的真正價值是：</strong>
</p>

<p align="center" style="color:#c9d1d9;">
✅ Orchestration intelligence · 協調智慧<br>
✅ Routing systems · 路由系統<br>
✅ Context authority · 上下文權限<br>
✅ Governance enforcement · 治理執行<br>
✅ Adaptive runtime intelligence · 自適應執行智慧
</p>

<br>

<p align="center" style="color:#e94560; font-weight:bold; font-size:1.1em;">
These systems must remain:<br>
isolated · private · authority-controlled · non-public · kernel-bound
</p>
<p align="center" style="color:#e94560; font-weight:bold; font-size:1.1em;">
這些系統必須保持：<br>
隔離 · 私有 · 權限控制 · 非公開 · 核心綁定
</p>

<p align="center" style="color:#e94560; font-weight:bold; font-size:1.2em; margin-top:20px;">
at all times · 始終如此
</p>

<br>

<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
