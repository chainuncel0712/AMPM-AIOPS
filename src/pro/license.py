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
                "核心 Runtime 狀態機",
                "基礎三層記憶系統",
                "基礎工具系統",
                "Telegram Bot 介面",
                "防火牆與熔斷器",
                "Plugin SDK",
                "基本儀表板",
            ],
            "pro": [
                "社群版全部功能 +",
                "自我進化循環 (Evolution Cycle)",
                "自我修復 (Self-Repair)",
                "工具自動生成 (Tool Creator)",
                "多 Agent 調度",
                "中樞神經系統 (Orchestrator)",
                "進階儀表板",
                "Email 技術支援",
            ],
            "enterprise": [
                "專業版全部功能 +",
                "完整商業模組 (行銷/SEO/社群)",
                "加密貨幣/NFT 模組全套",
                "多租戶 SaaS 系統",
                "自訂進化策略",
                "私有部署支援",
                "SLA 保證",
            ],
        }
        return features.get(self.get_tier(), features["community"])
    
    def is_feature_allowed(self, feature_name: str) -> bool:
        """檢查特定功能是否被允許"""
        tier_features = {
            "community": ["runtime", "memory", "tools", "telegram", "firewall", "plugin", "dashboard"],
            "pro": ["runtime", "memory", "tools", "telegram", "firewall", "plugin", "dashboard",
                    "evolution", "self_repair", "tool_creator", "orchestrator", "multi_agent"],
            "enterprise": ["runtime", "memory", "tools", "telegram", "firewall", "plugin", "dashboard",
                          "evolution", "self_repair", "tool_creator", "orchestrator", "multi_agent",
                          "commerce", "crypto", "nft", "saas", "custom_evolution"],
        }
        allowed = tier_features.get(self.get_tier(), tier_features["community"])
        return feature_name in allowed
    
    def validate_key(self, key: str) -> bool:
        """驗證授權金鑰"""
        import hashlib
        if not key or "AMPM-" not in key:
            return False
        
        # 決定層級
        if "AMPM-PRO" in key:
            self.license_data["tier"] = "pro"
        elif "AMPM-ENT" in key:
            self.license_data["tier"] = "enterprise"
        
        key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
        
        # 此處的金鑰雜湊會與 keygen.py 配對
        # 正式販售時，將 keygen.py 產生的雜湊貼到這裡
        valid_hashes = {
            "pro": ["a1b2c3d4"],
            "enterprise": ["e5f6g7h8"],
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
