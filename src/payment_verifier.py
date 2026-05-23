"""BSC USDT payment verifier — checks BscScan for incoming transfers."""

import os
import json
import time
from pathlib import Path
from datetime import datetime

import requests

BSCSCAN_API = "https://api.bscscan.com/api"
WALLET = "0x7f3110c1314bD68Fdf8E32cD921E646912108587"
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"  # USDT BEP20
CLAIMED_FILE = Path(__file__).parent.parent / "data" / "claimed_txids.json"

AMOUNT_PLANS = [
    (300, 365, "enterprise", "企業版（$300/年）"),
    (25,  90,  "pro",       "專業版（$25/季）"),
    (10,  30,  "basic",     "基礎版（$10/月）"),
]


def _api_key():
    key = os.environ.get("BSCSCAN_API_KEY", "")
    if not key:
        key = "YourBscScanApiKeyHere"  # placeholder
    return key


def _load_claimed():
    if CLAIMED_FILE.exists():
        try:
            return set(json.loads(CLAIMED_FILE.read_text()))
        except Exception:
            return set()
    return set()


def _save_claimed(claimed: set):
    CLAIMED_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLAIMED_FILE.write_text(json.dumps(list(claimed), indent=2))


def verify_tx(txid: str) -> dict:
    """
    Verify a BSC transaction on BscScan.
    Returns dict with keys: success (bool), message (str),
    optionally: amount (float), from_address (str), plan (str), days (int)
    """
    txid = txid.strip()
    if not txid.startswith("0x") or len(txid) != 66:
        return {"success": False, "message": "❌ TXID 格式錯誤，應為 66 字元的 0x 開頭哈希。"}

    claimed = _load_claimed()
    if txid in claimed:
        return {"success": False, "message": "❌ 此 TXID 已被兌換過。"}

    # Call BscScan
    params = {
        "module": "account",
        "action": "tokentx",
        "txhash": txid,
        "apikey": _api_key(),
    }
    try:
        resp = requests.get(BSCSCAN_API, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        return {"success": False, "message": f"❌ 查詢 BscScan 失敗：{e}"}

    if data.get("status") != "1" or not data.get("result"):
        msg = data.get("result", data.get("message", "查無交易"))
        if "No transactions found" in str(msg):
            return {"success": False, "message": "❌ 該 TXID 在鏈上未找到交易。"}
        return {"success": False, "message": f"❌ BscScan 查詢失敗：{msg}"}

    # Find matching transfer
    transfers = data["result"] if isinstance(data["result"], list) else [data["result"]]
    for tx in transfers:
        if (tx.get("to", "").lower() == WALLET.lower()
                and tx.get("contractAddress", "").lower() == USDT_CONTRACT.lower()):
            try:
                raw_amount = tx.get("value", "0")
                decimals = int(tx.get("tokenDecimal", 18))
                amount = float(raw_amount) / (10 ** decimals)
            except Exception:
                continue

            from_addr = tx.get("from", "unknown")
            timestamp = int(tx.get("timeStamp", 0))
            tx_date = datetime.utcfromtimestamp(timestamp).isoformat() if timestamp else "unknown"

            # Find matching plan
            for min_amount, days, tier, plan in sorted(AMOUNT_PLANS, reverse=True):
                if amount >= min_amount:
                    # Mark claimed
                    claimed.add(txid)
                    _save_claimed(claimed)
                    return {
                        "success": True,
                        "amount": amount,
                        "from_address": from_addr,
                        "plan": plan,
                        "tier": tier,
                        "days": days,
                        "tx_date": tx_date,
                        "message": f"✅ 收到 {amount:.2f} USDT，符合{plan}（{days} 天）。"
                    }

            # Amount too small
            return {
                "success": False,
                "message": f"❌ 收到 {amount:.2f} USDT，但最低方案為 $10。請補足差額後聯繫管理員。"

            }

    return {"success": False, "message": "❌ 該交易未包含轉入收款錢包的 USDT BEP20 轉帳。"}
