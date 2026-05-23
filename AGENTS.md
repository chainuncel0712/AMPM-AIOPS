# AMPM-AIOPS — 專案備忘錄

## 專案定位
Telegram AI Bot 授權系統。用戶付 USDT → 自動開通授權 → 在自己的 VPS 跑 Bot。

## 架構
- **AMPM-AIOPS** (public): 框架 + 授權 + 付款
- **AMPM-KERNEL** (private): 核心智能 (brain/runtime/decisions)
- **AMPM-SDK** (public): Plugin 開發套件
- **AMPM-PLUGINS/DOCS/DASHBOARD** (public): 生態系

## 當前方案（定價）
| 方案 | 價格 | 天數 |
|------|------|------|
| 月 | $15 | 30 |
| 季 | $39 | 90 |
| 年 | $168 | 365 |

付錢全解鎖，不分級。

## 錢包（收款）
- BNB Chain BEP20: `0x7f3110c1314bD68Fdf8E32cD921E646912108587`
- 設定在 `src/payment_verifier.py` 的 `WALLET`

## 運作流程
用戶付 USDT → 貼 TXID → `/activate <TXID>` → BscScan 驗證 → 自動開通

## BscScan API
- 需要去 https://bscscan.com 註冊免費帳號 → API Keys 建立 Key
- 填入 `.env` 的 `BSCSCAN_API_KEY`
- 目前是 `YourBscScanApiKeyHere`（佔位符）

## Telegram Bot Token（已測試）
| 角色 | Token | 狀態 |
|------|-------|------|
| 黑曜（主 Bot） | (已設定於 .env) | ✅ 運行中 |
| 售後服務 | (已設定於 .env) | ✅ 可用 |
| 戰略長 | (已設定於 .env) | ✅ |
| 營運經理 | (已設定於 .env) | ✅ |
| 市場分析師 | (已設定於 .env) | ✅ |
| 銷售總監 | (已設定於 .env) | ✅ |
| 技術支援 | (已設定於 .env) | ✅ |
| 客戶成功 | (已設定於 .env) | ✅ |
| 財務總監 | (已設定於 .env) | ✅ |
| 資源協調員 | (已設定於 .env) | ✅ |
| 行政監管 | (已設定於 .env) | ✅ |
| 入職引導 | (已設定於 .env) | ✅ |
| ❌ 老闆/技術長/業務/EA/啟淵 | Unauthorized |

## 主要檔案
- `main.py` — Bot 入口
- `service_bot.py` — 售後服務客服（token 問題待修）
- `src/config.py` — 設定（讀 .env）
- `src/license_manager.py` — 授權碼管理
- `src/payment_verifier.py` — BscScan 對帳
- `src/support.py` — FAQ 客服引擎
- `data/licenses.json` — 授權資料庫
- `data/claimed_txids.json` — 已兌換 TXID
- `data/faq.json` — FAQ 知識庫

## 服務管理
- 主 Bot PID: `pgrep -f "python3.*main.py"`
- 主 Bot log: `/tmp/黑曜.log`
- 服務 Bot: `service_bot.py`（token 問題待修）
- 服務 Bot log: `/tmp/service_bot.log`
- Watchdog: `/home/pop5057273712_gmail_com/bin/watchdog.sh`
- Cron auto-sync: `*/5 * * * *` git push

## 待辦 / 已知問題
1. Service bot token 驗證失敗（`InvalidToken`），但 token 本身有效（HTTP API 測試 OK），懷疑是 python-telegram-bot 版本或 env 載入順序問題
2. BscScan API Key 尚未申請，目前是佔位符
3. 4 個舊 repo 待刪除（需 `delete_repo` scope 或從 GitHub web 手動刪）

## 使用方式（管理員）
```bash
# 手動產生授權碼
cd /home/pop5057273712_gmail_com/AMPM-AIOPS
python3 -c "
import sys; sys.path.insert(0, 'src')
import license_manager as lm
uid = int(input('用戶 ID: '))
days = int(input('天數: '))
tier = input('方案 (basic/pro/business): ')
key = lm.generate_key(uid, days, tier)
lm.activate(key, uid)
print(f'授權碼: {key}')
"
```

## 商業模式
- 賣 Bot 授權，不是賣程式碼
- 用戶自備 VPS，你收授權費
- 核心競爭力：持續更新 + 技術支援
- 防盜版靠服務，不靠技術鎖
