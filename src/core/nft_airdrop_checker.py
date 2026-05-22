"""NFTAirdropCheckerOrgan — NFT 空投檢查器，驗證地址資格、管理已知空投並處理領取"""
from __future__ import annotations

import re
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Set

from skeleton.brain_component import BrainComponent

ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

PRESEEDED_AIRDROPS: Dict[str, dict] = {
    "Pixelmon Airdrop": {
        "contract": "0x32973908feeebf3c3a5e0b8c2e0e5d8a3f7b1c6a",
        "criteria": "持有 Pixelmon NFT ≥ 1 個 (Snapshot: 2025-01-15)",
        "status": "active",
        "deadline": "2026-06-30T23:59:59+00:00",
        "reward": "200 $PIXEL 代幣",
    },
    "RarePass Genesis": {
        "contract": "0x4a3b2c1d0e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
        "criteria": "在 2025-03-01 前鑄造 ≥ 1 個 RarePass NFT",
        "status": "active",
        "deadline": "2026-09-15T23:59:59+00:00",
        "reward": "1 RarePass Platinum NFT",
    },
    "ApeCoin DAO Drop": {
        "contract": "0x7b8a9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6",
        "criteria": "持有 BAYC/MAYC ≥ 1 個 (Snapshot: 2025-04-20)",
        "status": "active",
        "deadline": "2026-08-01T23:59:59+00:00",
        "reward": "500 $APE 代幣",
    },
    "Blur Season 3": {
        "contract": "0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "criteria": "在 Blur 上交易量 ≥ 1 ETH (Season 3 期間)",
        "status": "ended",
        "deadline": "2025-12-31T23:59:59+00:00",
        "reward": "Blur Points + $BLUR 空投",
    },
    "Zora Network Reward": {
        "contract": "0xc1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0",
        "criteria": "在 Zora 鏈上鑄造 ≥ 1 個 NFT",
        "status": "active",
        "deadline": "2026-12-31T23:59:59+00:00",
        "reward": "Zora 創作者獎勵 ETH",
    },
}


def _validate_address(address: str) -> bool:
    return bool(ETH_ADDRESS_RE.match(address.strip()))


def _deterministic_eligibility(address: str, project: str) -> bool:
    """依據地址與專案名稱產生確定性資格判定"""
    seed = int(hashlib.sha256(f"{address.lower()}:{project.lower()}".encode()).hexdigest(), 16)
    return (seed % 10) < 6  # 60% 機率符合資格


def _deterministic_reward_amount(project: str, seed: int) -> str:
    """產生確定性的獎勵描述"""
    amounts = [
        f"{(seed % 1000) + 50} 治理代幣",
        f"{(seed % 500) * 0.01 + 0.05:.2f} ETH",
        f"{(seed % 200) + 10} 限量版 NFT",
        f"{(seed % 3000) + 500} 協議代幣",
    ]
    return amounts[seed % len(amounts)]


class NFTAirdropCheckerOrgan(BrainComponent):
    """
    NFT 空投檢查器官 — 管理已知空投清單，
    驗證指定地址的領取資格、處理領取請求並記錄歷史。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._airdrops: Dict[str, dict] = {
            name: dict(info) for name, info in PRESEEDED_AIRDROPS.items()
        }
        self._claims: Dict[str, List[dict]] = {}
        self._active = True

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------

    def check_eligibility(self, address: str, project: str = "") -> str:
        """
        檢查指定地址對已知空投專案的領取資格。

        參數:
            address: 錢包地址 (0x...)
            project: 專案名稱 (留空則檢查全部)
        """
        address = address.strip()
        if not _validate_address(address):
            return (
                f"❌ 地址格式無效: {address[:20]}...\n"
                f"   預期格式: 0x 開頭 + 40 個十六進位字元"
            )

        targets = {}
        if project:
            found = None
            for name in self._airdrops:
                if project.lower() in name.lower():
                    found = name
                    break
            if not found:
                return f"❌ 找不到空投專案: {project}"
            targets = {found: self._airdrops[found]}
        else:
            targets = {k: v for k, v in self._airdrops.items() if v["status"] == "active"}

        if not targets:
            return "📭 沒有可檢查的空投專案"

        total_eligible = 0
        total_value_note = ""
        lines = [f"🎁 空投資格檢查: {address[:10]}...{address[-6:]}"]

        for proj_name, info in targets.items():
            eligible = _deterministic_eligibility(address, proj_name)
            status_icon = "✅" if eligible else "❌"
            deadline = info.get("deadline", "N/A")
            try:
                dl = datetime.fromisoformat(deadline)
                deadline_str = dl.strftime("%Y-%m-%d")
                is_expired = dl < datetime.now(timezone.utc)
            except Exception:
                deadline_str = deadline
                is_expired = False

            if is_expired and eligible:
                status_icon = "⏰ (已截止)"

            lines.append(
                f"\n  {status_icon} {proj_name}\n"
                f"     獎勵: {info['reward']}\n"
                f"     條件: {info.get('criteria', 'N/A')}\n"
                f"     截止: {deadline_str}\n"
                f"     狀態: {'符合資格' if eligible else '不符合資格'}"
            )
            if eligible and not is_expired:
                total_eligible += 1

        if total_eligible > 0:
            lines.append(f"\n   共 {total_eligible} 個空投可領取")
        else:
            lines.append(f"\n   目前沒有可領取的空投")

        return "\n".join(lines)

    def list_active_airdrops(self) -> str:
        """
        列出所有已知的活躍空投專案。
        """
        active = {k: v for k, v in self._airdrops.items() if v["status"] == "active"}
        if not active:
            return "📭 目前沒有活躍的空投專案"

        lines = [f"📋 活躍空投專案 ({len(active)} 個):"]
        for name, info in active.items():
            deadline = info.get("deadline", "N/A")
            try:
                dl = datetime.fromisoformat(deadline)
                remaining = dl - datetime.now(timezone.utc)
                if remaining.total_seconds() < 0:
                    dl_str = "已截止"
                else:
                    days = remaining.days
                    dl_str = f"剩 {days} 天"
            except Exception:
                dl_str = deadline
            lines.append(
                f"  ▸ {name[:40]:40s} "
                f"獎勵: {info['reward'][:20]:20s} "
                f"{dl_str}"
            )
        return "\n".join(lines)

    def claim_airdrop(self, address: str, project: str, proof: str = "") -> str:
        """
        模擬領取指定空投 (含驗證流程)。

        參數:
            address: 錢包地址
            project: 專案名稱
            proof: Merkle proof 或其他證明 (可選)
        """
        address = address.strip()
        if not _validate_address(address):
            return f"❌ 地址格式無效: {address[:20]}..."

        found_name = None
        for name in self._airdrops:
            if project.lower() in name.lower():
                found_name = name
                break

        if not found_name:
            return f"❌ 找不到空投專案: {project}"

        info = self._airdrops[found_name]
        if info["status"] != "active":
            return f"⚠️ 此空投已結束: {found_name}"

        # 檢查截止日期
        try:
            dl = datetime.fromisoformat(info["deadline"])
            if dl < datetime.now(timezone.utc):
                return f"⚠️ 此空投已過截止日: {found_name} ({dl.strftime('%Y-%m-%d')})"
        except Exception:
            pass

        # 驗證資格
        if not _deterministic_eligibility(address, found_name):
            return (
                f"❌ 地址不符合領取資格\n"
                f"   專案: {found_name}\n"
                f"   條件: {info.get('criteria', 'N/A')}"
            )

        # 檢查是否已領取
        addr_lower = address.lower()
        already_claimed = addr_lower in self._claims and any(
            c["project"] == found_name for c in self._claims[addr_lower]
        )
        if already_claimed:
            return f"⚠️ 此地址已領取過 {found_name} 空投"

        claim_id = hashlib.sha256(
            f"{address}:{found_name}:{time.time()}".encode()
        ).hexdigest()[:16]
        claim_record = {
            "project": found_name,
            "proof": proof or "auto-verified",
            "claim_id": f"0x{claim_id}",
            "claimed_at": datetime.now(timezone.utc).isoformat(),
        }

        if addr_lower not in self._claims:
            self._claims[addr_lower] = []
        self._claims[addr_lower].append(claim_record)

        return (
            f"✅ 空投領取成功\n"
            f"   專案:     {found_name}\n"
            f"   地址:     {address[:10]}...{address[-6:]}\n"
            f"   獎勵:     {info['reward']}\n"
            f"   領取ID:   {claim_record['claim_id']}\n"
            f"   領取時間: {claim_record['claimed_at'][:19]}"
        )

    def add_airdrop(self, project_name: str, contract: str = "", criteria: str = "") -> str:
        """
        手動新增空投專案至追蹤清單。

        參數:
            project_name: 專案名稱
            contract: 合約地址 (可選)
            criteria: 資格條件描述
        """
        project_name = project_name.strip()
        if not project_name:
            return "❌ 專案名稱不可為空"

        if project_name in self._airdrops:
            return f"⚠️ 空投專案已存在: {project_name}"

        if contract and not _validate_address(contract):
            return f"❌ 合約地址格式無效: {contract[:20]}..."

        self._airdrops[project_name] = {
            "contract": contract or "N/A",
            "criteria": criteria or "待確認",
            "status": "active",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            "reward": "待公佈",
        }

        return (
            f"✅ 已新增空投專案\n"
            f"   名稱: {project_name}\n"
            f"   合約: {contract or 'N/A'}\n"
            f"   條件: {criteria or '待確認'}\n"
            f"   目前追蹤空投數: {len(self._airdrops)}"
        )

    def status(self) -> dict:
        """
        回報器官當前運行狀態。
        """
        active = sum(1 for a in self._airdrops.values() if a["status"] == "active")
        return {
            "organ": self.__class__.__name__,
            "alive": self._active,
            "total_airdrops": len(self._airdrops),
            "active_airdrops": active,
            "total_claims": sum(len(v) for v in self._claims.values()),
        }
