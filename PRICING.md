<p align="center"><img src="assets/300.png" width="180"></p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">AMPM-AIOPS 定價與功能對照</h1>

<h2 align="center" style="color:#58a6ff;">三級方案</h2>

| 功能 | 🟢 Community | 🟡 Pro | 🔴 Enterprise |
|------|:---:|:---:|:---:|
| **價格** | **免費** | **$29/月 或 $199/年** | **$99/月 或 $799/年** |
| | | | |
| 核心 Runtime 狀態機 | ✅ | ✅ | ✅ |
| 三層記憶系統 | ✅ | ✅ | ✅ |
| Telegram Bot | ✅ | ✅ | ✅ |
| 基礎安全（防火牆） | ✅ | ✅ | ✅ |
| Plugin SDK | ✅ | ✅ | ✅ |
| | | | |
| 自我進化循環 | ❌ | ✅ | ✅ |
| 自動修復 | ❌ | ✅ | ✅ |
| 工具自動生成 | ❌ | ✅ | ✅ |
| 多 Agent 協作 | ❌ | ✅ | ✅ |
| 儀表板（Dashboard） | ❌ | ✅ | ✅ |
| Email 技術支援 | ❌ | ✅ | ✅ |
| | | | |
| 行銷自動化模組 | ❌ | ❌ | ✅ |
| SEO / 廣告優化 | ❌ | ❌ | ✅ |
| 加密貨幣 / NFT 工具 | ❌ | ❌ | ✅ |
| 多租戶 SaaS 系統 | ❌ | ❌ | ✅ |
| 內容自動出版 | ❌ | ❌ | ✅ |
| 私有部署支援 | ❌ | ❌ | ✅ |
| SLA 保證 | ❌ | ❌ | ✅ |

<br>
<hr style="border:1px solid #30363d;">

<h2 align="center" style="color:#58a6ff;">賣法建議</h2>

<h3 style="color:#d29922;">1. 主要賣 Pro（$29/月）</h3>

- 這是大部分人會買的等級
- 月費低，心理門檻小
- 年費打 55 折（$29×12=$348 → $199/年）

<h3 style="color:#e94560;">2. Enterprise 鎖定企業客戶</h3>

- 月費 $99，年費 $799
- 也可以賣「終身授權」$999（一次付清，永久使用）
- 這群人對價格不敏感，但要完整功能

<h3 style="color:#2ea043;">3. Community 永遠免費</h3>

- 讓大家先試用，覺得好用再升級
- 免費版就是活廣告

<br>
<hr style="border:1px solid #30363d;">

<h2 align="center" style="color:#58a6ff;">實際操作（你現在可以做的事）</h2>

<h3 style="color:#58a6ff;">1. 在 Gumroad 建立三個商品</h3>

| 商品名稱 | 價格 |
|----------|------|
| AMPM-AIOPS Pro（月費） | $29/月 |
| AMPM-AIOPS Pro（年費） | $199/年 |
| AMPM-AIOPS Enterprise（年費） | $799/年 |

<h3 style="color:#58a6ff;">2. 用 keygen.py 產生金鑰</h3>

```bash
cd AMPM-AIOPS
python tools/keygen.py
```

<p style="color:#c9d1d9;">
會產生 Pro 和 Enterprise 金鑰，複製到 Gumroad 商品內容。
</p>

<h3 style="color:#58a6ff;">3. 買家拿到金鑰後</h3>

<p style="color:#c9d1d9;">
他們只需要在 <code>.env</code> 加入：
</p>

```
AMPM_LICENSE_KEY=AMPM-PRO-XXXX-XXXX-XXXX
```

<p style="color:#c9d1d9;">
Bot 自動解鎖對應功能。
</p>

<br>
<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
