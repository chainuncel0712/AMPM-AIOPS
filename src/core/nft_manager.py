"""NFTManagerOrgan — NFT 投資組合管理器，追蹤持有集合、計算總值與各項統計指標"""
from __future__ import annotations

import re
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List

from skeleton.brain_component import BrainComponent

ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SUPPORTED_CHAINS = ["ethereum", "polygon", "arbitrum", "optimism", "bsc", "avalanche", "base", "zora", "solana"]

KNOWN_COLLECTION_PRICES: Dict[str, float] = {
    "Bored Ape Yacht Club": 28.0,
    "Mutant Ape Yacht Club": 5.5,
    "Azuki": 7.0,
    "Pudgy Penguins": 10.2,
    "CloneX": 3.8,
    "Doodles": 2.5,
    "Milady Maker": 4.2,
    "DeGods": 9.5,
    "Lil Pudgys": 1.8,
    "Captainz": 2.0,
    "CryptoPunks": 60.0,
    "Moonbirds": 1.5,
    "Cool Cats": 1.1,
    "World of Women": 0.8,
    "Meebits": 3.0,
    "VeeFriends": 2.2,
    "Otherside Koda": 4.8,
    "Nakamigos": 0.9,
    "Renga": 0.4,
    "Checks VV": 0.3,
}


def _validate_contract(contract: str) -> bool:
    """驗證合約地址格式"""
    return bool(ETH_ADDRESS_RE.match(contract.strip()))


def _validate_chain(chain: str) -> str:
    """驗證並正規化鏈名稱"""
    c = chain.strip().lower()
    if c not in SUPPORTED_CHAINS:
        raise ValueError(f"不支援的鏈: '{chain}'，支援: {', '.join(SUPPORTED_CHAINS)}")
    return c


def _deterministic_floor(collection_name: str) -> float:
    """從集合名稱產生確定性模擬地板價"""
    if collection_name in KNOWN_COLLECTION_PRICES:
        base = KNOWN_COLLECTION_PRICES[collection_name]
        seed = int(hashlib.sha256(collection_name.encode()).hexdigest(), 16) % 1000
        drift = (seed / 5000.0 - 0.1) * 0.05  # ±5%
        return round(base * (1.0 + drift), 4)
    seed = int(hashlib.sha256(collection_name.encode()).hexdigest(), 16) % 10000
    return round(0.05 + (seed / 100.0), 4)


def _calc_24h_change(floor: float) -> float:
    """從地板價推導一個合理的 24h 變化"""
    seed = int(hashlib.sha256(f"{floor}".encode()).hexdigest(), 16) % 100
    return round((seed / 50.0 - 1.0) * 10, 2)  # -10% ~ +10%


class NFTManagerOrgan(BrainComponent):
    """
    NFT 投資組合管理器官 — 維護使用者持有的 NFT 集合清單，
    追蹤每筆鑄造/購買成本、計算投資組合總值與各集合表現。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._portfolio: Dict[str, dict] = {}
        self._active = True

    # ------------------------------------------------------------------
    # 輔助方法
    # ------------------------------------------------------------------

    def _normalize_name(self, name: str) -> str:
        return name.strip()

    def _collection_floor(self, name: str) -> float:
        return _deterministic_floor(name)

    def _calc_portfolio_value(self, collection: dict) -> tuple:
        """計算集合的總成本與當前市值"""
        floor = self._collection_floor(collection["name"])
        items = collection.get("items", [])
        total_cost = sum(it.get("purchase_price_eth", 0.0) for it in items)
        total_value = len(items) * floor
        profit = total_value - total_cost
        profit_pct = (profit / total_cost * 100) if total_cost > 0 else 0.0
        return floor, len(items), total_cost, total_value, profit, profit_pct

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def add_collection(self, name: str, contract: str = "", chain: str = "ethereum") -> str:
        """
        將集合加入投資組合追蹤。

        參數:
            name: 集合名稱
            contract: 合約地址 (可選)
            chain: 區塊鏈名稱
        """
        name = self._normalize_name(name)
        if not name:
            return "❌ 集合名稱不可為空"

        if name in self._portfolio:
            return (
                f"⚠️ 已存在此集合: {name}\n"
                f"   使用 remove_collection() 移除後再重新加入"
            )

        if contract and not _validate_contract(contract):
            return f"❌ 合約地址格式無效: {contract[:20]}..."

        try:
            chain_key = _validate_chain(chain)
        except ValueError as e:
            return f"❌ {e}"

        self._portfolio[name] = {
            "name": name,
            "contract": contract or "未設定",
            "chain": chain_key,
            "items": [],
            "added_at": datetime.now(timezone.utc).isoformat(),
        }

        return (
            f"✅ 已加入投資組合\n"
            f"   集合: {name}\n"
            f"   合約: {contract or '未設定'}\n"
            f"   鏈: {chain_key}\n"
            f"   持有數量: 0 (使用 add_collection 加入後可手動維護)\n"
            f"   組合集合數: {len(self._portfolio)}"
        )

    def get_portfolio(self) -> str:
        """
        取得完整投資組合摘要，包含各集合市值與總值。
        """
        if not self._portfolio:
            return "📭 投資組合為空，使用 add_collection() 加入集合"

        lines = ["📊 NFT 投資組合報告"]
        total_value = 0.0
        total_cost = 0.0
        total_items = 0

        for name, collection in self._portfolio.items():
            floor, count, cost, value, profit, profit_pct = self._calc_portfolio_value(collection)
            change_24h = _calc_24h_change(floor)
            if count > 0:
                lines.append(
                    f"\n  ▸ {name[:35]}\n"
                    f"    合約: {collection['contract'][:10]}...  |  鏈: {collection['chain']}\n"
                    f"    持有: {count} 個 NFT  |  地板價: {floor:.4f} ETH  |  24h: {change_24h:+.2f}%\n"
                    f"    成本: {cost:.4f} ETH  |  市值: {value:.4f} ETH  |  損益: {profit:+.4f} ETH ({profit_pct:+.1f}%)"
                )
            else:
                lines.append(
                    f"\n  ▸ {name[:35]} [0 個 NFT]\n"
                    f"    合約: {collection['contract'][:10]}...  |  鏈: {collection['chain']}\n"
                    f"    地板價: {floor:.4f} ETH  |  24h: {change_24h:+.2f}%"
                )
            total_value += value
            total_cost += cost
            total_items += count

        total_profit = total_value - total_cost
        total_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0.0

        lines.append(f"\n{'─' * 50}")
        lines.append(f"  總持有: {total_items} 個 NFT")
        lines.append(f"  總成本: {total_cost:.4f} ETH")
        lines.append(f"  總市值: {total_value:.4f} ETH")
        lines.append(f"  總損益: {total_profit:+.4f} ETH ({total_pct:+.1f}%)")
        return "\n".join(lines)

    def get_collection_stats(self, collection: str) -> str:
        """
        取得指定集合的詳細統計資料。

        參數:
            collection: 集合名稱
        """
        found = None
        for name in self._portfolio:
            if collection.strip().lower() in name.lower():
                found = name
                break

        if not found:
            return f"❌ 投資組合中找不到集合: {collection}"

        col = self._portfolio[found]
        floor = self._collection_floor(found)
        change_24h = _calc_24h_change(floor)
        change_7d = _calc_24h_change(floor) * 3.2  # 放大 7d 波動
        items = col.get("items", [])
        total_cost = sum(it.get("purchase_price_eth", 0.0) for it in items)
        total_value = len(items) * floor
        profit = total_value - total_cost
        profit_pct = (profit / total_cost * 100) if total_cost > 0 else 0.0

        known = found in KNOWN_COLLECTION_PRICES
        market_rank = "n/a"
        if known:
            sorted_prices = sorted(KNOWN_COLLECTION_PRICES.values(), reverse=True)
            rank = sorted_prices.index(KNOWN_COLLECTION_PRICES[found]) + 1 if floor > 0 else 0
            market_rank = f"#{rank}/{len(sorted_prices)}"

        lines = [
            f"📊 {found} 詳細統計",
            f"   合約地址:    {col['contract']}",
            f"   鏈:          {col['chain']}",
            f"   加入時間:    {col['added_at'][:19]}",
            f"   目前地板價:  {floor:.4f} ETH",
            f"   24h 變化:    {change_24h:+.2f}%",
            f"   7d 變化:     {change_7d:+.2f}%",
            f"   持有數量:    {len(items)} 個 NFT",
            f"   總成本:      {total_cost:.4f} ETH",
            f"   總市值:      {total_value:.4f} ETH",
            f"   損益:        {profit:+.4f} ETH ({profit_pct:+.1f}%)",
            f"   市場排名:    {market_rank}",
        ]

        if items:
            lines.append("\n   持有明細:")
            for i, it in enumerate(items, 1):
                lines.append(
                    f"     #{i:<3} Token #{it.get('token_id', '?'):>5}  "
                    f"買入: {it.get('purchase_price_eth', 0):.4f} ETH"
                )

        return "\n".join(lines)

    def list_all_collections(self) -> str:
        """
        列出投資組合中所有集合名稱。
        """
        if not self._portfolio:
            return "📭 投資組合為空"

        lines = [f"📋 投資組合集合 ({len(self._portfolio)} 個):"]
        for name, col in self._portfolio.items():
            count = len(col.get("items", []))
            floor = self._collection_floor(name)
            change = _calc_24h_change(floor)
            lines.append(
                f"  ▸ {name[:35]:36s} "
                f"持有: {count:>3} 個  |  "
                f"地板: {floor:.4f} ETH  |  "
                f"24h: {change:+.2f}%"
            )
        return "\n".join(lines)

    def add_item(self, collection: str, token_id: str = "", purchase_price_eth: float = 0.0) -> str:
        """
        手動新增單個 NFT 至指定集合 (輔助方法，用於維護持倉)。

        參數:
            collection: 集合名稱
            token_id: Token ID (可選)
            purchase_price_eth: 購買價格 (ETH)
        """
        found = None
        for name in self._portfolio:
            if collection.strip().lower() in name.lower():
                found = name
                break
        if not found:
            return f"❌ 投資組合中找不到集合: {collection}"

        if purchase_price_eth < 0:
            return f"❌ 購買價格不可為負: {purchase_price_eth}"

        item = {
            "token_id": token_id or f"#{len(self._portfolio[found]['items']) + 1}",
            "purchase_price_eth": purchase_price_eth,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
        }
        self._portfolio[found]["items"].append(item)

        return (
            f"✅ 已新增 NFT 至 {found}\n"
            f"   Token: {item['token_id']}\n"
            f"   買入價: {purchase_price_eth:.4f} ETH\n"
            f"   集合總持有: {len(self._portfolio[found]['items'])} 個"
        )

    def remove_collection(self, collection: str) -> str:
        """
        從投資組合移除指定集合。

        參數:
            collection: 集合名稱
        """
        found = None
        for name in list(self._portfolio.keys()):
            if collection.strip().lower() in name.lower():
                found = name
                break

        if not found:
            return f"❌ 投資組合中找不到集合: {collection}"

        items_count = len(self._portfolio[found].get("items", []))
        del self._portfolio[found]

        return (
            f"🗑️ 已移除集合: {found}\n"
            f"   曾持有: {items_count} 個 NFT\n"
            f"   組合剩餘集合: {len(self._portfolio)}"
        )

    def status(self) -> dict:
        """
        回報器官當前運行狀態。
        """
        total_items = sum(len(c.get("items", [])) for c in self._portfolio.values())
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "portfolio_collections": len(self._portfolio),
            "total_items": total_items,
            "supported_chains": SUPPORTED_CHAINS,
        }
