# Cloudflare API Token 驗證方法

## 1. 驗證 API Token 是否有效

Cloudflare 提供了 API 端點來驗證你的 API Token 是否有效。你可以使用 `curl` 工具來進行驗證。

### 步驟

1. 準備你的 API Token（假設為 `CF_API_TOKEN`）。
2. 執行以下指令：

```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer CF_API_TOKEN" \
     -H "Content-Type: application/json"
```

3. 如果回應如下，表示 Token 有效：

```json
{
  "result": {
    "id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "status": "active"
  },
  "success": true,
  "errors": [],
  "messages": []
}
```

4. 若無效，會收到 `success: false` 或錯誤訊息。

---

## 2. Cloudflare 網路身分（Identity）建立

Cloudflare 支援多種身分提供者（IdP），如 Google Workspace、Microsoft Entra ID、Okta 等。你可以在 Cloudflare Zero Trust 控制台設定。

### 步驟摘要

1. 登入 [Cloudflare Zero Trust](https://dash.teams.cloudflare.com/)
2. 前往 **Settings > Authentication > Login methods**
3. 點擊 **Add a login method**，選擇你的身分提供者（如 Google、Azure AD、GitHub 等）
4. 依照指示設定 IdP 並授權 Cloudflare
5. 設定完成後，可用於 Access Policy、網路存取等

### 參考文件
- [Cloudflare 官方文件：Configure an identity provider](https://developers.cloudflare.com/cloudflare-one/identity/idp-integration/)
- [Cloudflare One docs: Identity providers](https://developers.cloudflare.com/cloudflare-one/identity/idp-integration/overview/)

---

## 附錄：常見問題

- **API Token 權限不足怎麼辦？**
  - 請確認 Token 已授權正確範圍（如 Zone、User、Account 權限）。
- **支援哪些身分提供者？**
  - Google Workspace、Microsoft Entra ID、Okta、GitHub、OneLogin 等。

---

本文件彙整 Cloudflare API Token 驗證與網路身分建立之實務步驟，適合技術人員快速查閱與操作。