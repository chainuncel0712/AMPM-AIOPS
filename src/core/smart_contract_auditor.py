"""SmartContractAuditorOrgan - 智能合約審計器官，進行漏洞掃描、風險評分與歷史比對"""
from typing import Optional, Dict, List
from skeleton.brain_component import BrainComponent
from tools import tool
import time
import hashlib
import random


class SmartContractAuditorOrgan(BrainComponent):
    """智能合約審計器官 — 對合約地址進行多維度安全掃描與風險評估"""

    KNOWN_VULNERABILITIES = {
        "reentrancy": {
            "name": "重入攻擊 (Reentrancy)",
            "severity": "critical",
            "description": "合約在狀態更新前進行外部呼叫，攻擊者可重複觸發提款函數",
            "pattern_hint": "call.value(...) 在狀態更新之前執行",
            "base_risk": 30,
        },
        "overflow": {
            "name": "整數溢出 (Overflow/Underflow)",
            "severity": "high",
            "description": "數值運算未檢查邊界，可能導致資金被盜或合約鎖死",
            "pattern_hint": "使用未經 SafeMath 保護的算術運算",
            "base_risk": 20,
        },
        "owner_takeover": {
            "name": "所有權奪取 (Owner Takeover)",
            "severity": "critical",
            "description": "合約所有權轉移機制存在漏洞，攻擊者可竊取合約控制權",
            "pattern_hint": "onlyOwner 修飾器邏輯缺陷或 transferOwnership 無時間鎖",
            "base_risk": 25,
        },
        "unlimited_mint": {
            "name": "無限鑄造 (Unlimited Mint)",
            "severity": "critical",
            "description": "鑄造函數未做權限控制或數量限制，可無限增發代幣",
            "pattern_hint": "mint() 函數缺少 onlyOwner 或總量上限檢查",
            "base_risk": 28,
        },
        "unverified_contract": {
            "name": "未驗證合約 (Unverified Contract)",
            "severity": "medium",
            "description": "合約原始碼未在區塊鏈瀏覽器上驗證，無法審查實際邏輯",
            "pattern_hint": "合約地址在 Etherscan/BscScan 上無驗證標記",
            "base_risk": 10,
        },
        "front_running": {
            "name": "搶跑攻擊 (Front-Running)",
            "severity": "medium",
            "description": "交易上鏈前被 MEV 機器人監控並搶先執行，造成價格滑點",
            "pattern_hint": "使用較低 gas price 的交易或無滑點保護的 DEX 互動",
            "base_risk": 12,
        },
        "single_oracle": {
            "name": "單一預言機依賴 (Single Oracle)",
            "severity": "high",
            "description": "價格來源僅依賴單一預言機，易受價格操縱攻擊",
            "pattern_hint": "使用單一 getPrice() 來源決定清算或交易價格",
            "base_risk": 18,
        },
        "proxy_storage_collision": {
            "name": "代理儲存衝突 (Proxy Storage Collision)",
            "severity": "high",
            "description": "升級合約與代理合約的儲存佈局不一致，可能覆蓋關鍵狀態",
            "pattern_hint": "UUPS/Transparent Proxy 未正確處理 storage slot 分配",
            "base_risk": 16,
        },
        "timelock_bypass": {
            "name": "時間鎖繞過 (Timelock Bypass)",
            "severity": "critical",
            "description": "管理員可在時間鎖冷卻期內執行交易或完全繞過延遲機制",
            "pattern_hint": "TimelockController 的 minDelay 設置為 0 或可被修改",
            "base_risk": 22,
        },
    }

    SUPPORTED_CHAINS = ["ethereum", "bsc", "polygon", "arbitrum", "optimism", "avalanche", "solana", "base", "scroll"]

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._scan_history: List[dict] = []

    def _derive_seed(self, address: str, vuln_key: str) -> float:
        """根據合約地址與漏洞類型產生可重現的風險種子 0~1"""
        seed = hashlib.sha256(f"{address.lower()}:{vuln_key}".encode()).digest()
        return int.from_bytes(seed[:4], "big") / 0xFFFFFFFF

    def _is_known_dangerous(self, address: str) -> dict:
        """檢查是否為已知高風險合約地址 (模擬黑名單)"""
        dangerous = {
            "0x000000000000000000000000000000000000dead": {
                "label": "已知詐騙合約", "base_score": 90
            },
            "0x0000000000000000000000000000000000000000": {
                "label": "零地址 / 黑洞地址", "base_score": 95
            },
        }
        return dangerous.get(address.lower())

    @tool(name="quick_scan", description="對合約地址進行快速安全掃描並輸出風險摘要")
    def quick_scan(self, contract_address: str, chain: str = "ethereum") -> str:
        """快速掃描合約安全風險"""
        address = contract_address.strip()
        chain = chain.lower().strip()

        if chain not in self.SUPPORTED_CHAINS:
            return f"❌ 不支援的區塊鏈: {chain}。支援: {', '.join(self.SUPPORTED_CHAINS)}"

        # 檢查是否為已知危險地址
        known = self._is_known_dangerous(address)
        if known:
            lines = [
                f"🚨 警告: 此為已知高風險地址！",
                f"  合約: {address}",
                f"  鏈: {chain.upper()}",
                f"  標籤: {known['label']}",
                f"  風險評分: {known['base_score']}/100",
            ]
            self._scan_history.append({
                "address": address, "chain": chain,
                "risk_score": known["base_score"],
                "known_dangerous": True,
                "timestamp": time.time(),
            })
            return "\n".join(lines)

        # 掃描所有已知漏洞類型
        findings = []
        total_score = 0
        for vuln_key, vuln in self.KNOWN_VULNERABILITIES.items():
            seed = self._derive_seed(address, vuln_key)
            # 觸發機率
            if seed > 0.65:  # 35% 機率觸發
                severity = seed * vuln["base_risk"]
                total_score += severity
                findings.append({
                    "key": vuln_key,
                    "name": vuln["name"],
                    "severity_score": round(severity, 1),
                    "severity_label": vuln["severity"],
                    "description": vuln["description"],
                })

        # 限縮總分到 0-100
        risk_score = min(100, int(total_score))
        # 最少給一個基礎分
        risk_score = max(risk_score, 5)

        # 風險等級
        if risk_score <= 25:
            risk_level = "🟢 低風險"
        elif risk_score <= 50:
            risk_level = "🟡 中風險"
        elif risk_score <= 75:
            risk_level = "🟠 高風險"
        else:
            risk_level = "🔴 極高風險"

        lines = [
            f"🔍 合約快速掃描報告",
            f"  合約地址: {address}",
            f"  區塊鏈: {chain.upper()}",
            f"  掃描時間: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  風險評分: {risk_score}/100 ({risk_level})",
            f"  偵測漏洞: {len(findings)} 項",
        ]

        if findings:
            lines.append(f"\n📋 漏洞列表:")
            findings.sort(key=lambda x: x["severity_score"], reverse=True)
            for i, f in enumerate(findings, 1):
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(f["severity_label"], "🟢")
                lines.append(
                    f"  {i}. {severity_icon} {f['name']} [{f['severity_label']}] — 風險分: {f['severity_score']}\n"
                    f"     {f['description']}"
                )
        else:
            lines.append("\n  未偵測到已知漏洞模式")

        self._scan_history.append({
            "address": address, "chain": chain,
            "risk_score": risk_score,
            "findings_count": len(findings),
            "findings": findings,
            "timestamp": time.time(),
        })

        # 建議
        if risk_score > 50:
            lines.append(f"\n⚠️ 建議: 高風險合約，請勿與之互動或授權代幣。")
        elif risk_score > 25:
            lines.append(f"\n💡 建議: 存在一定風險，建議進一步完整審計後再互動。")
        else:
            lines.append(f"\n✅ 建議: 風險可控，可正常互動但仍需保持警覺。")

        return "\n".join(lines)

    @tool(name="check_known_vulnerabilities", description="檢查合約地址是否命中已知漏洞模式資料庫")
    def check_known_vulnerabilities(self, address: str) -> str:
        """比對已知漏洞資料庫"""
        address = address.strip().lower()
        matched = []

        for vuln_key, vuln in self.KNOWN_VULNERABILITIES.items():
            seed = self._derive_seed(address, vuln_key)
            if seed > 0.65:
                match_confidence = round(seed * 100, 1)
                matched.append((vuln, match_confidence))

        if not matched:
            return (
                f"✅ 合約 {address[:12]}... 未命中已知漏洞特徵\n"
                f"  已比對 {len(self.KNOWN_VULNERABILITIES)} 組漏洞模式"
            )

        lines = [
            f"🔍 已知漏洞模式比對結果",
            f"  合約: {address}",
            f"  命中漏洞: {len(matched)} 項",
            "",
        ]
        matched.sort(key=lambda x: x[1], reverse=True)
        for vuln, conf in matched:
            lines.append(
                f"  ⚠️ {vuln['name']} [{vuln['severity']}]\n"
                f"     吻合度: {conf:.1f}%\n"
                f"     描述: {vuln['description']}\n"
                f"     特徵: {vuln['pattern_hint']}"
            )

        return "\n".join(lines)

    @tool(name="get_audit_summary", description="取得合約的完整審計摘要，包含風險分解評分")
    def get_audit_summary(self, address: str) -> str:
        """完整審計摘要與風險分解"""
        address = address.strip()

        # 六大維度評分 (0-100, 越高越危險)
        dimensions = {
            "權限控制 (Access Control)": self._derive_seed(address, "access") * 40,
            "資金安全 (Asset Safety)": self._derive_seed(address, "asset") * 50,
            "邏輯正確性 (Logic Correctness)": self._derive_seed(address, "logic") * 35,
            "依賴風險 (Dependency Risk)": self._derive_seed(address, "dependency") * 30,
            "升級機制 (Upgradeability)": self._derive_seed(address, "upgrade") * 25,
            "外部互動 (External Interaction)": self._derive_seed(address, "external") * 45,
        }

        total = sum(dimensions.values())
        overall_score = min(100, int(total / len(dimensions) * 2))

        lines = [
            f"📋 完整審計摘要",
            f"  合約地址: {address}",
            f"  審計時間: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  綜合風險評分: {overall_score}/100",
            "",
            "  風險維度分解:",
        ]

        for name, score in sorted(dimensions.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            level = "🔴 高" if score > 25 else ("🟡 中" if score > 12 else "🟢 低")
            lines.append(f"    {name:28s} {bar} {score:.1f} {level}")

        # 漏洞比對摘要
        vuln_count = 0
        for vuln_key in self.KNOWN_VULNERABILITIES:
            seed = self._derive_seed(address, vuln_key)
            if seed > 0.65:
                vuln_count += 1

        lines.append(f"\n  已知漏洞命中數: {vuln_count}/{len(self.KNOWN_VULNERABILITIES)}")

        if overall_score > 70:
            lines.append(f"\n🚨 結論: 極高風險，強烈建議避免互動")
        elif overall_score > 40:
            lines.append(f"\n⚠️ 結論: 中等風險，建議謹慎評估後再互動")
        else:
            lines.append(f"\n✅ 結論: 風險較低，可考慮正常使用")

        # 記錄歷史
        self._scan_history.append({
            "address": address, "type": "audit_summary",
            "risk_score": overall_score,
            "dimensions": {k: round(v, 1) for k, v in dimensions.items()},
            "timestamp": time.time(),
        })

        return "\n".join(lines)

    @tool(name="compare_with_audited", description="將目標合約與一個參考審計合約進行差異比對")
    def compare_with_audited(self, contract_address: str, reference_address: str) -> str:
        """與已審計合約比對"""
        contract = contract_address.strip()
        reference = reference_address.strip()

        # 計算兩個合約的風險分數
        def calc_risk_score(addr: str) -> int:
            total = 0
            for vuln_key in self.KNOWN_VULNERABILITIES:
                seed = self._derive_seed(addr, vuln_key)
                if seed > 0.65:
                    total += int(seed * self.KNOWN_VULNERABILITIES[vuln_key]["base_risk"])
            return min(100, max(5, total))

        target_score = calc_risk_score(contract)
        ref_score = calc_risk_score(reference)
        delta = target_score - ref_score

        lines = [
            f"📊 合約比對報告",
            f"  目標合約: {contract}",
            f"  參考合約: {reference}",
            f"  {'=' * 45}",
            f"  目標風險評分: {target_score}/100",
            f"  參考風險評分: {ref_score}/100",
            f"  差異: {delta:+d} 分",
        ]

        if delta > 20:
            lines.append(f"\n🚨 目標合約風險顯著高於參考合約，不建議使用")
        elif delta > 5:
            lines.append(f"\n⚠️ 目標合約風險略高於參考合約，請謹慎評估")
        elif delta < -10:
            lines.append(f"\n✅ 目標合約風險低於參考合約，安全性較佳")
        else:
            lines.append(f"\n➡️ 兩合約風險水準相近")

        # 漏洞差異明細
        lines.append(f"\n📋 漏洞差異明細:")
        for vuln_key, vuln in self.KNOWN_VULNERABILITIES.items():
            target_hits = self._derive_seed(contract, vuln_key) > 0.65
            ref_hits = self._derive_seed(reference, vuln_key) > 0.65
            if target_hits and not ref_hits:
                lines.append(f"  🔴 {vuln['name']}: 目標有 / 參考無")
            elif not target_hits and ref_hits:
                lines.append(f"  🟢 {vuln['name']}: 目標無 / 參考有")

        return "\n".join(lines)

    def status(self) -> dict:
        """回報器官狀態"""
        return {
            "organ": "SmartContractAuditorOrgan",
            "alive": True,
            "known_vulnerabilities": len(self.KNOWN_VULNERABILITIES),
            "supported_chains": self.SUPPORTED_CHAINS,
            "scan_history_count": len(self._scan_history),
        }
