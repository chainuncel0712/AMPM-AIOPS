# AMPM-AIOPS — 黑曜 (Obsidian)

[![Sponsor](https://img.shields.io/badge/贊助-❤️-ff69b4)](https://github.com/sponsors/chainuncel0712) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> A Modular AI Operating System. Runtime. Multi-agent. Self-healing. Long-term memory. Built for VPS.

---

## 一句話

普通的 AI 對話框，聊完就忘，只會給建議。

黑曜不一樣：它會記住你、能自己拆任務、能派 Agent 去執行、出錯會自己修、還會從經驗中進化。

---

## 技術定位

AMPM-AIOPS 是一個**模組化的 AI 作業系統（AIOS）**，設計目標是在 VPS 上持續自主運作。

它**不是**一個聊天機器人，也**不是** AGI。

它是：

| 能力層 | 說明 |
|--------|------|
| **Runtime** | 生命週期狀態機，管理 IDLE → OBSERVE → THINK → ... → EVOLVE 全循環 |
| **Orchestration** | 中樞調度，任務路由、Agent 協調、負載平衡 |
| **Multi-Agent** | 多代理系統，可動態建立/釋放部門與 Agent，自動拆解並分派任務 |
| **Self-Healing** | 回覆失敗自動修復，系統異常自動復原 |
| **Memory** | 三層記憶架構（工作/情節/語義），支援向量檢索、自動整理與遺忘 |
| **Tooling** | 內建工具系統、Tool Creator（自動生成工具）、Plugin SDK |
| **Evolution** | 進化循環，從經驗中學習並優化參數（含沙盒防護） |
| **Multi-Model** | 多層 LLM 備援（ATXP → DeepSeek → OpenRouter → NVIDIA → Ollama） |

---

## 系統架構

```
src/
├── brain/         # 大腦皮層：思考、決策、LLM 呼叫
├── memory/        # 記憶系統：工作記憶、情節記憶、語義記憶
├── immune/        # 免疫系統：防火牆、矛盾檢測、自我修復
├── muscle/        # 肌肉系統：工具執行、Agent 管理
├── nerve/         # 神經系統：網路搜尋、外部感知
├── blood/         # 數據匯流排：事件總線、排程器
├── core/          # 核心模組：進化循環、任務規劃、效能監控
├── skin/          # 介面層：人格、語音、介面
├── womb/          # 模組工廠：Agent 建立、插件載入
├── skeleton/      # 骨架：基礎類別、註冊表、DNA
├── compass/       # 方向感測器：KPI 追蹤、目標管理
└── meta/          # Meta 層：世界模型、系統意識、進化治理
```

---

## 進階商業模組

核心框架為 MIT 開源，以下商業模組另有授權：

- **行銷自動化**：Email 行銷、社群管理、SEO、廣告投放
- **內容出版**：自動寫文章、電子書出版
- **加密貨幣**：錢包管理、跨鏈橋接、Gas 追蹤、合約審計
- **NFT 工具**：狙擊手、鯨魚追蹤、地板掃描、空投檢查
- **企業 SaaS**：多租戶系統、API 金鑰管理、CRM

---

## 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp .env.example .env
# 編輯 .env，至少填入一個 LLM API Key
```

### 3. 啟動
```bash
python main.py      # 完整版（含 LangGraph、儀表板）
python bot.py       # 輕量版（純 Telegram Bot）
```

---

## 誰適合使用

- 需要在 **VPS 上長期自主運作** AI 系統的開發者
- 想研究 **Multi-Agent 架構** 與 **Runtime 狀態機** 的工程師
- 需要 **自動化商業流程**（行銷、加密貨幣、內容出版）的創業者
- 不想被綁在某個雲端服務上，希望**完全掌控自己 AI** 的人

---

## 開源與授權

| 部分 | 授權 | 說明 |
|------|------|------|
| `src/` 核心框架 | MIT | 器官架構、Runtime、記憶系統、工具系統 |
| `src/core/` 商業模組 | Proprietary | 市場分析、營收優化、NFT 工具等 |

---

## 誰做的

一個沒有工程背景的人，賣掉房子，全職做了八個月。

沒有團隊，沒有資金，只有一個終端機、一個 AI 對話框、和一個不想放棄的念頭。

[❤️ 支持這個專案](https://github.com/sponsors/chainuncel0712)
