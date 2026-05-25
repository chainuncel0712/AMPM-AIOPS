# AMPM AI — 專業出版計畫書

---

## 1. 品牌系統 (Brand System)

### 1.1 品牌定位
| 項目 | 內容 |
|------|------|
| 品牌名稱 | AM&PM ADVENTURE |
| 一句話定位 | 從白天到夜晚，用知識與想像陪伴每個冒險靈魂 |
| 核心 IP | PANEY（白天黑貓）+ MONEY（夜晚虎斑） |
| 系列口號 | 白天勇敢出發，晚上安心回家 |
| 目標客群 | 童書 3-6 歲親子 / 工具書成人創作者 |

### 1.2 視覺識別系統
| 標誌類型 | 用途 | 檔案 |
|----------|------|------|
| 品牌標準字 Text Logo | 官網、名片、社群頭像 | `web_logo.png` |
| 童書 IP 圓形徽章 | 童書封面角標、書腰、貼紙 | `children_logo.jpg` |
| 工具書科技識別 | 電子書封面、數位平台 | — |

### 1.3 色彩系統
| 角色 | 色名 | HEX | 用途 |
|------|------|-----|------|
| **主色** | 炭墨棕 | `#241E1C` | 標題、深色背景 |
| **輔色 A** | 日光橙 | `#FF8C1A` | CTA、強調 |
| **輔色 B** | 智慧藍 | `#189FFF` | 科技感、黑夜氛圍 |
| **中性色** | 霜白 | `#F7F7F7` | 內頁底色 |
| **強調色** | 星光黃 | `#FFD966` | 裝飾點綴 |

### 1.4 字體系統
| 用途 | 中文 | 英文 |
|------|------|------|
| 印刷標題 | 思源黑體 Bold | Poppins Bold |
| 印刷內文 | 思源宋體 Regular | Nunito Regular |
| 數位閱讀 | 蘋方/微軟正黑體 | Inter |
| 工具書圖表 | 思源黑體 Medium | IBM Plex Sans |

---

## 2. 出版管線架構 (Publishing Pipeline)

### 2.1 三條產線
```
電子工具書                 童書繪本                 客服網站
──────────                ──────                  ──────
trend_analysis            trend_analysis           create_site
  ↓                          ↓                       ↓
select_topic              select_theme             auto_deploy
  ↓                          ↓                       ↓
generate_outline          create_characters         record_order
  ↓                          ↓                       ↓
write_content             write_story              handle_ticket
  ↓                          ↓                       ↓
compile_epub ─┬─▶ SVG     compile_epub ─┬─▶ SVG    upgrade
              │  佔位圖                  │  佔位圖
              ▼                          ▼
        quality_gate ──▶ submit_review ──▶ approve ──▶ publish
```

### 2.2 品質標準
| 檢查項 | 電子書 | 童書 |
|--------|--------|------|
| 最小字數 | 500 | 300 |
| 必含封面 | ✅ | ✅ |
| 完整目錄 | ✅ | — |
| 角色設定 | — | ✅ |
| EPUB 結構 | 3.0 valid | 3.0 valid |
| 品牌色 CSS | ✅ | ✅ |
| 系列口號 | — | ✅ |

### 2.3 輸出規格
| 項目 | 規格 |
|------|------|
| 格式 | EPUB 3.0 |
| 封面 | 內嵌 base64 / 獨立 XHTML |
| 內文編碼 | UTF-8 |
| 語言 | zh-TW |
| 元數據 | title, creator, identifier, date |
| 目錄 | NCX + 導航 |

---

## 3. PANEY & MONEY 系列 roadmap

### 3.1 第一季 20 本（2026 Q2-Q3）

| # | 中文書名 | 主題 | 狀態 |
|---|----------|------|------|
| 1 | PANEY & MONEY 的收收探險：玩具回家了！ | 收玩具/自理 | ✅ 可出版 |
| 2 | PANEY & MONEY 的洗手任務：泡泡打敗細菌 | 衛生習慣 | 📋 待產出 |
| 3 | PANEY & MONEY 的刷牙特攻：牙牙星星亮晶晶 | 刷牙/睡前 | 📋 待產出 |
| 4 | PANEY & MONEY 的睡前安心：我有點怕黑 | 怕黑/情緒 | ✅ 可出版 |
| 5 | PANEY & MONEY 的上學安心：我想家了怎麼辦？ | 分離焦慮 | 📋 待產出 |
| 6 | PANEY & MONEY 的輪流遊戲：一起玩更好玩 | 輪流/分享 | 📋 待產出 |
| 7 | PANEY & MONEY 的生氣火山：我需要冷靜一下 | 生氣管理 | ✅ 可出版 |
| 8 | PANEY & MONEY 的難過雲朵：我想要抱抱 | 難過/表達 | 📋 待產出 |
| 9 | PANEY & MONEY 的緊張蝴蝶：第一次也可以慢慢來 | 緊張/勇氣 | 📋 待產出 |
| 10 | PANEY & MONEY 的害羞小屋：我想說你好 | 害羞/社交 | 📋 待產出 |
| 11 | PANEY & MONEY 的吃飯小勇氣：先嘗一口就好 | 飲食習慣 | 📋 待產出 |
| 12 | PANEY & MONEY 的穿衣任務：自己來我可以 | 穿衣/自理 | 📋 待產出 |
| 13 | PANEY & MONEY 的上廁所小隊：記得先說一聲 | 如廁/自理 | 📋 待產出 |
| 14 | PANEY & MONEY 的出門安全：牽手不走丟 | 外出安全 | 📋 待產出 |
| 15 | PANEY & MONEY 的收心回家：玩完要收尾 | 作息轉場 | 📋 待產出 |
| 16 | PANEY & MONEY 的洗澡小泡泡：水不怕我 | 洗澡/怕水 | 📋 待產出 |
| 17 | PANEY & MONEY 的睡醒起床：早安三步驟 | 起床作息 | 📋 待產出 |
| 18 | PANEY & MONEY 的整理小書包：明天出發準備好 | 整理/準備 | 📋 待產出 |
| 19 | PANEY & MONEY 的失敗也可以：再試一次就好 | 挫折復原 | 📋 待產出 |
| 20 | PANEY & MONEY 的吵吵停一下：小聲也能被聽見 | 音量/表達 | 📋 待產出 |

### 3.2 每本固定結構
```
1. 白天情境 — PANEY 遇到一個狀況
2. 情緒命名 — 「我現在覺得＿＿。」
3. 一個技巧 — 深呼吸/抱抱/數數/喝水
4. 夜晚收尾 — MONEY 帶入習慣（收拾/刷牙/晚安）
5. 最後一頁 — 系列口號 + 親子互動提問
```

### 3.3 上架平台策略
| 平台 | 類型 | 優先級 |
|------|------|--------|
| Readmoo 讀墨 | 繁中電子書 | P0 |
| Amazon KDP | 全球英文 | P1 |
| Google Play Books | 全球 | P1 |
| Apple Books | 全球 | P2 |
| Kobo | 全球 | P2 |
| 博客來 | 繁中 | P2 |

### 3.4 自動化生產排程
| 階段 | 頻率 | 產出 |
|------|------|------|
| 選題 | 每週 | 2 本新主題 |
| 內容生成 | 每日 | 1 本完成 EPUB |
| 品質審核 | 即時 | auto_publish on/off |
| 上架 | 即時 | 5 平台同步 |
| 銷售追蹤 | 每日 | 日報推送 Telegram |

---

## 4. 技術實作方案

### 4.1 封面生成系統
| 元素 | 來源 | 實作方式 |
|------|------|----------|
| 品牌徽章 | `children_logo.jpg` | base64 內嵌 |
| 背景色 | 品牌色系 | CSS inline |
| 中英文書名 | 自動代入 | SVG text + Poppins |
| 貓咪角色 | PANEY & MONEY SVG | 佔位/API 生圖 |
| 價格/系列標 | 自動生成 | 右下角 badge |

### 4.2 EPUB CSS 品牌模板
```css
:root {
  --brand-dark: #241E1C;
  --brand-orange: #FF8C1A;
  --brand-blue: #189FFF;
  --brand-light: #F7F7F7;
  --brand-gold: #FFD966;
  --font-cn: 'Noto Sans TC', 'Source Han Sans', sans-serif;
  --font-en: 'Poppins', 'Inter', sans-serif;
}
```

### 4.3 自動化排程建議
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Resource    │───▶│  Publisher  │───▶│  Supervisor │
│  Scout       │    │  Engine     │    │             │
│  (每小時)    │    │  (每6小時)  │    │  (每30分鐘) │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Website    │
                    │  (AMPMAIOPS)│
                    │  :5050      │
                    └─────────────┘
```

---

## 5. 網站與金流整合

### 5.1 註冊網站功能
| 功能 | 狀態 | 路徑 |
|------|------|------|
| 方案展示 | ✅ | `/register` |
| TXID 驗證 | ✅ | `/activate` POST |
| 授權碼生成 | ✅ | license_manager |
| 品牌視覺 | 🔄 套用品牌色 | CSS 待更新 |
| SSL 憑證 | 📋 Let's Encrypt | 待設定 |
| 正式域名 | 📋 AMPM-AIOPS.COM | 待綁定 |

### 5.2 收款設定
| 項目 | 內容 |
|------|------|
| 鏈 | BNB Chain BEP20 |
| 合約 | USDT `0x55d398...` |
| 錢包 | `0x7f3110...` |
| 方案 | $15/月 · $39/季 · $120/年 |

---

## 6. 下一步執行項目 (Priority)

| P | 項目 | 預估工時 |
|---|------|----------|
| P0 | EPUB 封面整合品牌徽章 + 色系 | 1h |
| P0 | 完成第 1/4/7 本完整商品頁素材 | 2h |
| P1 | 自動循環從 24h 改為 6h | 0.5h |
| P1 | 登錄頁品牌視覺更新 | 1h |
| P1 | SSL + 域名指向 | 1h |
| P2 | 英文版 EPUB 輸出 | 2h |
| P2 | Amazon KDP 自動上架 API | 4h |
| P3 | 系列周邊自動產生（書腰/貼紙） | 3h |
