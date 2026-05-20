# Cloudflare 網路身分建立研究

## 1. 驗證 Cloudflare API Token 是否有效

可使用 curl 指令驗證 Cloudflare API Token 是否有效：

```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
     -H "Authorization: Bearer <API_TOKEN>" \
     -H "Content-Type:application/json"
```

回應範例（有效時）：
```json
{
  "result": {
    "id": "...",
    "status": "active"
  },
  "success": true,
  ...
}
```

## 2. 用 Cloudflare API 檢查 AMPM-AIOPS.COM 網域的 DNS 設定

步驟：
1. 取得 zone id：

```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones?name=ampm-aiops.com" \
     -H "Authorization: Bearer <API_TOKEN>" \
     -H "Content-Type:application/json"
```

2. 查詢 DNS 記錄：

```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
     -H "Authorization: Bearer <API_TOKEN>" \
     -H "Content-Type:application/json"
```

## 3. 設定 Email Routing（如 admin@ampm-aiops.com → 你的信箱）

### 步驟
1. 先建立目標信箱（destination address）：

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/email/routing/addresses" \
     -H "Authorization: Bearer <API_TOKEN>" \
     -H "Content-Type:application/json" \
     --data '{"email":"your@email.com"}'
```

2. 建立轉發規則（routing rule）：

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/email/routing/rules" \
     -H "Authorization: Bearer <API_TOKEN>" \
     -H "Content-Type:application/json" \
     --data '{
       "name": "admin forward",
       "enabled": true,
       "matchers": [{"type": "literal", "field": "to", "value": "admin@ampm-aiops.com"}],
       "actions": [{"type": "forward", "value": ["your@email.com"]}]
     }'
```

> 注意：API 權限需包含 Email Routing 權限，否則會出現權限錯誤。

## 4. 參考資料
- [Cloudflare API v4 Documentation](https://api.cloudflare.com/)
- [Configure rules and addresses · Cloudflare Email Routing docs](https://developers.cloudflare.com/email-routing/addresses/)
- [List DNS Records | Cloudflare API](https://api.cloudflare.com/#dns-records-for-a-zone-list-dns-records)
- [Verify API Token for CloudFlare API · GitHub](https://gist.github.com/)
