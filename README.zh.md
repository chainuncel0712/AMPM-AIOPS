# 黑曜 — 系統總覽

## 這是什麼？
Telegram AI Bot 授權系統。用戶付款取得授權碼，在自己的 VPS 上跑黑曜機器人。

---

## 檔案結構

```
AMPM-AIOPS/
├── main.py                  # Bot 入口，啟動 + Telegram 輪詢
├── .env                     # API 金鑰（Telegram token、模型、BscScan）
├── .gitignore               # 排除 kernel 代碼、敏感檔案
├── assets/
│   └── 100.jpg              # 收款 QR Code（BNB Chain）
├── src/
│   ├── config.py            # 設定檔（讀取 .env）
│   ├── license_manager.py   # 授權碼管理（產生/啟用/檢查）
│   ├── payment_verifier.py  # BscScan 自動對帳
│   ├── core/
│   │   └── langgraph_executor.py  # 對話引擎
│   └── ...（kernel 目錄：brain、runtime、memory 等）
└── data/
    └── licenses.json        # 授權碼資料庫（自動產生）
    └── claimed_txids.json   # 已兌換 TXID 記錄（自動產生）
```

---

## 核心運作流程

```
用戶付款（USDT BEP20 到指定錢包）
  → 用戶輸入 /activate <TXID>
  → payment_verifier.py 查 BscScan 驗證
  → license_manager.py 自動產生授權碼 + 啟用
  → Bot 每次訊息檢查 license_manager.check_access()
  → 根據 tier 開放對應功能
```

---

## 三種方案（當前設定）

| 方案 | 價格 | 用戶對象 | 開放功能 |
|------|------|----------|----------|
| 基礎 | $10/月 | 個人嚐鮮 | 基本對話 + 任務執行 |
| 專業 | $25/季 | 常用個人 | 基礎 + 記憶分析 + 檔案處理 |
| 企業 | $300/年 | 公司/工作室 | 全部解鎖 |

價格修改：`main.py` → `/pricing` handler

---

## 手動產生授權碼（管理員用）

如果有人轉帳給你、沒用 TXID 自動開通：

```bash
cd /home/pop5057273712_gmail_com/AMPM-AIOPS
python3 -c "
import sys; sys.path.insert(0, 'src')
import license_manager as lm
uid = int(input('用戶 Telegram ID: '))
days = int(input('天數（30/90/365）: '))
tier = input('方案（basic/pro/enterprise）: ')
key = lm.generate_key(uid, days, tier)
lm.activate(key, uid)
print(f'✅ 授權碼：{key}')
"
```

---

## 錢包

**BNB Chain（BEP20）**
`0x7f3110c1314bD68Fdf8E32cD921E646912108587`

設置於 `src/payment_verifier.py` → `WALLET`

---

## 重要檔案位置

- Bot log：`/tmp/黑曜.log`
- 監控腳本：`/home/pop5057273712_gmail_com/bin/watchdog.sh`（每 20 秒檢查 Bot 是否活著）
- 授權資料：`data/licenses.json`
- 已兌換 TXID：`data/claimed_txids.json`

---

## BscScan API Key

目前設定為 `YourBscScanApiKeyHere`，需要去 https://bscscan.com 註冊免費帳號 → API Keys → 建立 Key → 填入 `.env` 的 `BSCSCAN_API_KEY`。

---

## Git 同步

Cron 每 5 分鐘自動 `git push`。位置：
```bash
crontab -l  # 查看目前設定
```

---

## 其他備註

- 舊的 GITHUB_API_KEY 已過期，要更新的話用 `gh auth login`
- 架構轉移：AMPM-AIOPS 是 public framework，AMPM-KERNEL 是 private 核心
- SDK 套件：`pip install git+https://github.com/chainuncel0712/AMPM-SDK.git`
