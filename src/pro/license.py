"""
License Key System — 離線驗證 + 補餘機製
=========================================
Tiers: community (免費) / pro / enterprise
"""
import hashlib, hmac, json, os, time, random
from pathlib import Path
from datetime import datetime, timedelta

_BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def _b62encode(n: int) -> str:
    if n == 0:
        return _BASE62[0]
    chars = []
    while n > 0:
        chars.append(_BASE62[n % 62])
        n //= 62
    return "".join(reversed(chars))


class LicenseManager:
    SECRET = os.getenv("AMPM_LICENSE_SECRET", "change-me-in-production")

    TIERS = {
        "community": 0,
        "pro": 1,
        "enterprise": 2,
    }
    TIER_LABELS = {
        "community": "社群版 (免費)",
        "pro": "專業版 💎",
        "enterprise": "企業版 🏢",
    }

    FEATURES = {
        "community": [
            "30 個核心器官",
            "自我診斷 / 修復",
            "Telegram Bot",
            "記憶系統 (短期 + 長期)",
            "工具系統 (162 個)",
            "科技感儀表板",
            "定時調度系統",
            "健康循環系統",
        ],
        "pro": [
            "40 個核心器官",
            "自我診斷 / 修復",
            "Telegram Bot",
            "一鍵安裝腳本",
            "SEO / 廣告零件",
            "AI 內容生成",
            "記憶系統 (完整)",
            "工具系統 (200+ 個)",
            "科技感儀表板",
            "定時調度系統",
            "健康循環系統",
            "優先技術支援",
        ],
        "enterprise": [
            "50 個核心器官",
            "自我診斷 / 修復",
            "Telegram Bot",
            "一鍵安裝腳本",
            "SEO / 廣告零件",
            "AI 內容生成",
            "雲端託管服務",
            "專屬技術支援",
            "定製新零件",
            "SLA 保障",
            "記憶系統 (文明級)",
            "工具系統 (250+ 個)",
            "科技感儀表板",
            "定時調度系統",
            "健康循環系統",
        ],
    }

    def __init__(self, license_file="data/license.json"):
        self.license_file = Path(license_file)
        self.license_data = self._load()

    def _load(self):
        if self.license_file.exists():
            try:
                return json.loads(self.license_file.read_text())
            except Exception:
                pass
        return {"tier": "community", "expires": None, "key": ""}

    def _save(self):
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.license_file.write_text(json.dumps(self.license_data, indent=2))

    # ── 金鑰產生 ──────────────────────────────────────────

    @staticmethod
    def generate_key(tier: str, expiry_days: int = 365) -> str:
        """
        產生 HMAC 簽章授權金鑰。
        格式: AMPM-{TIER}-{PAYLOAD}{SIGNATURE}
        PAYLOAD = base62(unixtime + 隨機數) (6~8 碼)
        SIGNATURE = HMAC-SHA256(PAYLOAD, SECRET) 前 8 碼
        """
        payload_int = int(time.time()) << 20 | random.getrandbits(20)
        payload = _b62encode(payload_int)
        sig = hmac.new(
            LicenseManager.SECRET.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()[:8]
        return f"AMPM-{LicenseManager._tier_code(tier)}-{payload}-{sig}"

    @staticmethod
    def _tier_code(tier: str) -> str:
        return {"pro": "PRO", "enterprise": "ENT"}.get(tier, tier.upper())[:4]

    @staticmethod
    def validate_key(key: str) -> dict:
        """
        驗證金鑰格式與簽章，不回傳敏感資訊。
        回傳: {"valid": bool, "tier": str, "reason": str}
        """
        if not key or not key.startswith("AMPM-"):
            return {"valid": False, "tier": "community", "reason": "格式錯誤"}
        parts = key.split("-")
        if len(parts) != 4:
            return {"valid": False, "tier": "community", "reason": "格式錯誤"}
        prefix, tier_code, payload, sig = parts[0], parts[1], parts[2], parts[3]
        tier_map = {"PRO": "pro", "ENT": "enterprise"}
        tier = tier_map.get(tier_code, "community")
        if tier == "community":
            return {"valid": False, "tier": "community", "reason": "未知版本"}
        expected_sig = hmac.new(
            LicenseManager.SECRET.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()[:8]
        if sig != expected_sig:
            return {"valid": False, "tier": "community", "reason": "簽章不符"}
        return {"valid": True, "tier": tier, "reason": ""}

    # ── 商業邏輯 ──────────────────────────────────────────

    def get_tier(self) -> str:
        return self.license_data.get("tier", "community")

    def is_valid(self) -> bool:
        tier = self.get_tier()
        if tier == "community":
            return True
        expires = self.license_data.get("expires")
        if expires:
            try:
                if datetime.fromisoformat(expires) < datetime.now():
                    return False
            except Exception:
                return False
        return True

    def get_features(self) -> list:
        return self.FEATURES.get(self.get_tier(), self.FEATURES["community"])

    def activate_key(self, key: str) -> dict:
        """嘗試啟用一個金鑰，回傳結果。"""
        result = self.validate_key(key)
        if not result["valid"]:
            return result
        self.license_data["tier"] = result["tier"]
        self.license_data["key"] = key
        self.license_data["expires"] = (
            datetime.now() + timedelta(days=365)
        ).isoformat()
        self.license_data["activated_at"] = datetime.now().isoformat()
        self._save()
        return result

    def load_from_env(self):
        key = os.getenv("AMPM_LICENSE_KEY", "")
        if key:
            self.activate_key(key)
