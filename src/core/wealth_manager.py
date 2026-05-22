"""WealthManagerOrgan — 財富管理引擎，負責儲蓄管理、投資追蹤、資產配置與財務規劃。"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Tuple

from skeleton.brain_component import BrainComponent
from tools import tool

ACCOUNT_TYPES: Dict[str, Dict[str, Any]] = {
    "savings": {
        "name": "儲蓄帳戶",
        "asset_class": "現金等價物",
        "liquidity": "高 (即時)",
        "risk_level": "極低",
        "typical_apy_range": (0.01, 2.0),
    },
    "checking": {
        "name": "活期帳戶",
        "asset_class": "現金等價物",
        "liquidity": "高 (即時)",
        "risk_level": "極低",
        "typical_apy_range": (0.0, 0.1),
    },
    "fixed_deposit": {
        "name": "定期存款",
        "asset_class": "固定收益",
        "liquidity": "低 (鎖倉)",
        "risk_level": "極低",
        "typical_apy_range": (2.0, 6.0),
    },
    "stocks": {
        "name": "股票",
        "asset_class": "股票",
        "liquidity": "高 (T+2)",
        "risk_level": "中高",
        "typical_apy_range": (-30.0, 40.0),
    },
    "crypto": {
        "name": "加密貨幣",
        "asset_class": "數位資產",
        "liquidity": "高 (即時)",
        "risk_level": "極高",
        "typical_apy_range": (-90.0, 300.0),
    },
    "etf": {
        "name": "ETF",
        "asset_class": "多元資產",
        "liquidity": "高 (T+2)",
        "risk_level": "中",
        "typical_apy_range": (-20.0, 30.0),
    },
    "bonds": {
        "name": "債券",
        "asset_class": "固定收益",
        "liquidity": "中",
        "risk_level": "低",
        "typical_apy_range": (2.0, 8.0),
    },
}

ALLOCATION_MODELS: Dict[str, Dict[str, float]] = {
    "conservative": {
        "savings": 0.60,
        "bonds": 0.20,
        "stocks": 0.10,
        "crypto": 0.10,
    },
    "moderate": {
        "savings": 0.40,
        "bonds": 0.20,
        "stocks": 0.20,
        "crypto": 0.20,
    },
    "aggressive": {
        "savings": 0.10,
        "bonds": 0.10,
        "stocks": 0.40,
        "crypto": 0.40,
    },
}

ASSET_CLASS_MAP: Dict[str, str] = {
    "savings": "現金等價物",
    "checking": "現金等價物",
    "fixed_deposit": "固定收益",
    "stocks": "股票",
    "crypto": "數位資產",
    "etf": "多元資產",
    "bonds": "固定收益",
}


def _make_account_id(name: str, atype: str) -> str:
    """為帳戶產生唯一識別碼。"""
    raw = f"{name}|{atype}|{datetime.now(timezone.utc).isoformat()}".encode("utf-8")
    return "acct_" + hashlib.sha256(raw).hexdigest()[:12]


def _compound_interest(principal: float, apy_percent: float, days: float) -> float:
    """計算複利終值。

    公式: A = P * (1 + r/n)^(n*t)
    此處使用連續複利近似: A = P * e^(r*t)
    其中 r = APY 日利率，t = 天數。

    參數：
        principal: 本金
        apy_percent: 年化收益率 (百分比)
        days: 持有天數
    """
    if days <= 0:
        return principal
    daily_rate = apy_percent / 100.0 / 365.0
    return principal * math.exp(daily_rate * days)


def _dca_purchase_amount(total_amount: float, frequency: str, duration_months: int) -> Tuple[float, int]:
    """計算 DCA 每期投入金額與總期數。

    參數：
        total_amount: 總投資金額
        frequency: 頻率 (daily / weekly / biweekly / monthly)
        duration_months: 投資期間 (月)
    """
    frequency_map = {
        "daily": 30,
        "weekly": 4,
        "biweekly": 2,
        "monthly": 1,
    }
    freq_lower = frequency.strip().lower()
    if freq_lower not in frequency_map:
        raise ValueError(f"不支援的頻率: {frequency}，可用: daily, weekly, biweekly, monthly")

    periods_per_month = frequency_map[freq_lower]
    total_periods = int(duration_months * periods_per_month)
    if total_periods <= 0:
        raise ValueError(f"投資期間需產生至少 1 期，目前: {total_periods} 期")

    per_purchase = total_amount / total_periods
    return per_purchase, total_periods


class WealthManagerOrgan(BrainComponent):
    """財富管理引擎 — 管理多帳戶資產、計算淨值、
    提供資產配置建議、DCA 計劃與緊急預備金檢查。"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__()
        self.dna = dna or {}
        self._accounts: Dict[str, dict] = {}
        self._history: List[dict] = []
        self._monthly_expenses: float = 0.0
        self._active = True

    def _get_account(self, account_name: str) -> Optional[dict]:
        """按名稱查詢帳戶。"""
        for acct_id, acct in self._accounts.items():
            if acct["name"].lower() == account_name.strip().lower():
                return acct
        return None

    @tool
    def set_monthly_expenses(self, amount: float) -> str:
        """
        設定每月開支。

        設定每月生活費用估算，此數值將用於緊急預備金
        檢查與儲蓄率計算。

        參數：
            amount: 每月開支金額
        """
        if amount < 0:
            return "❌ 每月開支不可為負數"
        self._monthly_expenses = amount
        return (
            f"💰 每月生活開支已設定: ${amount:,.2f}\n"
            f"   6 個月緊急預備金目標: ${amount * 6:,.2f}"
        )

    @tool
    def add_account(self, name: str, account_type: str, balance: float, currency: str = "USD", apy: float = 0.0) -> str:
        """
        新增帳戶。

        將儲蓄、投資或理財帳戶加入財富管理系統，
        支援存款、股票、加密貨幣、ETF、債券等類型。

        參數：
            name: 帳戶名稱
            account_type: 帳戶類型 (savings / checking / fixed_deposit / stocks / crypto / etf / bonds)
            balance: 帳戶餘額
            currency: 貨幣代碼 (預設 USD)
            apy: 年化收益率百分比 (如 4.5 表示 4.5%)
        """
        atype = account_type.strip().lower()
        if atype not in ACCOUNT_TYPES:
            valid = ", ".join(ACCOUNT_TYPES.keys())
            return f"❌ 不支援的帳戶類型: '{account_type}'，可用: {valid}"

        if balance < 0:
            return "❌ 帳戶餘額不可為負數"

        acct_id = _make_account_id(name, atype)
        now = datetime.now(timezone.utc).isoformat()

        self._accounts[acct_id] = {
            "name": name.strip(),
            "type": atype,
            "type_display": ACCOUNT_TYPES[atype]["name"],
            "asset_class": ASSET_CLASS_MAP[atype],
            "balance": balance,
            "currency": currency.strip().upper(),
            "apy": apy,
            "created_at": now,
            "last_updated": now,
        }

        return (
            f"✅ 已新增 {ACCOUNT_TYPES[atype]['name']}: {name}\n"
            f"   帳戶編號: {acct_id}\n"
            f"   類型: {ACCOUNT_TYPES[atype]['name']} ({ACCOUNT_TYPES[atype]['asset_class']})\n"
            f"   餘額: {balance:,.2f} {currency.upper()}\n"
            f"   年化收益率: {apy:.2f}%\n"
            f"   風險等級: {ACCOUNT_TYPES[atype]['risk_level']}\n"
            f"   流動性: {ACCOUNT_TYPES[atype]['liquidity']}\n"
            f"   創建時間: {now[:19]}\n"
            f"   總管理帳戶數: {len(self._accounts)}"
        )

    @tool
    def calculate_net_worth(self) -> str:
        """
        計算淨資產。

        彙總所有帳戶的當前餘額，計算總淨資產，
        並按資產類別（現金等價物、固定收益、股票、數位資產、多元資產）
        進行分類明細。
        """
        if not self._accounts:
            return "📭 目前沒有任何帳戶，請先使用 add_account 新增"

        total_net_worth = 0.0
        class_breakdown: Dict[str, float] = {}
        account_details: List[dict] = []

        for acct_id, acct in self._accounts.items():
            balance = acct["balance"]
            asset_class = acct["asset_class"]
            total_net_worth += balance
            class_breakdown[asset_class] = class_breakdown.get(asset_class, 0.0) + balance
            account_details.append({
                "id": acct_id,
                "name": acct["name"],
                "type": acct["type_display"],
                "balance": balance,
                "currency": acct["currency"],
                "apy": acct["apy"],
                "class": asset_class,
            })

        lines = [
            "╔═══════════════════════════════════╗",
            "║     💰 淨資產總覽                ║",
            "╚═══════════════════════════════════╝",
            "",
            f"📊 總淨資產: ${total_net_worth:,.2f}",
            f"   管理帳戶數: {len(self._accounts)} 個",
            f"   報表時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "─" * 42,
            "📂 按資產類別分佈:",
            "─" * 42,
        ]

        class_order = ["現金等價物", "固定收益", "股票", "多元資產", "數位資產"]
        for cls in class_order:
            val = class_breakdown.get(cls, 0.0)
            if val > 0:
                pct = (val / total_net_worth * 100) if total_net_worth > 0 else 0
                bar_len = int(pct / 5)
                bar = "█" * bar_len
                lines.append(f"  {cls:12s}: ${val:>12,.2f}  ({pct:5.1f}%)  {bar}")

        other_classes = [c for c in class_breakdown if c not in class_order]
        if other_classes:
            lines.append("  ─ 其他類別 ─")
            for cls in other_classes:
                val = class_breakdown[cls]
                pct = (val / total_net_worth * 100) if total_net_worth > 0 else 0
                lines.append(f"  {cls:12s}: ${val:>12,.2f}  ({pct:5.1f}%)")

        lines.append("")
        lines.append("─" * 42)
        lines.append("📋 帳戶明細:")
        lines.append("─" * 42)
        for acct in sorted(account_details, key=lambda a: a["balance"], reverse=True):
            lines.append(
                f"  [{acct['id']}] {acct['name']:15s} | {acct['type']:6s} | "
                f"${acct['balance']:>12,.2f} {acct['currency']:4s} | "
                f"APY {acct['apy']:>5.1f}%"
            )

        if self._monthly_expenses > 0:
            months_of_expenses = total_net_worth / self._monthly_expenses
            lines.append("")
            lines.append(f"🛡️ 緊急預備金覆蓋: {months_of_expenses:.1f} 個月 (目標 ≥ 6 個月)")
            if months_of_expenses < 6:
                shortfall = self._monthly_expenses * 6 - total_net_worth
                lines.append(f"   ⚠️ 短缺 ${shortfall:,.2f}")

        return "\n".join(lines)

    @tool
    def track_interest(self, account_name: str) -> str:
        """
        追蹤利息收益。

        根據帳戶 APY 與創建迄今的時間計算已累積利息。
        對於加密貨幣帳戶，額外計算質押獎勵。

        參數：
            account_name: 帳戶名稱
        """
        acct = self._get_account(account_name)
        if not acct:
            return f"❌ 找不到帳戶: {account_name}"

        bal = acct["balance"]
        apy = acct["apy"]
        atype = acct["type"]

        created_str = acct["created_at"]
        try:
            created_dt = datetime.fromisoformat(created_str)
        except Exception:
            return f"❌ 無法解析帳戶創建時間: {created_str}"

        now = datetime.now(timezone.utc)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        days_held = (now - created_dt).total_seconds() / 86400.0

        if apy > 0:
            future_value = _compound_interest(bal, apy, days_held)
            interest_earned = future_value - bal
        else:
            future_value = bal
            interest_earned = 0.0

        effective_apy = ((future_value / bal) ** (365.0 / max(days_held, 1)) - 1) * 100 if bal > 0 and days_held > 0 else 0.0

        lines = [
            f"📈 {acct['name']} 利息追蹤",
            f"   帳戶類型: {acct['type_display']}",
            f"   資產類別: {acct['asset_class']}",
            f"   本金: ${bal:,.2f} {acct['currency']}",
            f"   年化 APY: {apy:.2f}%",
            f"   持有天數: {days_held:.0f} 天",
            f"   累計利息: ${interest_earned:,.2f}",
            f"   當前終值: ${future_value:,.2f}",
            f"   實際年化報酬: {effective_apy:.2f}%",
        ]

        if atype == "crypto":
            staking_reward_rate = apy * 0.5 if apy > 0 else 2.0
            staking_value = _compound_interest(bal, staking_reward_rate, days_held)
            staking_earned = staking_value - bal
            lines.append("")
            lines.append("🪙 加密貨幣質押獎勵 (額外):")
            lines.append(f"   質押 APY: {staking_reward_rate:.2f}%")
            lines.append(f"   質押收益: ${staking_earned:,.2f}")
            lines.append(f"   含質押總值: ${future_value + staking_earned:,.2f}")

        if apy == 0:
            lines.append("")
            lines.append("💡 該帳戶 APY 為 0，無利息收入。考慮將資金轉入高收益帳戶。")

        return "\n".join(lines)

    @tool
    def suggest_allocation(self, risk_level: str) -> str:
        """
        資產配置建議。

        根據保守、穩健或積極三種風險偏好，
        產出建議的資產配置比例與具體金額。

        參數：
            risk_level: 風險等級 (conservative / moderate / aggressive)
        """
        rl = risk_level.strip().lower()
        valid_levels = list(ALLOCATION_MODELS.keys())
        if rl not in ALLOCATION_MODELS:
            return f"❌ 不支援的風險等級: {risk_level}，可用: {', '.join(valid_levels)}"

        allocation = ALLOCATION_MODELS[rl]
        total_balance = sum(a["balance"] for a in self._accounts.values())

        risk_labels = {
            "conservative": "保守型",
            "moderate": "穩健型",
            "aggressive": "積極型",
        }

        lines = [
            f"⚖️ 資產配置建議 — {risk_labels[rl]} ({rl})",
            f"   當前總資產: ${total_balance:,.2f}",
            f"",
            f"   目標配置:",
        ]

        for atype, target_pct in allocation.items():
            target_amount = total_balance * target_pct
            type_info = ACCOUNT_TYPES.get(atype, {})
            type_name = type_info.get("name", atype)

            current_in_type = sum(
                a["balance"] for a in self._accounts.values()
                if a["type"] == atype or (atype == "savings" and a["type"] in ("savings", "checking"))
            )
            current_pct = (current_in_type / total_balance * 100) if total_balance > 0 else 0
            diff = target_amount - current_in_type

            if abs(diff) < 1:
                action = "✅ 已達標"
            elif diff > 0:
                action = f"📥 需增加 ${diff:,.2f}"
            else:
                action = f"📤 建議減少 ${abs(diff):,.2f}"

            bar = "█" * int(target_pct * 100 / 5) + "░" * (20 - int(target_pct * 100 / 5))
            lines.append(f"  {type_name:10s}: {bar} {target_pct:.0%}")
            lines.append(f"    → 目標金額: ${target_amount:>12,.2f} | 當前: ${current_in_type:>12,.2f} ({current_pct:.1f}%) | {action}")

        lines.append("")
        lines.append("📊 配置策略說明:")

        strategy_notes = {
            "conservative": [
                "保本為首要目標，追求穩定現金流",
                "大量配置現金與固定收益，適合退休或短期目標",
                "加密貨幣僅作小額配置，不影響整體穩定性",
                "年化波動度預估: 3%-8%",
            ],
            "moderate": [
                "在增長與安全之間平衡",
                "股債平衡配置，兼顧收益與風險",
                "加密貨幣作為增長催化劑",
                "年化波動度預估: 10%-20%",
            ],
            "aggressive": [
                "追求最大資本增長，承受較大波動",
                "高比例股票與加密貨幣配置",
                "適合長期投資者與風險承受度高的個人",
                "年化波動度預估: 25%-60%",
            ],
        }

        for note in strategy_notes.get(rl, []):
            lines.append(f"  • {note}")

        if total_balance == 0:
            lines.append("")
            lines.append("⚠️  當前無資產，請先使用 add_account 建立帳戶")

        return "\n".join(lines)

    @tool
    def dca_plan(self, asset: str, total_amount: float, frequency: str, duration_months: int) -> str:
        """
        DCA 投資計劃。

        計算定期定額投資計劃，包含每期投入金額、
        期數總覽與不同年化報酬情境下的預估終值。

        參數：
            asset: 投資標的名稱
            total_amount: 總投資金額
            frequency: 投入頻率 (daily / weekly / biweekly / monthly)
            duration_months: 投資期間 (月)
        """
        if total_amount <= 0:
            return "❌ 總投資金額必須大於 0"
        if duration_months <= 0:
            return "❌ 投資期間月數必須大於 0"

        try:
            per_purchase, total_periods = _dca_purchase_amount(total_amount, frequency, duration_months)
        except ValueError as e:
            return f"❌ {e}"

        freq_map = {
            "daily": ("每天", 365),
            "weekly": ("每週", 52),
            "biweekly": ("每雙週", 26),
            "monthly": ("每月", 12),
        }
        freq_label, freq_per_year = freq_map[frequency.strip().lower()]

        scenario_returns = [(-10, "熊市"), (0, "持平"), (10, "溫和牛市"), (30, "強勢牛市"), (100, "極端牛市")]

        lines = [
            f"📊 DCA 投資計劃: {asset}",
            f"",
            f"   總投資金額: ${total_amount:,.2f}",
            f"   投入頻率: {freq_label}",
            f"   投資期間: {duration_months} 個月",
            f"   總期數: {total_periods} 期",
            f"   每期投入: ${per_purchase:,.2f}",
            f"",
            "─" * 42,
            "📈 情竇模擬 — 不同年化報酬率下的終值:",
            "─" * 42,
        ]

        monthly_rate = per_purchase * (freq_per_year / 12)
        for ann_return, scenario_name in scenario_returns:
            period_rate = ann_return / 100.0 / freq_per_year
            if period_rate == 0:
                fv = per_purchase * total_periods
                formula = "本金總和 (0% 增長)"
            else:
                fv = per_purchase * ((1 + period_rate) ** total_periods - 1) / period_rate
                formula = f"FV = PMT × [(1+r)^{total_periods} - 1] / r"

            total_return = fv - total_amount
            return_pct = (total_return / total_amount * 100) if total_amount > 0 else 0
            emoji = "🟢" if return_pct > 0 else ("🔴" if return_pct < 0 else "🟡")

            lines.append(
                f"  {emoji} {scenario_name:8s} ({ann_return:+3d}% APR): "
                f"終值 ${fv:>12,.2f}  |  總報酬 {total_return:>+10,.2f} ({return_pct:+.1f}%)"
            )

        lines.append("")
        lines.append("─" * 42)
        lines.append("📋 執行計劃時間表:")
        lines.append("─" * 42)

        today = datetime.now(timezone.utc)
        for i in range(min(total_periods, 10)):
            period_days = int(30 / (freq_per_year / 12.0) * (i + 1))
            purchase_date = (today + timedelta(days=period_days)).strftime("%Y-%m-%d")
            cumulative = per_purchase * (i + 1)
            lines.append(f"  第 {i + 1:4d} 期 | {purchase_date} | 投入 ${per_purchase:,.2f} | 累計 ${cumulative:,.2f}")

        if total_periods > 10:
            lines.append(f"  ... 共 {total_periods} 期 ...")
            final_date = (today + timedelta(days=int(30 * duration_months))).strftime("%Y-%m-%d")
            lines.append(f"  最終期 ({total_periods}) | {final_date} | 累計 ${total_amount:,.2f}")

        lines.append("")
        lines.append("💡 DCA 策略優點:")
        lines.append("  • 平滑市場波動，降低擇時風險")
        lines.append("  • 紀律投資，避免情緒化交易")
        lines.append("  • 長期執行，利用複利效應")
        lines.append("  • 無需大量資本即可開始")

        return "\n".join(lines)

    @tool
    def emergency_fund_check(self) -> str:
        """
        緊急預備金檢查。

        計算所有高流動性資產（儲蓄、活期帳戶），
        對比 6 個月生活開支目標，產出短缺報告。
        """
        if self._monthly_expenses <= 0:
            return (
                "⚠️ 尚未設定每月開支\n"
                "   請先使用 set_monthly_expenses 設定後再檢查"
            )

        liquid_balance = sum(
            a["balance"] for a in self._accounts.values()
            if a["type"] in ("savings", "checking")
        )

        target_6m = self._monthly_expenses * 6
        target_3m = self._monthly_expenses * 3
        shortfall = target_6m - liquid_balance
        months_covered = liquid_balance / self._monthly_expenses

        if months_covered >= 6:
            status = "✅ 充足"
            emoji = "🟢"
        elif months_covered >= 3:
            status = "🟡 接近達標"
            emoji = "🟡"
        else:
            status = "🔴 不足"
            emoji = "🔴"

        lines = [
            f"🛡️ {emoji} 緊急預備金檢查",
            f"",
            f"   每月生活開支: ${self._monthly_expenses:,.2f}",
            f"   6 個月目標: ${target_6m:,.2f}",
            f"   3 個月最低: ${target_3m:,.2f}",
            f"",
            "─" * 42,
            f"   高流動性資產 (儲蓄 + 活期):",
            f"   目前金額: ${liquid_balance:,.2f}",
            f"   覆蓋月數: {months_covered:.1f} 個月",
            f"",
            f"   狀態: {status}",
        ]

        if shortfall > 0:
            lines.append(f"   短缺金額: ${shortfall:,.2f}")
            lines.append("")
            lines.append("📋 達成目標建議:")
            monthly_savings_needed_12m = shortfall / 12
            lines.append(f"   • 若 12 個月內達標: 每月需儲蓄 ${monthly_savings_needed_12m:,.2f}")
            monthly_savings_needed_6m = shortfall / 6
            lines.append(f"   • 若 6 個月內達標: 每月需儲蓄 ${monthly_savings_needed_6m:,.2f}")
            lines.append(f"   • 削減非必要開支以加速累積")
            lines.append(f"   • 將部分低流動性資產轉為高流動性")
        else:
            surplus = liquid_balance - target_6m
            lines.append(f"   超額儲備: ${surplus:,.2f}")
            lines.append("")
            lines.append("💡 建議:")
            lines.append(f"   • 可將超額 ${surplus:,.2f} 配置到投資帳戶以獲得更高收益")
            lines.append(f"   • 將部分資金轉入定期存款或 ETF")

        return "\n".join(lines)

    @tool
    def monthly_snapshot(self) -> str:
        """
        月度淨值快照。

        擷取當前所有帳戶淨值的時間戳記快照，
        儲存於歷史記錄中以供長期趨勢分析。
        """
        total_net_worth = sum(a["balance"] for a in self._accounts.values())
        total_interest_earning = sum(a["balance"] for a in self._accounts.values() if a["apy"] > 0)
        total_non_interest = sum(a["balance"] for a in self._accounts.values() if a["apy"] == 0)

        now = datetime.now(timezone.utc)
        snapshot = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m"),
            "net_worth": total_net_worth,
            "account_count": len(self._accounts),
            "interest_earning_balance": total_interest_earning,
            "non_interest_balance": total_non_interest,
            "monthly_expenses": self._monthly_expenses,
        }

        per_type = {}
        for a in self._accounts.values():
            atype = a["type"]
            per_type[atype] = per_type.get(atype, 0.0) + a["balance"]
        snapshot["breakdown_by_type"] = per_type

        self._history.append(snapshot)

        lines = [
            f"📸 月度淨值快照 — {now.strftime('%Y年%m月')}",
            f"",
            f"   快照時間: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"   總淨資產: ${total_net_worth:,.2f}",
            f"   帳戶總數: {len(self._accounts)}",
            f"   生息資產: ${total_interest_earning:,.2f}",
            f"   非生息資產: ${total_non_interest:,.2f}",
            f"",
            "   按帳戶類型細分:",
        ]

        for atype, amt in sorted(per_type.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total_net_worth * 100) if total_net_worth > 0 else 0
            type_name = ACCOUNT_TYPES.get(atype, {}).get("name", atype)
            lines.append(f"     {type_name}: ${amt:,.2f} ({pct:.1f}%)")

        lines.append("")
        if self._monthly_expenses > 0:
            months_cov = total_net_worth / self._monthly_expenses
            savings_rate = self._monthly_expenses / (total_net_worth + self._monthly_expenses) * 100 if total_net_worth > 0 else 0
            lines.append(f"   緊急預備金覆蓋: {months_cov:.1f} 個月")
            lines.append(f"   月度提取率: {savings_rate:.1f}%")

        lines.append("")
        lines.append(f"📈 歷史快照總數: {len(self._history)}")

        if len(self._history) >= 2:
            prev = self._history[-2]["net_worth"]
            change = total_net_worth - prev
            change_pct = (change / prev * 100) if prev > 0 else 0
            emoji = "🟢" if change >= 0 else "🔴"
            lines.append(f"   {emoji} 較上月變化: {change:+,.2f} ({change_pct:+.2f}%)")

            months_ago_6 = max(0, len(self._history) - 6)
            if months_ago_6 < len(self._history):
                prev_6m = self._history[months_ago_6]["net_worth"]
                change_6m = total_net_worth - prev_6m
                change_6m_pct = (change_6m / prev_6m * 100) if prev_6m > 0 else 0
                lines.append(f"   📅 較 6 個月前變化: {change_6m:+,.2f} ({change_6m_pct:+.2f}%)")

        return "\n".join(lines)

    def get_history(self) -> List[dict]:
        """取得歷史快照清單。"""
        return list(self._history)

    def get_accounts(self) -> Dict[str, dict]:
        """取得所有帳戶字典。"""
        return dict(self._accounts)

    def status(self) -> dict:
        """回報財富管理引擎當前運行狀態。"""
        total_net_worth = sum(a["balance"] for a in self._accounts.values())
        months_covered = 0.0
        savings_rate = 0.0
        if self._monthly_expenses > 0:
            months_covered = total_net_worth / self._monthly_expenses
            savings_rate = (total_net_worth / (total_net_worth + self._monthly_expenses * 12)) * 100 if total_net_worth > 0 else 0

        return {
            "name": "WealthManagerOrgan",
            "alive": self._active,
            "accounts": len(self._accounts),
            "total_net_worth": total_net_worth,
            "monthly_savings_rate": round(savings_rate, 2),
            "emergency_fund_months": round(months_covered, 1),
            "snapshots_count": len(self._history),
            "monthly_expenses": self._monthly_expenses,
        }
