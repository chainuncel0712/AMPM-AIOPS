#!/usr/bin/env python3
"""金鑰產生器 — 一鍵產生 AMPM-AIOPS 授權金鑰"""
import hashlib
import random
import string
from datetime import datetime

def generate_key(tier="pro", count=10):
    """產生授權金鑰"""
    keys = []
    prefix = {"pro": "AMPM-PRO", "enterprise": "AMPM-ENT"}
    p = prefix.get(tier, "AMPM-PRO")
    
    for _ in range(count):
        # 金鑰格式：AMPM-PRO-XXXX-XXXX-XXXX
        segments = []
        for _ in range(3):
            seg = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            segments.append(seg)
        key = f"{p}-{'-'.join(segments)}"
        key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
        keys.append({"key": key, "hash": key_hash, "tier": tier})
    
    return keys

if __name__ == "__main__":
    print("=" * 60)
    print("  AMPM-AIOPS 授權金鑰產生器")
    print("=" * 60)
    
    pro_keys = generate_key("pro", 10)
    ent_keys = generate_key("enterprise", 5)
    
    print("\n🔑 Pro 金鑰 (10 組)：")
    for k in pro_keys:
        print(f"  {k['key']}  (hash: {k['hash']})")
    
    print("\n🔑 Enterprise 金鑰 (5 組)：")
    for k in ent_keys:
        print(f"  {k['key']}  (hash: {k['hash']})")
    
    print("\n📋 Gumroad 貼上專用格式：")
    print("-" * 40)
    for k in pro_keys:
        print(k['key'])
    for k in ent_keys:
        print(k['key'])
    
    print("\n✅ 把上面的金鑰複製到 Gumroad 商品內容即可")
    print("⚠️ 這些金鑰僅供展示，正式販售時請重新產生！")
