<p align="center"><img src="assets/300.png" width="180"></p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">AMPM-AIOPS Architecture Overview</h1>

```
╔══════════════════════════════════════════════════════════════╗
║              AMPM — AI Operating System                     ║
║         A self-evolving AI OS with biological metaphor      ║
╚══════════════════════════════════════════════════════════════╝
```

<h2 align="center" style="color:#58a6ff;">System Architecture</h2>

```
                        ┌──────────────────────┐
                        │     User / Input       │
                        │  (chat / task / api)   │
                        └──────────┬───────────┘
                                   │
                          ┌────────▼────────┐
                          │    skin/        │  ← 對外接口 (WebSocket / CLI)
                          │    web/         │  ← Dashboard (Flask)
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │    nerve/       │  ← 感知層 — 接收、解析、分類輸入
                          │    nose.py      │  ← 嗅覺 — 環境異常偵測
                          │    breath.py    │  ← 呼吸 — 系統心跳定時器
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │    brain/       │  ← 決策中樞 — 意識、反思、計劃
                          │    meta_cognition│  ← 元認知 — 自我觀察、策略調整
                          │    agents.py    │  ← 代理系統 — 任務分解與指派
                          │    decisions/   │  ← 決策軌跡
                          └────────┬────────┘
                          ┌────────▼────────┐
                          │    muscle/      │  ← 行動層 — 工具協調與執行
                          │    tools.py     │  ← 工具註冊中心
                          │    executor.py  │  ← 命令執行器
                          └────────┬────────┘
                          ┌────────▼────────┐
                          │    memory.py    │  ← 記憶系統 (短期+長期)
                          │    memory_vector │  ← 向量記憶
                          │    bag/         │  ← 經驗包
                          │    civiliza...  │  ← 文明記憶 (跨世代)
                          └────────┬────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
  ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
  │  immune/    │          │  runtime/   │          │  evolution  │
  │  安全/修復   │          │  系統生命週期 │          │  演化引擎   │
  │  monitor.py │          │  lifecycle/ │          │  evolution.py│
  │  self_heal  │          │  breath.py  │          │  dna_system/ │
  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
         │                         │                         │
         │              ┌──────────▼──────────┐              │
         │              │     governance/     │              │
         │              │  gatekeeper         │              │
         │              │  security_zone      │              │
         │              │  event_log          │              │
         │              │  control_plane      │              │
         │              │  isolation          │              │
         │              │  scoring / audit    │              │
         │              └─────────────────────┘              │
         │                                                   │
         └──────────────────┬────────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │  commerce/  │  ← 商業系統 (Pricing/License/LemonSqueezy)
                     │  pro/       │  ← PRO 版功能
                     │  studio/    │  ← 創作工作室
                     └─────────────┘
```

<h2 align="center" style="color:#58a6ff;">Organ System Map</h2>

| Organ | Directory | Role in the AI Body |
|-------|-----------|-------------------|
| 🧠 **Brain** | `src/brain/` | 決策中樞、自我意識、反思、計劃、意圖路由 |
| 🔌 **Nerve** | `src/nerve/` | 感知層 — 接收外部輸入，解析意圖，分類訊息 |
| 💪 **Muscle** | `src/muscle/` | 行動層 — 協調工具、排程執行、物理操作 |
| 🛡️ **Immune** | `src/immune/` | 安全層 — 自我修復、異常偵測、損害控制 |
| 🧬 **DNA** | `src/dna_system/` | 遺傳系統 — 配置繼承、器官藍圖、基因表現 |
| 💓 **Runtime** | `src/runtime/` | 生命維持 — 系統循環、排程器、資源管理 |
| 🫁 **Breath** | `src/breath.py` | 呼吸 — 系統心跳、週期性喚醒 |
| 👃 **Nose** | `src/nose.py` | 嗅覺 — 環境氣味、異常值監控 |
| 🫀 **Circulatory** | `src/core/circulatory.py` | 循環系統 — 模組間訊息傳遞與協調 |
| 🧠 **Meta-Cognition** | `src/meta_cognition/` | 元認知 — 自我觀察、策略調整、成長記錄 |
| 📚 **Memory** | `src/memory.py` | 記憶系統 — 短期工作記憶、長期儲存 |
| 🧭 **Vector Memory** | `src/memory_vector.py` | 向量記憶 — 語義搜尋、相似度匹配 |
| 🌍 **Civilization Memory** | `src/civilization_memory/` | 文明記憶 — 跨世代知識傳承 |
| 👜 **Bag** | `src/bag/` | 經驗包 — 儲存過往經驗與教訓 |
| 🔄 **Evolution** | `src/core/evolution_cycle.py` | 演化循環 — 自我評估、策略演化、行為優化 |
| 🎯 **Goals** | `src/goals/` | 目標系統 — 長期目標管理、優先級排序 |
| 🏛️ **Governance** | `src/governance/` | 治理層 — 權限控制、安全隔離、審計、評分 |
| 🏪 **Commerce** | `src/commerce/` | 商業系統 — 定價、授權、Lemon Squeezy |
| ⭐ **PRO** | `src/pro/` | PRO 版 — 進階功能、授權驗證 |
| 🎨 **Studio** | `src/studio/` | 創作工作室 — 內容生成、品牌建立 |
| 🦴 **Skeleton** | `src/skeleton/` | 骨架 — 系統基礎結構與配置 |
| 🧬 **Organs** | `src/organs/` | 器官註冊中心 — 零件載入與生命週期管理 |
| 🗑️ **Waste** | `src/waste/` | 廢物處理 — 資源回收、日誌輪替 |
| 🤝 **Trust** | `src/trust/` | 信任系統 — 代理信譽評分 |
| ⏱️ **Temporal** | `src/temporal/` | 時間感知 — 排程、時序處理 |
| 🔧 **Tools** | `src/tools.py` | 工具註冊中心 — 所有可用工具的統一入口 |
| ⚙️ **Executor** | `src/executor.py` | 命令執行器 — 安全執行外部命令 |
| 🛣️ **Bridge** | `src/bridge/` | 橋接層 — 外部服務整合 |
| 🔌 **Circuit** | `src/circuit/` | 電路 — 系統內部通訊與事件匯流排 |
| 🌐 **Web** | `src/web/` | Web 介面 — Flask dashboard |
| 🗺️ **Compass** | `src/compass/` | 方向感測器 — 任務優先級與方向判斷 |
| 📋 **Tasks** | `src/tasks/` | 任務系統 — 任務排程、追蹤、完成度 |
| 🧵 **Thread** | `src/thread_mgt.py` | 執行緒管理 — 背景執行緒生命週期 |
| 🔄 **Rollback** | `src/rollback.py` | 回滾系統 — 安全回退機制 |
| 🏠 **Homeostasis** | `src/core/homeostasis.py` | 恆定系統 — 維持系統內部平衡 |
| 🔐 **Gatekeeper** | `src/governance/gatekeeper.py` | 閘門 — 唯一入口檢查、執行緒註冊 |
| 📊 **Event Log** | `src/governance/event_log.py` | 事件日誌 — 不可篡改行為記錄 |
| 🪟 **Window** | `src/window.py` | 系統監控窗 |
| 📱 **Dashboard** | `src/dashboard/` | 操作面板 (Flask) |
| 🧭 **Handler** | `src/handler.py` | 請求處理入口 |

<h2 align="center" style="color:#58a6ff;">Entry Points & Startup Flow</h2>

```
main.py
  ├── Lock check (/tmp/ampm_obsidian.lock)
  ├── Gatekeeper.check_entry("main")
  ├── Modules loaded (34/81 organs)
  │   ├── memory (src/memory.py)
  │   ├── tools (src/tools.py)
  │   ├── compass (src/compass/)
  │   ├── nose (src/nose.py)
  │   ├── breath (src/breath.py)
  │   ├── brain (src/brain/)
  │   └── ...
  ├── Threads launched
  │   ├── ProactiveExecutor (task scanning)
  │   ├── EvolutionCycle (self-evaluation)
  │   ├── AgentSupervisor (agent health)
  │   ├── Rebirth (system upgrade)
  │   └── ...
  ├── Flask dashboard started
  └── Bot polling loop started

daemon.sh
  └── Wraps main.py with heartbeat monitoring & auto-restart
```

<h2 align="center" style="color:#58a6ff;">Data Flow (Lifecycle)</h2>

```
                    ┌─────────────────────────────────────┐
                    │          外部輸入 / Input             │
                    │   (WebSocket / CLI / Dashboard)      │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
               ┌───▶│      Nerve — 感知解析                │────┐
               │    │  - 訊息分類、意圖識別                │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               │    │      Brain — 決策                    │    │
               │    │  - 情境理解、計劃制定                │    │
               │    │  - 代理分配 (AgentCompany)           │    │
               │    │  - 工具選擇                         │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               │    │   Governance — 權限檢查               │    │
               │    │  - SecurityZone 跨區檢查             │    │
               │    │  - Isolation 工具隔離               │    │
               │    │  - Gatekeeper 模組權限               │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               │    │    Muscle + Tools — 執行              │    │
               │    │  - write_file / read_file            │    │
               │    │  - run_command (sandboxed)           │    │
               │    │  - web_search / generate_image       │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               │    │    Memory — 儲存                      │    │
               │    │  - 短期記憶 (對話上下文)              │    │
               │    │  - 長期記憶 (向量資料庫)              │    │
               │    │  - 文明記憶 (跨世代傳承)              │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               │    │    Evolution — 學習                   │    │
               │    │  - 策略觀察與記錄                    │    │
               │    │  - 行為評分                          │    │
               │    │  - 演化提案（不自動套用）            │    │
               │    └──────────────┬──────────────────────┘    │
               │                   │                           │
               │    ┌──────────────▼──────────────────────┐    │
               └────│   Immune — 自我修復                   │◀───┘
                    │  - 異常偵測                          │
                    │  - 自動修復                          │
                    │  - 損害控制                          │
                    └─────────────────────────────────────┘
```

<h2 align="center" style="color:#58a6ff;">Key Design Principles</h2>

1. **生物隱喻分層**：Decision (brain) → Execution (muscle/tools) → Memory — 三層硬切
2. **治理優先**：所有跨層操作必須經過 Gatekeeper + SecurityZone + ControlPlane
3. **可驗證性**：EventLog 記錄每次 decision → tool_call → output，支援完整 replay
4. **安全隔離**：子代理只能使用 whitelist 工具、寫入 jail 目錄、執行 filter 命令
5. **演化不自動**：Evolution 只提案、觀察、記錄，不自動修改任何檔案
6. **單一入口**：所有 thread 必須從 main.py 啟動並註冊到 Gatekeeper

<br>
<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
