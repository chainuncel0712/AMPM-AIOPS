"""
授權產生器 - 用於產生付費授權金鑰
支援 Gumroad 自動發送
"""
import json
import hashlib
import hmac
import os
from datetime import datetime, timedelta

# 從環境變數讀取秘密金鑰
SECRET_KEY = os.getenv("LICENSE_SECRET_KEY", "your-secret-key-change-this")

def generate_license(tier: str, days: int = 365) -> str:
    """產生授權金鑰"""
    data = {
        "tier": tier,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(days=days)).isoformat(),
    }
    
    # 產生簽名
    message = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    license_key = f"{tier.upper()}-{signature}"
    return license_key

def validate_license(license_key: str) -> dict:
    """驗證授權金鑰"""
    try:
        parts = license_key.split("-")
        tier = parts[0].lower()
        signature = parts[1]
        
        # 驗證簽名
        expected_data = {
            "tier": tier,
            "created": "2026-01-01T00:00:00",
            "expires": (datetime.now() + timedelta(days=365)).isoformat()
        }
        message = json.dumps(expected_data, sort_keys=True)
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        if signature == expected_signature:
            return {
                "valid": True,
                "tier": tier,
                "expires": (datetime.now() + timedelta(days=365)).isoformat()
            }
        
        return {"valid": False, "tier": "community"}
    except:
        return {"valid": False, "tier": "community"}

def generate_license_for_gumroad(tier: str, customer_email: str) -> dict:
    """
    為 Gumroad 買家產生授權金鑰
    
    參數：
        tier: 版本 (basic, pro, enterprise)
        customer_email: 買家 Email
    
    回傳：
        包含授權資訊的字典
    """
    days_map = {
        "basic": 365,
        "pro": 365,
        "enterprise": 30  # 月費制
    }
    
    days = days_map.get(tier, 365)
    license_key = generate_license(tier, days)
    
    return {
        "license_key": license_key,
        "tier": tier,
        "customer_email": customer_email,
        "expires": (datetime.now() + timedelta(days=days)).isoformat(),
        "created": datetime.now().isoformat()
    }
