import json
import os
from datetime import datetime, timedelta, timezone
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


def _load_licenses():
    """相容新舊格式：{key: {...}} 或 {last_updated, licenses: {key: {...}}}"""
    data = _load()
    if isinstance(data, dict) and "licenses" in data:
        return data["licenses"]
    return data

def _save_licenses(licenses: dict):
    _save({"last_updated": datetime.now(timezone.utc).isoformat(), "licenses": licenses})


def generate_key(user_id: int, days: int = 30, tier: str = "basic") -> str:
    import secrets
    key = "AMPM-" + secrets.token_hex(8).upper()
    expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    licenses = _load_licenses()
    licenses[key] = {
        "user_id": user_id,
        "expires": expiry,
        "active": True,
        "tier": tier,
    }
    _save_licenses(licenses)
    return key


def activate(key: str, user_id: int) -> str:
    licenses = _load_licenses()
    if key not in licenses:
        return "❌ 授權碼無效。"
    lic = licenses[key]
    if lic.get("user_id") and lic["user_id"] != user_id:
        return "❌ 此授權碼已綁定其他使用者。"
    if not lic.get("active", True):
        return "❌ 此授權碼已停用。"
    expiry = datetime.fromisoformat(lic["expires"]).replace(tzinfo=timezone.utc)
    if expiry < datetime.now(timezone.utc):
        return "❌ 授權碼已過期。"
    lic["user_id"] = user_id
    lic["activated_at"] = datetime.now(timezone.utc).isoformat()
    _save_licenses(licenses)
    remaining = (expiry - datetime.now(timezone.utc)).days
    return f"✅ 啟用成功！剩餘 {remaining} 天。"


def check_access(user_id: int) -> tuple:
    """Returns (allowed: bool, message: str, tier: str)"""
    licenses = _load_licenses()
    for key, lic in licenses.items():
        if lic.get("user_id") == user_id and lic.get("active", True):
            expiry = datetime.fromisoformat(lic["expires"]).replace(tzinfo=timezone.utc)
            if expiry > datetime.now(timezone.utc):
                remaining = (expiry - datetime.now(timezone.utc)).days
                tier = lic.get("tier", "basic")
                return True, f"剩餘 {remaining} 天", tier
            else:
                lic["active"] = False
                _save_licenses(licenses)
                return False, "❌ 授權已過期。請續費。", "none"
    return False, "⛔ 無有效授權。請輸入 /activate <授權碼>", "none"


def get_user_tier(user_id: int) -> str:
    licenses = _load_licenses()
    for key, lic in licenses.items():
        if lic.get("user_id") == user_id and lic.get("active", True):
            expiry = datetime.fromisoformat(lic["expires"]).replace(tzinfo=timezone.utc)
            if expiry > datetime.now(timezone.utc):
                return lic.get("tier", "basic")
    return "none"


def status(user_id: int) -> str:
    licenses = _load_licenses()
    for key, lic in licenses.items():
        if lic.get("user_id") == user_id:
            expiry = datetime.fromisoformat(lic["expires"]).replace(tzinfo=timezone.utc)
            remaining = (expiry - datetime.now(timezone.utc)).days
            active = lic.get("active", True) and remaining > 0
            status_text = "✅ 啟用中" if active else "❌ 已過期"
            return (
                f"📋 訂閱狀態\n"
                f"狀態：{status_text}\n"
                f"到期：{expiry.strftime('%Y-%m-%d')}\n"
                f"剩餘：{max(0, remaining)} 天"
            )
    return "📋 尚無授權記錄。"
