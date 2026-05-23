# [public] License Manager — subscription & access control for AMPM bot

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "licenses.json"


def _load():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def generate_key(user_id: int, days: int = 30) -> str:
    """Generate a license key for a user. Returns the key string."""
    import secrets
    key = "AMPM-" + secrets.token_hex(8).upper()
    expiry = (datetime.utcnow() + timedelta(days=days)).isoformat()
    data = _load()
    data[key] = {"user_id": user_id, "expires": expiry, "active": True}
    _save(data)
    return key


def activate(key: str, user_id: int) -> str:
    """Activate a license key for a user. Returns status message."""
    data = _load()
    if key not in data:
        return "❌ 授權碼無效。"
    lic = data[key]
    if lic.get("user_id") and lic["user_id"] != user_id:
        return "❌ 此授權碼已綁定其他使用者。"
    if not lic.get("active", True):
        return "❌ 此授權碼已停用。"
    expiry = datetime.fromisoformat(lic["expires"])
    if expiry < datetime.utcnow():
        return "❌ 授權碼已過期。"
    lic["user_id"] = user_id
    lic["activated_at"] = datetime.utcnow().isoformat()
    _save(data)
    remaining = (expiry - datetime.utcnow()).days
    return f"✅ 啟用成功！剩餘 {remaining} 天。"


def check_access(user_id: int) -> tuple:
    """Check if user has active access. Returns (allowed: bool, message: str)."""
    data = _load()
    for key, lic in data.items():
        if lic.get("user_id") == user_id and lic.get("active", True):
            expiry = datetime.fromisoformat(lic["expires"])
            if expiry > datetime.utcnow():
                remaining = (expiry - datetime.utcnow()).days
                return True, f"剩餘 {remaining} 天"
            else:
                lic["active"] = False
                _save(data)
                return False, "❌ 授權已過期。請聯繫管理員續期。"
    return False, "⛔ 無有效授權。請輸入 /activate <授權碼>"


def status(user_id: int) -> str:
    """Get subscription status for a user."""
    data = _load()
    for key, lic in data.items():
        if lic.get("user_id") == user_id:
            expiry = datetime.fromisoformat(lic["expires"])
            remaining = (expiry - datetime.utcnow()).days
            active = lic.get("active", True) and remaining > 0
            status_text = "✅ 啟用中" if active else "❌ 已過期"
            return (
                f"📋 訂閱狀態\n"
                f"狀態：{status_text}\n"
                f"到期：{expiry.strftime('%Y-%m-%d')}\n"
                f"剩餘：{max(0, remaining)} 天"
            )
    return "📋 尚無授權記錄。請輸入 /activate <授權碼>"
