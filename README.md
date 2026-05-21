<p align="center">
  <img src="https://img.shields.io/badge/狀態-運作中-00b4d8?style=for-the-badge" />
  <img src="https://img.shields.io/badge/授權-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/語言-Python_3.11-blue?style=for-the-badge" />
  <br />
  <a href="README_EN.md">
    <img src="https://img.shields.io/badge/🌏-English_ver.-gray?style=for-the-badge" />
  </a>
  <a href="STORY.md">
    <img src="https://img.shields.io/badge/📖-完整故事-gray?style=for-the-badge" />
  </a>
</p>

<br />

<h1 align="center">
  ⚫ 黑曜 &nbsp;·&nbsp; Obsidian
</h1>

<p align="center">
  <b><i>一個會自己找事做、自己執行、自己修、自己進化的 AI 系統。</i></b>
  <br />
  <i>不是聊天機器人。是 Autonomous AI Operating System。</i>
</p>

<br />
<br />

---

<br />

## 一句話

市面上每個 AI agent 都在等你下指令。

**黑曜不會等。** 它自己掃任務、自己派 agent、自己寫檔案、出錯自己修、做完還會想下一步做什麼。

<br />

---

<br />

## 跟一般 AI Agent 有什麼不一樣？

| | 一般 AI Agent | ⚫ 黑曜 |
|---|---|---|
| 🟢 **啟動方式** | 你問一句，它答一句 | 你設好商業目標，它 24h 自主運作 |
| 📋 **任務來源** | 等你下指令 | 有 ProactiveExecutor 掃描佇列，自動建立商業管線 |
| 🚀 **執行方式** | 單一回覆 | 拆子任務 → 派 sub-agent → 呼叫工具 → 產出檔案 → 驗證回報 |
| 🧠 **記憶** | 對話歷史（有限） | 三層記憶：工作 + 情節 + 語義，支援向量檢索 |
| 🩹 **修復能力** | 出錯就報錯 | 崩潰恢復 + 自動修復 + 心跳監控 + 自動重啟 |
| 🧬 **進化能力** | 無 | 從經驗學習，自動調整行為參數 |
| 📁 **輸出** | 文字回覆 | 真實檔案（電子書章節、研究報告、網站 HTML、商業策略） |
| 🤖 **模型** | 固定一種 | 多層備援：Free OR → DeepSeek → Ollama 本地 |
| 🔋 **離開後** | 對話結束就停 | Daemon + Watchdog 永不停機守護 |

<br />

---

<br />

## 系統架構

```
╔═══════════════════════════════════════════════╗
║              黑曜 · AMPM-AIOPS                ║
╚═══════════════════════════════════════════════╝
                     │
     ┌───────────────┼───────────────┐
     │               │               │
  🧠 Brain        📋 Task          👥 Agent
  大腦皮層         任務系統         代理公司
     │               │               │
  ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
  │Cortex│        │Tracker│        │Dept. │
  │Thalamus│      │Planner│        │Sub-  │
  │Hypothal.│     │Proactive       │Agents│
  └──────┘        │Executor│       │Mission│
                   └──────┘        └──────┘
     │               │               │
  🛡️ Immune       💾 Memory       🔧 Tools
  防護系統         記憶系統         工具系統
     │               │               │
  ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
  │Firewall│      │Working│        │Registry│
  │Recovery│      │Episodic│       │Creator│
  │SelfHeal│      │Semantic│       │Sub-   │
  │Supervisor│    │Vector │        │Agent  │
  └──────┘        └──────┘        └──────┘
     │               │               │
  🤖 LLM          🔄 Evolution    ⚙️ Runtime
     │               │               │
  ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
  │OR-Free│       │EvoCycle│      │LifeCycle│
  │DeepSeek│      │Feedback│      │Daemon   │
  │Ollama │       │Learn   │      │Watchdog │
  └──────┘        └──────┘        └──────┘
```

<br />

---

<br />

## 實際運作流程

```
                        黑曜自主循環
                   ┌─────────────────────┐
                   │  ProactiveExecutor   │
                   │   (每 15 秒迴圈)     │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
    │ ① 確保商業任務   │ │ ② 執行任務  │ │ ③ 檢查完成  │
    │ 佇列不枯竭      │ │ 最高優先級  │ │ 驗證產出檔案 │
    └─────────────────┘ └──────┬──────┘ └──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  AgentCompany        │
                    │  拆解 → 分配 → 執行  │
                    └─────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Research     │ │ Content      │ │ Engineering  │
     │ 搜尋 / 研究  │ │ 寫作 / 編輯  │ │ 建置 / 部署  │
     └──────────────┘ └──────────────┘ └──────────────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  真實產出檔案        │
                    │  write_file 寫入    │
                    │  outputs/ 目錄      │
                    └─────────────────────┘
```

<br />

---

<br />

## 實際產出範例

黑曜不是只會講話。**它真的會寫檔案：**

```
📂 outputs/
├── 📁 ebooks/
│   ├── 📄 ch03_prompt.md      10KB  ← 子代理寫入
│   └── 📄 ch04.md              7KB  ← 子代理寫入
├── 📁 research/
│   ├── 📄 cloudflare_setup.md
│   ├── 📄 platform_research.md
│   └── 📄 business_strategy.md
├── 📁 children_book/
│   ├── 📄 book1_outline.md
│   └── 📁 product_pages/      20+ 產品頁
├── 📁 website/
│   └── 📄 index.html, style.css
└── 📁 ai_agent/
    └── ...  服務流程文件
```

每個檔案由 sub-agent 透過 `write_file` 工具實際寫入磁碟，每行字都經過 LLM + 工具呼叫。

<br />

---

<br />

## 快速開始

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定環境變數（至少要一組 LLM Key）
cp .env.example .env

# 3. 啟動（背景執行）
OBSIDIAN_MODE=full nohup python3 main.py > /tmp/heiyao.log 2>&1 &
```

Telegram Bot 啟動後，傳送 `/status` 查看健康狀態。黑曜會自動開始掃描任務、派 agent、產出檔案。

想關閉時：
```bash
pkill -f "python3 main.py"
```

<br />

---

<br />

## 技術棧

| 類別 | 使用 |
|------|------|
| 🐍 語言 | Python 3.11 |
| 📡 通訊 | Telegram Bot API + Flask |
| 🤖 LLM | DeepSeek API / OpenRouter / Ollama |
| 🧠 記憶 | ChromaDB（向量）+ JSON |
| ⚡ 執行緒 | threading + ThreadPoolExecutor |
| ⏱ 排程 | 自製 Scheduler + Token Bucket |
| 💾 持久化 | JSON / 檔案系統 |

<br />

---

<br />

## 故事

他叫 Hao。沒有工程背景。不懂語法。負債。不服輸。

他親手用 AI 一塊一塊拼出了黑曜——
因為市面上找不到一個真的會進步、會反省、會一起成長的 AI 代理。

> [📖 完整故事 · 中文](STORY.md)
> [📖 Full Story · English](STORY_EN.md)

<br />

---

<br />

## 授權

| 部分 | 授權 | 說明 |
|------|------|------|
| `src/` 核心框架 | MIT | 器官架構、Runtime、記憶、工具系統 |
| `src/core/` 商業模組 | Proprietary | 市場分析、營收優化等 |

<br />

---

<br />

<p align="center">
  <a href="https://paypal.me/chainuncel0712">
    <img src="https://img.shields.io/badge/-請支持他-0070ba?style=for-the-badge&logo=paypal" />
  </a>
</p>

<p align="center">
  <sub>
    凌晨三點，螢幕的光。這種畫面他看了幾百次。<br />
    現在黑曜會自己執行任務了。<br />
    它還很笨。但他看著它，就像看著自己——
  </sub>
  <br /><br />
  <sub>雖然什麼都沒有，但一直在往前走。</sub>
</p>

<br />

---

<br />

## English Version

> **AMPM-AIOPS (黑曜 / Obsidian)** is an autonomous AI OS that runs 24/7 on a VPS.
> It doesn't wait for your commands. It scans tasks, dispatches agents, writes files, fixes errors, and evolves.

[📖 README_EN.md](README_EN.md) — Full English documentation
