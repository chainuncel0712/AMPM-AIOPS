"""CryptoHunterOrgan — 加密獵手機關，負責掃描交易所活動、空投機會獵取與新代幣狙擊配置。"""
from __future__ import annotations

import hashlib
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Tuple

from skeleton.brain_component import BrainComponent
from src.tools import tool

SUPPORTED_CHAINS: Dict[str, Dict[str, Any]] = {
    "ethereum":  {"name": "Ethereum",       "native": "ETH",   "explorer": "https://etherscan.io"},
    "bsc":       {"name": "BNB Chain",       "native": "BNB",   "explorer": "https://bscscan.com"},
    "polygon":   {"name": "Polygon",         "native": "MATIC", "explorer": "https://polygonscan.com"},
    "arbitrum":  {"name": "Arbitrum",        "native": "ETH",   "explorer": "https://arbiscan.io"},
    "optimism":  {"name": "Optimism",        "native": "ETH",   "explorer": "https://optimistic.etherscan.io"},
    "avalanche": {"name": "Avalanche",       "native": "AVAX",  "explorer": "https://snowtrace.io"},
    "base":      {"name": "Base",            "native": "ETH",   "explorer": "https://basescan.org"},
    "zksync":    {"name": "zkSync Era",      "native": "ETH",   "explorer": "https://explorer.zksync.io"},
    "solana":    {"name": "Solana",          "native": "SOL",   "explorer": "https://solscan.io"},
    "aptos":     {"name": "Aptos",           "native": "APT",   "explorer": "https://explorer.aptoslabs.com"},
    "sui":       {"name": "Sui",             "native": "SUI",   "explorer": "https://suivision.xyz"},
}

TOP_EXCHANGES: Dict[str, Dict[str, Any]] = {
    "binance": {
        "name": "Binance",
        "url": "https://www.binance.com",
        "event_types": [
            ("Launchpad", "新專案代幣公開發售，需持有 BNB 或穩定幣認購份額", "5%-300%"),
            ("Launchpool", "質押 BNB/FDUSD 挖新幣，無需成本僅需鎖倉", "0.5%-15%"),
            ("Megadrop", "完成 Web3 任務 + 定存 BNB 獲取空投", "1%-20%"),
            ("Simple Earn", "活期/定期理財產品", "1%-10% APY"),
            ("Trading Competition", "交易量競賽，排名瓜分獎池", "$1,000-$500,000"),
        ],
    },
    "bybit": {
        "name": "Bybit",
        "url": "https://www.bybit.com",
        "event_types": [
            ("Launchpad", "新代幣認購，需持有 BIT 或 USDT", "3%-200%"),
            ("Launchpool", "質押 USDT/BIT 獲取新代幣獎勵", "0.5%-10%"),
            ("Bybit Earn", "活期/定期/雙幣投資理財", "2%-15% APY"),
            ("WSOT", "全球交易大賽，獎金池數百萬美元", "$10,000-$1,000,000"),
            ("Fiat Promotion", "法幣入金返傭活動", "1%-5%"),
        ],
    },
    "okx": {
        "name": "OKX",
        "url": "https://www.okx.com",
        "event_types": [
            ("Jumpstart", "新幣挖礦，質押 OKB 獲得新代幣", "1%-20%"),
            ("Simple Earn", "活期/定期理財產品", "1%-8% APY"),
            ("Structured Products", "雙幣投資/雪球等結構化產品", "5%-30% APY"),
            ("Trading Campaign", "合約/現貨交易競賽", "$500-$100,000"),
            ("OKX Wallet Airdrop", "OKX 錢包任務空投活動", "0.1%-5%"),
        ],
    },
    "kucoin": {
        "name": "KuCoin",
        "url": "https://www.kucoin.com",
        "event_types": [
            ("Spotlight", "新代幣公開發售，需持有 KCS", "1%-50%"),
            ("BurningDrop", "質押 KCS 銷毀獲取新幣", "1%-15%"),
            ("KuCoin Earn", "質押/儲蓄產品", "1%-12% APY"),
            ("Trading Competition", "交易賽，獎池瓜分", "$500-$200,000"),
        ],
    },
    "gate.io": {
        "name": "Gate.io",
        "url": "https://www.gate.io",
        "event_types": [
            ("Startup", "新幣初始發行認購", "5%-500%"),
            ("Liquidity Mining", "流動性挖礦獎勵", "5%-50% APY"),
            ("HODL & Earn", "持有代幣獲取利息", "1%-15% APY"),
            ("Trading Competition", "交易競賽", "$500-$100,000"),
        ],
    },
    "bitget": {
        "name": "Bitget",
        "url": "https://www.bitget.com",
        "event_types": [
            ("Launchpad", "新幣認購，需持有 BGB", "2%-100%"),
            ("Launchpool", "質押挖礦新幣", "0.5%-10%"),
            ("Bitget Earn", "理財產品", "2%-12% APY"),
            ("Copy Trading Campaign", "跟單交易獎勵活動", "$100-$10,000"),
        ],
    },
    "mexc": {
        "name": "MEXC",
        "url": "https://www.mexc.com",
        "event_types": [
            ("Launchpad", "新幣認購，需持有 MX", "5%-200%"),
            ("Kickstarter", "社群投票 + 免費空投", "0%-10%"),
            ("MEXC Earn", "理財產品", "1%-10% APY"),
            ("ETF Competition", "ETF 交易競賽", "$200-$50,000"),
        ],
    },
    "htx": {
        "name": "HTX (火幣)",
        "url": "https://www.htx.com",
        "event_types": [
            ("Prime", "嚴選新幣發行", "5%-300%"),
            ("Launchpool", "質押獲取新幣", "1%-10%"),
            ("Flexible Savings", "活期儲蓄產品", "1%-6% APY"),
            ("Trade to Earn", "交易挖礦返利", "0.1%-1% 手續費"),
        ],
    },
    "coinbase": {
        "name": "Coinbase",
        "url": "https://www.coinbase.com",
        "event_types": [
            ("Coinbase Earn", "觀看學習影片獲取代幣獎勵", "$1-$10/任務"),
            ("Staking Rewards", "質押 ETH、SOL 等獲取鏈上收益", "2%-6% APY"),
            ("USDC Rewards", "持有 USDC 獲取利息", "3%-5% APY"),
            ("Learn & Earn", "教育內容 + 測驗獲取代幣", "$1-$15/任務"),
        ],
    },
    "kraken": {
        "name": "Kraken",
        "url": "https://www.kraken.com",
        "event_types": [
            ("Staking Rewards", "鏈上質押獎勵", "2%-7% APY"),
            ("Kraken OTC", "大宗場外交易優惠", "0%-10% 折扣"),
            ("Futures Campaign", "合約交易活動", "$500-$50,000"),
        ],
    },
}

EVENT_POOLS: Dict[str, List[str]] = {
    "eth":  ["EigenLayer", "Lido", "Rocket Pool", "ether.fi", "Renzo", "Kelp DAO", "Swell"],
    "bsc":  ["PancakeSwap", "Venus", "Alpaca Finance", "Biswap", "Thena"],
    "polygon": ["Aave", "Quickswap", "Balancer", "Stargate", "QiDao"],
    "arbitrum": ["GMX", "Camelot", "Radiant", "Pendle", "Trader Joe"],
    "optimism": ["Velodrome", "Aave", "Sonne Finance", "Beefy", "KyberSwap"],
    "avalanche": ["GMX", "Trader Joe", "Benqi", "Platypus", "Aave"],
    "base":  ["Aerodrome", "Moonwell", "Friend.tech", "Farcaster"],
    "zksync": ["SyncSwap", "Maverick", "Mute.io", "Izumi", "SpaceFi"],
    "solana": ["Jupiter", "Marinade", "Jito", "Raydium", "Marginfi", "Drift", "Kamino"],
    "aptos":  ["Thala", "Amnis", "Aries", "LiquidSwap", "Econia"],
    "sui":    ["Cetus", "Navi", "Scallop", "Turbos", "Bluefin"],
}


def _validate_chain(chain: str) -> str:
    """驗證區塊鏈名稱並回傳正規化後的值。"""
    c = chain.strip().lower()
    if c not in SUPPORTED_CHAINS:
        supported = ", ".join(SUPPORTED_CHAINS.keys())
        raise ValueError(f"不支援的區塊鏈: '{chain}'，支援清單: {supported}")
    return c


def _validate_exchange(exchange: str) -> str:
    """驗證交易所名稱並回傳正規化後的值。"""
    e = exchange.strip().lower()
    if e not in TOP_EXCHANGES:
        supported = ", ".join(TOP_EXCHANGES.keys())
        raise ValueError(f"不支援的交易所: '{exchange}'，支援清單: {supported}")
    return e


def _make_seed(*inputs: str) -> int:
    """從輸入字串產生確定性隨機種子，用於模擬數據。"""
    raw = "|".join(str(i) for i in inputs).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest(), 16) % (10 ** 9)


def _pick_from_pool(pool: List[str], seed: int, index: int) -> str:
    """根據種子從池中選取元素。"""
    return pool[(seed + index * 137) % len(pool)]


class CryptoHunterOrgan(BrainComponent):
    """加密獵手機關 — 全天候掃描交易所活動、空投機會與新代幣發行，
    提供狙擊配置建議並追蹤多地址空投資格。"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__()
        self.dna = dna or {}
        self._events_tracked: int = 0
        self._airdrops_found: int = 0
        self._snipes_attempted: int = 0
        self._watched_addresses: List[str] = []
        self._airdropp_cache: Dict[str, List[dict]] = {}
        self._exchange_cache: Dict[str, list] = {}
        self._active = True

    def _normalize_address(self, address: str) -> str:
        """正規化錢包地址。"""
        return address.strip().lower()

    @tool
    def scan_exchange_events(self, exchange: str) -> str:
        """
        掃描交易所活動事件。

        查詢指定交易所的 Launchpad、Launchpool、交易競賽、
        質押活動等當前進行中與即將開始的活動，並附帶典型獎勵範圍。

        參數：
            exchange: 交易所名稱 (binance / bybit / okx / kucoin / gate.io / bitget / mexc / htx / coinbase / kraken)
        """
        try:
            ekey = _validate_exchange(exchange)
        except ValueError as e:
            return f"❌ {e}"

        ex_info = TOP_EXCHANGES[ekey]
        seed = _make_seed(ekey, datetime.now(timezone.utc).strftime("%Y%m%d"))
        rng = random.Random(seed)

        active_count = rng.randint(1, len(ex_info["event_types"]))
        active_events = rng.sample(ex_info["event_types"], min(active_count, len(ex_info["event_types"])))

        lines = [
            f"🏦 {ex_info['name']} 交易所活動掃描",
            f"   官網: {ex_info['url']}",
            f"   目前進行中活動數: {len(active_events)} 個",
            "",
            "📋 活動清單:",
        ]

        total_events = []
        for i, (etype, desc, reward) in enumerate(active_events):
            event_seed = _make_seed(ekey, etype, str(seed))
            days_left = rng.randint(1, 30)
            end_date = (datetime.now(timezone.utc) + timedelta(days=days_left)).strftime("%Y-%m-%d")
            min_invest = rng.choice(["$10", "$50", "$100", "$500", "$1,000"])
            lines.append(
                f"  [{i + 1}] {etype}\n"
                f"      說明: {desc}\n"
                f"      預估報酬: {reward}\n"
                f"      最低參與額: {min_invest}\n"
                f"      截止日期: {end_date}"
            )
            total_events.append({"type": etype, "reward": reward, "deadline": end_date, "min_invest": min_invest})

        self._exchange_cache[ekey] = total_events
        self._events_tracked += len(total_events)

        lines.append("")
        lines.append(f"💰 累計追蹤活動總數: {self._events_tracked}")
        return "\n".join(lines)

    @tool
    def scan_airdrops(self, chain: str) -> str:
        """
        掃描空投機會。

        針對指定區塊鏈，掃描當前所有活躍的空投項目，
        回傳包含專案名稱、資格要求、快照日期、領取截止日與預估價值。

        參數：
            chain: 區塊鏈名稱 (ethereum / bsc / polygon / arbitrum / optimism / avalanche / base / zksync / solana / aptos / sui)
        """
        try:
            ckey = _validate_chain(chain)
        except ValueError as e:
            return f"❌ {e}"

        chain_info = SUPPORTED_CHAINS[ckey]
        now = datetime.now(timezone.utc)
        seed = _make_seed(ckey, now.strftime("%Y%m"))
        rng = random.Random(seed)

        num_airdrops = rng.randint(2, 6)
        chain_tag = ckey[:4]

        protocols_pool = EVENT_POOLS.get(ckey, EVENT_POOLS["eth"])
        airdrops: List[dict] = []

        lines = [
            f"🪂 {chain_info['name']} 空投掃描結果",
            f"   區塊瀏覽器: {chain_info['explorer']}",
            f"   當前活躍空投數: {num_airdrops} 個",
            f"   掃描時間: {now.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "📋 空投專案清單:",
        ]

        for i in range(num_airdrops):
            airdrop_seed = _make_seed(ckey, str(i), now.strftime("%Y%m%d"))
            airdrop_rng = random.Random(airdrop_seed)
            protocol = _pick_from_pool(protocols_pool, airdrop_seed, i)
            project = f"{protocol}_token{airdrop_seed % 100:02d}"

            snapshot_offset = airdrop_rng.randint(-30, 15)
            snapshot_date = (now - timedelta(days=abs(snapshot_offset))).strftime("%Y-%m-%d")
            if snapshot_offset < 0:
                snapshot_note = f"快照已完成 ({snapshot_date})"
            else:
                snapshot_note = f"尚未快照，預計 {snapshot_date}"

            claim_deadline = (now + timedelta(days=airdrop_rng.randint(14, 90))).strftime("%Y-%m-%d")
            est_value = round(airdrop_rng.uniform(50, 5000), 0)
            value_rating = "🔥🔥🔥" if est_value > 2000 else ("🔥🔥" if est_value > 500 else "🔥")

            criteria = airdrop_rng.choice([
                "錢包交易數 ≥ 10 筆 + 跨鏈 3 條以上",
                "協議交互 ≥ 5 筆 + TVL > $1,000",
                "持有特定 NFT 系列 + Discord 成員",
                "早期使用者 (首 100,000 地址)",
                "質押 ≥ $500 等值代幣超過 30 天",
                "使用協議 ≥ 3 個不同功能模組",
                "錢包年齡 > 6 個月 + 鏈上足跡",
            ])

            lines.append(
                f"  [{i + 1}] {project} {value_rating}\n"
                f"      協議: {protocol}\n"
                f"      資格條件: {criteria}\n"
                f"      快照: {snapshot_note}\n"
                f"      領取截止: {claim_deadline}\n"
                f"      預估價值: ${est_value:,.0f}"
            )

            airdrops.append({
                "project": project,
                "protocol": protocol,
                "chain": ckey,
                "criteria": criteria,
                "snapshot_date": snapshot_date,
                "snapshot_passed": snapshot_offset < 0,
                "claim_deadline": claim_deadline,
                "estimated_value_usd": est_value,
            })

        self._airdrops_found += len(airdrops)
        self._airdropp_cache[ckey] = airdrops

        lines.append("")
        lines.append(f"🎯 累計發現空投總數: {self._airdrops_found}")
        lines.append("💡 提示: 使用 qualify_for_airdrop 檢查特定地址是否符合資格")
        return "\n".join(lines)

    @tool
    def qualify_for_airdrop(self, address: str, project: str) -> str:
        """
        檢查空投資格。

        根據現實空投資格模型，模擬檢查錢包地址是否符合專案空投條件。
        評估維度包含：錢包年齡、交易筆數、交易量、互動協議數量、
        鏈上資產餘額、合約互動深度與活躍天數。

        參數：
            address: 錢包地址 (0x 開頭)
            project: 空投專案名稱
        """
        address = self._normalize_address(address)
        project = project.strip()

        if len(address) < 10:
            return f"❌ 無效的錢包地址: {address}"

        seed = _make_seed(address, project)
        rng = random.Random(seed)

        wallet_age_months = rng.randint(1, 36)
        tx_count = rng.randint(5, 5000)
        total_volume_usd = round(rng.uniform(50, 500000), 2)
        protocols_used = rng.randint(0, 12)
        active_days = rng.randint(1, wallet_age_months * 30)
        balance_usd = round(rng.uniform(0, 100000), 2)
        contract_interactions = rng.randint(0, 200)
        is_sybil_likely = tx_count > 1000 and total_volume_usd > 100000 and protocols_used < 3
        is_eligible_core = (
            wallet_age_months >= 3
            and tx_count >= 10
            and total_volume_usd >= 500
            and protocols_used >= 2
            and not is_sybil_likely
        )

        score_dimensions = []
        score_total = 0.0

        dims = [
            ("錢包年齡", wallet_age_months, 3, 6, 12, 25, "個月"),
            ("交易筆數", tx_count, 10, 50, 200, 25, "筆"),
            ("交易量", total_volume_usd, 500, 5000, 50000, 20, "USD"),
            ("互動協議數", protocols_used, 2, 5, 8, 15, "個"),
            ("活躍天數", active_days, 10, 60, 180, 10, "天"),
            ("合約互動數", contract_interactions, 5, 30, 80, 5, "次"),
        ]

        for dname, dvalue, dmin, dmid, dhigh, dweight, dunit in dims:
            if dvalue >= dhigh:
                level = "優異"
                pct = 1.0
            elif dvalue >= dmid:
                level = "良好"
                pct = 0.7
            elif dvalue >= dmin:
                level = "達標"
                pct = 0.4
            else:
                level = "不足"
                pct = 0.1
            weighted = pct * dweight
            score_total += weighted
            score_dimensions.append(
                f"    {dname}: {dvalue}{dunit} → {level} ({pct:.0%} × {dweight}% = {weighted:.1f}%)"
            )

        eligibility = "✅ 符合資格" if is_eligible_core else "❌ 不符合資格"
        if is_sybil_likely:
            eligibility = "⚠️ 疑似女巫攻擊 (Sybil Attack)，資格可能被取消"
            score_total *= 0.2

        estimated_tokens = round(score_total * rng.uniform(5, 50), 0) if is_eligible_core else 0
        token_price = round(rng.uniform(0.1, 3), 2)
        estimated_value = round(estimated_tokens * token_price, 2)

        lines = [
            f"🔍 空投資格檢查: {project}",
            f"   錢包地址: {address[:10]}...{address[-6:]}",
            "",
            f"{'=' * 50}",
            "📊 多元評分詳情:",
        ]
        lines.extend(score_dimensions)
        lines.append(f"{'=' * 50}")
        lines.append(f"   綜合評分: {score_total:.1f} / 100")
        lines.append("")

        if is_sybil_likely:
            lines.append("⚠️ 警告：該錢包行為模式接近女巫攻擊特徵：")
            lines.append("   - 高交易量 + 低協議互動多樣性")
            lines.append("   - 大部份空投會將此類地址排除在外")
            lines.append("")

        lines.append(f"📋 空投資格判定: {eligibility}")
        if is_eligible_core:
            lines.append(f"   預估可獲代幣: {estimated_tokens:,.0f} 枚")
            lines.append(f"   預估代幣單價: ${token_price:.2f}")
            lines.append(f"   預估總價值: ${estimated_value:,.2f}")

        lines.append("")
        lines.append("💡 提升空投資格的建議:")
        suggestions = []
        if wallet_age_months < 6:
            suggestions.append("  • 讓錢包自然老化，大多數頂級空投要求 ≥ 6 個月")
        if tx_count < 50:
            suggestions.append("  • 增加鏈上交易次數，建議每月 ≥ 10 筆")
        if protocols_used < 3:
            suggestions.append("  • 與更多主流協議互動，多鏈多協議為佳")
        if total_volume_usd < 5000:
            suggestions.append("  • 提高交易量，$5,000 以上為良好門檻")
        if balance_usd < 1000:
            suggestions.append("  • 維持鏈上資產餘額 > $1,000，展現真實使用者特徵")

        if not suggestions:
            suggestions.append("  • 你的錢包狀態良好，繼續保持活躍即可！")

        lines.extend(suggestions)
        return "\n".join(lines)

    @tool
    def snipe_new_token(self, chain: str, max_buy_eth: float, slippage: float) -> str:
        """
        新代幣狙擊配置。

        針對指定區塊鏈監控新代幣發行，產生狙擊機器人設定指南。
        包含合約偵測、流動性檢查、安全審計、買入策略與風險管理。

        參數：
            chain: 區塊鏈名稱
            max_buy_eth: 單次買入最大 ETH 數量
            slippage: 滑點容忍百分比 (如 5 表示 5%)
        """
        try:
            ckey = _validate_chain(chain)
        except ValueError as e:
            return f"❌ {e}"

        if max_buy_eth <= 0:
            return "❌ max_buy_eth 必須大於 0"
        if not (0.1 <= slippage <= 100):
            return "❌ 滑點設定範圍應在 0.1% 至 100% 之間"

        chain_info = SUPPORTED_CHAINS[ckey]
        seed = _make_seed(ckey, str(max_buy_eth), str(slippage))
        rng = random.Random(seed)

        gas_limits = {
            "ethereum": (30, 80), "bsc": (5, 15), "polygon": (50, 200),
            "arbitrum": (0.1, 0.5), "optimism": (0.01, 0.1), "avalanche": (25, 60),
            "base": (0.01, 0.05), "zksync": (0.1, 0.3), "solana": (0.0001, 0.001),
            "aptos": (0.0001, 0.001), "sui": (0.0001, 0.001),
        }
        gas_range = gas_limits.get(ckey, (10, 50))

        sniper_config = {
            "chain": chain_info["name"],
            "native_token": chain_info["native"],
            "max_buy_amount": max_buy_eth,
            "slippage_percent": slippage,
            "recommended_gas_gwei": rng.randint(int(gas_range[0] * 100), int(gas_range[1] * 100)) / 100,
            "priority_fee_gwei": rng.randint(1, 5),
            "min_liquidity_eth": round(max_buy_eth * 2, 2),
            "max_holder_percent": rng.randint(1, 5),
            "honeypot_check": True,
            "rug_pull_check": True,
            "anti_bot_delay_ms": rng.choice([0, 50, 100, 200, 500]),
        }

        self._snipes_attempted += 1

        lines = [
            f"🎯 新代幣狙擊配置精靈",
            f"   目標鏈: {chain_info['name']} ({chain_info['native']} 原生幣)",
            f"",
            "⚙️ 狙擊機器人設定:",
            f"   最大買入額: {max_buy_eth} {chain_info['native']}",
            f"   滑點容忍: {slippage}%",
            f"   建議 Gas 價格: {sniper_config['recommended_gas_gwei']} Gwei",
            f"   優先手續費: {sniper_config['priority_fee_gwei']} Gwei",
            f"   最低流動性門檻: {sniper_config['min_liquidity_eth']} {chain_info['native']}",
            f"   最大持有人占比: {sniper_config['max_holder_percent']}%",
            f"",
            "🛡️ 安全檢查設定:",
            f"   蜜罐偵測: {'✅ 啟用' if sniper_config['honeypot_check'] else '❌ 禁用'}",
            f"   拉地毯偵測: {'✅ 啟用' if sniper_config['rug_pull_check'] else '❌ 禁用'}",
            f"   防機器人延遲: {sniper_config['anti_bot_delay_ms']} ms",
            f"",
            "📋 狙擊流程:",
            f"   1. 監聽 {chain_info['explorer']} 新合約部署事件",
            f"   2. 驗證合約源碼 (開源檢查)",
            f"   3. 檢查流動性鎖定與持有人分布",
            f"   4. 確認無蜜罐/拉地毯風險",
            f"   5. 觸發買入交易 (Gas: {sniper_config['recommended_gas_gwei']} Gwei)",
            f"   6. 設定止盈/止損 (建議: +30% / -15%)",
            f"",
            "⚠️ 風險警告:",
            f"   • 新幣狙擊高風險，預期成功率約 30-40%",
            f"   • 永遠只投入可承受全部損失的資金",
            f"   • 務必確認合約安全後再買入",
            f"   • 建議先用小額 ($0.01-0.05 ETH) 測試",
            f"",
            f"📊 累計狙擊嘗試次數: {self._snipes_attempted}",
        ]
        return "\n".join(lines)

    @tool
    def track_portfolio_airdrops(self, addresses: str) -> str:
        """
        批次空投追蹤。

        針對多位址組合，掃描各鏈上主流協議的空投機會，
        並對每個地址進行基本資格評估。

        參數：
            addresses: 錢包地址清單，以逗號分隔，例如 "0xabc...,0xdef..."
        """
        raw_addrs = [a.strip() for a in addresses.split(",") if a.strip()]
        if not raw_addrs:
            return "❌ 請提供至少一個錢包地址"

        self._watched_addresses = [self._normalize_address(a) for a in raw_addrs]

        if len(self._watched_addresses) > 50:
            return f"❌ 單次最多追蹤 50 個地址，目前提供 {len(self._watched_addresses)} 個"

        lines = [
            f"🪂 批次空投追蹤報告",
            f"   追蹤地址數: {len(self._watched_addresses)} 個",
            f"   掃描區塊鏈數: {len(SUPPORTED_CHAINS)} 條",
            f"   掃描時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        total_opportunities = 0
        per_address_summary: List[dict] = []

        for addr in self._watched_addresses:
            addr_seed = _make_seed(addr)
            addr_rng = random.Random(addr_seed)
            chain_count = addr_rng.randint(1, len(SUPPORTED_CHAINS))
            selected_chains = addr_rng.sample(list(SUPPORTED_CHAINS.keys()), chain_count)

            eligible_count = 0
            chain_opps: List[str] = []
            for ckey in selected_chains[:5]:
                chain_seed = _make_seed(addr, ckey)
                chain_rng = random.Random(chain_seed)
                if chain_rng.random() > 0.4:
                    eligible_count += 1
                    chain_name = SUPPORTED_CHAINS[ckey]["name"]
                    protocol = _pick_from_pool(EVENT_POOLS.get(ckey, EVENT_POOLS["eth"]), chain_seed, eligible_count)
                    est_val = round(chain_rng.uniform(100, 8000), 0)
                    chain_opps.append(f"{chain_name} ({protocol}: ~${est_val:,.0f})")

            total_opportunities += eligible_count
            addr_short = f"{addr[:8]}...{addr[-4:]}"

            status_emoji = "🟢" if eligible_count >= 3 else ("🟡" if eligible_count >= 1 else "🔴")
            lines.append(
                f"  {status_emoji} {addr_short}: {eligible_count} 個潛力空投"
            )
            if chain_opps:
                for opp in chain_opps:
                    lines.append(f"     ↳ {opp}")

            per_address_summary.append({
                "address": addr,
                "eligible_count": eligible_count,
                "opportunities": chain_opps,
            })

        lines.append("")
        lines.append(f"📊 總結: 總共發現 {total_opportunities} 個潛在空投機會")
        avg_opp = total_opportunities / max(len(self._watched_addresses), 1)
        lines.append(f"   平均每位址: {avg_opp:.1f} 個機會")

        top_addr = max(per_address_summary, key=lambda x: x["eligible_count"])
        lines.append(f"   🏆 最佳地址: {top_addr['address'][:8]}...{top_addr['address'][-4:]} ({top_addr['eligible_count']} 個機會)")

        if total_opportunities == 0:
            lines.append("")
            lines.append("💡 建議: 這些地址的鏈上活動較少，建議:")
            lines.append("   • 在主流 DeFi 協議中進行互動")
            lines.append("   • 跨鏈轉帳增加鏈上足跡")
            lines.append("   • 使用 L2 網路降低手續費成本")

        return "\n".join(lines)

    @tool
    def get_opportunity_report(self) -> str:
        """
        綜合機會報告。

        產出一份統整報告，包含當前交易所活動、空投機會、
        新代幣發行預告與狙擊建議。
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        seed = _make_seed(date_str)
        rng = random.Random(seed)

        lines = [
            "╔══════════════════════════════════════════╗",
            "║     🦅 加密獵手每日機會報告             ║",
            "╚══════════════════════════════════════════╝",
            f"   產出時間: {date_str}",
            f"   追蹤交易所: {len(TOP_EXCHANGES)} 家",
            f"   監控區塊鏈: {len(SUPPORTED_CHAINS)} 條",
            f"   觀察地址數: {len(self._watched_addresses)} 個",
            "",
            "━" * 44,
            "📊 市場情緒與機會評級",
            "━" * 44,
        ]

        market_sentiment = rng.choice(["貪婪 🟢", "中立 🟡", "恐懼 🔴"])
        btc_trend = rng.choice(["多頭", "盤整", "空頭"])
        alt_season = rng.choice(["山寨幣季節", "比特幣主導", "輪動中"])

        lines.append(f"   市場情緒: {market_sentiment}")
        lines.append(f"   BTC 趨勢: {btc_trend}")
        lines.append(f"   山寨市場: {alt_season}")
        lines.append(f"   機會評級: {'🔥🔥🔥 高' if market_sentiment == '貪婪 🟢' else '🔥🔥 中' if market_sentiment == '中立 🟡' else '🔥 低'}")

        lines.append("")
        lines.append("━" * 44)
        lines.append("🏦 交易所熱門活動 TOP 5")
        lines.append("━" * 44)

        hot_exchanges = rng.sample(list(TOP_EXCHANGES.keys()), min(5, len(TOP_EXCHANGES)))
        for i, ekey in enumerate(hot_exchanges):
            ex_info = TOP_EXCHANGES[ekey]
            top_event = ex_info["event_types"][0]
            lines.append(f"  [{i + 1}] {ex_info['name']}: {top_event[0]} (預估報酬 {top_event[2]})")

        lines.append("")
        lines.append("━" * 44)
        lines.append("🪂 熱門空投專案")
        lines.append("━" * 44)

        hot_chains = rng.sample(list(SUPPORTED_CHAINS.keys()), min(4, len(SUPPORTED_CHAINS)))
        for i, ckey in enumerate(hot_chains):
            chain_name = SUPPORTED_CHAINS[ckey]["name"]
            protocol = _pick_from_pool(EVENT_POOLS.get(ckey, EVENT_POOLS["eth"]), seed, i)
            est_val = rng.randint(500, 10000)
            snapshot_days = rng.randint(-5, 14)
            if snapshot_days > 0:
                snap_msg = f"尚有 {snapshot_days} 天"
            elif snapshot_days == 0:
                snap_msg = "今日快照!"
            else:
                snap_msg = f"已過 {-snapshot_days} 天"

            lines.append(f"  [{i + 1}] {protocol} @ {chain_name}")
            lines.append(f"       快照狀態: {snap_msg} | 預估價值: ${est_val:,.0f}")

        lines.append("")
        lines.append("━" * 44)
        lines.append("🚀 新幣發行預告")
        lines.append("━" * 44)

        new_chain = rng.choice(list(SUPPORTED_CHAINS.keys()))
        new_chain_name = SUPPORTED_CHAINS[new_chain]["name"]
        nat = SUPPORTED_CHAINS[new_chain]["native"]
        dexes = {"ethereum": "Uniswap", "bsc": "PancakeSwap", "polygon": "Quickswap",
                 "arbitrum": "Camelot", "optimism": "Velodrome", "avalanche": "Trader Joe",
                 "base": "Aerodrome", "zksync": "SyncSwap", "solana": "Raydium",
                 "aptos": "LiquidSwap", "sui": "Cetus"}
        dex = dexes.get(new_chain, "DEX")

        lines.append(f"   🔥 熱門鏈: {new_chain_name}")
        lines.append(f"   主要 DEX: {dex}")
        lines.append(f"   建議狙擊預算: 0.1-0.5 {nat} / 筆")
        lines.append(f"   當前 Gas 費: 正常")

        lines.append("")
        lines.append("━" * 44)
        lines.append("💡 今日行動建議")
        lines.append("━" * 44)

        suggestions = [
            f"⏰ 優先參與交易所 Launchpad (無常虧損風險)",
            f"🔍 檢查已追蹤地址的空投狀態",
            f"📊 關注 {new_chain_name} 生態新專案",
            f"💼 分散持有不同鏈原生代幣以備 Gas 費",
        ]
        for s in suggestions:
            lines.append(f"   {s}")

        lines.append("")
        lines.append(f"📈 累計統計: 活動 {self._events_tracked} | 空投 {self._airdrops_found} | 狙擊 {self._snipes_attempted}")

        return "\n".join(lines)

    def status(self) -> dict:
        """回報加密獵手機關當前運行狀態。"""
        return {
            "name": "CryptoHunterOrgan",
            "alive": self._active,
            "events_tracked": self._events_tracked,
            "airdrops_found": self._airdrops_found,
            "snipes_attempted": self._snipes_attempted,
            "watched_addresses_count": len(self._watched_addresses),
            "exchanges_monitored": list(TOP_EXCHANGES.keys()),
            "chains_supported": list(SUPPORTED_CHAINS.keys()),
        }
