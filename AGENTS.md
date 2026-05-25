# AMPM-AIOPS — 專案備忘錄

## 專案定位
Telegram AI Bot 授權系統。用戶付 USDT → 自動開通授權 → 在自己的 VPS 跑 Bot。

## 🌐 完整生態系（2026-05-25 狀態）

| Repository | 可見性 | 狀態 |
|------------|--------|------|
| **AMPM-AIOPS** (public) | 🔓 Public | ✅ 運行中 47/47 器官正常 |
| **AMPM-KEL** (private) | 🔒 Private | ✅ 3 commits, 220+ 源碼檔案 |
| **ampm-core** (public) | 🔓 Public | ✅ v0.1.0, 首次 commit |
| **AMPM-PLUGINS** (public) | 🔓 Public | ✅ 首次 commit, 插件骨架 |
| **AMPM-SDK** (public) | 🔓 Public | ✅ 首次 commit, SDK v0.1.0 |
| **AMPM-DASHBOARD** (public) | 🔓 Public | ✅ 首次 commit, 獨立儀表板 |
| **AMPM-DOCS** (public) | 🔓 Public | ❌ 待建立 |

## 當前運行狀態

### 黑曜主體 (PID 1917061)
- **運行時間**: 1天 5小時+（持續成長中）
- **器官**: 47/47 正常（100%）
- **進化循環**: #2915 次
- **吸收**: 3874 條資訊
- **進化分數**: 4,728,141
- **LLM 供應鏈**: DeepSeek (primary) → NVIDIA NIM (secondary) → Ollama (fallback, 本機未啟動)

### 進化引擎
```
🧬 進化循環 #2915
📥 吸收: 3874 條
✅ 好的: 3723 條
❌ 排除: 151 條
📊 進化分數: 4728141
📚 累積好資訊: 200 條
```

### 器官清單（每 300 秒健康檢查）
```
memorymanager, toolsystem, agent_company, modelcapability,
breathsystem, nosesystem, compass, decisionrecorder,
tasktracker, circuitcontroller, monitor, evolution_cycle,
eventbus, scheduler, vitalmonitor, firewall, breaker,
contradiction, self_heal, muscle, tool_registry, tool_creator,
hypothalamus, persona, cortex, wardrobe, face, voice,
birth, agent_template, placenta, nursery, plugin_loader,
memory_cleaner, tool_garbage, log_rotator, websearch,
self_awareness, rebirth, inheritance, input_guard,
conversation, feedback_learn, crash_recovery, task_planner,
performance_profiler, memory, evolution_module
```

## 當前方案（定價）
| 方案 | 價格 | 天數 |
|------|------|------|
| 月 | $15 | 30 |
| 季 | $39 | 90 |
| 年 | $120 | 365 |

付錢全解鎖，不分級。

## 錢包（收款）
- BNB Chain BEP20: `0x7f3110c1314bD68Fdf8E32cD921E646912108587`
- 設定在 `src/payment_verifier.py` 的 `WALLET`

## 運作流程
用戶付 USDT → 貼 TXID → `/activate <TXID>` → BscScan 驗證 → 自動開通

## Telegram Bot Token（已測試且運行中）
| 角色 | Token | 狀態 |
|------|-------|------|
| 黑曜（主 Bot） | (已設定於 .env) | ✅ 運行中 (PID 1917061) |
| 售後服務 | (已設定於 .env) | ✅ 可使用 |

## 主要檔案
- `main.py` — Bot 入口
- `service_bot.py` — 售後服務客服
- `src/config.py` — 設定（讀 .env）
- `src/license_manager.py` — 授權碼管理
- `src/payment_verifier.py` — BscScan 對帳
- `src/support.py` — FAQ 客服引擎
- `data/licenses.json` — 授權資料庫
- `data/faq.json` — FAQ 知識庫

## 服務管理
- 主 Bot PID: 1917061
- 主 Bot log: `/tmp/黑曜.log`
- 服務 Bot: `python3 service_bot.py`
- Watchdog: `/home/pop5057273712_gmail_com/bin/watchdog.sh`

## 待辦 / 已知問題
1. BscScan API Key 仍是佔位符（需要去 bscscan.com 申請免費 Key）
2. Ollama 本機未啟動（非必要，但有 DeepSeek/NVIDIA 備援）
3. 儀表板 flask-cors 未安裝（已修復，重啟 Bot 後生效）
4. `dashboard/pricing.html` 舊版定價 ($29/$99/$199) 需處理或刪除

## 商業模式
- 賣 Bot 授權，不是賣程式碼
- 用戶自備 VPS，你收授權費
- 核心競爭力：持續更新 + 技術支援
- 防盜版靠服務，不靠技術鎖
