"""NFTMarketMakerOrgan — NFT 造市引擎，管理買賣雙向掛單價差與潛在利潤計算"""
from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List

from skeleton.brain_component import BrainComponent

SPREAD_MIN = 0.1
SPREAD_MAX = 100.0

SUPPORTED_MARKETS = ["opensea", "blur", "looksrare", "x2y2", "rarible", "sudoswap"]


def _short_uid() -> str:
    """產生短唯一識別碼"""
    return uuid.uuid4().hex[:12]


def _deterministic_floor(name: str) -> float:
    """從集合名稱產生確定性模擬地板價"""
    seed = int(hashlib.sha256(name.encode()).hexdigest(), 16) % 10000
    return round(0.05 + (seed / 100.0), 4)


class NFTMarketMakerOrgan(BrainComponent):
    """
    NFT 造市器器官 — 為指定集合建立雙向掛單市場，
    管理買入價與賣出價的價差設定，並即時計算潛在利潤。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._markets: Dict[str, dict] = {}
        self._id_counter = 0
        self._active = True

    # ------------------------------------------------------------------
    # 輔助方法
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"MK-{self._id_counter:04d}"

    def _calculate_prices(self, floor_price: float, spread_percent: float) -> tuple:
        """根據地板價與價差百分比計算買入/賣出價格"""
        half_spread = spread_percent / 2.0
        bid_factor = 1.0 - (half_spread / 100.0)
        ask_factor = 1.0 + (half_spread / 100.0)
        bid_price = round(floor_price * bid_factor, 4)
        ask_price = round(floor_price * ask_factor, 4)
        return bid_price, ask_price

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def create_market(self, collection: str, spread_percent: float) -> str:
        """
        為指定集合建立雙向造市市場。

        參數:
            collection: 集合名稱或代稱
            spread_percent: 買賣價差百分比 (0.1-100)

        回傳:
            市場建立結果，包含買入/賣出價格與預估利潤
        """
        collection = collection.strip()
        if not collection:
            return "❌ 集合名稱不可為空"

        try:
            spread_percent = float(spread_percent)
        except (TypeError, ValueError):
            return f"❌ 價差百分比格式無效: {spread_percent}"

        if not (SPREAD_MIN <= spread_percent <= SPREAD_MAX):
            return f"❌ 價差百分比需在 {SPREAD_MIN}-{SPREAD_MAX}% 之間，收到: {spread_percent}"

        floor_price = _deterministic_floor(collection)
        bid_price, ask_price = self._calculate_prices(floor_price, spread_percent)
        potential_profit = round(ask_price - bid_price, 4)
        market_id = self._next_id()

        self._markets[market_id] = {
            "id": market_id,
            "collection": collection,
            "spread_percent": spread_percent,
            "floor_price": floor_price,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "potential_profit": potential_profit,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return (
            f"📊 造市市場已建立\n"
            f"   市場ID:     {market_id}\n"
            f"   集合:       {collection[:30]}\n"
            f"   地板價:     {floor_price:.4f} ETH\n"
            f"   買入價:     {bid_price:.4f} ETH\n"
            f"   賣出價:     {ask_price:.4f} ETH\n"
            f"   價差:       {spread_percent:.2f}%\n"
            f"   單筆潛在利潤: {potential_profit:.4f} ETH\n"
            f"   狀態:       活躍"
        )

    def list_active_markets(self) -> str:
        """
        列出所有活躍的造市市場。
        """
        active = {mid: m for mid, m in self._markets.items() if m["active"]}
        if not active:
            return "📭 目前沒有活躍的造市市場"

        lines = [f"📋 活躍造市市場 ({len(active)} 個):"]
        for mid, mkt in active.items():
            lines.append(
                f"  ▸ [{mid}] {mkt['collection'][:25]:26s} "
                f"買 {mkt['bid_price']:.4f} / 賣 {mkt['ask_price']:.4f} ETH "
                f"價差 {mkt['spread_percent']:.1f}%"
            )
        total_potential = sum(m["potential_profit"] for m in active.values())
        lines.append(f"\n   活躍市場潛在總利潤: {total_potential:.4f} ETH")
        return "\n".join(lines)

    def update_spread(self, market_id: str, new_spread: float) -> str:
        """
        更新指定市場的買賣價差。

        參數:
            market_id: 市場ID
            new_spread: 新價差百分比
        """
        if market_id not in self._markets:
            return f"❌ 找不到市場ID: {market_id}"

        mkt = self._markets[market_id]
        if not mkt["active"]:
            return f"⚠️ 市場 {market_id} 已取消，無法更新價差"

        try:
            new_spread = float(new_spread)
        except (TypeError, ValueError):
            return f"❌ 新價差格式無效: {new_spread}"

        if not (SPREAD_MIN <= new_spread <= SPREAD_MAX):
            return f"❌ 價差需在 {SPREAD_MIN}-{SPREAD_MAX}% 之間，收到: {new_spread}"

        old_spread = mkt["spread_percent"]
        bid_price, ask_price = self._calculate_prices(mkt["floor_price"], new_spread)
        mkt["spread_percent"] = new_spread
        mkt["bid_price"] = bid_price
        mkt["ask_price"] = ask_price
        mkt["potential_profit"] = round(ask_price - bid_price, 4)

        return (
            f"🔄 已更新市場 [{market_id}] 價差\n"
            f"   集合:       {mkt['collection'][:30]}\n"
            f"   舊價差:     {old_spread:.2f}%\n"
            f"   新價差:     {new_spread:.2f}%\n"
            f"   新買入價:   {bid_price:.4f} ETH\n"
            f"   新賣出價:   {ask_price:.4f} ETH\n"
            f"   新潛在利潤: {mkt['potential_profit']:.4f} ETH"
        )

    def cancel_market(self, market_id: str) -> str:
        """
        取消指定造市市場。

        參數:
            market_id: 市場ID
        """
        if market_id not in self._markets:
            return f"❌ 找不到市場ID: {market_id}"

        mkt = self._markets[market_id]
        if not mkt["active"]:
            return f"⚠️ 市場 {market_id} 已於先前取消 ({mkt['collection'][:25]}...)"

        mkt["active"] = False
        return (
            f"🛑 已取消市場 [{market_id}]\n"
            f"   集合:       {mkt['collection'][:30]}\n"
            f"   價差:       {mkt['spread_percent']:.2f}%\n"
            f"   建立時間:   {mkt['created_at'][:19]}"
        )

    def status(self) -> dict:
        """
        回報器官當前運行狀態。
        """
        active_count = sum(1 for m in self._markets.values() if m["active"])
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "total_markets": len(self._markets),
            "active_markets": active_count,
            "supported_markets": SUPPORTED_MARKETS,
        }
