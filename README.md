<p align="center"><img src="assets/300.png" width="160"></p>

<h1 align="center">AMPM-AIOPS</h1>
<h3 align="center" style="color:#e94560; letter-spacing:4px;">AI OPERATING SYSTEM · 自動賺錢的 AI 系統</h3>

<p align="center">
  <strong>不是 chatbot，不是 agent 框架。</strong><br>
  是一台在 VPS 上 24 小時自主運作、<strong>自動出版賺錢</strong>的 AI 作業系統。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram" />
  <img src="https://img.shields.io/badge/LLM-7+%20Providers-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Organs-66-red?style=flat-square" />
  <img src="https://img.shields.io/badge/License-Commercial-gold?style=flat-square" />
</p>

<p align="center">
  <a href="#-它能做什麼">它能做什麼</a> •
  <a href="#-已證實的成果">已證實成果</a> •
  <a href="#-架構">架構</a> •
  <a href="#-商業授權--定價">定價與授權</a> •
  <a href="#-快速開始">快速開始</a> •
  <a href="#-生態系">生態系</a>
</p>

---

## 🚀 它能做什麼

| 功能 | 說明 | 狀態 |
|------|------|------|
| **自動出版電子書** | 選題 → 寫作 → 排版 → 上架 KDP / Readmoo，全自動 | ✅ 上線中 |
| **自動交易** | Gate.io 多指標策略，24h 掃盤自動下單，內建風控 | ✅ 上線中 |
| **Telegram AI 助理** | 記憶對話、主動提商業建議、執行工具指令 | ✅ 上線中 |
| **品牌 IP 管理** | 雙貓 IP（AM&PM Adventure）封面/周邊圖自動生成 | ✅ 上線中 |
| **多模型 LLM 路由** | FreeModel / DeepSeek / NVIDIA / OpenRouter 7 層備援 | ✅ 上線中 |
| **自我進化** | 每週自動優化選題策略、定價、寫作品質 | ✅ 上線中 |

---

## 📊 已證實的成果

```
📚 已產出書籍：  《小狐狸的第一個存錢罐》等童書 IP
🤖 系統器官數：  66 個器官 · 正常率 100%
💹 自動交易：    104 筆 · 勝率 59% · 已實現盈虧 +$2.10 USDT (持續累積)
⚙️ 運行時間：    24/7 無中斷（VPS 自動重啟守護）
🔗 整合平台：    Amazon KDP · Readmoo · Gate.io · Cloudflare · 7 個 LLM
```

> 系統仍在成長。每一週自動進化，數字持續更新。

---

## 🧬 架構

這是「開放表層 + 私有核心」的雙層設計：

```
┌─────────────────────────────────────────────────┐
│              AMPM-AIOPS (本倉庫，公開)            │
│   Telegram Bot · 授權 · 付款 · 監控 · 出版管線    │
└──────────────────┬──────────────────────────────┘
                   │  import (私有，不隨倉庫分發)
          ┌────────▼──────────┐
          │   AMPM-KERNEL     │  ← 真正的大腦
          │  Brain · Runtime  │    購買完整授權才取得
          │  Governance · Evo │
          └───────────────────┘
```

### 66 個器官分工（部分展示）

| 層級 | 器官 | 功能 |
|:---|:---|:---|
| 🧠 大腦 | Cortex · Thalamus · Memory | 思考、路由、記憶 |
| ⚙️ 執行 | MuscularExecutor · ToolChain | 工具調用、工作流 |
| 📚 出版 | PipelineEngine · Publisher | 電子書/童書全自動流水線 |
| 💹 交易 | AutoSniper · RiskManager | 多指標掃盤、風控下單 |
| 🛡️ 防護 | Governance · Gatekeeper · Immune | 權限、免疫、自我修復 |
| 🔄 進化 | EvolutionEngine · LearningEngine | 每週自動優化 |
| 👁️ 感知 | Eye(WebSearch) · Ear · Nose | 外部資訊獲取與過濾 |

---

## 💰 商業授權 & 定價

> 本專案採**商業授權**，原始碼免費閱讀，部署需授權。

| 方案 | 價格 | 包含 |
|:---|:---|:---|
| **開發者** | $49 USDT | AIOPS 公開層 · 部署授權 · 6 個月更新 |
| **完整版** | $149 USDT | AIOPS + KERNEL 核心 · 1 年更新 · 私訊技術支援 |
| **白牌授權** | 洽談 | 品牌替換 · 商業再分發 · 客製化 |

📬 **購買 / 詢問**：Telegram [@ampm_ops](https://t.me/ampm_ops) 或 [info@ampm-aiops.com](mailto:info@ampm-aiops.com)

---

## ⚡ 快速開始

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/AMPM-AIOPS
cd AMPM-AIOPS

# 2. 建立虛擬環境
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 複製並填寫設定
cp .env.example .env
# 至少填入：TELEGRAM_TOKEN_OBSIDIAN · AUTHORIZED_USER_IDS · 任一 LLM KEY

# 4. 啟動
./venv/bin/python3 main.py
```

> **最低需求**：一台 VPS（1 vCPU / 1GB RAM）+ Telegram Bot Token + 任一免費 LLM API

---

## 🌐 生態系

| 倉庫 | 說明 |
|:---|:---|
| **AMPM-AIOPS** (本倉庫) | 主框架，Telegram Bot + 出版管線 |
| **AMPM-KERNEL** (私有) | 真正的 AI 大腦，購買完整版授權後取得 |
| **AMPM-SDK** | 開發者 SDK，自行開發插件 |
| **AMPM-PLUGINS** | 社群插件生態 |
| **AMPM-DASHBOARD** | 獨立監控 UI |

---

## 🙋 FAQ

**Q：免費版和完整版差在哪？**  
A：免費版（本倉庫）可以跑 Telegram Bot + 出版管線。完整版多了 KERNEL：完整記憶系統、自我進化、Cortex 大腦、LLM 智能路由——這些讓系統真正能「自己越變越強」。

**Q：需要多少技術能力？**  
A：能用指令列、填 .env、在 VPS 跑 Python 即可。提供部署說明文件。

**Q：LLM 費用貴嗎？**  
A：系統預設走免費的 FreeModel (gpt-5.4 等級) 和 DeepSeek，日常使用幾乎 $0。

**Q：自動交易安全嗎？**  
A：內建多重風控（單筆止損、日虧上限、倉位上限）。仍有虧損風險，請小額測試。

---

## 📄 授權聲明

本專案採 **AMPM Commercial License**（見 [LICENSE](LICENSE)）。  
原始碼可供學習閱讀，**部署、商業用途、再分發需取得授權**。

---

<p align="center">
  <strong>AM&PM ADVENTURE</strong> · 雙猫 IP · 自動出版 · AI 變現<br>
  <a href="https://t.me/ampm_ops">Telegram</a> · <a href="mailto:info@ampm-aiops.com">Email</a>
</p>
