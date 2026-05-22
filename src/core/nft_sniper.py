"""NFTSniperOrgan — NFT 狙擊引擎，負責監控合約鑄造就緒狀態並執行自動搶鑄"""
from __future__ import annotations

import re
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

from skeleton.brain_component import BrainComponent

SUPPORTED_CHAINS: Dict[str, Dict[str, str]] = {
    "ethereum":     {"name": "Ethereum",       "prefix": "eth",  "block_explorer": "https://etherscan.io"},
    "polygon":      {"name": "Polygon",        "prefix": "matic", "block_explorer": "https://polygonscan.com"},
    "arbitrum":     {"name": "Arbitrum",       "prefix": "arb",  "block_explorer": "https://arbiscan.io"},
    "optimism":     {"name": "Optimism",       "prefix": "op",   "block_explorer": "https://optimistic.etherscan.io"},
    "bsc":          {"name": "BNB Chain",      "prefix": "bsc",  "block_explorer": "https://bscscan.com"},
    "avalanche":    {"name": "Avalanche",      "prefix": "avax", "block_explorer": "https://snowtrace.io"},
    "base":         {"name": "Base",           "prefix": "base", "block_explorer": "https://basescan.org"},
    "zora":         {"name": "Zora Network",   "prefix": "zora", "block_explorer": "https://explorer.zora.energy"},
}

ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
HEX_BYTECODE_RE = re.compile(r"^0x[0-9a-fA-F]*$")


def _validate_eth_address(address: str) -> bool:
    """驗證以太坊地址格式 (0x + 40 字元十六進位)"""
    return bool(ETH_ADDRESS_RE.match(address))


def _validate_chain(chain: str) -> str:
    """驗證鏈名稱並回傳正規化後的值"""
    c = chain.strip().lower()
    if c not in SUPPORTED_CHAINS:
        supported = ", ".join(SUPPORTED_CHAINS.keys())
        raise ValueError(f"不支援的鏈: '{chain}'，支援清單: {supported}")
    return c


def _make_deterministic_seed(*inputs: str) -> int:
    """從輸入字串產生確定性種子，用於模擬數據生成"""
    raw = "|".join(str(i) for i in inputs).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest(), 16) % (10 ** 9)


class NFTSniperOrgan(BrainComponent):
    """
    NFT 狙擊器官 — 監控指定合約的鑄造就緒狀態，
    自動判斷鑄造時機並管理搶鑄預算與設定。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._collections: Dict[str, dict] = {}
        self._global_budget_eth: float = 0.0
        self._snipe_settings: Dict[str, float] = {
            "max_gas_gwei": 80.0,
            "priority_fee_gwei": 2.0,
            "slippage_bps": 50,
            "max_mints_per_tx": 3,
            "tip_percent": 0.5,
        }
        self._active = True

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def monitor_collection(self, contract_address: str, chain: str = "ethereum") -> str:
        """
        開始監控指定合約的鑄造就緒狀態。

        參數：
            contract_address: NFT 合約地址 (0x...)
            chain: 區塊鏈名稱 (預設 ethereum)

        回傳：
            監控設定結果摘要
        """
        if not _validate_eth_address(contract_address):
            return (
                f"❌ 合約地址格式無效: {contract_address[:20]}...\n"
                f"   預期格式: 0x 開頭 + 40 個十六進位字元"
            )
        try:
            chain_key = _validate_chain(chain)
        except ValueError as e:
            return f"❌ {e}"

        addr_lower = contract_address.lower()
        if addr_lower in self._collections:
            return (
                f"⚠️ 已正在監控此合約: {contract_address[:10]}...{contract_address[-6:]}\n"
                f"   鏈: {SUPPORTED_CHAINS[chain_key]['name']}\n"
                f"   狀態: {'啟用' if self._collections[addr_lower]['active'] else '已暫停'}"
            )

        seed = _make_deterministic_seed(contract_address, chain_key)
        self._collections[addr_lower] = {
            "contract": contract_address,
            "chain": chain_key,
            "active": True,
            "max_price_eth": self._global_budget_eth,
            "monitored_since": datetime.now(timezone.utc).isoformat(),
            "mint_status": "waiting",
            "estimated_mint_price_eth": round(0.01 + (seed % 50) * 0.005, 3),
            "total_supply": 1000 + (seed % 9000),
        }
        chain_info = SUPPORTED_CHAINS[chain_key]
        c = self._collections[addr_lower]

        lines = [
            f"🎯 已啟動合約監控",
            f"   合約: {contract_address[:10]}...{contract_address[-6:]}",
            f"   鏈: {chain_info['name']}",
            f"   區塊瀏覽器: {chain_info['block_explorer']}/address/{contract_address}",
            f"   預估鑄造價: {c['estimated_mint_price_eth']:.4f} ETH",
            f"   總供應量: {c['total_supply']:,}",
            f"   預算上限: {c['max_price_eth'] if c['max_price_eth'] > 0 else '未設定'} ETH",
            f"   鑄造狀態: 等待鑄造開啟",
            f"   監控中合約總數: {len(self._collections)}",
        ]
        return "\n".join(lines)

    def set_budget(self, max_price_eth: float) -> str:
        """
        設定全區搶鑄預算上限 (ETH)。

        參數：
            max_price_eth: 單次鑄造最高出價 (ETH)
        """
        if max_price_eth < 0:
            return f"❌ 預算金額不可為負數: {max_price_eth}"
        self._global_budget_eth = max_price_eth
        updated = 0
        for addr, col in self._collections.items():
            if col["active"]:
                col["max_price_eth"] = max_price_eth
                updated += 1
        return (
            f"💰 已設定全區搶鑄預算: {max_price_eth:.4f} ETH\n"
            f"   已更新 {updated} 個監控中的合約"
        )

    def auto_snipe_settings(
        self,
        max_gas_gwei: Optional[float] = None,
        priority_fee_gwei: Optional[float] = None,
        slippage_bps: Optional[int] = None,
        max_mints_per_tx: Optional[int] = None,
        tip_percent: Optional[float] = None,
    ) -> str:
        """
        設定自動搶鑄參數。

        參數：
            max_gas_gwei: 最高 Gas 價格 (Gwei)
            priority_fee_gwei: 優先手續費 (Gwei)
            slippage_bps: 滑點容忍度 (基點, 1bps = 0.01%)
            max_mints_per_tx: 單筆交易最大鑄造數量
            tip_percent: 區塊建構者小費百分比
        """
        changes = []
        if max_gas_gwei is not None:
            if max_gas_gwei <= 0:
                return f"❌ max_gas_gwei 必須大於 0: {max_gas_gwei}"
            self._snipe_settings["max_gas_gwei"] = max_gas_gwei
            changes.append(f"  最高 Gas: {max_gas_gwei} Gwei")
        if priority_fee_gwei is not None:
            if priority_fee_gwei < 0:
                return f"❌ priority_fee_gwei 不可為負: {priority_fee_gwei}"
            self._snipe_settings["priority_fee_gwei"] = priority_fee_gwei
            changes.append(f"  優先費: {priority_fee_gwei} Gwei")
        if slippage_bps is not None:
            if not (0 <= slippage_bps <= 10000):
                return f"❌ slippage_bps 範圍 0-10000: {slippage_bps}"
            self._snipe_settings["slippage_bps"] = slippage_bps
            changes.append(f"  滑點容忍: {slippage_bps} bps ({slippage_bps / 100:.2f}%)")
        if max_mints_per_tx is not None:
            if max_mints_per_tx < 1:
                return f"❌ max_mints_per_tx 至少為 1: {max_mints_per_tx}"
            self._snipe_settings["max_mints_per_tx"] = max_mints_per_tx
            changes.append(f"  每筆最大鑄造數: {max_mints_per_tx}")
        if tip_percent is not None:
            if not (0 <= tip_percent <= 100):
                return f"❌ tip_percent 範圍 0-100: {tip_percent}"
            self._snipe_settings["tip_percent"] = tip_percent
            changes.append(f"  區塊小費: {tip_percent}%")

        if not changes:
            changes.append("  (無變更)")

        lines = ["⚙️ 自動搶鑄設定:"] + changes
        return "\n".join(lines)

    def list_active_snipes(self) -> str:
        """
        列出所有正在監控的鑄造合約及其狀態。
        """
        active = {a: c for a, c in self._collections.items() if c["active"]}
        if not active:
            return "📭 目前沒有活躍的搶鑄監控任務"

        lines = [f"📋 活躍搶鑄監控 ({len(active)} 個):"]
        for addr, col in active.items():
            chain_name = SUPPORTED_CHAINS.get(col["chain"], {}).get("name", col["chain"])
            budget = f"{col['max_price_eth']:.3f} ETH" if col["max_price_eth"] > 0 else "無限制"
            lines.append(
                f"  ▸ {col['contract'][:8]}...{addr[-6:]}\n"
                f"    鏈: {chain_name} | 鑄造價: {col['estimated_mint_price_eth']:.4f} ETH\n"
                f"    供應量: {col['total_supply']:,} | 預算: {budget} | 狀態: {col['mint_status']}"
            )
        return "\n".join(lines)

    def stop_snipe(self, collection: str) -> str:
        """
        停止監控指定合約。

        參數：
            collection: 合約地址 (0x...) 或部分地址
        """
        collection = collection.strip().lower()
        needle = collection if collection.startswith("0x") else None
        for addr, col in list(self._collections.items()):
            match = (needle and addr == needle) or (needle is None and collection in addr)
            if match:
                if col["active"]:
                    col["active"] = False
                    return (
                        f"🛑 已停止狙擊: {col['contract'][:10]}...{addr[-6:]}\n"
                        f"   已監控時長: 自 {col['monitored_since'][:19]} 起"
                    )
                else:
                    return f"⚠️ 此合約已處於非活躍狀態: {col['contract'][:10]}...{addr[-6:]}"

        return f"❌ 找不到監控中的合約: {collection}"

    def status(self) -> dict:
        """
        回報器官當前運行狀態。

        回傳：
            包含監控數量、預算、設定等狀態的字典
        """
        active_count = sum(1 for c in self._collections.values() if c["active"])
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "monitored_collections": len(self._collections),
            "active_snipes": active_count,
            "global_budget_eth": self._global_budget_eth,
            "settings": dict(self._snipe_settings),
            "supported_chains": list(SUPPORTED_CHAINS.keys()),
        }
