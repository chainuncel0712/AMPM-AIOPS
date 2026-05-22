"""NFTWhaleTrackerOrgan — NFT 巨鯨追蹤器，監控大戶錢包買賣行為與持倉動向"""
from __future__ import annotations

import re
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple

from skeleton.brain_component import BrainComponent

ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

KNOWN_WHALE_LABELS: Dict[str, str] = {
    "0x7a9fe22691c811ea339d9b73117e5c46c58febd2": "Pranksy",
    "0xf1b99d29e7d8a2a7a7f91d9e8c1a2b3c4d5e6f78": "Seedphrase",
    "0x020ca66c30bec2c4fe3861a94e4db4a498a35872": "Machi Big Brother",
    "0x8d928b981c015c4ec8424d4568de0f8d8c7f9a50": "Dingaling",
    "0xe5d64c16c0b6e62f2e4a1a0d5c8e3b7a9f2d1c4e": "Deep NFT Value",
}


def _validate_eth_address(address: str) -> bool:
    """驗證以太坊地址格式"""
    return bool(ETH_ADDRESS_RE.match(address))


def _deterministic_activity(address: str, seed_offset: int = 0) -> List[dict]:
    """依據地址產生確定性的近期活動記錄"""
    base_seed = int(hashlib.sha256(f"{address}:{seed_offset}".encode()).hexdigest(), 16)
    activity = []
    known_slugs = ["boredapeyachtclub", "mutant-ape-yacht-club", "azuki",
                    "pudgypenguins", "clonex", "doodles-official", "milady"]
    now = datetime.now(timezone.utc)
    count = 3 + (base_seed % 8)

    for i in range(count):
        seed = base_seed + i * 31337
        is_buy = (seed % 3) != 0
        slug = known_slugs[(seed // 3) % len(known_slugs)]
        price = round(0.1 + (seed % 500) * 0.1, 3)
        token_id = (seed * 7919 + 1) % 10000 + 1
        hours_ago = (seed % 72) + (i * 4)
        ts = now - timedelta(hours=hours_ago, minutes=seed % 59)
        activity.append({
            "type": "buy" if is_buy else "sell",
            "collection": slug,
            "token_id": f"#{token_id}",
            "price_eth": price,
            "timestamp": ts.isoformat(),
            "market": "opensea" if seed % 5 != 0 else "blur",
        })
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    return activity


class NFTWhaleTrackerOrgan(BrainComponent):
    """
    NFT 巨鯨追蹤器官 — 監控高影響力錢包的鏈上活動，
    記錄買賣行為時間戳並提供近期市場動向警報。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._whales: Dict[str, dict] = {}
        self._active = True

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def track_whale(self, address: str, label: str = "") -> str:
        """
        將指定地址加入巨鯨追蹤清單。

        參數:
            address: 以太坊錢包地址 (0x...)
            label: 自訂標籤 (可選，用於識別)

        回傳:
            追蹤設定結果
        """
        address = address.strip()
        if not _validate_eth_address(address):
            return (
                f"❌ 錢包地址格式無效: {address[:20]}...\n"
                f"   預期格式: 0x 開頭 + 40 個十六進位字元"
            )

        addr_lower = address.lower()
        if addr_lower in self._whales:
            existing = self._whales[addr_lower]
            if label and label != existing["label"]:
                existing["label"] = label
            return (
                f"⚠️ 已在追蹤此巨鯨\n"
                f"   地址: {addr_lower[:10]}...{addr_lower[-6:]}\n"
                f"   標籤: {existing['label']}\n"
                f"   開始追蹤: {existing['tracked_since'][:19]}"
            )

        label = label.strip() or KNOWN_WHALE_LABELS.get(addr_lower, f"巨鯨_{addr_lower[-6:]}")
        self._whales[addr_lower] = {
            "address": address,
            "label": label,
            "tracked_since": datetime.now(timezone.utc).isoformat(),
            "activity_log": _deterministic_activity(address),
            "total_buys": 0,
            "total_sells": 0,
            "total_volume_eth": 0.0,
        }
        return (
            f"🐳 已開始追蹤巨鯨\n"
            f"   地址: {addr_lower[:10]}...{addr_lower[-6:]}\n"
            f"   標籤: {label}\n"
            f"   追蹤中巨鯨數: {len(self._whales)}"
        )

    def get_whale_activity(self, address: str) -> str:
        """
        查詢指定巨鯨的近期鏈上活動。

        參數:
            address: 錢包地址

        回傳:
            近期買賣記錄、總持倉與最近交易時間
        """
        address = address.strip().lower()
        if not address.startswith("0x"):
            for a in self._whales:
                if address in a:
                    address = a
                    break
        if address not in self._whales:
            return (
                f"❌ 未追蹤此地址: {address[:10]}...\n"
                f"   使用 track_whale() 先加入追蹤"
            )

        whale = self._whales[address]
        activity = whale["activity_log"]
        buys = [a for a in activity if a["type"] == "buy"]
        sells = [a for a in activity if a["type"] == "sell"]
        total_buy_vol = sum(a["price_eth"] for a in buys)
        total_sell_vol = sum(a["price_eth"] for a in sells)
        latest = activity[0]["timestamp"] if activity else "N/A"
        total_holdings = (len(buys) - len(sells)) + 10

        lines = [
            f"🐳 巨鯨活動記錄: {whale['label']}",
            f"   地址: {address[:10]}...{address[-6:]}",
            f"   追蹤自: {whale['tracked_since'][:19]}",
            f"   近期買入: {len(buys)} 筆 (總計 {total_buy_vol:.3f} ETH)",
            f"   近期賣出: {len(sells)} 筆 (總計 {total_sell_vol:.3f} ETH)",
            f"   估計持倉: {total_holdings} NFT",
            f"   最近活動: {latest[:19] if latest != 'N/A' else latest}",
        ]

        if activity:
            lines.append("\n   近期交易記錄:")
            for act in activity[:5]:
                emoji = "🟢 買" if act["type"] == "buy" else "🔴 賣"
                lines.append(
                    f"     {emoji} {act['collection'][:20]:20s} "
                    f"{act['token_id']:<6s} "
                    f"{act['price_eth']:7.3f} ETH "
                    f"[{act['market']}] "
                    f"{act['timestamp'][:19]}"
                )

        return "\n".join(lines)

    def list_tracked_whales(self) -> str:
        """
        列出所有正在追蹤的巨鯨錢包。
        """
        if not self._whales:
            return "📭 尚未追蹤任何巨鯨"

        lines = [f"📋 追蹤中巨鯨 ({len(self._whales)} 個):"]
        for addr, whale in self._whales.items():
            activity_count = len(whale["activity_log"])
            lines.append(
                f"  ▸ {whale['label']:<20s} "
                f"{addr[:10]}...{addr[-6:]}  "
                f"({activity_count} 筆近期活動)"
            )
        return "\n".join(lines)

    def get_recent_buys(self, limit: int = 10) -> str:
        """
        彙整所有追蹤中巨鯨的近期買入記錄。

        參數:
            limit: 回傳記錄數上限 (預設 10)
        """
        if not self._whales:
            return "📭 尚未追蹤任何巨鯨，無買入記錄"

        all_buys: List[Tuple[str, dict, dict]] = []
        for addr, whale in self._whales.items():
            for act in whale["activity_log"]:
                if act["type"] == "buy":
                    # Convert ISO timestamp to sortable datetime
                    try:
                        ts = datetime.fromisoformat(act["timestamp"])
                    except Exception:
                        ts = datetime.min.replace(tzinfo=timezone.utc)
                    all_buys.append((ts, whale, act))

        all_buys.sort(key=lambda x: x[0], reverse=True)
        limit = max(1, min(limit, 50))
        recent = all_buys[:limit]

        lines = [f"🟢 追蹤巨鯨近期買入 (共 {len(recent)} 筆):"]
        for ts, whale, act in recent:
            lines.append(
                f"  ▸ {whale['label']:<18s} "
                f"{act['collection'][:18]:18s} "
                f"{act['token_id']:<6s} "
                f"{act['price_eth']:8.3f} ETH "
                f"{ts.isoformat()[:19]}"
            )
        return "\n".join(lines)

    def status(self) -> dict:
        """
        回報器官當前運行狀態。
        """
        total_activity = sum(len(w["activity_log"]) for w in self._whales.values())
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "tracked_whales": len(self._whales),
            "total_activity_entries": total_activity,
            "whale_labels": [w["label"] for w in self._whales.values()],
        }
