# AMPM-AIOPS — 黑曜 (Obsidian)

[![Sponsor](https://img.shields.io/badge/贊助-❤️-ff69b4)](https://github.com/sponsors/chainuncel0712) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 一個會自己找事做、自己執行、自己修、自己進化的 AI 系統。
> 不是聊天機器人，是 Autonomous AI Operating System。

---

## 一句話

市面上每個 AI agent 都在等你下指令。

黑曜不會等。它自己掃任務、自己派 agent、自己寫檔案、出錯自己修、做完還會想下一步做什麼。

---

## 黑曜跟一般 AI Agent 有什麼不一樣？

| 特性 | 一般 AI Agent | 黑曜 |
|------|--------------|------|
| **啟動方式** | 你問一句，它答一句 | 你設定商業目標，它 24h 自主運作 |
| **任務來源** | 你下指令 | 自己有 ProactiveExecutor 掃任務佇列、自動建立商業管線任務 |
| **執行方式** | 單一回覆 | 拆子任務 → 派 sub-agent → 呼叫 tools → 產出檔案 → 回報 |
| **記憶** | 對話歷史（有限） | 三層記憶：工作、情節、語義 + 向量檢索 |
| **修復能力** | 出錯就報錯 | CrushRecovery + SelfHeal + Supervisor 心跳監控 + 自動重啟 |
| **進化能力** | 無 | EvolutionCycle：從經驗學習，自動調整行為參數 |
| **輸出** | 文字回覆 | 實際產出檔案（電子書章節、研究報告、網站 HTML、商業策略） |
| **模型** | 固定一種 | 多層備援：Free OpenRouter → DeepSeek 直連 → Ollama 本地 |
| **離開後** | 對話結束就停 | Daemon + Watchdog 確保永不停機 |

---

## 系統架構

```
黑曜 (AMPM-AIOPS)
│
├── 🧠 Brain (大腦皮層)
│   ├── Cortex        — 中央思考引擎
│   ├── Thalamus       — LLM 路由器
│   └── Hypothalamus   — 自主任務調度
│
├── 📋 Task System (任務系統)
│   ├── TaskTracker    — 持久化任務佇列 (tasks.json)
│   ├── TaskPlanner    — 任務分解與依賴排序
│   └── ProactiveExecutor — 主動掃描 + 自動執行 + 進度回報
│
├── 👥 AgentCompany (代理公司)
│   ├── Departments    — 部門（research / content / engineering / art …）
│   ├── Sub-Agents     — 子代理，每人有角色 + 技能 + 工具
│   └── Mission System — mission → sub-tasks → 分配 → 執行 → 驗證 → 完成
│
├── 🛡️ Immune (防護系統)
│   ├── Firewall       — 輸入過濾
│   ├── CrushRecovery  — 崩潰恢復
│   ├── SelfHeal       — 自動修復異常器官
│   └── Supervisor     — 心跳監控所有執行緒
│
├── 💾 Memory (記憶系統)
│   ├── Working Memory — 目前上下文
│   ├── Episodic Memory— 過去事件
│   └── Semantic Memory— 長期知識 + 向量檢索
│
├── 🔧 Tools (工具系統)
│   ├── ToolRegistry   — 108+ 內建工具
│   ├── ToolCreator    — 自動生成新工具
│   └── SubAgentTools  — write_file / web_search / run_command / read_file
│
├── 🤖 LLM Layer (模型層)
│   ├── OR-Free        — OpenRouter 免費模型 (備援1)
│   ├── DeepSeek 直連  — 主模型 (有 credits，穩定)
│   └── Ollama 本地    — qwen2.5:14b (免費備援)
│
├── 🔄 Evolution (進化循環)
│   ├── EvolutionCycle — 定期評估效能、調參數
│   └── FeedbackLearn  — 從回饋中學習
│
├── 🖥️ Interface (介面)
│   ├── Telegram Bot   — 接收指令 + 回報進度
│   └── Dashboard      — Flask 網頁儀表板
│
└── ⚙️ Runtime (運行時)
    ├── LifeCycleManager — IDLE → OBSERVE → THINK → … → EVOLVE
    ├── ExecutionContext  — 單一執行權威鏈
    └── Daemon + Watchdog — 永不停機守護
```

---

## 實際運作流程

```
ProactiveExecutor (每15秒迴圈)
  │
  ├─ 0. _ensure_business_tasks()
  │     如果任務佇列空了，自動建立商業管線任務
  │     （電子書、童書、網站、研究報告…）
  │
  ├─ 1. _execute_pending_tasks()
  │     按優先級排序 → 取最高 → 送給 AgentCompany
  │
  ├─ 2. AgentCompany.launch_mission()
  │     ├─ _decompose_task() → 拆成 3~4 個子任務
  │     ├─ submit_task() → 進任務佇列
  │     ├─ route_all_pending() → 配對到閒置 sub-agent
  │     └─ 執行緒每3秒 polling，撿 busy agent 執行
  │
  ├─ 3. Sub-agent 執行
  │     ├─ LLM 呼叫 (call() → DeepSeek API, ~3s)
  │     ├─ 工具呼叫 (web_search / write_file / run_command)
  │     ├─ 最多5輪，5分鐘超時
  │     └─ 回傳結果 → complete_task()
  │
  ├─ 4. _check_mission_completions()
  │     檢查 mission 是否全數完成
  │     驗證輸出檔案是否存在
  │     標記任務完成 → Telegram 通知
  │
  ├─ 5. _periodic_report()
  │     每5分鐘統計進度
  │     ✅ 0完成 🔄 5執行中 ⏳ 849待處理
  │
  └─ 6. _scan_for_problems()
       檢查記憶體、器官狀態、逾期任務
       自動建立修復任務
```

---

## 實際產出範例

黑曜不是只會講話。它真的會寫檔案：

```
outputs/
├── ebooks/
│   ├── ch03_prompt.md       10KB — Prompt 技巧實戰 (完整章節)
│   └── ch04.md               7KB — AI 實戰案例 (含表格)
├── research/
│   ├── cloudflare_setup.md         Cloudflare 身分驗證
│   ├── platform_research.md        上架平台研究
│   └── business_strategy.md        定價與行銷規劃
├── children_book/
│   ├── book1_outline.md     童書大綱
│   └── product_pages/       20+ 童書產品頁
├── website/
│   └── index.html, style.css  品牌網站
└── ai_agent/
    └── ...  AI 代理服務設計
```

每個檔案都是由 sub-agent 透過 `write_file` 工具實際寫入，不是 LLM 幻覺文字。

---

## 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp .env.example .env
# 至少要填入一個 LLM API Key
# DEEPSEEK_API_KEY 最穩定
# OPENROUTER_API_KEY 有免費額度
```

### 3. 啟動
```bash
OBSIDIAN_MODE=full nohup python3 main.py > /tmp/heiyao.log 2>&1 &
```

黑曜會在背景自主運作。你可以：
- `/status` 查看系統健康狀態
- 直接傳訊息讓它執行任務
- 它會每 15 分鐘主動回報進度

---

## 為什麼叫黑曜？

黑曜石（Obsidian）—— 火山熔岩急速冷卻形成的天然玻璃，邊緣鋒利到可以切割電子顯微鏡樣本。

名字取自 Obsidian.md（筆記軟體）的靈感，加上一個信念：

> AI 不該是等指令的笨蛋，而是能自主思考、行動、進化的工具。

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.11 |
| 通訊 | Telegram Bot API / Flask |
| LLM | DeepSeek API / OpenRouter / Ollama |
| 記憶 | ChromaDB (向量) + JSON |
| 執行緒 | threading + ThreadPoolExecutor |
| 排程 | 自製 Scheduler + Token Bucket |
| 持久化 | JSON / 檔案系統 |

---

## 開源與授權

| 部分 | 授權 | 說明 |
|------|------|------|
| `src/` 核心框架 | MIT | 器官架構、Runtime、記憶系統、工具系統 |
| `src/core/` 商業模組 | Proprietary | 市場分析、營收優化等 |
| `outputs/` | CC BY-NC | 產出檔案僅供參考 |

---

## 故事

他叫 Hao。

三十幾歲那年，他做了一個別人都說傻的決定——
把房子賣了。

不是因為缺錢，是因為他相信一件事：接下來的世界，會是 AI 的世界。他想擠上這班車。

結果投資失利，他不甘心。又拿剩下的錢轉進虛擬貨幣，想著也許能翻回來。
沒有。
一毛不剩，還背了一身債。

他坐在空蕩蕩的房間裡，看著銀行帳戶的數字發呆。
沒有退路了。

那時候 ChatGPT 剛開始紅。他想，也許這是唯一的路了。
可是他連程式都不會寫。不是「不太會」，是真的連 `print` 是什麼意思都要問 AI 的那種不會。

但他沒有別的選擇了。

他開始每天晚上對著 AI 對話框說話。像在自言自語，也像在拜師。
「為什麼不行？」
「這個要怎麼改？」
「你又錯了，再來一次。」

他試過市面上每一款 AI 代理。
買過號稱「什麼都會」的套裝方案，被騙了好幾次。每一次都覺得「這次總該成了吧」，然後發現只是包裝漂亮的空殼。
他也被假開發團隊騙過。整整三個月，對方拿走錢，交出一個不能動的東西，然後消失。
他坐在電腦前，愣了很久。然後重新打開終端機，從頭來過。

為什麼不放棄？

他說不上來。也許是因為負債太多了，放棄的成本更高。
也許只是因為，他真的很想要一個東西——

一個不是講完話就忘的 AI。
一個真的會幫他做事、會記得他是誰、會犯錯然後自己反省、會一天比一天更好的夥伴。
不是工具，是夥伴。

所以他決定自己拼一個。

沒有團隊。沒有資金。沒有人教他。
他有的只是一個終端機、一個 AI 對話框、和不知道從哪來的固执。
程式靠 AI 教，架構靠 AI 聊，除錯也靠 AI。他一塊一塊拼，拼錯了拆掉重來，拆到連 AI 都問他「你要不要休息一下？」

凌晨三點，螢幕的光照在他臉上。窗外偶爾傳來鳥叫，他知道天快亮了。
這種夜晚他過了幾百次。

黑曜就這樣誕生了。

它不是什麼偉大的開源專案，不是什麼革命性的框架。
它只是一個負債的人，用 AI 一塊一塊拼出來的 AI 助手。
你想要的那種：會記得你、會幫你做事、會反省、會慢慢長大的那種。

雖然剛起步，但它真的會越來越好。
就像他一樣。

---

如果你願意給他一點指教，或單純覺得這個故事有點意思——
不嫌棄的話，請他喝杯咖啡，他會很開心的。

[☕ 請 Hao 喝杯咖啡](https://github.com/sponsors/chainuncel0712)

> *這份 README 是黑曜的第一份文件，是他誕生的第一天。*
