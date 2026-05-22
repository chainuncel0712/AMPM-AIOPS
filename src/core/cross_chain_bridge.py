"""
跨鏈橋接引擎 — CrossChainBridgeOrgan
計算最佳跨鏈路徑、估算手續費與時間，支援多條鏈與主流跨鏈橋。
"""
import json
import os
import secrets
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any

from skeleton.brain_component import BrainComponent
from tools import tool


class CrossChainBridgeOrgan(BrainComponent):
    """
    跨鏈橋接引擎

    功能清單：
    1. 最佳路徑 — 根據金額與鏈組合推薦最優跨鏈橋
    2. 費用估算 — 計算 Gas 費與橋接協議費用
    3. 鏈支援 — 列出所有支援的來源與目標鏈
    4. 時間估算 — 預估跨鏈完成所需時間
    5. 歷史記錄 — 儲存每筆跨鏈估算供後續分析
    """

    SUPPORTED_CHAINS: Dict[str, Dict[str, Any]] = {
        "ethereum":  {"name": "Ethereum",      "symbol": "ETH",  "chain_id": 1,      "l2": False, "avg_block_time": 12},
        "bsc":       {"name": "BNB Smart Chain","symbol": "BNB",  "chain_id": 56,     "l2": False, "avg_block_time": 3},
        "polygon":   {"name": "Polygon",        "symbol": "MATIC","chain_id": 137,    "l2": True,  "avg_block_time": 2},
        "arbitrum":  {"name": "Arbitrum One",   "symbol": "ETH",  "chain_id": 42161,  "l2": True,  "avg_block_time": 0.25},
        "optimism":  {"name": "OP Mainnet",     "symbol": "ETH",  "chain_id": 10,     "l2": True,  "avg_block_time": 2},
        "avalanche": {"name": "Avalanche C",    "symbol": "AVAX", "chain_id": 43114,  "l2": False, "avg_block_time": 2},
        "base":      {"name": "Base",           "symbol": "ETH",  "chain_id": 8453,   "l2": True,  "avg_block_time": 2},
        "zksync":    {"name": "zkSync Era",     "symbol": "ETH",  "chain_id": 324,    "l2": True,  "avg_block_time": 1},
    }

    KNOWN_BRIDGES: Dict[str, Dict[str, Any]] = {
        "stargate": {
            "name": "Stargate Finance",
            "type": "liquidity",
            "fee_pct_range": (0.03, 0.10),
            "base_fee_usd": 0.50,
            "confirmation_blocks": 12,
            "supported_chains": {"ethereum", "bsc", "polygon", "arbitrum", "optimism", "avalanche", "base"},
            "url": "https://stargate.finance",
        },
        "across": {
            "name": "Across Protocol",
            "type": "intent",
            "fee_pct_range": (0.02, 0.08),
            "base_fee_usd": 0.30,
            "confirmation_blocks": 6,
            "supported_chains": {"ethereum", "arbitrum", "optimism", "polygon", "base", "zksync"},
            "url": "https://across.to",
        },
        "hop": {
            "name": "Hop Protocol",
            "type": "amm",
            "fee_pct_range": (0.04, 0.15),
            "base_fee_usd": 0.80,
            "confirmation_blocks": 15,
            "supported_chains": {"ethereum", "arbitrum", "optimism", "polygon", "base"},
            "url": "https://hop.exchange",
        },
        "synapse": {
            "name": "Synapse Protocol",
            "type": "liquidity",
            "fee_pct_range": (0.05, 0.12),
            "base_fee_usd": 0.60,
            "confirmation_blocks": 20,
            "supported_chains": {"ethereum", "bsc", "polygon", "arbitrum", "optimism", "avalanche", "base"},
            "url": "https://synapseprotocol.com",
        },
        "connext": {
            "name": "Connext",
            "type": "intent",
            "fee_pct_range": (0.03, 0.09),
            "base_fee_usd": 0.40,
            "confirmation_blocks": 8,
            "supported_chains": {"ethereum", "bsc", "polygon", "arbitrum", "optimism", "base"},
            "url": "https://connext.network",
        },
        "orbiter": {
            "name": "Orbiter Finance",
            "type": "liquidity",
            "fee_pct_range": (0.02, 0.06),
            "base_fee_usd": 0.25,
            "confirmation_blocks": 10,
            "supported_chains": {"ethereum", "bsc", "polygon", "arbitrum", "optimism", "base", "zksync"},
            "url": "https://orbiter.finance",
        },
    }

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self.name = dna.get("name", "cross_chain_bridge") if dna else "cross_chain_bridge"
        self._alive = True
        self._history: List[Dict[str, Any]] = []

    def _get_available_bridges(self, from_chain: str, to_chain: str) -> List[Tuple[str, Dict]]:
        """找出連接兩條鏈的所有可用跨鏈橋"""
        available = []
        for bridge_key, bridge_info in self.KNOWN_BRIDGES.items():
            if from_chain in bridge_info["supported_chains"] and to_chain in bridge_info["supported_chains"]:
                available.append((bridge_key, bridge_info))
        return available

    def _estimate_gas_fee_usd(self, chain: str) -> float:
        """
        估算指定鏈上單筆交易的 Gas 費用（美元）

        基於各鏈的典型 Gas 價格與 ETH 市價約 $3100 計算。
        """
        gas_estimates = {
            "ethereum":  (15, 21000),
            "bsc":       (3, 21000),
            "polygon":   (50, 21000),
            "arbitrum":  (0.1, 21000),
            "optimism":  (0.02, 21000),
            "avalanche": (25, 21000),
            "base":      (0.015, 21000),
            "zksync":    (0.03, 21000),
        }
        gas_price_gwei, gas_limit = gas_estimates.get(chain, (15, 21000))
        eth_price = 3100.0
        gas_fee_eth = (gas_price_gwei * gas_limit) / 1e9
        return round(gas_fee_eth * eth_price, 4)

    def _estimate_bridge_fee_usd(self, bridge_info: Dict, amount_usd: float) -> float:
        """計算跨鏈橋協議費用"""
        low_pct, high_pct = bridge_info["fee_pct_range"]
        mid_pct = (low_pct + high_pct) / 2
        pct_fee = amount_usd * (mid_pct / 100)
        total_fee = round(bridge_info["base_fee_usd"] + pct_fee, 4)
        return total_fee

    def _estimate_confirmation_time(self, bridge_info: Dict, from_chain: str, to_chain: str) -> Tuple[int, int]:
        """
        估算跨鏈確認時間（秒）

        回傳 (最小秒數, 最大秒數)
        """
        from_block = self.SUPPORTED_CHAINS[from_chain]["avg_block_time"]
        to_block = self.SUPPORTED_CHAINS[to_chain]["avg_block_time"]
        blocks = bridge_info["confirmation_blocks"]

        min_sec = int(blocks * min(from_block, to_block) * 0.8)
        max_sec = int(blocks * max(from_block, to_block) * 1.5)
        if from_chain == "ethereum":
            min_sec = max(min_sec, 120)
            max_sec = max(max_sec, 600)
        return min_sec, max_sec

    @tool(name="find_best_route", description="尋找兩條鏈之間最優的跨鏈橋路徑")
    def find_best_route(self, from_chain: str, to_chain: str, amount: float) -> str:
        """
        尋找最佳跨鏈路徑

        根據交易金額比較所有可用跨鏈橋的總費用
        （來源鏈 Gas + 橋接協議費 + 目標鏈 Gas），
        回推薦最經濟實惠的路徑。

        參數：
            from_chain: 來源區塊鏈
            to_chain: 目標區塊鏈
            amount: 跨鏈金額（以來源鏈原生代幣計價）
        """
        from_chain = from_chain.lower().strip()
        to_chain = to_chain.lower().strip()

        if from_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的來源鏈: {from_chain}，可用: {', '.join(self.SUPPORTED_CHAINS.keys())}"
        if to_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的目標鏈: {to_chain}，可用: {', '.join(self.SUPPORTED_CHAINS.keys())}"
        if from_chain == to_chain:
            return "❌ 來源鏈與目標鏈相同，無需跨鏈"

        try:
            available = self._get_available_bridges(from_chain, to_chain)
            if not available:
                return f"❌ 找不到 {from_chain.upper()} → {to_chain.upper()} 的可用跨鏈橋"

            amount_usd = amount * 3100.0
            from_gas = self._estimate_gas_fee_usd(from_chain)
            to_gas = self._estimate_gas_fee_usd(to_chain)

            results = []
            for bridge_key, bridge_info in available:
                bridge_fee = self._estimate_bridge_fee_usd(bridge_info, amount_usd)
                total_fee = round(from_gas + bridge_fee + to_gas, 4)
                min_sec, max_sec = self._estimate_confirmation_time(bridge_info, from_chain, to_chain)
                results.append({
                    "bridge_key": bridge_key,
                    "bridge_name": bridge_info["name"],
                    "bridge_type": bridge_info["type"],
                    "bridge_url": bridge_info["url"],
                    "from_gas_usd": from_gas,
                    "bridge_fee_usd": bridge_fee,
                    "to_gas_usd": to_gas,
                    "total_fee_usd": total_fee,
                    "min_time_sec": min_sec,
                    "max_time_sec": max_sec,
                })

            results.sort(key=lambda r: r["total_fee_usd"])
            best = results[0]

            record = {
                "from_chain": from_chain,
                "to_chain": to_chain,
                "amount": amount,
                "amount_usd": amount_usd,
                "best_bridge": best["bridge_name"],
                "total_fee_usd": best["total_fee_usd"],
                "all_options": results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._history.append(record)
            if len(self._history) > 500:
                self._history = self._history[-500:]

            lines = [
                f"🔗 跨鏈最佳路徑：{self.SUPPORTED_CHAINS[from_chain]['name']} → {self.SUPPORTED_CHAINS[to_chain]['name']}",
                f"  交易金額：{amount} {self.SUPPORTED_CHAINS[from_chain]['symbol']} (約 ${amount_usd:,.2f})",
                f"",
                f"  推薦橋接：{best['bridge_name']} ({best['bridge_type']})",
                f"  橋接網址：{best['bridge_url']}",
                f"",
                f"  費用明細：",
                f"    來源鏈 Gas： ${best['from_gas_usd']:.4f}",
                f"    橋接協議費： ${best['bridge_fee_usd']:.4f}",
                f"    目標鏈 Gas： ${best['to_gas_usd']:.4f}",
                f"    總費用：     ${best['total_fee_usd']:.4f}",
                f"",
                f"  預估時間：{best['min_time_sec']} ~ {best['max_time_sec']} 秒",
            ]

            if len(results) > 1:
                lines.append(f"\n  其他可用橋接方案：")
                for r in results[1:6]:
                    lines.append(
                        f"    {r['bridge_name']:20s} | "
                        f"總費用：${r['total_fee_usd']:.4f} | "
                        f"時間：{r['min_time_sec']}~{r['max_time_sec']}s"
                    )

            lines.append(f"\n  查詢時間：{datetime.now(timezone.utc).isoformat()}")
            return "\n".join(lines)

        except Exception as e:
            return f"❌ 路徑分析失敗：{str(e)}"

    @tool(name="estimate_fees", description="估算指定跨鏈路徑的總手續費")
    def estimate_fees(self, from_chain: str, to_chain: str, amount: float) -> str:
        """
        估算跨鏈手續費

        計算從來源鏈到目標鏈的完整跨鏈成本，
        包含來源鏈 Gas 費、跨鏈橋協議費與目標鏈 Gas 費。

        參數：
            from_chain: 來源區塊鏈
            to_chain: 目標區塊鏈
            amount: 跨鏈金額（以來源鏈原生代幣計價）
        """
        from_chain = from_chain.lower().strip()
        to_chain = to_chain.lower().strip()

        if from_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的來源鏈: {from_chain}"
        if to_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的目標鏈: {to_chain}"
        if from_chain == to_chain:
            return "❌ 來源鏈與目標鏈相同，無需跨鏈"

        try:
            available = self._get_available_bridges(from_chain, to_chain)
            if not available:
                return f"❌ 找不到 {from_chain.upper()} → {to_chain.upper()} 的可用跨鏈橋"

            amount_usd = amount * 3100.0
            from_gas = self._estimate_gas_fee_usd(from_chain)
            to_gas = self._estimate_gas_fee_usd(to_chain)

            lines = [
                f"💲 跨鏈費用估算",
                f"  路徑：{self.SUPPORTED_CHAINS[from_chain]['name']} → {self.SUPPORTED_CHAINS[to_chain]['name']}",
                f"  金額：{amount} {self.SUPPORTED_CHAINS[from_chain]['symbol']} (約 ${amount_usd:,.2f})",
                f"",
            ]

            for bridge_key, bridge_info in available:
                bridge_fee = self._estimate_bridge_fee_usd(bridge_info, amount_usd)
                total = round(from_gas + bridge_fee + to_gas, 4)
                fee_pct = round((total / amount_usd) * 100, 3) if amount_usd > 0 else 0
                lines.append(
                    f"  {bridge_info['name']:20s} | "
                    f"Gas: ${from_gas:.4f} | "
                    f"橋接費: ${bridge_fee:.4f} | "
                    f"目標Gas: ${to_gas:.4f} | "
                    f"總費: ${total:.4f} ({fee_pct}%)"
                )

            lines.append(f"\n  查詢時間：{datetime.now(timezone.utc).isoformat()}")
            return "\n".join(lines)

        except Exception as e:
            return f"❌ 費用估算失敗：{str(e)}"

    @tool(name="list_supported_chains", description="列出跨鏈橋接引擎支援的所有區塊鏈")
    def list_supported_chains(self) -> str:
        """
        列出支援區塊鏈

        回傳所有支援的來源/目標鏈及其網路屬性。
        """
        lines = ["🌉 跨鏈橋接引擎 — 支援區塊鏈清單："]
        for key, info in self.SUPPORTED_CHAINS.items():
            l2_label = "L2" if info["l2"] else "L1"
            bridge_count = sum(
                1 for b in self.KNOWN_BRIDGES.values()
                if key in b["supported_chains"]
            )
            lines.append(
                f"  {key.upper():12s} | {info['name']:18s} "
                f"| {l2_label:2s} | 代幣：{info['symbol']:5s} "
                f"| Chain ID：{info['chain_id']:6d} "
                f"| 可用橋：{bridge_count} 個"
            )
        return "\n".join(lines)

    @tool(name="estimate_time", description="估算跨鏈交易完成所需時間")
    def estimate_time(self, from_chain: str, to_chain: str) -> str:
        """
        估算跨鏈時間

        根據來源鏈與目標鏈的出塊時間及跨鏈橋確認區塊數，
        估算跨鏈交易完成的時間範圍。

        參數：
            from_chain: 來源區塊鏈
            to_chain: 目標區塊鏈
        """
        from_chain = from_chain.lower().strip()
        to_chain = to_chain.lower().strip()

        if from_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的來源鏈: {from_chain}"
        if to_chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的目標鏈: {to_chain}"
        if from_chain == to_chain:
            return "❌ 來源鏈與目標鏈相同，無需跨鏈"

        try:
            available = self._get_available_bridges(from_chain, to_chain)
            if not available:
                return f"❌ 找不到 {from_chain.upper()} → {to_chain.upper()} 的可用跨鏈橋"

            from_info = self.SUPPORTED_CHAINS[from_chain]
            to_info = self.SUPPORTED_CHAINS[to_chain]

            lines = [
                f"⏱️ 跨鏈時間估算",
                f"  路徑：{from_info['name']} → {to_info['name']}",
                f"  來源出塊時間：{from_info['avg_block_time']} 秒/區塊",
                f"  目標出塊時間：{to_info['avg_block_time']} 秒/區塊",
                f"",
            ]

            for bridge_key, bridge_info in available:
                min_sec, max_sec = self._estimate_confirmation_time(bridge_info, from_chain, to_chain)
                min_display = f"{min_sec}s" if min_sec < 120 else f"{min_sec // 60}m {min_sec % 60}s"
                max_display = f"{max_sec}s" if max_sec < 120 else f"{max_sec // 60}m {max_sec % 60}s"
                lines.append(
                    f"  {bridge_info['name']:20s} | "
                    f"確認區塊：{bridge_info['confirmation_blocks']:3d} | "
                    f"預估：{min_display} ~ {max_display}"
                )

            lines.append(f"\n  查詢時間：{datetime.now(timezone.utc).isoformat()}")
            return "\n".join(lines)

        except Exception as e:
            return f"❌ 時間估算失敗：{str(e)}"

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self._alive,
            "supported_chains": len(self.SUPPORTED_CHAINS),
            "known_bridges": len(self.KNOWN_BRIDGES),
            "history_count": len(self._history),
        }
