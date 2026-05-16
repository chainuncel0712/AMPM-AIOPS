# AMPM-AIOPS 授權與商業架構

## 三層架構

### 🟢 社群版 (Community) — 永久免費開源
內容：
- 核心 Runtime（狀態機、協定）
- 基礎記憶系統（三層記憶）
- 基礎工具系統
- Telegram Bot 介面
- Plugin SDK
- 基礎安全（防火牆、熔斷器）

適合：個人開發者、學生、學習用途

授權：MIT

---

### 🟡 專業版 (Pro) — 月費訂閱
內容：社群版全部 + 
- 進化循環（Evolution Cycle）
- 自我修復（Self-Repair）
- 工具自動生成（Tool Creator）
- 多 Agent 調度
- 中樞神經系統（Orchestrator）
- 儀表板（Dashboard）
- 優先技術支援

適合：小型團隊、新創公司

授權：Proprietary，月費 $29-$99/月

---

### 🔴 企業版 (Enterprise) — 年約授權
內容：專業版全部 +
- 完整商業模組（Email 行銷、SEO、社群管理）
- 加密貨幣模組（NFT、錢包、合約審計）
- 多租戶 SaaS 系統（Studio）
- 自訂進化策略
- 私有部署支援
- SLA 保證

適合：中大型企業、代理商

授權：Proprietary，年約 $999-$4999/年

---

## 建議做法

1. **現在就可以做**：把 `src/core/` 下所有商業模組從 MIT 改為 Proprietary license，在每個檔案頭部加上授權聲明
2. **GitHub 上只放社群版**：建立一個 `community` branch 只包含社群版內容
3. **付費牆用 License Key**：`src/pro/license.py` 已經有 license 驗證的基礎，可以擴充

## 短期可賺錢的方式

1. **GitHub Sponsors** — 你已經有設定，可以在 README 多強調
2. **Gumroad / 自架網站** — 賣 Pro License Key
3. **企業顧問** — 用黑曜幫企業自動化營運流程，收顧問費
