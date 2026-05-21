<p align="center">
  <img src="https://img.shields.io/badge/status-active-00b4d8?style=for-the-badge" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/language-Python_3.11-blue?style=for-the-badge" />
  <br />
  <a href="README.md">
    <img src="https://img.shields.io/badge/🌏-中文版-gray?style=for-the-badge" />
  </a>
  <a href="STORY_EN.md">
    <img src="https://img.shields.io/badge/📖-Full_Story-gray?style=for-the-badge" />
  </a>
</p>

<br />

<h1 align="center">
  ⚫ Obsidian &nbsp;·&nbsp; 黑曜
</h1>

<p align="center">
  <b><i>An AI system that finds its own work, executes it, fixes itself, and evolves.</i></b>
  <br />
  <i>Not a chatbot. An autonomous AI Operating System.</i>
</p>

<br />
<br />

---

<br />

## In One Line

Every AI agent waits for your command.

**Obsidian doesn't.** It scans tasks, dispatches agents, writes files, fixes errors, and plans the next move — all on its own.

<br />

---

<br />

## How Is It Different?

| | Typical AI Agent | ⚫ Obsidian |
|---|---|---|
| 🟢 **Mode** | You ask, it answers | Runs 24/7 autonomously |
| 📋 **Task source** | Your commands | ProactiveExecutor scans queue, auto-creates pipeline tasks |
| 🚀 **Execution** | Single reply | Decomposes → assigns agents → calls tools → writes files → reports |
| 🧠 **Memory** | Conversation history (limited) | 3-tier: working + episodic + semantic + vector retrieval |
| 🩹 **Self-healing** | Error messages | Crash recovery + auto-repair + heartbeat monitoring + restart |
| 🧬 **Evolution** | None | Learns from experience, adjusts behavior over time |
| 📁 **Output** | Text responses | Real files (ebook chapters, research, HTML sites, strategies) |
| 🤖 **Models** | Fixed one | Multi-layer: Free OR → DeepSeek → Local Ollama |
| 🔋 **Uptime** | Ends when you leave | Daemon + watchdog — never stops |

<br />

---

<br />

## Architecture

```
╔═══════════════════════════════════════════════╗
║            Obsidian · AMPM-AIOPS              ║
╚═══════════════════════════════════════════════╝
                     │
     ┌───────────────┼───────────────┐
     │               │               │
  🧠 Brain         📋 Task          👥 Agent
  (Cortex)         (Queue)          (Company)
     │               │               │
  ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
  │Cortex│        │Tracker│        │Dept. │
  │Thalamus│      │Planner│        │Sub-  │
  │Hypothal.│     │Proactive       │Agents│
  └──────┘        │Executor│       │Mission│
                   └──────┘        └──────┘
     │               │               │
  🛡️ Immune       💾 Memory       🔧 Tools
  (Defense)       (Storage)        (Actions)
     │               │               │
  ┌──┴──┐        ┌──┴──┐        ┌──┴──┐
  │Firewall│      │Working│        │Registry│
  │Recovery│      │Episodic│       │Creator│
  │SelfHeal│      │Semantic│       │Sub-   │
  │Supervisor│    │Vector │        │Agent  │
  └──────┘        └──────┘        └──────┘
     │               │               │
  🤖 LLM          🔄 Evolution    ⚙️ Runtime
  (Models)        (Growth)         (Engine)
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

## How It Works

```
                 Obsidian Autonomy Loop
              ┌─────────────────────────┐
              │   ProactiveExecutor     │
              │   (every 15 seconds)    │
              └────────────┬────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
  ┌────────────────┐ ┌────────────┐ ┌──────────────┐
  │ ① Ensure Tasks │ │ ② Execute  │ │ ③ Verify    │
  │ Auto-create    │ │ Priority   │ │ Output files │
  │ pipeline tasks │ │ → Agent    │ │ → Notify     │
  └────────────────┘ └─────┬──────┘ └──────────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │  AgentCompany        │
                  │  Decompose → Assign  │
                  │  → Execute → Verify  │
                  └─────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ Research     │ │ Content      │ │ Engineering  │
  │ web_search   │ │ write_file   │ │ run_command  │
  └──────────────┘ └──────────────┘ └──────────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │  Real File Output   │
                  │  writes to disk via │
                  │  write_file tool    │
                  └─────────────────────┘
```

<br />

---

<br />

## Real Outputs

Obsidian doesn't just talk. **It writes real files:**

```
📂 outputs/
├── 📁 ebooks/
│   ├── 📄 ch03_prompt.md      10KB  ← written by sub-agent
│   └── 📄 ch04.md              7KB  ← written by sub-agent
├── 📁 research/
│   ├── 📄 cloudflare_setup.md
│   ├── 📄 platform_research.md
│   └── 📄 business_strategy.md
├── 📁 children_book/
│   ├── 📄 book1_outline.md
│   └── 📁 product_pages/      20+ product pages
├── 📁 website/
│   └── 📄 index.html, style.css
└── 📁 ai_agent/
    └── ...  service flow docs
```

Every file is written to disk by a sub-agent via the `write_file` tool. Real bytes, real paragraphs, real output.

<br />

---

<br />

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set environment (at least one LLM key)
cp .env.example .env

# 3. Launch (background)
OBSIDIAN_MODE=full nohup python3 main.py > /tmp/heiyao.log 2>&1 &
```

Send `/status` to the Telegram bot to check system health. Obsidian will automatically scan tasks, dispatch agents, and produce files.

To stop:
```bash
pkill -f "python3 main.py"
```

<br />

---

<br />

## Tech Stack

| Category | Technology |
|----------|-----------|
| 🐍 Language | Python 3.11 |
| 📡 Comms | Telegram Bot API + Flask |
| 🤖 LLM | DeepSeek API / OpenRouter / Ollama |
| 🧠 Memory | ChromaDB (vector) + JSON |
| ⚡ Threading | threading + ThreadPoolExecutor |
| ⏱ Scheduler | Custom Scheduler + Token Bucket |
| 💾 Persistence | JSON / filesystem |

<br />

---

<br />

## The Story

His name is Hao. No engineering background. Doesn't understand syntax. In debt. Won't give up.

He built Obsidian piece by piece with AI — because he couldn't find a single AI agent that would truly grow, reflect, and evolve with him.

> [📖 Full Story](STORY_EN.md)
> [📖 完整故事 · 中文](STORY.md)

<br />

---

<br />

## License

| Component | License | Note |
|-----------|---------|------|
| `src/` core framework | MIT | Architecture, Runtime, Memory, Tools |
| `src/core/` commercial | Proprietary | Market analysis, revenue optimization |

<br />

---

<br />

<p align="center">
  <a href="https://github.com/sponsors/chainuncel0712">
    <img src="https://img.shields.io/badge/☕-Buy_Hao_a_coffee-ff69b4?style=for-the-badge" />
  </a>
</p>

<p align="center">
  <sub>
    3 AM. The glow of the screen. He's seen this hundreds of times.<br />
    Now Obsidian executes tasks on its own.<br />
    It's still dumb. But when he looks at it, he sees himself —
  </sub>
  <br /><br />
  <sub>With nothing, but always moving forward.</sub>
</p>
