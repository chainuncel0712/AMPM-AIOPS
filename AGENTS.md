# AMPM-AIOPS — 專案備忘錄

## 專案定位
Telegram AI Bot 授權系統 + 三條自動出版管線。用戶付 USDT → 自動開通授權 → 在自己的 VPS 跑 Bot。

## 🌐 完整生態系（2026-05-25 更新）

| Repository | 可見性 | 狀態 |
|------------|--------|------|
| **AMPM-AIOPS** (public) | 🔓 Public | ✅ 運行中 50 機械組件正常 |
| **AMPM-KEL** (private) | 🔒 Private | ✅ 3 commits, 220+ 源碼檔案 |
| **ampm-core** (public) | 🔓 Public | ✅ v0.1.0, 首次 commit |
| **AMPM-PLUGINS** (public) | 🔓 Public | ✅ 首次 commit, 插件骨架 |
| **AMPM-SDK** (public) | 🔓 Public | ✅ 首次 commit, SDK v0.1.0 |
| **AMPM-DASHBOARD** (public) | 🔓 Public | ✅ 首次 commit, 獨立儀表板 |
| **AMPM-DOCS** (public) | 🔓 Public | ❌ 待建立 |

## 🏭 出版工廠架構（2026-05-25 新增）

### 新增 3 個出版機械組件（原 47 → 現 50）

| 機械組件 | 檔名 | 功能 | 頻率 |
|------|------|------|------|
| 🦅 **ResourceScout** | `src/resource_scout.py` | 外出找免費優質資源（圖片/字型/API/趨勢/工具） | 每 1 小時 |
| 🏭 **PublisherEngine** | `src/pipeline_engine.py` | 統一出版循環引擎，整合電子書/童書/客服網站三條產線 | `/publish cycle` |
| 🛡️ **PipelineSupervisor** | `src/pipeline_supervisor.py` | 品質監督/停滯偵測/生產力指標 | 每 30 分鐘 |

### 三條產線循環

```
ResourceScout (資源補充)
    ↓
PublisherEngine.auto_cycle
    ├── EbookPipeline  (電子工具書)
    │   ├── trend_analysis → select_topic → generate_outline
    │       │   ├── write_content → compile_epub → quality_gate → submit_for_review
    │   └── approve → publish (Amazon KDP + 14 平台)
    ├── KidBookPipeline (童書)
    │   ├── trend_analysis → select_theme → create_characters
    │       ├── write_story → compile_epub → quality_gate → submit_for_review
    │   └── approve → publish (Amazon KDP + 14 平台)
    └── ServiceWebsitePipeline (AI 客服網站)
        ├── create_site → auto_deploy → record_order
        └── handle_ticket → upgrade → renew
            ↓
PipelineSupervisor (品質檢查 + 停滯預警)
    ↓
Telegram 日報 (每 10 分鐘)
```

### 品質原則
- **單一執行權威**：ExecutionContext 是唯一決策者，所有機械組件只能 observe，不能 override
- **不跳過不卡住**：失敗自動重試 3 次，絕不跳過步驟
- **人工審核閘門**：所有內容到 `pending_review` 停住，等人類批准才能上架
- **品質監督只報警不阻擋**：標記問題但不阻擋流程

### Telegram 指令
```
/publish status                  — 三條產線即時狀態
/publish cycle                   — 執行一次完整循環
/publish ebook trend             — 電子書市場趨勢
/publish kidbook trend           — 童書市場趨勢
/publish ebook select <主題>      — 新選題
/publish kidbook select <書名> <主題> <年齡>
/publish approve <book_id>       — 批准上架
/publish reject <book_id> <原因>  — 退回
/publish supervisor inspect      — 品質體檢
/publish resource scout          — 資源偵查
/publish resource status         — 資源庫狀態
/publish auto on <小時>          — 啟動自動循環
/publish auto off                — 停止自動循環
```

## 當前運行狀態

### 黑曜主體
- **PID**: 2807917
- **運行時間**: 持續成長中
- **機械組件**: 50/50 正常（47 原有 + 3 新出版機械組件）
- **LLM 供應鏈**: DeepSeek (primary) → NVIDIA NIM (secondary) → Ollama (fallback, 本機未啟動)
- **Dashboard**: http://localhost:5050 ✅
- **Log**: `/tmp/黑曜.log`
- **看門狗**: 每 15 分鐘檢查
- **日報**: 每 10 分鐘 Telegram 推播
- **資源偵查**: 每 1 小時外出
- **品質監督**: 每 30 分鐘檢查

### 資源庫狀態
- 免費圖片: 5 來源 (Unsplash, Pexels, Pixabay, Openverse, Stable Diffusion)
- 插畫/向量: 5 來源 (Humaaans, unDraw, ManyPixels, OpenDoodles, FreeSVG)
- 免費字型: 4 來源 (Google Fonts, Noto Sans TC, LXGW WenKai, 思源字型)
- 圖示/SVG: 4 來源 (Tabler, Feather, Lucide, SVG Repo)
- 免費 API: 7 來源 (DeepSeek, NVIDIA, OpenRouter, HuggingFace, Replicate, Stability AI, Gemini)
- 趨勢來源: 5 來源 (Google Trends, Amazon, Readmoo, Kobo, 博客來)
- 開源工具: 7 來源 (GitHub, Calibre, EPUBCheck, Kindle Previewer, Inkscape, GIMP, Krita)

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

## Telegram Bot Token
| 角色 | Token | 狀態 |
|------|-------|------|
| 黑曜（主 Bot） | (已設定於 .env) | ✅ 運行中 (PID 2807917) |
| 售後服務 | (已設定於 .env) | ✅ 可使用 |

## 主要檔案

### 核心系統
- `main.py` — Bot 入口（含日報排程、資源偵查啟動、品質監督啟動）
- `service_bot.py` — 售後服務客服
- `src/config.py` — 設定（讀 .env）
- `src/license_manager.py` — 授權碼管理
- `src/payment_verifier.py` — BscScan 對帳
- `src/support.py` — FAQ 客服引擎

### 執行引擎
- `src/runtime/execution_context.py` — 單一執行權威，6 階段管線（security→intent→route→execute→respond→remember），已整合 pipeline intent

### 出版管線（新增）
- `src/pipeline_engine.py` — 統一出版引擎，管理三條產線的循環
- `src/pipeline_service.py` — AMPM-AIOPS.COM 客服網站專用管線
- `src/resource_scout.py` — 資源偵查機械組件，管理 37 個免費資源來源
- `src/pipeline_supervisor.py` — 品質監督機械組件，計算完成率與停滯監控

### 資料檔案
- `data/licenses.json` — 授權資料庫
- `data/faq.json` — FAQ 知識庫
- `data/pipeline/` — 出版管線資料（ebooks, kidbooks, service sites, cycle log）
- `data/supervisor/` — 品質監督審計與停滯紀錄
- `data/resources/` — 資源庫目錄

## 服務管理
- 主 Bot PID: 2807917
- 主 Bot log: `/tmp/黑曜.log`
- 服務 Bot: `python3 service_bot.py`
- 看門狗: `/home/pop5057273712_gmail_com/bin/watchdog.sh`（每 15 分鐘）
- Dashboard: http://localhost:5050

## 待辦 / 已知問題
1. BscScan API Key 仍是佔位符（需要去 bscscan.com 申請免費 Key）
2. Ollama 本機未啟動（非必要，但有 DeepSeek/NVIDIA 備援）
3. 出版管線目前用模板內容（離線測試），上線後接 DeepSeek LLM 生成真實內容
4. 童書插圖尚未接入真實圖片生成 API（需整合 Stable Diffusion / DALL-E）
5. AMPM-AIOPS.COM 網站尚未建置（domain 已保留但尚未部署）
6. `dashboard/pricing.html` 舊版定價 ($29/$99/$199) 需處理或刪除

## 核心設計原則
- **單一執行權威**：ExecutionContext 是唯一決策者，禁止任何機械組件修改 execution path
- **不跳過**：失敗自動重試（最多 3 次），絕不跳過未完成的書
- **只觀察不阻擋**：監督機械組件只能報警，不能 halt 流程
- **人工審核閘門**：所有內容必須人類批准才能上架
- **資源自給自足**：ResourceScout 確保 37 個免費來源永遠活著

## 商業模式
- 賣 Bot 授權，不是賣程式碼
- 用戶自備 VPS，你收授權費
- 核心競爭力：持續更新 + 技術支援 + 自動出版管線
- 防盜版靠服務，不靠技術鎖
