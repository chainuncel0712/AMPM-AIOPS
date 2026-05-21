# 黑曜商業版設定指南

## 1. 設定環境變數

```bash
# 必要：金鑰 HMAC 密鑰（一定要換）
export AMPM_LICENSE_SECRET="your-random-secret-here"

# 選用：Lemon Squeezy（付款自動發金鑰）
export LEMON_SQUEEZY_SECRET="whsec_xxxxx"
export LEMON_SQUEEZY_API_KEY="your-api-key"

# 選用：Stripe（傳統付款）
export STRIPE_SECRET_KEY="sk_xxxxx"
```

## 2. 產生授權金鑰

```bash
# 產生專業版金鑰（365 天）
python scripts/manage_license.py generate pro

# 產生企業版金鑰
python scripts/manage_license.py generate enterprise

# 自訂有效期
python scripts/manage_license.py generate enterprise --days 180

# 驗證金鑰
python scripts/manage_license.py validate AMPM-PRO-xxxx-xxxx

# 列出各版本功能
python scripts/manage_license.py list
```

## 3. 上架商品 (Lemon Squeezy)

1. 註冊 [Lemon Squeezy](https://lemonsqueezy.com)
2. 建立商品 → 建立兩個 variant：
   - **黑曜專業版** — $29/月 (或 $290/年)
   - **黑曜企業版** — $99/月 (或 $990/年)
3. 到 Store → Webhooks 新增：
   - URL: `https://你的網址/api/commerce/lemon-webhook`
   - Events: `order_created`, `subscription_created`
4. 把 variant ID 填入 `src/commerce/lemon.py` 的 `VARIANT_TIERS` 對照表

## 4. 版本比較

| 功能 | 社群版 🆓 | 專業版 💎 | 企業版 🏢 |
|------|:--------:|:--------:|:--------:|
| 核心器官 | 30 個 | 40 個 | 50 個 |
| 自我診斷 / 修復 | ✅ | ✅ | ✅ |
| Telegram Bot | ✅ | ✅ | ✅ |
| 記憶系統 | 短期+長期 | 完整 | 文明級 |
| 工具系統 | 162 個 | 200+ 個 | 250+ 個 |
| SEO / 廣告零件 | - | ✅ | ✅ |
| AI 內容生成 | - | ✅ | ✅ |
| 雲端託管服務 | - | - | ✅ |
| 專屬技術支援 | - | ✅ | ✅ |
| 定製新零件 | - | - | ✅ |
| SLA 保障 | - | - | ✅ |
| **價格** | **免費** | **$29/月** | **$99/月** |

## 5. 買家如何使用

買家收到金鑰後：

```bash
# 方式一：環境變數（推薦）
export AMPM_LICENSE_KEY="AMPM-PRO-xxxx-xxxx"
python main.py

# 方式二：寫入設定檔
echo '{"tier": "pro", "key": "AMPM-PRO-xxxx-xxxx"}' > data/license.json
```

系統啟動時會自動驗證金鑰並解鎖對應功能。
