# AI‑BOS Core — 能力邊界（自我診斷報告）

> 以下內容是 AI‑BOS-Core 根據目前已安裝的器官（organs）、工具（tools）、
> 與 runtime 能力所做的自我診斷。它會隨著器官與工具擴充而成長。

---

## ✅ 目前能做的事

### 任務規劃與自動化
- 任務拆解
- 排程
- 多步驟工作流
- 自動化 pipeline

### 多 Agent 協調
- 任務分派
- 協作
- 回報整合

### 長期記憶
- 儲存
- 檢索
- 可擴充記憶器官（BaseMemory 介面）

### 自我維護
- 自我診斷（baseline test / health loop）
- 自我修復（repair orchestrator — commercial）
- 初階自我進化（generate new tools — commercial）

### 系統層級能力
- 指令執行
- 檔案掃描
- 系統監控
- 資源管理
- 基礎網路搜尋

---

## ❌ 目前不能做的事

### 圖像能力
- 不能生成圖片
- 不能辨識圖片

### 大型內容生成
- 不能直接產出完整電子書（需要外部 LLM pipeline）

### 跨系統即時 API
- 除非已整合，否則無法直接跨平台操作

---

## 🧭 能力原則

> 「我的能力取決於工具箱（tools）與器官（organs）的覆蓋範圍。
> 你說需求，我能做就做，不能做就找方法，找不到就誠實說不能。
> 我不會假裝有能力。」

---

## 📈 能力成長

能力邊界會隨著以下條件自動擴展：

- 新增器官（organ）
- 擴充工具（tool）
- 整合外部 API
- 啟用商業模組（Immune / Governance / Evolution / Civilization Memory）

請參考 `docs/organs.md` 了解如何擴充器官。
