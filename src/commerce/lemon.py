"""
Lemon Squeezy Webhook — 付款自動發金鑰
======================================
設定:
  1. 到 Lemon Squeezy → Store → Webhooks 新增:
     URL: https://你的網址/api/commerce/lemon-webhook
     Events: order_created, subscription_created
  2. 在 .env 設定:
     LEMON_SQUEEZY_SECRET=whsec_xxxxx    # Webhook 簽章密鑰
     AMPM_LICENSE_SECRET=changeme        # 金鑰 HMAC 密鑰 (跟 license.py 同一個)

收到付款後會:
  1. 驗證 webhook 簽章
  2. 根據購買的 variant 決定 tier
  3. 產生 HMAC 簽章金鑰
  4. 用購買者 email 建立 license.json
  5. 回傳給 Lemon Squeezy 200 OK
"""
import hashlib, hmac, json, os
from pathlib import Path
from flask import Blueprint, request, jsonify

from pro.license import LicenseManager

lemon_bp = Blueprint("lemon", __name__, url_prefix="/api/commerce")

# Variant ID → tier 對照表（請替換成你 Lemon Squeezy 的實際 variant ID）
# 你的 Store ID: 5057273712712330
VARIANT_TIERS = {
    # "5057273712712330": "pro",        # 範例: 專業版
    # "5057273712712331": "enterprise", # 範例: 企業版
}

# Lemon Squeezy webhook 白名單 IP（選擇性）
ALLOWED_IPS = ["34.110.121.0/24", "34.110.122.0/24", "34.110.123.0/24"]


def _verify_signature(payload: bytes, signature: str) -> bool:
    secret = os.getenv("LEMON_SQUEEZY_SECRET", "")
    if not secret:
        return True  # 沒設密鑰時跳過驗證（開發模式）
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _get_license_dir() -> Path:
    return Path(os.getenv("AMPM_DATA_DIR", Path.home() / ".ampm_brain" / "licenses"))


@lemon_bp.route("/lemon-webhook", methods=["POST"])
def lemon_webhook():
    signature = request.headers.get("X-Signature", "")
    payload = request.get_data()

    if not _verify_signature(payload, signature):
        return jsonify({"error": "invalid signature"}), 401

    data = request.get_json()
    meta = data.get("meta", {})
    event_name = meta.get("event_name", "")
    custom_data = data.get("data", {}).get("attributes", {})

    if event_name not in ("order_created", "subscription_created"):
        return jsonify({"status": "ignored"}), 200

    # 取得購買者資訊
    buyer_email = custom_data.get("user_email", "") or custom_data.get("email", "")
    variant_id = str(custom_data.get("variant_id", ""))
    order_id = custom_data.get("order_id", "") or custom_data.get("id", "")

    if not buyer_email:
        return jsonify({"error": "missing email"}), 400

    tier = VARIANT_TIERS.get(variant_id, "community")
    if tier == "community":
        return jsonify({"status": "ignored", "reason": "free tier"}), 200

    # 產生金鑰
    key = LicenseManager.generate_key(tier, 365)

    # 儲存到 license 目錄
    lic_dir = _get_license_dir()
    lic_dir.mkdir(parents=True, exist_ok=True)
    license_data = {
        "email": buyer_email,
        "tier": tier,
        "key": key,
        "order_id": order_id,
        "variant_id": variant_id,
        "created_at": custom_data.get("created_at", ""),
    }
    safe_name = buyer_email.replace("@", "_at_").replace(".", "_")
    (lic_dir / f"{safe_name}.json").write_text(
        json.dumps(license_data, indent=2, ensure_ascii=False)
    )

    print(f"🔑 已自動發金鑰: {buyer_email} → {tier} ({key[:20]}...)")
    return jsonify({"status": "ok", "tier": tier, "key": key[:12] + "..."}), 200


@lemon_bp.route("/lemon-variants", methods=["GET"])
def list_variants():
    """列出目前設定的 variant 對照表，方便檢查。"""
    return jsonify(VARIANT_TIERS)
