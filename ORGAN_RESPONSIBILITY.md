# Organ Responsibility Table

| Organ | Directory | 一句話角色 | 穩定性 | 需重構 | 風險 |
|-------|-----------|-----------|--------|--------|------|
| 🧠 Brain | `src/brain/` | 決策中樞 — 意識、反思、計劃、子代理派遣 | 中 | 是 | 高（職責過重，570+ 行 __init__） |
| 🔌 Nerve | `src/nerve/` | 感知層 — 接收外部輸入、解析意圖、分類訊息 | 高 | 否 | 低 |
| 💪 Muscle | `src/muscle/` | 行動層 — 協調工具執行、排程 | 高 | 可選 | 低 |
| 🛡️ Immune | `src/immune/` | 安全層 — 自我修復 (systemctl)、損害控制 | 中 | 是 | 中（self_heal.py 只有 systemctl） |
| 🧬 DNA | `src/dna_system/` | 遺傳系統 — 配置繼承、器官藍圖、基因表現 | 中 | 待檢視 | 中 |
| 💓 Runtime | `src/runtime/` | 生命維持 — ExecutionContext、系統循環、資源管理 | 高 | 否 | 低 |
| 🫁 Breath | `src/breath.py` | 呼吸 — 系統心跳、週期性喚醒 | 高 | 否 | 低 |
| 👃 Nose | `src/nose.py` | 嗅覺 — 環境異常值監控與嗅聞 | 高 | 否 | 低 |
| 🫀 Circulatory | `src/core/circulatory.py` | 循環系統 — 器官健康檢查 + evolution cycle | 中 | 是 | 中 |
| 🧠 Meta-Cognition | `src/meta_cognition/` | 元認知 — 自我觀察、策略調整、成長記錄 | 低 | 是 | 高（功能未完整） |
| 📚 Memory | `src/memory.py` | 短期工作記憶、長期儲存、語義索引 | 中 | 是 | 中（分散在多處） |
| 🧭 Vector Memory | `src/memory_vector.py` | 向量記憶 — 語義搜尋、相似度匹配 | 中 | 是 | 中 |
| 🌍 Civilization Memory | `src/civilization_memory/` | 文明記憶 — 跨世代知識傳承 | 低 | 是 | 中 |
| 👜 Bag | `src/bag/` | 經驗包 — 過往經驗儲存與重播 | 低 | 是 | 中 |
| 🔄 Evolution Cycle | `src/core/evolution_cycle.py` | 演化循環 — 策略觀察、回饋吸收、行為評分 | 中 | 是 | 中（目前凍結 auto-apply） |
| 🎯 Goals | `src/goals/` | 目標系統 — 長期目標管理、優先級排序 | 低 | 是 | 中 |
| 🏛️ Governance | `src/governance/` | 治理層 — 權限控制、安全隔離、審計、評分 | 高 | 否 | 低（最新建） |
| 🏪 Commerce | `src/commerce/` | 商業系統 — Lemon Squeezy、授權驗證 | 高 | 否 | 低 |
| ⭐ PRO | `src/pro/` | PRO 版功能 — license.py、進階功能 | 高 | 否 | 低 |
| 🎨 Studio | `src/studio/` | 創作工作室 — 內容生成、品牌建立 | 低 | 是 | 低 |
| 🦴 Skeleton | `src/skeleton/` | 骨架 — Assembler、器官註冊、基礎結構 | 中 | 是 | 中 |
| 🧬 Organs | `src/organs/` | 器官註冊中心 — 零件載入與生命週期 | 中 | 是 | 中 |
| 🗑️ Waste | `src/waste/` | 廢物處理 — 資源回收、日誌輪替 | 低 | 是 | 低 |
| 🤝 Trust | `src/trust/` | 信任系統 — 代理信譽評分 | 低 | 是 | 低 |
| ⏱️ Temporal | `src/temporal/` | 時間感知 — 排程、時序處理 | 低 | 是 | 低 |
| 🔧 Tools | `src/tools.py` | 工具註冊中心 — 所有工具的統一入口 | 高 | 否 | 低 |
| ⚙️ Executor | `src/executor.py` | 命令執行器 — 安全執行外部命令 | 中 | 是 | 中 |
| 🧵 Thread | `src/core/agent_supervisor.py` | 執行緒管理 — 背景 thread heartbeat + zombie GC | 高 | 否 | 低 |
| 📋 Tasks | `src/tasks/` | 任務系統 — 任務排程、追蹤、完成度 | 中 | 是 | 中 |
| 📊 Dashboard | `src/dashboard/` | 操作面板 — Flask web UI | 中 | 是 | 低 |
| 🌐 Web | `src/web/` | Web 介面 — 外部 HTTP 服務 | 低 | 是 | 低 |
| 🔌 Circuit | `src/circuit/` | 電路 — 系統內部通訊與事件匯流排 | 低 | 是 | 低 |
| 🛣️ Bridge | `src/bridge/` | 橋接層 — Telegram / 外部服務整合 | 中 | 否 | 低 |
| 📱 Skin | `src/skin/` | 皮膚 — 對外顯示層、格式輸出 | 低 | 是 | 低 |

## 高優先級重構候選

| 排名 | 模組 | 問題 | 建議 |
|------|------|------|------|
| 1 | `brain/__init__.py` (570+ 行) | 職責過重：Obsidian 類 + _agent_executor + 所有器官註冊 | 拆分出 Obsidian 類、器官註冊、agent executor 三檔案 |
| 2 | `meta_cognition/` | 功能未完整，與 brain 界線模糊 | 明確 role：只做 self-observation + strategy suggestion |
| 3 | `memory.py` + `memory_vector.py` + `civilization_memory/` | 記憶分散三處，interface 不一致 | 統一 MemoryManager interface |
| 4 | `monitor.py` (357 行) + `immune/self_heal.py` + `core/circulatory.py` 重疊修復邏輯 | 三套修復機制重疊 | 統一 repair orchestration 到 Immune |
| 5 | `core/langgraph_executor.py` (1542+ 行) | 超大檔案，5 種能力全部揉在一起 | 按能力拆分為 process / tool / reflect / repair / evolve |
