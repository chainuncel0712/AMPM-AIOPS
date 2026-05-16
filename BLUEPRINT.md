# 黑曜機械人 (HeiYao) — 器官藍圖

## 專案定位
AI Agent 仿生架構 — 每個目錄/檔案對應生物器官，實現自我進化、自我修復。

---

## 目錄總覽（95 器官）
```
src/
├── brain/     (5)  中樞神經 — 核心決策
├── nerve/     (4)  感知系統 — 多模態輸入
├── blood/     (3)  循環系統 — 事件驅動
├── muscle/    (3)  肌肉系統 — 工具執行
├── immune/    (3)  免疫系統 — 容錯保護
├── circuit/   (2)  電路保護 — 第二層容錯（合併 immune 後的 breaker）
├── skin/      (4)  外皮 — 人格/外觀
├── womb/      (4)  子宮 — Agent 生成/進化
├── waste/     (3)  排泄 — 清理/回收
├── bag/       (2)  囊袋 — 外掛/搜尋
├── web/       (1)  網路 — 搜尋介面
├── skeleton/  (8)  骨架 — 基礎框架
├── core/      (32) 核心業務 — Web3/NFT/行銷
├── decisions/ (1)  決策記錄
├── tasks/     (1)  任務追蹤
├── compass/   (1)  方向指南
├── organs/    (2)  備用器官（memory 空殼，待實作）
├── pro/       (1)  授權模組
├── dashboard/ (1)  控制面板
├── [root].py  (13) 頂層獨立器官
└── data/      (7)  狀態持久化
```

---

## 一、中樞神經系統（src/brain/）

### 1.1 cortex.py — 大腦皮層（核心已實作，需重構路徑引用）
- **職責**: 高級認知，接收輸入 → 防火牆檢查 → LLM 推理 → 工具執行 → 自我反思 → 回覆
- **依賴**: llm, memory, compass, decisions, tasks, executor, registry, persona, firewall, breaker, eye, self_review, self_repair
- **輸入**: user_msg: str
- **輸出**: str (回覆)
- **狀態**: ✅ 完整（325行），需更新 import 路徑

### 1.2 thalamus.py — 丘腦（已實作，需確認）
- **職責**: 訊息中繼，接收 Telegram/webhook 訊息，路由到 cortex
- **依賴**: cortex, handler
- **狀態**: ⚠️ 需檢查內容

### 1.3 hypothalamus.py — 下丘腦（合併，只留 src/brain/）
- **職責**: 定時任務排程 — 每30分鐘 sniff、每6小時清理記憶、每24小時成長報告
- **狀態**: ⚠️ 有兩份（brain + core），需合併到 brain/，刪除 core/

### 1.4 self_repair.py — 自我修復（已實作）
- **職責**: 檢查死掉的器官，嘗試重新初始化
- **依賴**: skeleton.assembler
- **狀態**: ✅ 完整

### 1.5 self_review.py — 自我反思（已實作）
- **職責**: 每次回覆後自我評估，寫入記憶
- **依賴**: llm, contradiction
- **狀態**: ✅ 完整

---

## 二、感知系統（src/nerve/）

### 2.1 eye.py — 視覺
- **職責**: 文字搜尋（web_search），解析搜尋結果
- **狀態**: ⚠️ 需檢查

### 2.2 eye_vision.py — 電腦視覺
- **職責**: 圖片/影片輸入處理
- **狀態**: ⚠️ 需檢查

### 2.3 ear.py — 聽覺
- **職責**: 語音輸入轉文字
- **狀態**: ⚠️ 需檢查

### 2.4 ear_voice.py — 語音輸出
- **職責**: 文字轉語音輸出
- **狀態**: ⚠️ 需檢查

---

## 三、循環系統（src/blood/）

### 3.1 event_bus.py — 事件匯流排
- **職責**: pub/sub 模式事件分發，器官間解耦通訊
- **API**: subscribe(event, callback), publish(event, data)
- **狀態**: ⚠️ 需檢查

### 3.2 scheduler.py — 排程器
- **職責**: 定時任務管理（cron-like）
- **API**: add_job(interval, func), remove_job(id), list_jobs()
- **狀態**: ⚠️ 需檢查

### 3.3 monitor.py — 監控器
- **職責**: 器官心跳監控，每5分鐘檢查一輪
- **狀態**: ⚠️ 需檢查

---

## 四、肌肉系統（src/muscle/）

### 4.1 executor.py — 執行器
- **職責**: 執行 LLM 選擇的工具呼叫，捕捉例外
- **狀態**: ⚠️ 需檢查

### 4.2 tool_creator.py — 工具生成器
- **職責**: 從範本動態生成新工具代碼
- **狀態**: ⚠️ 需檢查

### 4.3 tool_registry.py — 工具註冊中心
- **職責**: 註冊/查詢/列出所有可用工具
- **狀態**: ⚠️ 需檢查

---

## 五、免疫系統（src/immune/）

### 5.1 firewall.py — 防火牆
- **職責**: 輸入過濾（惡意prompt、SQL注入、XSS）
- **狀態**: ⚠️ 需檢查

### 5.2 breaker.py — 熔斷器（合併 immune + circuit）
- **職責**: 連續失敗 N 次後暫時停用器官
- **API**: record_failure(organ), record_success(organ), is_circuit_open(organ)
- **狀態**: ⚠️ 兩份合併到 immune/

### 5.3 self_heal.py — 自癒
- **職責**: 檢測異常後自動重啟器官
- **狀態**: ⚠️ 需檢查

---

## 六、電路保護（src/circuit/）— 刪除 breaker.py 和 contradiction.py，只留：

### 6.1 controller.py — 控制器
- **職責**: 服務啟動/停止/重啟
- **狀態**: ⚠️ 需檢查

### 6.2 health.py — 健康檢查
- **職責**: 回報系統整體健康狀態 → circulatory
- **狀態**: ⚠️ 需檢查

---

## 七、外皮系統（src/skin/）

### 7.1 persona.py — 人格
- **職責**: 管理 Agent 名稱、語氣、個性設定
- **狀態**: ⚠️ 需檢查

### 7.2 voice.py — 語音風格
- **職責**: 控制輸出語氣、繁簡體、正式度
- **狀態**: ⚠️ 需檢查

### 7.3 face.py — 外觀
- **職責**: 回覆格式排版、emoji 風格
- **狀態**: ⚠️ 需檢查

### 7.4 wardrobe.py — 衣櫃
- **職責**: 切換不同人格模板（專業模式/聊天模式/導師模式）
- **狀態**: ⚠️ 需檢查

---

## 八、繁殖系統（src/womb/）

### 8.1 birth.py — 誕生
- **職責**: 從 agent_template 複製出新 Agent 實例
- **狀態**: ⚠️ 需檢查

### 8.2 nursery.py — 育嬰室
- **職責**: 監控新生 Agent 的健康狀態，淘汰不合格的
- **狀態**: ⚠️ 需檢查

### 8.3 placenta.py — 胎盤
- **職責**: 為新生 Agent 分配資源（CPU/記憶體/API quota）
- **狀態**: ⚠️ 需檢查

### 8.4 agent_template.py — Agent 模板
- **職責**: 定義新 Agent 的最小基因組
- **狀態**: ⚠️ 需檢查

---

## 九、排泄系統（src/waste/）

### 9.1 cleaner.py — 清理器
- **職責**: 定期刪除過期資料、舊日誌
- **狀態**: ⚠️ 需檢查

### 9.2 log_rotator.py — 日誌輪轉
- **職責**: 日誌按大小/時間切割，保留最近 N 份
- **狀態**: ⚠️ 需檢查

### 9.3 tool_garbage.py — 工具回收
- **職責**: 標記長期未使用的工具，定期清理
- **狀態**: ⚠️ 需檢查

---

## 十、囊袋（src/bag/）

### 10.1 plugin_loader.py — 外掛載入器
- **職責**: 從 plugins/ 目錄動態載入外部模組
- **狀態**: ⚠️ 需檢查

### 10.2 web_search.py — 網頁搜尋
- **職責**: DuckDuckGo/Google 搜尋，回傳摘要
- **狀態**: ⚠️ 需檢查

---

## 十一、骨架（src/skeleton/）

### 11.1 base_organ.py — 基礎器官類別
- **職責**: 所有器官的抽象父類，定義 start()/stop()/heartbeat()
- **狀態**: ⚠️ 需檢查

### 11.2 brain_component.py — 大腦組件類別
- **職責**: 商業器官的父類，提供 LLM 存取、日誌、錯誤處理
- **狀態**: ⚠️ 需檢查

### 11.3 assembler.py — 組裝器
- **職責**: 掃描目錄 → 載入 BrainComponent 子類 → 實例化 → 存入 organs dict
- **狀態**: ✅ 完整

### 11.4 dna.py — 基因
- **職責**: 定義器官的配置基因（參數、能力、版本）
- **狀態**: ⚠️ 需檢查

### 11.5 registry.py — 註冊中心
- **職責**: 中央註冊表，記錄所有可用器官的 metadata
- **狀態**: ⚠️ 需檢查

### 11.6 manifest.py — 清單
- **職責**: 宣告每個器官的依賴、介面、版本
- **狀態**: ⚠️ 需檢查

### 11.7 auto_grow.py — 自動成長
- **職責**: 從 GitHub/社群拉取新器官，自動加入系統
- **狀態**: ⚠️ 需檢查

### 11.8 fallback.py — 降級方案
- **職責**: 當某器官失效時，提供最小可行替代
- **狀態**: ⚠️ 需檢查

---

## 十二、核心業務器官（src/core/）— 32 個，大部分需重寫

### 區塊鏈/NFT（9 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| crypto_wallet.py | 建立錢包、簽署交易、查詢餘額 | ❌ 空殼 |
| gas_tracker.py | 查詢各鏈 Gas 費用 | ❌ 空殼 |
| cross_chain_bridge.py | 跨鏈路徑計算、橋接合約呼叫 | ❌ 空殼 |
| nft_sniper.py | 監控新發售、自動 mint | ❌ 空殼 |
| nft_floor_scanner.py | 掃描地板價、流動性分析 | ❌ 空殼 |
| nft_whale_tracker.py | 追蹤鯨魚錢包動向 | ❌ 空殼 |
| nft_market_maker.py | 自動掛單、做市策略 | ❌ 空殼 |
| nft_airdrop_checker.py | 檢查空投資格、領取空投 | ❌ 空殼 |
| nft_manager.py | 管理 NFT 持倉、查看屬性 | ❌ 空殼 |

### 市場分析（4 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| market_analyzer.py | 技術分析、趨勢判斷 | ❌ 空殼 |
| market_data.py | 從 API 拉取即時價格數據 | ❌ 空殼 |
| portfolio_tracker.py | 投資組合追蹤、盈虧計算 | ❌ 空殼 |
| smart_contract_auditor.py | 合約安全掃描（呼叫外部 API） | ❌ 空殼 |

### 行銷引擎（5 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| auto_content_creator.py | AI 生成部落格/社群貼文 | ❌ 空殼 |
| social_media_manager.py | 排程發文、跨平台管理 | ❌ 空殼 |
| seo_optimizer.py | 關鍵字分析、SEO 建議 | ❌ 空殼 |
| email_marketer.py | 自動化 Email 行銷 | ❌ 空殼 |
| ad_manager.py | 廣告預算管理、ROI 追蹤 | ❌ 空殼 |

### 商業智慧（4 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| customer_persona.py | 客戶畫像分析 | ❌ 空殼 |
| revenue_optimizer.py | 營收模型優化 | ❌ 空殼 |
| landing_page_crm.py | Landing Page 管理 + CRM | ❌ 空殼 |
| daily_growth_report.py | 每日成長報告生成 | ❌ 空殼 |

### 自主系統（6 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| self_evolution_engine.py | 自我進化：評估→突變→測試→接納 | ⚠️ 需檢查 |
| self_learn.py | 從對話中學習，更新知識庫 | ❌ 空殼 |
| auto_learning.py | 自動搜尋學習資源 | ❌ 空殼 |
| auto_repair.py | 背景執行緒，每10分鐘檢查死器官 | ✅ 完整 |
| auto_job_system.py | 自動化工作排程 | ❌ 空殼 |
| planner.py | 任務規劃、優先排序、分解子任務 | ❌ 空殼 |

### 基礎設施（4 個）
| 器官 | 職責 | 狀態 |
|------|------|------|
| langgraph_executor.py | LLM 思考引擎（手寫迴圈） | ✅ 完整 |
| circulatory.py | 健康循環 + VPS 資源監控 | ✅ 完整 |
| plugin_manager.py | 載入/管理外部外掛 | ❌ 空殼 |
| hypothalamus.py | **與 brain/ 重複，需刪除** | ❌ 刪除 |

---

## 十三、頂層獨立器官（src/*.py）

| 檔案 | 職責 | 狀態 |
|------|------|------|
| config.py | 讀取 .env，提供全域設定 | ✅ |
| llm.py | LLM 客戶端（OpenAI-compatible API） | ⚠️ |
| memory.py | 短期記憶（對話記錄） | ⚠️ |
| memory_vector.py | 向量記憶（語義搜尋） | ⚠️ |
| tools.py | 工具定義與註冊 | ⚠️ |
| evolution.py | 進化循環邏輯 | ⚠️ |
| models.py | 模型能力註冊 | ⚠️ |
| breath.py | 呼吸系統（心跳/生命週期） | ⚠️ |
| nose.py | 嗅覺（sniffer） | ⚠️ |
| agents.py | Agent 管理器 | ⚠️ |
| executor.py | 舊版執行器 | ⚠️ |
| handler.py | Telegram 訊息處理器 | ⚠️ |
| monitor.py | 系統監控 + 自動修復 | ⚠️ |

---

## 十四、資料層（data/）

| 檔案 | 用途 | 狀態 |
|------|------|------|
| long_term_memory.json | 長期記憶（重要性 > 0.7 的事實） | ❌ 不存在 |
| self_learn.json | 自學記錄（學到什麼、何時學的） | ❌ 不存在 |
| planner_tasks.json | 任務清單（待辦/進行中/完成） | ❌ 不存在 |
| health_report.json | 健康報告（器官狀態快照） | ❌ 不存在 |
| evolution_log.json | 進化記錄（每次變異的 diff） | ❌ 不存在 |
| startup_diagnosis.json | 啟動診斷（最後一次啟動的器官狀態） | ✅ |
| compass/direction.json | 北極星目標 | ✅ |
| tools/registry.json | 工具註冊表 | ✅ |
| state/heartbeat.json | 最後心跳 | ✅ |

---

## 十五、合併/刪除清單

```
刪除:
  src/core/hypothalamus.py    → 留 src/brain/hypothalamus.py
  src/circuit/breaker.py        → 合併到 src/immune/breaker.py
  src/circuit/contradiction.py  → 合併到 src/immune/contradiction.py
  src/orgs/                     → 空目錄，刪除
  src/organs/                   → Assembler 沒掃，留著或刪除

搬移:
  src/memory.py        → src/brain/memory/memory.py
  src/tools.py         → src/brain/tools/tools.py
  src/evolution.py     → src/brain/evolution.py
  src/breath.py        → src/brain/breath.py
  src/nose.py          → src/brain/nose.py
  src/models.py        → src/brain/models.py
```

---

## 十六、重建優先級

### P0 — 立刻修（阻塞啟動）
1. 搬移 memory/tools/evolution/breath/nose/models 到 brain/ 下
2. 刪除重複器官（hypothalamus, breaker, contradiction）
3. 更新所有 import 路徑

### P1 — 核心器官重寫（決定能不能用）
4. crypto_wallet.py — 錢包是 Web3 入口
5. market_data.py — 數據是分析基礎
6. gas_tracker.py — 交易必需品
7. nft_sniper.py — 核心業務
8. cross_chain_bridge.py — 核心業務

### P2 — 商業器官重寫
9. market_analyzer.py
10. portfolio_tracker.py
11. auto_content_creator.py
12. social_media_manager.py
13. email_marketer.py

### P3 — 輔助器官重寫
14. 剩下的 NFT 器官（floor_scanner, whale_tracker, market_maker, airdrop_checker, manager）
15. 行銷引擎（seo_optimizer, ad_manager, landing_page_crm）
16. 商業智慧（customer_persona, revenue_optimizer, daily_growth_report）

### P4 — 自主系統重寫
17. self_learn.py
18. auto_learning.py
19. auto_job_system.py
20. planner.py
21. plugin_manager.py

### P5 — 資料層初始化
22. 建立 5 個 data/*.json
23. 補 requirements.txt
24. 重構 main.py 啟動流程

---

## 十七、器官間依賴圖（簡化）

```
cortex ─────┬─→ llm (LLM 客戶端)
            ├─→ firewall (免疫)
            ├─→ breaker (熔斷)
            ├─→ eye → web_search (搜尋)
            ├─→ executor → tool_registry → [所有工具器官]
            ├─→ memory (記憶)
            ├─→ self_review → self_repair (自我反思→修復)
            ├─→ persona (人格)
            └─→ compass (方向)

assembler ─→ 掃描 src/core/、src/nerve/、src/immune/ 等
            → 載入 BrainComponent 子類
            → 注入到 Obsidian.organs

hypothalamus ─→ scheduler (排程)
              → cleaner (清理)
              → daily_growth_report (日報)

circulatory ─→ monitor (心跳)
             → auto_repair (修復)
             → self_evolution_engine (進化)
```

---

## 十八、技術約定

- **語言**: Python 3.11
- **LLM**: OpenAI-compatible API (DeepSeek/Ollama)
- **通訊**: organs 之間用 event_bus (pub/sub)
- **儲存**: JSON 檔案（data/）+ 記憶體向量（memory_vector）
- **部署**: bare metal + daemon.sh
- **編碼風格**: 繁體中文 docstring，英文變數名
- **每個器官**: 繼承 BrainComponent，實作 start()/stop()/heartbeat()
- **工具**: 註冊到 tool_registry，executor 呼叫
