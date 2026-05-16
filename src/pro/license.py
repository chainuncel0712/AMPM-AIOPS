"""
授權驗證系統 - 用於商業版功能解鎖
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

class LicenseManager:
    def __init__(self, license_file="data/license.json"):
        self.license_file = Path(license_file)
        self.license_data = self._load()
    
    def _load(self):
        if self.license_file.exists():
            try:
                with open(self.license_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"tier": "community", "expires": None}
    
    def get_tier(self):
        """取得目前版本層級"""
        return self.license_data.get("tier", "community")
    
    def is_valid(self):
        """檢查授權是否有效"""
        tier = self.get_tier()
        if tier == "community":
            return True  # 社區版永遠有效
        expires = self.license_data.get("expires")
        if expires:
            try:
                exp_date = datetime.fromisoformat(expires)
                if exp_date < datetime.now():
                    return False  # 已過期
            except:
                return False
        return True
    
    def get_features(self):
        """取得目前版本可用的功能"""
        features = {
            "community": [
                "核心機械零件 (30 個)",
                "自我診斷 / 修復",
                "Telegram Bot",
                "記憶系統",
                "工具系統 (162 個)",
                "科技感儀表板",
                "定時調度系統",
                "健康循環系統",
            ],
            "basic": [
                "核心機械零件 (30 個)",
                "自我診斷 / 修復",
                "Telegram Bot",
                "一鍵安裝腳本",
                "記憶系統",
                "工具系統 (162 個)",
                "科技感儀表板",
                "定時調度系統",
                "健康循環系統",
            ],
            "pro": [
                "核心機械零件 (40 個)",
                "自我診斷 / 修復",
                "Telegram Bot",
                "一鍵安裝腳本",
                "加密 / NFT 零件",
                "SEO / 廣告零件",
                "AI 內容生成",
                "記憶系統",
                "工具系統 (200+ 個)",
                "科技感儀表板",
                "定時調度系統",
                "健康循環系統",
            ],
            "enterprise": [
                "核心機械零件 (50 個)",
                "自我診斷 / 修復",
                "Telegram Bot",
                "一鍵安裝腳本",
                "加密 / NFT 零件",
                "SEO / 廣告零件",
                "AI 內容生成",
                "雲端託管服務",
                "專屬技術支援",
                "定製新零件",
                "SLA 保障",
                "記憶系統",
                "工具系統 (250+ 個)",
                "科技感儀表板",
                "定時調度系統",
                "健康循環系統",
            ],
        }
        return features.get(self.get_tier(), features["community"])
    
    def validate_key(self, key: str) -> bool:
        """驗證授權金鑰"""
        import hashlib
        if not key or "AMPM-" not in key:
            return False
        
        if "AMPM-PRO" in key:
            self.license_data["tier"] = "pro"
        elif "AMPM-ENT" in key:
            self.license_data["tier"] = "enterprise"
        
        key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
        
        valid_hashes = {
            "pro": ["97068ed4","35e42cb5","60fd1dfd","d2442225","836c0dc5",
                    "777449d8","65ecfedd","c9b1c025","ce526e19","4d66c0ee"],
            "enterprise": ["21519d65","e17b9160","ebfd839e","25d6c76f","e2e4eca1"],
        }
        
        for tier, hashes in valid_hashes.items():
            if key_hash in hashes:
                self.license_data["tier"] = tier
                return True
        return False
    
    def load_from_env(self):
        """從環境變數載入授權"""
        key = os.getenv("AMPM_LICENSE_KEY", "")
        if key:
            self.validate_key(key)
            print(f"🔑 已從環境變數載入授權：{self.get_tier()}")
