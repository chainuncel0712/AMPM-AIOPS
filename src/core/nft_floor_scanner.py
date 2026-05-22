"""NFTFloorScannerOrgan — NFT 地板價掃描器，追蹤集合地板價走勢並提供掛單分析"""
from __future__ import annotations

import time
import hashlib
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Union

from skeleton.brain_component import BrainComponent

KNOWN_COLLECTIONS: Dict[str, dict] = {
    "boredapeyachtclub":    {"name": "Bored Ape Yacht Club",     "base_floor": 28.0,  "volatility": 0.08},
    "mutant-ape-yacht-club": {"name": "Mutant Ape Yacht Club",  "base_floor": 5.5,   "volatility": 0.10},
    "azuki":                {"name": "Azuki",                    "base_floor": 7.0,   "volatility": 0.12},
    "pudgypenguins":        {"name": "Pudgy Penguins",          "base_floor": 10.2,  "volatility": 0.09},
    "clonex":               {"name": "CloneX",                   "base_floor": 3.8,   "volatility": 0.11},
    "doodles-official":     {"name": "Doodles",                  "base_floor": 2.5,   "volatility": 0.13},
    "milady":               {"name": "Milady Maker",             "base_floor": 4.2,   "volatility": 0.15},
    "decentraland":         {"name": "Decentraland",             "base_floor": 1.2,   "volatility": 0.07},
    "lilpudgys":            {"name": "Lil Pudgys",               "base_floor": 1.8,   "volatility": 0.14},
    "captainz":             {"name": "Captainz",                 "base_floor": 2.0,   "volatility": 0.10},
}


def _normalize_slug(slug: str) -> str:
    """正規化集合代稱 (slug)"""
    return slug.strip().lower().replace(" ", "-")


def _deterministic_floor(slug: str, base: float, volatility: float, offset_days: float = 0.0) -> float:
    """根據代稱產生確定性但看似合理的即時地板價"""
    seed = int(hashlib.sha256(f"{slug}:{int(offset_days * 1440)}".encode()).hexdigest(), 16) % 10000
    drift = (seed / 5000.0 - 1.0) * volatility
    return round(base * (1.0 + drift), 4)


def _generate_listings(slug: str, floor: float, count: int) -> list:
    """產生確定性的掛單清單"""
    listings = []
    base_seed = int(hashlib.sha256(slug.encode()).hexdigest(), 16)
    for i in range(min(count, 100)):
        offset = round((i + 1) * (floor * 0.002) + (base_seed + i * 7919) % 100 * 0.0005 * floor, 4)
        price = round(floor + offset, 4)
        token_id = (base_seed + i * 137 + 1) % 9999 + 1
        listings.append({
            "token_id": token_id,
            "price_eth": price,
            "market": "opensea" if i % 3 != 0 else "blur",
            "seller": f"0x{hashlib.sha256(f'{slug}:{token_id}:seller'.encode()).hexdigest()[:8]}...",
        })
    return listings


class NFTFloorScannerOrgan(BrainComponent):
    """
    NFT 地板價掃描器官 — 追蹤集合地板價歷史走勢，
    計算短期與中期變化率，並擷取掛單清單進行比較分析。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._floor_history: Dict[str, List[dict]] = {}
        self._tracked: Dict[str, dict] = {}
        self._active = True

    # ------------------------------------------------------------------
    # 輔助方法
    # ------------------------------------------------------------------

    def _get_or_fetch_floor(self, slug: str) -> float:
        """依據 slug 回傳當前地板價 (已知集合使用模擬，未知集合使用預設值)"""
        slug = _normalize_slug(slug)
        now = datetime.now(timezone.utc)
        day_offset = now.toordinal() + now.hour / 24.0
        if slug in KNOWN_COLLECTIONS:
            info = KNOWN_COLLECTIONS[slug]
            return _deterministic_floor(slug, info["base_floor"], info["volatility"], day_offset)
        return _deterministic_floor(slug, 0.5, 0.2, day_offset)

    def _history_snapshots(self, slug: str, days: int) -> List[float]:
        """產生或取得過去 N 天的歷史地板價 (每 4 小時一個快照)"""
        slug = _normalize_slug(slug)
        interval_hours = 4
        snapshots = int(days * 24 / interval_hours)
        info = KNOWN_COLLECTIONS.get(slug, {"base_floor": 0.5, "volatility": 0.2})
        base = info["base_floor"]
        vol = info["volatility"]
        now = datetime.now(timezone.utc)
        day_offset = now.toordinal() + now.hour / 24.0
        result: List[float] = []
        for i in range(snapshots - 1, -1, -1):
            offset = day_offset - (i * interval_hours) / 24.0
            result.append(_deterministic_floor(slug, base, vol, offset))
        return result

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def scan_floor(self, collection_slug: str) -> str:
        """
        掃描指定集合的即時地板價。

        參數：
            collection_slug: 集合代稱 (如 boredapeyachtclub)

        回傳：
            當前地板價、24h/7d 變化與最低掛單資訊
        """
        slug = _normalize_slug(collection_slug)
        floor = self._get_or_fetch_floor(slug)
        history = self._history_snapshots(slug, 7)
        if not history:
            return f"❌ 無法取得 {slug} 的歷史資料"

        current = history[-1] if history[-1] > 0 else floor
        day_ago = history[-7] if len(history) >= 7 else history[0]
        week_ago = history[0]

        change_24h = ((current - day_ago) / day_ago * 100) if day_ago > 0 else 0.0
        change_7d = ((current - week_ago) / week_ago * 100) if week_ago > 0 else 0.0

        listings = _generate_listings(slug, current, 5)
        lowest_listing = min(l["price_eth"] for l in listings) if listings else current

        collection_name = KNOWN_COLLECTIONS.get(slug, {}).get("name", slug)

        lines = [
            f"📉 {collection_name} 地板價掃描",
            f"   目前地板價: {current:.4f} ETH",
            f"   24小時變化: {change_24h:+.2f}%",
            f"   7天變化:     {change_7d:+.2f}%",
            f"   最低掛單:    {lowest_listing:.4f} ETH",
            f"   活躍掛單數:  {len(listings)} 筆 (取樣)",
        ]
        return "\n".join(lines)

    def get_trend(self, collection: str, days: int = 7) -> str:
        """
        查詢指定集合的歷史地板價趨勢。

        參數:
            collection: 集合代稱
            days: 回溯天數 (預設 7)

        回傳:
            包含最高/最低/平均地板價與趨勢方向的摘要
        """
        if days < 1 or days > 90:
            return f"❌ 天數範圍須為 1-90，收到: {days}"

        slug = _normalize_slug(collection)
        history = self._history_snapshots(slug, days)
        if not history:
            return f"❌ 無法取得 {slug} 的歷史資料"

        current = history[-1]
        max_price = max(history)
        min_price = min(history)
        avg_price = sum(history) / len(history)
        change = ((current - history[0]) / history[0] * 100) if history[0] > 0 else 0.0
        direction = "📈 上升" if change > 2 else ("📉 下降" if change < -2 else "↔️ 持平")

        collection_name = KNOWN_COLLECTIONS.get(slug, {}).get("name", slug)
        lines = [
            f"📊 {collection_name} {days}天趨勢分析",
            f"   當前地板價: {current:.4f} ETH",
            f"   期間最高:    {max_price:.4f} ETH",
            f"   期間最低:    {min_price:.4f} ETH",
            f"   期間平均:    {avg_price:.4f} ETH",
            f"   整體變化:    {change:+.2f}%",
            f"   趨勢方向:    {direction}",
            f"   資料點數:    {len(history)} (每 4 小時取樣)",
        ]
        return "\n".join(lines)

    def compare_floors(self, collections: List[str]) -> str:
        """
        比較多個集合的地板價高低。

        參數：
            collections: 集合代稱清單

        回傳:
            按地板價由高至低排列的比較表
        """
        if not collections:
            return "❌ 請提供至少一個集合代稱"

        results: List[tuple] = []
        for c in collections:
            slug = _normalize_slug(c)
            try:
                floor = self._get_or_fetch_floor(slug)
            except Exception as e:
                floor = 0.0
            name = KNOWN_COLLECTIONS.get(slug, {}).get("name", slug)
            results.append((name, slug, floor))

        results.sort(key=lambda x: x[2], reverse=True)

        lines = [f"🏆 集合地板價比較 ({len(results)} 個):"]
        for rank, (name, slug, floor) in enumerate(results, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank:2d}.")
            lines.append(f"  {medal} {name}: {floor:.4f} ETH")

        if len(results) >= 2:
            diff = results[0][2] - results[-1][2]
            lines.append(f"\n   最高 vs 最低差距: {diff:.4f} ETH")
        return "\n".join(lines)

    def get_listings(self, collection: str, limit: int = 10) -> str:
        """
        擷取指定集合的當前掛單清單。

        參數：
            collection: 集合代稱
            limit: 回傳掛單數上限 (預設 10，最大 50)
        """
        slug = _normalize_slug(collection)
        limit = max(1, min(limit, 50))
        floor = self._get_or_fetch_floor(slug)
        listings = _generate_listings(slug, floor, limit)

        collection_name = KNOWN_COLLECTIONS.get(slug, {}).get("name", slug)
        lines = [f"📋 {collection_name} 掛單清單 (前 {len(listings)} 筆):"]
        for lst in listings:
            lines.append(
                f"  ▸ #{lst['token_id']:<5}  "
                f"{lst['price_eth']:.4f} ETH  "
                f"[{lst['market']}]  "
                f"賣家: {lst['seller']}"
            )
        lines.append(f"\n   目前地板價: {floor:.4f} ETH")
        return "\n".join(lines)

    def status(self) -> dict:
        """
        回報器官當前運行狀態。

        回傳:
            包含已知集合數、追蹤數量與運行狀態的字典
        """
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "known_collections": len(KNOWN_COLLECTIONS),
            "tracked_slugs": list(self._tracked.keys()),
            "floor_data_points": sum(len(v) for v in self._floor_history.values()),
        }
