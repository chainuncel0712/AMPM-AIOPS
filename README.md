# 麻 Core — ai 30 basi

[中文](#中文) | [English](#english)

---

## 中文

### 來自真實處境的專案

2016 年，我面臨財務壓力，開始接虛擬貨幣與 AI 工具，希望在技術中找到轉機。過程中我賣掉房子，投入所有資源嘗試翻轉。

從三月開始，我幾乎把所有時間都投入在 AI 系統上。我高度依賴 GPT 來幫我設計系統、理解架構、建立流程。

但我很快發現一個死循環：**AI 給建議 → 照做 → 出問題 → 再問 → 調整 → 重來。** 不是往前，是繞圈。

更深層的問題：我沒正式工程背景。一切從零自學，透過 AI 摸索。這讓我更依賴 AI，也更被它的限制影響。

最後我理解到：問題不是工具不夠強。**是我在用「對話」建系統，而不是用「可控的結構」在建系統。**

### 不只是「又一個 AI 框架」

市面上有很多 AI agent 框架。但它們有一個共同的假設：**你已經知道你要什麼，你只需要工具來組裝。**

現實是：大多數人一開始不知道自己要什麼。他們需要一個**陪他們想清楚的 AI**，不是一個工具箱。

這是黑曜跟所有其他 AI 框架的根本差別。

| | LangChain | CrewAI | AutoGPT | 黑曜 |
|---|-----------|--------|---------|------|
| 定位 | 工具箱 | 工作流 | 自主任務 | **陪你長大的框架** |
| 人格 | 無 | 寫死 | 寫死 | **對話中長出來** |
| 記憶 | 短期 | 短期 | 無 | **長期持久化** |
| 自我演化 | ❌ | ❌ | ❌ | **從錯誤學習** |
| 自修復 | ❌ | ❌ | ❌ | **自動修復** |
| 資源治理 | ❌ | ❌ | ❌ | **記憶體自動平衡** |
| 開源 | ✅ | ✅ | ✅ | ✅ MIT |

### 獨特性

**1. 它不是助手，它沒有預設人格。**
所有 AI 產品出廠時都有一個身份：「我是你的助手」。黑曜沒有。它開機是一張白紙。你透過對話定義它是誰。這不是 prompt engineering — 這是架構設計。身份存在記憶層，不是寫在 system prompt 裡。

**2. 它會記住你。**
不是一個 session 的 context window。是長期持久化的 key-value 記憶 + 對話歷史 + 文明級事件記憶（episodic/failure/evolution）。你教過的事，三個月後問它，它記得。

**3. 它會自己演化。**
它有 10 層文明基礎設施：經濟成本意識、信任評分、行動模擬、目標層級、社會治理、時間週期偵測、DNA 可繼承特質、生命週期熱插拔。它不是靜態的工具 — 它是一個會自我評估、自我調整、自我修復的系統。

**4. 它不是「又一個 LLM wrapper」。**
市面上 90% 的 AI agent 框架本質上就是一個 prompt → LLM → parse → tool call 的循環。黑曜在這個循環之上，加了自我監控、自我修復、演化、文明治理四層。它不是 LLM 的外殼，它是 LLM 的主人。

### 快速開始

```bash
git clone https://github.com/chainuncel0712/AMPM-AIOPS.git
cd AMPM-AIOPS
cp .env.example .env  # Telegram token + API keys
pip install -r requirements.txt
python3 main.py
```

### ampm-core — 基礎版

30 個核心功能，不帶商業器官，一行啟動：

```bash
curl -fsSL https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/master/ampm-core-install.sh | bash
```

```python
from core import Core
c = Core()
```

---

## English

### Born from a real struggle, not a whitepaper

In 2024, facing financial pressure, I turned to crypto and AI tools, hoping technology could open a door. I sold my house. I went all in.

For months, I lived inside AI chat windows — GPT, Claude, others — using them to design systems, understand architecture, and build workflows. At first, it felt like progress.

Then I hit the loop: **AI gives advice → I follow it → something breaks → ask again → adjust → rebuild.** Not moving forward. Circling.

The deeper problem: I have no formal engineering background. Everything I learned, I learned through these same AI tools. This made me more dependent on them, and more vulnerable to their limitations.

Eventually I understood: **I was building a system through conversation. What I needed was an executable structure that could run, evolve, and maintain itself.**

### Not just "another AI framework"

Most AI agent frameworks share one assumption: you already know what you want, you just need tools to build it.

Reality: most people don't know what they want at the start. They need an AI that helps them figure it out — not a toolbox.

This is the fundamental difference between Heiyao and every other AI framework.

### What makes it different

**1. No preset identity.**
Every AI product ships with a built-in persona: "I am your assistant." Heiyao ships blank. Its identity is defined through conversation and stored in persistent memory — not hardcoded in a system prompt. It becomes whatever you need it to be.

**2. It remembers.**
Not context-window memory. Persistent key-value facts, conversation history, and civilization-level event memory (episodic, failure, evolutionary). What you taught it three months ago, it still knows.

**3. It evolves.**
10 civilization layers: cost awareness, trust scoring, action simulation, goal hierarchy, governance, temporal cycle detection, inheritable DNA traits, hot-swap organ lifecycle. It is not a static tool — it is a self-evaluating, self-adjusting, self-repairing system.

**4. It's not another LLM wrapper.**
90% of AI agent frameworks are: prompt → LLM → parse → tool call → repeat. Heiyao adds four layers on top: self-monitoring, self-repair, evolution, and civilization governance. It doesn't serve the LLM — the LLM serves it.

### Quick Start

```bash
git clone https://github.com/chainuncel0712/AMPM-AIOPS.git
cd AMPM-AIOPS
cp .env.example .env
pip install -r requirements.txt
python3 main.py
```

### ampm-core — 30 essential functions

```bash
curl -fsSL https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/master/ampm-core-install.sh | bash
```

### License

MIT — Core framework
Proprietary — `src/core/` commercial organs
