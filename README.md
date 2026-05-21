<div align="center">
  <h1>🧬 AI-BOS</h1>
  <p><strong>Artificial Intelligence Body Operating System</strong></p>
  <p><em>世界第一個 AI 生命體作業系統</em></p>
</div>

---

## 什麼是 AI-BOS？

AI-BOS（Artificial Intelligence Body Operating System）是一個以**生物體架構**為設計哲學的 AI 生命體作業系統。

有別於傳統 AI Agent 框架（LangChain、CrewAI、AutoGen）的函數呼叫與管線思維，AI-BOS 將 AI 系統視為一個**完整的生命體**，由 54+ 個器官協同運作：

| 系統 | 器官 | 功能 |
|------|------|------|
| 🧠 中樞神經 | brain, cortex, thalamus | 決策、路由、訊息中繼 |
| 💾 記憶系統 | memory, hippocampus, civilization_memory | 工作/語義/文明三層記憶 |
| 🛡️ 免疫系統 | firewall, breaker, guard, sandbox | 安全防護、異常檢測 |
| 🔬 感知系統 | nose, breath, compass | 環境感知、方向判斷 |
| 💪 行動系統 | muscle, executor, tools | 工具執行、行動力 |
| 🔄 循環系統 | blood, circulatory, scheduler | 訊息傳遞、排程 |
| 🧬 演化系統 | evolution, self_evolve, meta_cognition | 自我演化、後設認知 |
| ⚖️ 治理系統 | gatekeeper, control_plane, audit | 權限控制、審計追蹤 |
| 🔧 修復系統 | repair_orchestrator, self_heal | 自我修復、復原編排 |

## 🏗️ 架構圖

```
使用者輸入
    │
    ▼
┌──────────────┐
│  皮膚 (skin)  │  ← 對外介面層
│  嗅覺 (nose)  │
└──────┬───────┘
       │
┌──────▼───────┐
│  大腦 (brain) │  ← 中樞決策層
│  皮質 (cortex)│
└──────┬───────┘
       │
┌──────▼───────┐
│  免疫系統     │  ← 安全防護層
│  治理層       │
│  隔離層       │
└──────┬───────┘
       │
┌──────▼───────┐
│  記憶系統     │  ← 記憶層
│  演化系統     │
└──────┬───────┘
       │
┌──────▼───────┐
│  肌肉 (muscle)│  ← 執行層
│  工具 (tools) │
└──────────────┘
```

## 🔄 行為流程

### 啟動流程
1. DNA 載入 → 器官註冊表初始化
2. 器官掃描與註冊（54+ 器官）
3. 啟動自檢（寫入 startup_diagnosis.json）
4. 背景任務啟動（心跳、監視、演化循環）

### 決策流程
1. 使用者輸入 → 嗅覺感知（nose）→ 資訊增強
2. 呼吸調節（breath）→ 模型選擇與呼叫
3. 安全檢查（gatekeeper + 免疫系統）
4. 記憶檢索（memory）→ 上下文建構
5. LLM 推理 → 工具選擇與執行
6. 自我反省（self_reflect）→ 回覆輸出
7. 自我演化（self_evolve）→ 經驗寫入記憶

### 修復流程
1. 監視器（monitor）偵測異常
2. 免疫系統診斷問題類型
3. 修復編排器（repair_orchestrator）執行修復
4. 事件記錄（event_log）寫入審計軌跡

## 🚀 如何啟動

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定環境
cp .env.example .env
# 編輯 .env 填入 LLM API Keys

# 3. 啟動系統
python3 main.py

# 4. 測試
PYTHONPATH=src python3 tests/test_lifecycle_baseline.py
```

## 🔧 需求

- Python 3.10+
- LLM API Key（DeepSeek / Gemini / OpenAI / Ollama）
- Linux / macOS（部分功能需 POSIX 支援）

## 🧩 如何擴展

### 建立新器官

```python
from ai_bos.core import Organ

class MyOrgan(Organ):
    def __init__(self):
        super().__init__("my_organ")

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
```

在 Obsidian 中註冊：

```python
obsidian.organs_registry.add(MyOrgan())
```

### 擴展工具

```python
@tool(name="my_tool", description="我的自訂工具")
def my_tool(param: str) -> str:
    return f"處理結果: {param}"
```

## 📖 目錄結構

```
ai-bos/
├── core/              # 核心抽象層（Organ 介面、Lifecycle）
├── organs/            # 器官系統目錄
│   ├── brain/         # 中樞決策
│   ├── memory/        # 記憶管理
│   ├── tools/         # 工具系統
│   ├── skin/          # 對外介面
│   ├── muscle/        # 行動執行
│   ├── blood/         # 訊息傳遞
│   ├── breath/        # 呼吸調節
│   └── nose/          # 感知系統
├── lifecycle/         # 生命週期流程
├── executor/          # 執行器
└── docs/              # 文件
```

## ⚖️ 授權條款

本專案採用 **AGPL v3 + 自訂條款**：

- ✅ 自由使用、修改、分享（遵守 AGPL）
- ❌ 禁止商業用途（需另外授權）
- ❌ 禁止使用 "AI-BOS" 與 "AMPM" 商標於商業產品
- ✅ 開源專案與學術研究完全免費

詳見 [LICENSE](./LICENSE)、[COPYRIGHT](./COPYRIGHT)、[TRADEMARK](./TRADEMARK)。

## 📬 聯絡

- 問題回報：[GitHub Issues](https://github.com/chainuncel0712/AMPM-AIOPS/issues)
- 商業授權：chainuncel0712@gmail.com

---

<div align="center">
  <p><strong>AI-BOS：讓 AI 不只是工具，而是一個生命。</strong></p>
</div>
