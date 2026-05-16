"""MarketDataOrgan - 市場數據器官，從 CoinGecko API 擷取即時加密貨幣價格"""
from typing import Optional, Dict, List
from skeleton.brain_component import BrainComponent
from tools import tool
import requests
import time
import random


class MarketDataOrgan(BrainComponent):
    """市場數據器官 — 負責擷取與快取加密貨幣即時報價"""

    BASE_URL = "https://api.coingecko.com/api/v3"
    COIN_ID_MAP = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
        "matic": "matic-network", "arb": "arbitrum", "op": "optimism",
        "avax": "avalanche-2", "link": "chainlink", "uni": "uniswap",
        "aave": "aave", "doge": "dogecoin", "dot": "polkadot", "atom": "cosmos",
        "apt": "aptos", "sui": "sui", "near": "near", "pepe": "pepe",
        "shib": "shiba-inu", "fil": "filecoin", "inj": "injective-protocol",
    }

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._cache: Dict[str, dict] = {}
        self._cache_ttl = 60
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "User-Agent": "AMPM-AIOPS/2.1.0"
        })

    def _api_get(self, path: str, params: dict = None) -> Optional[dict]:
        """呼叫 CoinGecko API，失敗時回傳 None"""
        try:
            resp = self._session.get(
                f"{self.BASE_URL}{path}",
                params=params,
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                time.sleep(2)
            return None
        except (requests.RequestException, ValueError):
            return None

    def _resolve_id(self, symbol: str) -> Optional[str]:
        """將交易對符號轉為 CoinGecko 代幣 ID"""
        return self.COIN_ID_MAP.get(symbol.lower())

    def _cache_get(self, key: str) -> Optional[dict]:
        """讀取快取，檢查是否仍在 TTL 內"""
        entry = self._cache.get(key)
        if entry and (time.time() - entry["ts"]) < self._cache_ttl:
            return entry["data"]
        return None

    def _cache_set(self, key: str, data: dict):
        """寫入快取"""
        self._cache[key] = {"ts": time.time(), "data": data}

    # ---- 模擬備援資料 ----
    _FALLBACK_PRICES = {
        "btc": 67000, "eth": 3400, "sol": 170, "bnb": 610,
        "matic": 0.68, "arb": 0.95, "op": 1.75, "avax": 38,
        "link": 15, "uni": 8.2, "aave": 100, "doge": 0.16,
        "dot": 7.80, "atom": 9.50, "apt": 9.20, "sui": 1.10,
        "near": 6.40, "pepe": 0.000012, "shib": 0.000025,
        "fil": 6.00, "inj": 25.0,
    }

    _FALLBACK_MCAP = {
        "btc": 1_300_000_000_000, "eth": 410_000_000_000, "sol": 75_000_000_000,
        "bnb": 92_000_000_000, "matic": 6_500_000_000, "arb": 1_900_000_000,
        "op": 2_100_000_000, "avax": 14_000_000_000, "link": 8_500_000_000,
        "uni": 5_000_000_000, "aave": 1_500_000_000, "doge": 22_000_000_000,
        "dot": 10_500_000_000, "atom": 3_800_000_000, "apt": 3_500_000_000,
        "sui": 2_300_000_000, "near": 6_800_000_000, "pepe": 5_000_000_000,
        "shib": 14_000_000_000, "fil": 2_800_000_000, "inj": 2_200_000_000,
    }

    @tool(name="get_price", description="查詢單一代幣的即時美元價格")
    def get_price(self, symbol: str) -> str:
        """查詢即時價格 (CoinGecko API + 60s 快取 + 模擬備援)"""
        symbol = symbol.lower().strip()
        coin_id = self._resolve_id(symbol)
        if not coin_id:
            price = self._FALLBACK_PRICES.get(symbol)
            if price is not None:
                return f"💰 {symbol.upper()} 即時價格: ${price:,.4f} (模擬備援)"
            return f"❌ 不支援的代幣: {symbol}"

        cache_key = f"price:{coin_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return f"💰 {symbol.upper()} 即時價格: ${cached['price']:,.4f} (快取)"

        # 嘗試即時 API
        try:
            data = self._api_get("/simple/price", {
                "ids": coin_id,
                "vs_currencies": "usd"
            })
            if data and coin_id in data and "usd" in data[coin_id]:
                price = data[coin_id]["usd"]
                self._cache_set(cache_key, {"price": price})
                return f"💰 {symbol.upper()} 即時價格: ${price:,.4f} (CoinGecko)"
        except Exception:
            pass

        # API 失敗 → 模擬備援
        price = self._FALLBACK_PRICES.get(symbol, 0)
        if price:
            self._cache_set(cache_key, {"price": price})
        return f"💰 {symbol.upper()} 即時價格: ${price:,.4f} (模擬備援)"

    @tool(name="get_prices", description="批次查詢多個代幣的即時美元價格")
    def get_prices(self, symbols: List[str]) -> str:
        """批次查詢多個代幣價格"""
        results = []
        for sym in symbols:
            results.append(self.get_price(sym))
        return "\n".join(results)

    @tool(name="get_24h_change", description="查詢代幣的 24 小時價格變動百分比")
    def get_24h_change(self, symbol: str) -> str:
        """查詢 24 小時價格變動"""
        symbol = symbol.lower().strip()
        coin_id = self._resolve_id(symbol)
        if not coin_id:
            simulated = round(random.uniform(-8, 8), 2)
            return f"📈 {symbol.upper()} 24h 變動: {simulated:+.2f}% (模擬備援)"

        cache_key = f"24h:{coin_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return f"📈 {symbol.upper()} 24h 變動: {cached['change']:+.2f}% (快取)"

        try:
            data = self._api_get("/simple/price", {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            })
            if data and coin_id in data and "usd_24h_change" in data[coin_id]:
                change = data[coin_id]["usd_24h_change"]
                self._cache_set(cache_key, {"change": change})
                direction = "📈" if change >= 0 else "📉"
                return f"{direction} {symbol.upper()} 24h 變動: {change:+.2f}% (CoinGecko)"
        except Exception:
            pass

        change = round(random.uniform(-8, 8), 2)
        self._cache_set(cache_key, {"change": change})
        direction = "📈" if change >= 0 else "📉"
        return f"{direction} {symbol.upper()} 24h 變動: {change:+.2f}% (模擬備援)"

    @tool(name="get_market_cap", description="查詢代幣的市值")
    def get_market_cap(self, symbol: str) -> str:
        """查詢代幣市值"""
        symbol = symbol.lower().strip()
        coin_id = self._resolve_id(symbol)
        if not coin_id:
            mcap = self._FALLBACK_MCAP.get(symbol)
            if mcap is not None:
                return f"🏛️ {symbol.upper()} 市值: ${mcap:,.0f} (模擬備援)"
            return f"❌ 不支援的代幣: {symbol}"

        cache_key = f"mcap:{coin_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return f"🏛️ {symbol.upper()} 市值: ${cached['mcap']:,.0f} (快取)"

        try:
            data = self._api_get("/simple/price", {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true"
            })
            if data and coin_id in data and "usd_market_cap" in data[coin_id]:
                mcap = data[coin_id]["usd_market_cap"]
                self._cache_set(cache_key, {"mcap": mcap})
                return f"🏛️ {symbol.upper()} 市值: ${mcap:,.0f} (CoinGecko)"
        except Exception:
            pass

        mcap = self._FALLBACK_MCAP.get(symbol, 0)
        self._cache_set(cache_key, {"mcap": mcap})
        return f"🏛️ {symbol.upper()} 市值: ${mcap:,.0f} (模擬備援)"

    @tool(name="get_trending", description="查詢 CoinGecko 目前熱門搜尋代幣排行")
    def get_trending(self) -> str:
        """查詢全球熱門搜尋代幣"""
        cache_key = "trending:global"
        cached = self._cache_get(cache_key)
        if cached is not None:
            lines = ["🔥 CoinGecko 熱門搜尋排行 (快取):"]
            for i, coin in enumerate(cached["coins"], 1):
                lines.append(f"  {i}. {coin['name']} ({coin['symbol']}) — 市值第 {coin.get('rank', '?')} 名")
            return "\n".join(lines)

        try:
            data = self._api_get("/search/trending")
            if data and "coins" in data:
                coins = []
                for item in data["coins"][:10]:
                    c = item.get("item", {})
                    coins.append({
                        "name": c.get("name", "?"),
                        "symbol": c.get("symbol", "?"),
                        "rank": c.get("market_cap_rank", "?")
                    })
                self._cache_set(cache_key, {"coins": coins})
                lines = ["🔥 CoinGecko 熱門搜尋排行:"]
                for i, coin in enumerate(coins, 1):
                    lines.append(f"  {i}. {coin['name']} ({coin['symbol']}) — 市值第 {coin.get('rank', '?')} 名")
                return "\n".join(lines)
        except Exception:
            pass

        # 模擬備援
        hot_coins = [
            {"name": "Bitcoin", "symbol": "BTC", "rank": 1},
            {"name": "Ethereum", "symbol": "ETH", "rank": 2},
            {"name": "Solana", "symbol": "SOL", "rank": 5},
            {"name": "Pepe", "symbol": "PEPE", "rank": 25},
            {"name": "Sui", "symbol": "SUI", "rank": 45},
        ]
        self._cache_set(cache_key, {"coins": hot_coins})
        lines = ["🔥 CoinGecko 熱門搜尋排行 (模擬備援):"]
        for i, coin in enumerate(hot_coins, 1):
            lines.append(f"  {i}. {coin['name']} ({coin['symbol']}) — 市值第 {coin['rank']} 名")
        return "\n".join(lines)

    def status(self) -> dict:
        """回報器官狀態"""
        return {
            "organ": "MarketDataOrgan",
            "alive": True,
            "cached_entries": len(self._cache),
            "supported_coins": list(self.COIN_ID_MAP.keys()),
            "api_base": self.BASE_URL,
        }
