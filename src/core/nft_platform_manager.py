"""NFTPlatformManagerOrgan — NFT 鑄造平臺管理核心引擎，驅動鑄造、上架排程、廣告投放與銷售結算全鏈路自動化"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any

from skeleton.brain_component import BrainComponent
from src.tools import tool

AD_PLATFORMS: List[str] = ["twitter", "discord", "opensea_ads", "nft_calendar", "rarity_sniper"]
VALID_STATUSES: List[str] = ["draft", "minted", "listed", "scheduled", "sold"]
COLLECTION_CATEGORIES: List[str] = [
    "art", "music", "pfp", "game", "metaverse",
    "photography", "domain", "virtual_world", "membership", "utility",
]

_AD_COPY_TEMPLATES: Dict[str, List[str]] = {
    "twitter": [
        "🔥 全新 NFT「{name}」現已上架！來看看這件獨一無二的數位收藏品\n🎨 {description_trunc}\n🔗 立即收藏：{link}",
        "⚡️ 限量發行「{name}」— {description_trunc}\n錯過不再，立刻入手 👇\n{link}",
        "🌟 {name} 正式登陸！{description_trunc}\n價格：{price} ETH\n{link}",
    ],
    "discord": [
        "**🎉 新 NFT 上架通知**\n**{name}**\n> {description_trunc}\n💰 價格：{price} ETH\n🔗 {link}",
        "**🚀 限量發售** — **{name}**\n{description_trunc}\n立即查看：{link}",
    ],
    "opensea_ads": [
        "{name} — {description_trunc}\nPrice: {price} ETH | Royalty: {royalty}%\nView on OpenSea: {link}",
    ],
    "nft_calendar": [
        "Event: {name} NFT Drop\nDescription: {description_trunc}\nPrice: {price} ETH | Supply: {supply}\nDate: {date}",
    ],
    "rarity_sniper": [
        "{name} | {collection} | {price} ETH | Supply: {supply}",
    ],
}


def _truncate(text: str, max_len: int = 80) -> str:
    """截斷文字並附加省略符號"""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


class NFTPlatformManagerOrgan(BrainComponent):
    """NFT 鑄造平臺管理器官 — 掌控鑄造排程、定價策略、廣告投放與交易結算的神經中樞。

    內部資料結構：
        self._nfts           — token_id → NFT 完整記錄
        self._collections    — collection_id → 集合元資料
        self._scheduled      — schedule_id → 排程上架記錄
        self._sales_history  — 銷售歷史列表 [{sale_id, nft_id, buyer, price, ...}]
        self._price_history  — token_id → [{price, timestamp}, ...]
        self._ad_campaigns   — ad_id → 廣告活動記錄

    所有 ID 均透過 SHA-256 確定性雜湊生成，確保可重現性與唯一性。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._nfts: Dict[str, dict] = {}
        self._collections: Dict[str, dict] = {}
        self._scheduled: Dict[str, dict] = {}
        self._sales_history: List[dict] = []
        self._price_history: Dict[str, List[dict]] = {}
        self._ad_campaigns: Dict[str, dict] = {}
        self._alive: bool = True
        self._platform_name: str = (
            dna.get("platform_name", "未命名 NFT 平臺") if dna else "未命名 NFT 平臺"
        )

    # ------------------------------------------------------------------
    # 內部輔助方法 — 確定性 ID 生成與元資料構建
    # ------------------------------------------------------------------

    def _gen_token_id(self, name: str, description: str, created_at: str) -> str:
        """使用 SHA-256 產生確定性 token_id"""
        seed = f"{name}|{description}|{created_at}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    def _gen_collection_id(self, name: str, symbol: str) -> str:
        """使用 SHA-256 產生確定性 collection_id"""
        seed = f"collection|{name}|{symbol}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def _gen_schedule_id(self, nft_id: str, listing_date: str) -> str:
        """使用 SHA-256 產生確定性排程 ID"""
        seed = f"schedule|{nft_id}|{listing_date}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    def _gen_sale_id(self, nft_id: str, buyer_address: str) -> str:
        """使用 SHA-256 產生確定性銷售記錄 ID"""
        seed = f"sale|{nft_id}|{buyer_address}|{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def _gen_ad_id(self, nft_id: str) -> str:
        """使用 SHA-256 產生確定性廣告活動 ID"""
        seed = f"ad|{nft_id}|{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    def _build_opensea_metadata(self, nft: dict) -> dict:
        """構建符合 OpenSea Metadata Standard 的 NFT 元資料 JSON"""
        collection_info = self._collections.get(nft.get("collection_id", ""), {})
        return {
            "name": nft.get("name", ""),
            "description": nft.get("description", ""),
            "image": nft.get("image_url", ""),
            "external_url": nft.get("external_url", ""),
            "attributes": nft.get("attributes", []),
            "collection": {
                "name": collection_info.get("name", nft.get("collection_name", "")),
                "family": collection_info.get("symbol", ""),
            },
            "seller_fee_basis_points": int(nft.get("royalty_percent", 0) * 100),
            "token_id": nft.get("token_id", ""),
            "supply": nft.get("supply", 1),
        }

    def _format_currency(self, value_eth: float) -> str:
        """格式化 ETH 數值顯示"""
        return f"{value_eth:,.4f}"

    def _get_nft_or_error(self, nft_id: str) -> dict:
        """取得 NFT 記錄，若不存在則回傳錯誤訊息"""
        nft = self._nfts.get(nft_id)
        if nft is None:
            raise ValueError(f"找不到 NFT，token_id: {nft_id}")
        return nft

    # ------------------------------------------------------------------
    # 工具方法 — 對外暴露給 AI Agent 呼叫
    # ------------------------------------------------------------------

    @tool(name="create_nft", description="鑄造全新 NFT，產生 OpenSea 標準元資料並寫入平臺區塊")
    def create_nft(
        self,
        name: str,
        description: str,
        image_url: str,
        attributes: Optional[List[dict]] = None,
        collection: str = "",
        royalty_percent: float = 5.0,
        supply: int = 1,
    ) -> str:
        """鑄造全新 NFT

        於平臺上創建一個帶有完整元資料的 NFT 代幣，以 SHA-256 生成確定性
        token_id，並依 OpenSea Metadata Standard 格式儲存於內部神經記憶體。

        參數：
            name: NFT 名稱（不可為空）
            description: NFT 描述文字
            image_url: NFT 圖片或媒體資源的 URL
            attributes: 屬性列表，格式 [{"trait_type": "顏色", "value": "霓虹紫"}, ...]
            collection: 歸屬的集合名稱（可選，空白表示獨立 NFT）
            royalty_percent: 版稅百分比，範圍 0–100，預設 5.0%
            supply: 發行總量，預設 1
        """
        if not name or not name.strip():
            return json.dumps({"error": "NFT 名稱不可為空"}, ensure_ascii=False, indent=2)

        if royalty_percent < 0 or royalty_percent > 100:
            return json.dumps(
                {"error": f"版稅百分比必須在 0–100 之間，收到: {royalty_percent}"},
                ensure_ascii=False, indent=2,
            )

        if supply < 1:
            return json.dumps(
                {"error": f"發行量必須大於零，收到: {supply}"},
                ensure_ascii=False, indent=2,
            )

        attrs = attributes or []
        clean_name = name.strip()
        clean_desc = description.strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        token_id = self._gen_token_id(clean_name, clean_desc, now_iso)

        collection_id = ""
        if collection.strip():
            for cid, col in self._collections.items():
                if col.get("name", "").lower() == collection.strip().lower():
                    collection_id = cid
                    break

        nft_record: dict = {
            "token_id": token_id,
            "name": clean_name,
            "description": clean_desc,
            "image_url": image_url.strip(),
            "external_url": "",
            "attributes": attrs,
            "collection_name": collection.strip(),
            "collection_id": collection_id,
            "royalty_percent": royalty_percent,
            "supply": supply,
            "status": "draft",
            "current_price_eth": 0.0,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._nfts[token_id] = nft_record

        metadata = self._build_opensea_metadata(nft_record)
        return json.dumps(
            {
                "status": "success",
                "token_id": token_id,
                "message": f"✅ NFT「{clean_name}」已成功鑄造",
                "metadata": metadata,
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="schedule_listing", description="排程 NFT 未來上架時間，寫入排程佇列並自動計算結束時間")
    def schedule_listing(self, nft_id: str, listing_date: str, duration_days: int = 7) -> str:
        """排程 NFT 未來上架

        將指定 NFT 排入上架佇列，設定開始日期與持續天數，系統將自動計算
        上架結束時間。排程狀態分為 scheduled（待上架）、listed（已上架）、
        ended（已結束）。

        參數：
            nft_id: NFT 的 token_id
            listing_date: 上架日期，ISO 8601 格式（如 "2026-06-01T12:00:00+00:00"）
            duration_days: 上架持續天數，預設 7 天
        """
        if nft_id not in self._nfts:
            return json.dumps(
                {"error": f"找不到 NFT，token_id: {nft_id}"}, ensure_ascii=False, indent=2
            )
        if duration_days < 1:
            return json.dumps(
                {"error": f"持續天數必須大於零，收到: {duration_days}"},
                ensure_ascii=False, indent=2,
            )

        try:
            start_dt = datetime.fromisoformat(listing_date)
        except ValueError:
            return json.dumps(
                {"error": f"日期格式無效: {listing_date}，請使用 ISO 8601 格式"},
                ensure_ascii=False, indent=2,
            )

        end_dt = start_dt + timedelta(days=duration_days)
        schedule_id = self._gen_schedule_id(nft_id, listing_date)

        now_utc = datetime.now(timezone.utc)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        if start_dt > now_utc:
            listing_status = "scheduled"
        elif now_utc <= end_dt:
            listing_status = "listed"
        else:
            listing_status = "ended"

        schedule_record: dict = {
            "schedule_id": schedule_id,
            "nft_id": nft_id,
            "nft_name": self._nfts[nft_id]["name"],
            "listing_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat(),
            "duration_days": duration_days,
            "status": listing_status,
            "created_at": now_utc.isoformat(),
        }
        self._scheduled[schedule_id] = schedule_record

        if listing_status == "listed":
            self._nfts[nft_id]["status"] = "listed"
            self._nfts[nft_id]["updated_at"] = now_utc.isoformat()
        elif listing_status == "scheduled":
            self._nfts[nft_id]["status"] = "scheduled"
            self._nfts[nft_id]["updated_at"] = now_utc.isoformat()

        return json.dumps(
            {
                "status": "success",
                "schedule_id": schedule_id,
                "nft_id": nft_id,
                "nft_name": self._nfts[nft_id]["name"],
                "listing_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "listing_status": listing_status,
                "message": f"✅ NFT「{self._nfts[nft_id]['name']}」已排程上架，狀態: {listing_status}",
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="update_price", description="更新 NFT 上架價格並寫入價格歷史軌跡")
    def update_price(self, nft_id: str, new_price_eth: float) -> str:
        """更新 NFT 上架價格

        變更指定 NFT 的掛單價格，並將變更記錄寫入價格歷史，供後續分析
        定價策略與市場波動參考。

        參數：
            nft_id: NFT 的 token_id
            new_price_eth: 新價格（ETH）
        """
        try:
            nft = self._get_nft_or_error(nft_id)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

        if new_price_eth < 0:
            return json.dumps(
                {"error": f"價格不可為負數，收到: {new_price_eth}"},
                ensure_ascii=False, indent=2,
            )

        old_price = nft.get("current_price_eth", 0.0)
        now_iso = datetime.now(timezone.utc).isoformat()

        nft["current_price_eth"] = new_price_eth
        nft["updated_at"] = now_iso

        if nft_id not in self._price_history:
            self._price_history[nft_id] = []

        self._price_history[nft_id].append({
            "old_price_eth": old_price,
            "new_price_eth": new_price_eth,
            "change_pct": round(((new_price_eth - old_price) / old_price * 100), 2) if old_price > 0 else 100.0,
            "timestamp": now_iso,
        })

        direction = "🔺 調漲" if new_price_eth > old_price else ("🔻 調降" if new_price_eth < old_price else "➖ 持平")
        return json.dumps(
            {
                "status": "success",
                "nft_id": nft_id,
                "nft_name": nft["name"],
                "old_price_eth": old_price,
                "new_price_eth": new_price_eth,
                "direction": direction,
                "price_history_count": len(self._price_history[nft_id]),
                "message": f"✅ NFT「{nft['name']}」價格已更新: {self._format_currency(old_price)} → {self._format_currency(new_price_eth)} ETH",
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="create_collection", description="創建新的 NFT 集合，設定集合名稱、符號、分類與版稅")
    def create_collection(
        self,
        name: str,
        symbol: str,
        description: str,
        category: str = "art",
        royalty_percent: float = 5.0,
    ) -> str:
        """創建 NFT 集合

        於平臺上建立新的 NFT 集合容器，用於歸類與管理同系列 NFT。
        集合具備名稱、代幣符號、分類標籤及統一的版稅設定。

        參數：
            name: 集合名稱（不可為空）
            symbol: 集合代幣符號（如 "BAYC"、"AZUKI"）
            description: 集合描述
            category: 集合分類（art / music / pfp / game / metaverse / photography / virtual_world / membership / utility）
            royalty_percent: 版稅百分比，範圍 0–100，預設 5.0%
        """
        if not name or not name.strip():
            return json.dumps({"error": "集合名稱不可為空"}, ensure_ascii=False, indent=2)
        if not symbol or not symbol.strip():
            return json.dumps({"error": "集合符號不可為空"}, ensure_ascii=False, indent=2)
        if royalty_percent < 0 or royalty_percent > 100:
            return json.dumps(
                {"error": f"版稅百分比必須在 0–100 之間，收到: {royalty_percent}"},
                ensure_ascii=False, indent=2,
            )

        category_lower = category.strip().lower()
        if category_lower not in COLLECTION_CATEGORIES:
            return json.dumps(
                {"error": f"不支援的分類: {category}，可用分類: {', '.join(COLLECTION_CATEGORIES)}"},
                ensure_ascii=False, indent=2,
            )

        clean_name = name.strip()
        clean_symbol = symbol.strip().upper()
        collection_id = self._gen_collection_id(clean_name, clean_symbol)
        now_iso = datetime.now(timezone.utc).isoformat()

        collection_record: dict = {
            "collection_id": collection_id,
            "name": clean_name,
            "symbol": clean_symbol,
            "description": description.strip(),
            "category": category_lower,
            "royalty_percent": royalty_percent,
            "total_nfts": 0,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._collections[collection_id] = collection_record

        return json.dumps(
            {
                "status": "success",
                "collection_id": collection_id,
                "name": clean_name,
                "symbol": clean_symbol,
                "category": category_lower,
                "royalty_percent": royalty_percent,
                "message": f"✅ 集合「{clean_name}」({clean_symbol}) 已成功創建",
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="advertise_nft", description="為 NFT 建立廣告推廣活動，生成多平臺廣告文案變體")
    def advertise_nft(
        self,
        nft_id: str,
        budget_eth: float = 0.1,
        platforms: Optional[List[str]] = None,
        duration_days: int = 7,
    ) -> str:
        """建立 NFT 廣告推廣活動

        針對指定 NFT 建立跨平臺廣告活動，根據不同平臺（Twitter、Discord、
        OpenSea Ads、NFT Calendar、Rarity Sniper）自動生成對應的廣告文案變體，
        並計算預算分配與活動期間。

        參數：
            nft_id: NFT 的 token_id
            budget_eth: 廣告總預算（ETH），預設 0.1
            platforms: 目標平臺列表，預設全部（twitter, discord, opensea_ads, nft_calendar, rarity_sniper）
            duration_days: 廣告持續天數，預設 7 天
        """
        try:
            nft = self._get_nft_or_error(nft_id)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

        if budget_eth <= 0:
            return json.dumps(
                {"error": f"廣告預算必須大於零，收到: {budget_eth}"},
                ensure_ascii=False, indent=2,
            )
        if duration_days < 1:
            return json.dumps(
                {"error": f"廣告持續天數必須大於零，收到: {duration_days}"},
                ensure_ascii=False, indent=2,
            )

        target_platforms = platforms or AD_PLATFORMS
        invalid_platforms = [p for p in target_platforms if p not in AD_PLATFORMS]
        if invalid_platforms:
            return json.dumps(
                {"error": f"不支援的廣告平臺: {', '.join(invalid_platforms)}，可用: {', '.join(AD_PLATFORMS)}"},
                ensure_ascii=False, indent=2,
            )

        ad_id = self._gen_ad_id(nft_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        end_dt = datetime.now(timezone.utc) + timedelta(days=duration_days)
        per_platform_budget = budget_eth / len(target_platforms)
        price_str = self._format_currency(nft.get("current_price_eth", 0.0))
        desc_trunc = _truncate(nft.get("description", ""), 80)
        royalty_str = str(nft.get("royalty_percent", 5.0))
        supply_str = str(nft.get("supply", 1))
        collection_name = nft.get("collection_name", "獨立發行")
        nft_name = nft.get("name", nft_id)

        ad_copies: Dict[str, List[str]] = {}
        for plat in target_platforms:
            templates = _AD_COPY_TEMPLATES.get(plat, [])
            copies: List[str] = []
            for tpl in templates:
                copy_text = tpl.format(
                    name=nft_name,
                    description_trunc=desc_trunc,
                    price=price_str,
                    link=f"https://opensea.io/assets/ethereum/{nft_id}",
                    royalty=royalty_str,
                    supply=supply_str,
                    collection=collection_name,
                    date=now_iso[:10],
                )
                copies.append(copy_text)
            ad_copies[plat] = copies

        campaign_record: dict = {
            "ad_id": ad_id,
            "nft_id": nft_id,
            "nft_name": nft_name,
            "budget_eth": budget_eth,
            "platforms": target_platforms,
            "per_platform_budget_eth": round(per_platform_budget, 6),
            "duration_days": duration_days,
            "start_date": now_iso,
            "end_date": end_dt.isoformat(),
            "ad_copies": ad_copies,
            "status": "active",
            "created_at": now_iso,
        }
        self._ad_campaigns[ad_id] = campaign_record

        return json.dumps(
            {
                "status": "success",
                "ad_id": ad_id,
                "nft_id": nft_id,
                "nft_name": nft_name,
                "total_budget_eth": budget_eth,
                "per_platform_budget_eth": round(per_platform_budget, 6),
                "platforms": target_platforms,
                "duration_days": duration_days,
                "start_date": now_iso,
                "end_date": end_dt.isoformat(),
                "ad_copies": ad_copies,
                "message": f"✅ NFT「{nft_name}」廣告活動已啟動，涵蓋 {len(target_platforms)} 個平臺",
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="sell_nft", description="標記 NFT 為已售出，計算版稅分潤並記錄交易歷史")
    def sell_nft(self, nft_id: str, buyer_address: str, sale_price: float) -> str:
        """完成 NFT 銷售交易

        標記指定 NFT 為已售出狀態，根據買方地址與成交價格計算創作者版稅
        分潤，並將完整交易記錄寫入銷售歷史。

        參數：
            nft_id: NFT 的 token_id
            buyer_address: 買方錢包地址（0x 開頭）
            sale_price: 成交價格（ETH）
        """
        try:
            nft = self._get_nft_or_error(nft_id)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

        if sale_price < 0:
            return json.dumps(
                {"error": f"成交價格不可為負數，收到: {sale_price}"},
                ensure_ascii=False, indent=2,
            )

        royalty_percent = nft.get("royalty_percent", 0.0)
        royalty_amount = round(sale_price * royalty_percent / 100.0, 6)
        seller_revenue = round(sale_price - royalty_amount, 6)

        now_iso = datetime.now(timezone.utc).isoformat()
        sale_id = self._gen_sale_id(nft_id, buyer_address)

        sale_record: dict = {
            "sale_id": sale_id,
            "nft_id": nft_id,
            "nft_name": nft["name"],
            "buyer_address": buyer_address,
            "sale_price_eth": sale_price,
            "royalty_percent": royalty_percent,
            "royalty_amount_eth": royalty_amount,
            "seller_revenue_eth": seller_revenue,
            "sold_at": now_iso,
        }
        self._sales_history.append(sale_record)

        nft["status"] = "sold"
        nft["current_price_eth"] = sale_price
        nft["updated_at"] = now_iso

        if nft_id not in self._price_history:
            self._price_history[nft_id] = []
        self._price_history[nft_id].append({
            "old_price_eth": nft.get("current_price_eth", 0.0),
            "new_price_eth": sale_price,
            "change_pct": 0.0,
            "event": "sold",
            "timestamp": now_iso,
        })

        return json.dumps(
            {
                "status": "success",
                "sale_id": sale_id,
                "nft_id": nft_id,
                "nft_name": nft["name"],
                "buyer_address": buyer_address,
                "sale_price_eth": sale_price,
                "royalty_amount_eth": royalty_amount,
                "seller_revenue_eth": seller_revenue,
                "sold_at": now_iso,
                "message": f"✅ NFT「{nft['name']}」已售出！成交價: {self._format_currency(sale_price)} ETH，版稅: {self._format_currency(royalty_amount)} ETH",
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="get_platform_stats", description="取得 NFT 平臺的整體營運統計數據")
    def get_platform_stats(self) -> str:
        """取得平臺營運統計

        彙整 NFT 平臺的關鍵營運指標，包括總 NFT 數、總集合數、總銷售額、
        總營收、活躍上架數與排程上架數。
        """
        total_nfts = len(self._nfts)
        total_collections = len(self._collections)
        total_sales = len(self._sales_history)

        total_revenue = sum(sale.get("sale_price_eth", 0.0) for sale in self._sales_history)
        total_royalties = sum(sale.get("royalty_amount_eth", 0.0) for sale in self._sales_history)

        active_listings = sum(
            1 for nft in self._nfts.values() if nft.get("status") == "listed"
        )
        scheduled_listings = sum(
            1 for nft in self._nfts.values() if nft.get("status") == "scheduled"
        )
        sold_count = sum(
            1 for nft in self._nfts.values() if nft.get("status") == "sold"
        )
        draft_count = sum(
            1 for nft in self._nfts.values() if nft.get("status") == "draft"
        )

        active_campaigns = sum(
            1 for ad in self._ad_campaigns.values() if ad.get("status") == "active"
        )

        stats: dict = {
            "platform_name": self._platform_name,
            "total_nfts": total_nfts,
            "total_collections": total_collections,
            "total_sales": total_sales,
            "total_revenue_eth": round(total_revenue, 6),
            "total_royalties_eth": round(total_royalties, 6),
            "active_listings": active_listings,
            "scheduled_listings": scheduled_listings,
            "sold_nfts": sold_count,
            "draft_nfts": draft_count,
            "active_ad_campaigns": active_campaigns,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return json.dumps(stats, indent=2, ensure_ascii=False)

    @tool(name="list_nfts", description="依狀態篩選並列出 NFT 清單，顯示名稱、價格與集合資訊")
    def list_nfts(self, status_filter: str = "all") -> str:
        """依狀態列出 NFT 清單

        根據指定狀態篩選平臺上的 NFT，回傳格式化清單，包含名稱、價格、
        集合與建立時間。

        參數：
            status_filter: 狀態篩選條件 — draft / minted / listed / scheduled / sold / all
        """
        status_lower = status_filter.strip().lower()

        if status_lower == "all":
            filtered = list(self._nfts.values())
        elif status_lower in VALID_STATUSES:
            filtered = [nft for nft in self._nfts.values() if nft.get("status") == status_lower]
        else:
            return json.dumps(
                {"error": f"無效的狀態篩選: {status_filter}，可用: {', '.join(VALID_STATUSES)} / all"},
                ensure_ascii=False, indent=2,
            )

        if not filtered:
            return json.dumps(
                {"message": f"📭 無符合狀態「{status_lower}」的 NFT", "count": 0, "nfts": []},
                indent=2, ensure_ascii=False,
            )

        nft_list: List[dict] = []
        for nft in filtered:
            nft_list.append({
                "token_id": nft.get("token_id"),
                "name": nft.get("name"),
                "status": nft.get("status"),
                "price_eth": self._format_currency(nft.get("current_price_eth", 0.0)),
                "collection": nft.get("collection_name") or "獨立發行",
                "supply": nft.get("supply", 1),
                "created_at": nft.get("created_at", ""),
            })

        return json.dumps(
            {
                "status_filter": status_lower,
                "count": len(nft_list),
                "nfts": nft_list,
            },
            indent=2,
            ensure_ascii=False,
        )

    @tool(name="bulk_create_nfts", description="依據範本與變體列表批次鑄造多個 NFT")
    def bulk_create_nfts(self, template: str, variations: List[dict]) -> str:
        """批次鑄造多個 NFT

        以一個基礎範本搭配多個變體（如不同顏色、屬性組合）批次產生 NFT，
        每個變體將覆蓋範本中的對應欄位，並獨立生成 token_id。

        參數：
            template: JSON 字串範本，包含 name, description, image_url, attributes, collection, royalty_percent, supply
            variations: 變體列表，每個變體為 dict，key 覆蓋 template 中對應欄位
                       例如: [{"name": "變體 A", "attributes": [{"trait_type": "顏色", "value": "紅"}]}]
        """
        try:
            base = json.loads(template) if isinstance(template, str) else template
        except json.JSONDecodeError:
            return json.dumps(
                {"error": "範本 JSON 格式無效，請提供合法 JSON 字串"},
                ensure_ascii=False, indent=2,
            )

        if not variations:
            return json.dumps(
                {"error": "變體列表不可為空"}, ensure_ascii=False, indent=2,
            )

        base_name = base.get("name", "未命名 NFT")
        base_desc = base.get("description", "")
        base_image = base.get("image_url", "")
        base_attrs = base.get("attributes", [])
        base_collection = base.get("collection", "")
        base_royalty = base.get("royalty_percent", 5.0)
        base_supply = base.get("supply", 1)

        created_tokens: List[dict] = []
        errors: List[dict] = []

        for idx, variation in enumerate(variations):
            var_name = variation.get("name", f"{base_name} #{idx + 1}")
            var_desc = variation.get("description", base_desc)
            var_image = variation.get("image_url", base_image)
            var_attrs = variation.get("attributes", base_attrs)
            var_collection = variation.get("collection", base_collection)
            var_royalty = variation.get("royalty_percent", base_royalty)
            var_supply = variation.get("supply", base_supply)

            if not isinstance(var_attrs, list):
                errors.append({"index": idx, "error": f"attributes 必須為列表"})
                continue
            if var_royalty < 0 or var_royalty > 100:
                errors.append({"index": idx, "error": f"版稅百分比無效: {var_royalty}"})
                continue

            now_iso = datetime.now(timezone.utc).isoformat()
            token_id = self._gen_token_id(var_name, var_desc, now_iso)

            collection_id = ""
            if var_collection.strip():
                for cid, col in self._collections.items():
                    if col.get("name", "").lower() == var_collection.strip().lower():
                        collection_id = cid
                        break

            nft_record: dict = {
                "token_id": token_id,
                "name": var_name.strip(),
                "description": var_desc.strip(),
                "image_url": var_image.strip(),
                "external_url": "",
                "attributes": var_attrs,
                "collection_name": var_collection.strip(),
                "collection_id": collection_id,
                "royalty_percent": var_royalty,
                "supply": var_supply,
                "status": "draft",
                "current_price_eth": 0.0,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            self._nfts[token_id] = nft_record
            created_tokens.append({
                "index": idx,
                "token_id": token_id,
                "name": var_name.strip(),
            })

        return json.dumps(
            {
                "status": "success",
                "template_name": base_name,
                "total_variations": len(variations),
                "created_count": len(created_tokens),
                "error_count": len(errors),
                "created_tokens": created_tokens,
                "errors": errors,
                "message": f"✅ 批次鑄造完成: {len(created_tokens)}/{len(variations)} 個 NFT 已成功創建",
            },
            indent=2,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------
    # 生命週期與狀態回報
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """回報器官當前運行狀態

        回傳 NFT 平臺管理器官的即時狀態快照，包含總鑄造數、總集合數、
        總銷售額、總營收及活躍上架數量。
        """
        total_nfts = len(self._nfts)
        total_collections = len(self._collections)
        total_sales = len(self._sales_history)
        total_revenue = round(
            sum(sale.get("sale_price_eth", 0.0) for sale in self._sales_history), 6
        )
        active_listings = sum(
            1 for nft in self._nfts.values() if nft.get("status") == "listed"
        )

        return {
            "name": self.__class__.__name__,
            "alive": self._alive,
            "total_nfts": total_nfts,
            "total_collections": total_collections,
            "total_sales": total_sales,
            "total_revenue_eth": total_revenue,
            "active_listings": active_listings,
        }

    def on_startup(self) -> None:
        """器官啟動回呼 — 初始化內部神經矩陣"""
        self._alive = True

    def on_shutdown(self) -> None:
        """器官關閉回呼 — 凍結神經矩陣並儲存狀態快照"""
        self._alive = False
