"""RevenueOptimizerOrgan - 營收優化器官

負責管理營收流與支出，計算 MRR、ARR、淨利潤等關鍵指標，
追蹤月增長率與年增長率，並根據數據提供營收優化建議。
"""
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from skeleton.brain_component import BrainComponent
from tools import tool


class RevenueOptimizerOrgan(BrainComponent):
    """營收優化器官

    管理營收流、支出項目、計算財務指標，並產出優化建議。
    支援 MRR/ARR 計算、MoM/YoY 增長追蹤與費用類別分析。
    """

    def __init__(self, dna: Optional[dict] = None):
        """初始化營收優化器官

        Parameters
        ----------
        dna : dict, optional
            器官的 DNA 設定
        """
        super().__init__(dna)
        self._revenue_streams: Dict[str, Dict[str, Any]] = {}
        self._expenses: Dict[str, Dict[str, Any]] = {}
        self._monthly_revenue_history: Dict[str, float] = {}
        self._monthly_expense_history: Dict[str, float] = {}
        self._created_at = datetime.now().isoformat()

    def status(self) -> dict:
        """回報器官狀態"""
        mrr = self._calculate_mrr()
        monthly_expenses = self._get_current_month_expenses()
        return {
            "name": "RevenueOptimizerOrgan",
            "alive": True,
            "revenue_stream_count": len(self._revenue_streams),
            "expense_count": len(self._expenses),
            "mrr": mrr,
            "arr": mrr * 12,
            "net_monthly_profit": mrr - monthly_expenses,
            "growth_tracked_months": len(self._monthly_revenue_history),
        }

    def _get_current_month_key(self) -> str:
        """取得當前月份的識別鍵 (YYYY-MM)"""
        return datetime.now().strftime("%Y-%m")

    def _calculate_mrr(self) -> float:
        """計算目前 MRR (Monthly Recurring Revenue)

        彙總所有營收流，依頻率正規化為月營收：
        - monthly: 全額
        - quarterly: 除以 3
        - annually: 除以 12
        - one-time: 當月有則計入（存於 _monthly_revenue_history）

        Returns
        -------
        float
            月經常性營收總額
        """
        total = 0.0
        for stream in self._revenue_streams.values():
            freq = stream.get("frequency", "monthly")
            amount = stream.get("amount", 0.0)
            if freq == "monthly":
                total += amount
            elif freq == "quarterly":
                total += amount / 3.0
            elif freq == "annually":
                total += amount / 12.0
            # one-time 不計入 MRR
        return round(total, 2)

    def _get_current_month_expenses(self) -> float:
        """取得當月總支出"""
        current_month = self._get_current_month_key()
        return round(
            sum(e.get("amount", 0.0) for e in self._expenses.values()
                if e.get("month") == current_month), 2)

    def _compute_growth_rate(self, history: Dict[str, float]) -> float:
        """從歷史記錄計算月增長率 (MoM)

        Parameters
        ----------
        history : dict
            月份對營收的字典，key 為 YYYY-MM

        Returns
        -------
        float
            月增長率百分比
        """
        if len(history) < 2:
            return 0.0
        sorted_keys = sorted(history.keys())
        prev_month_key = sorted_keys[-2]
        current_month_key = sorted_keys[-1]
        prev_val = history[prev_month_key]
        curr_val = history[current_month_key]
        if prev_val == 0:
            return 100.0 if curr_val > 0 else 0.0
        return round((curr_val - prev_val) / prev_val * 100, 2)

    def _compute_yoy_growth(self, history: Dict[str, float]) -> Optional[float]:
        """計算年增長率 (YoY)

        比對目前月份與去年同月份的營收。
        """
        if not history:
            return None
        now = datetime.now()
        current_key = now.strftime("%Y-%m")
        last_year_key = f"{now.year - 1}-{now.month:02d}"
        curr = history.get(current_key, 0.0)
        prev = history.get(last_year_key, 0.0)
        if prev == 0:
            return None if curr == 0 else None
        return round((curr - prev) / prev * 100, 2)

    @tool(name="add_revenue_stream", description="新增一筆營收流")
    def add_revenue_stream(self, name: str, amount: float, frequency: str = "monthly") -> str:
        """新增一筆營收流

        Parameters
        ----------
        name : str
            營收流名稱（唯一識別）
        amount : float
            金額
        frequency : str
            頻率，可為 monthly, quarterly, annually, one-time
        """
        if not name or not isinstance(name, str):
            return "❌ 營收流名稱不可為空且必須是字串"
        if not isinstance(amount, (int, float)) or amount < 0:
            return "❌ 金額必須為非負數"

        valid_freq = {"monthly", "quarterly", "annually", "one-time"}
        if frequency not in valid_freq:
            return f"❌ 頻率必須為以下之一：{', '.join(sorted(valid_freq))}"

        self._revenue_streams[name] = {
            "name": name,
            "amount": float(amount),
            "frequency": frequency,
            "added_at": datetime.now().isoformat(),
        }

        # 記錄到當月營收歷史
        self._record_current_month()

        return (
            f"✅ 營收流已新增：{name}\n"
            f"  金額：${amount:,.2f}\n"
            f"  頻率：{frequency}\n"
            f"  目前 MRR：${self._calculate_mrr():,.2f}"
        )

    @tool(name="get_monthly_revenue", description="取得本月營收報告")
    def get_monthly_revenue(self) -> str:
        """取得本月營收完整報告，包含 MRR、ARR、淨利與增長率"""
        mrr = self._calculate_mrr()
        arr = mrr * 12
        total_expenses = self._get_current_month_expenses()
        net_profit = mrr - total_expenses
        mom_growth = self._compute_growth_rate(self._monthly_revenue_history)
        yoy_growth = self._compute_yoy_growth(self._monthly_revenue_history)

        # 費用分類彙總
        expense_by_category: Dict[str, float] = defaultdict(float)
        current_month = self._get_current_month_key()
        for _, e in self._expenses.items():
            if e.get("month") == current_month:
                expense_by_category[e.get("category", "未分類")] += e["amount"]

        lines = [
            "📈 本月營收報告",
            "",
            "💰 營收指標：",
            f"  月經常性營收 (MRR)：${mrr:,.2f}",
            f"  年經常性營收 (ARR)：${arr:,.2f}",
            f"  本月總支出：${total_expenses:,.2f}",
            f"  本月淨利潤：${net_profit:,.2f}",
            f"  淨利率：{(net_profit / mrr * 100) if mrr > 0 else 0:.1f}%",
            "",
            "📊 增長指標：",
            f"  月增長率 (MoM)：{mom_growth:+.2f}%",
            f"  年增長率 (YoY)：{f'{yoy_growth:+.2f}%' if yoy_growth is not None else '無足夠資料'}",
            "",
            "🏷️ 費用分類：",
        ]
        if expense_by_category:
            for cat, amt in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {cat}：${amt:,.2f}")
        else:
            lines.append("  （本月尚無費用記錄）")

        lines.extend([
            "",
            "📋 營收流明細：",
        ])
        if self._revenue_streams:
            for s in self._revenue_streams.values():
                lines.append(
                    f"  {s['name']}：${s['amount']:,.2f} ({s['frequency']})"
                )
        else:
            lines.append("  （尚無營收流，請使用 add_revenue_stream）")

        return "\n".join(lines)

    @tool(name="forecast_next_month", description="預測下個月營收")
    def forecast_next_month(self) -> str:
        """根據歷史增長率預測下個月營收

        使用最近三個月的加權平均增長率進行預測。
        """
        mrr = self._calculate_mrr()
        history = self._monthly_revenue_history

        if len(history) < 2:
            forecast = mrr
            confidence = "低（歷史資料不足）"
        else:
            # 取最近三筆增長率，加權平均
            sorted_keys = sorted(history.keys())
            growth_rates = []
            for i in range(1, len(sorted_keys)):
                prev = history[sorted_keys[i - 1]]
                curr = history[sorted_keys[i]]
                rate = (curr - prev) / prev * 100 if prev > 0 else 0
                growth_rates.append(rate)

            # 最近三個月加權：50%, 30%, 20%
            recent = growth_rates[-3:] if len(growth_rates) >= 3 else growth_rates
            if len(recent) == 1:
                avg_rate = recent[0]
            elif len(recent) == 2:
                avg_rate = recent[-1] * 0.6 + recent[-2] * 0.4
            else:
                avg_rate = recent[-1] * 0.5 + recent[-2] * 0.3 + recent[-3] * 0.2

            forecast = round(mrr * (1 + avg_rate / 100), 2)

            if abs(avg_rate) < 2:
                confidence = "高（增長穩定）"
            elif abs(avg_rate) < 10:
                confidence = "中（增長波動適中）"
            else:
                confidence = "低（增長波動較大）"

        mom_growth = self._compute_growth_rate(history)

        return (
            f"🔮 下月營收預測\n"
            f"\n"
            f"  目前 MRR：${mrr:,.2f}\n"
            f"  預測 MRR：${forecast:,.2f}\n"
            f"  預測變動：{((forecast - mrr) / mrr * 100) if mrr > 0 else 0:+.1f}%\n"
            f"  目前 MoM：{mom_growth:+.2f}%\n"
            f"  信心水準：{confidence}"
        )

    @tool(name="suggest_optimization", description="根據營收與支出數據提供優化建議")
    def suggest_optimization(self) -> str:
        """分析營收與支出狀況，產出營收優化建議

        考量面向：
        - 營收流集中度風險
        - 支出比例是否過高
        - 增長趨勢變化
        - 一次性營收佔比
        """
        suggestions = []
        mrr = self._calculate_mrr()
        total_expenses = self._get_current_month_expenses()

        # 1. 營收流集中度
        if len(self._revenue_streams) == 0:
            suggestions.append("🔴 尚無任何營收流，請立即使用 add_revenue_stream 建立營收來源")
        elif len(self._revenue_streams) == 1:
            suggestions.append(
                "🟡 營收來源僅有一個，高度集中風險，建議新增至少 2-3 個營收流以分散風險"
            )
        else:
            # 計算最大佔比
            total_all = sum(s["amount"] for s in self._revenue_streams.values())
            if total_all > 0:
                max_contrib = max(s["amount"] for s in self._revenue_streams.values())
                if max_contrib / total_all > 0.6:
                    suggestions.append(
                        "🟡 單一營收流佔比超過 60%，建議分散營收來源降低風險"
                    )

        # 2. 支出比例
        if mrr > 0:
            expense_ratio = total_expenses / mrr * 100
            if expense_ratio > 80:
                suggestions.append(
                    f"🔴 支出佔 MRR {expense_ratio:.0f}%，過高。建議檢視可削減的費用項目"
                )
            elif expense_ratio > 50:
                suggestions.append(
                    f"🟡 支出佔 MRR {expense_ratio:.0f}%，偏高。建議審視各類別支出效率"
                )
            elif expense_ratio < 20:
                suggestions.append(
                    f"🟢 支出佔 MRR {expense_ratio:.0f}%，偏低。可考慮增加投資以加速成長"
                )

        # 3. 增長趨勢
        growth = self._compute_growth_rate(self._monthly_revenue_history)
        if growth < -5:
            suggestions.append(
                f"🔴 MoM 增長率 {growth:+.1f}%，呈下滑趨勢。建議立即檢視客戶流失原因與市場變化"
            )
        elif growth < 0:
            suggestions.append(
                f"🟡 MoM 增長率 {growth:+.1f}%，輕微下滑。建議加強行銷與客戶維繫"
            )
        elif growth > 20:
            suggestions.append(
                f"🟢 MoM 增長率 {growth:+.1f}%，高速成長中。建議確保服務品質能跟上成長速度"
            )

        # 4. 一次性營收
        one_time_count = sum(
            1 for s in self._revenue_streams.values() if s["frequency"] == "one-time"
        )
        if one_time_count > 0:
            suggestions.append(
                "💡 存在一次性營收流，建議轉化為經常性營收（訂閱制）以提高可預測性"
            )

        # 5. 經常性營收比例
        recurring_streams = [
            s for s in self._revenue_streams.values()
            if s["frequency"] in ("monthly", "quarterly", "annually")
        ]
        if recurring_streams:
            recurring_ratio = sum(s["amount"] / (
                1 if s["frequency"] == "monthly"
                else 3 if s["frequency"] == "quarterly"
                else 12
            ) for s in recurring_streams)
            total_mrr = recurring_ratio
            if total_mrr > 0:
                suggestions.append(
                    f"📊 經常性營收佔比良好，可進一步透過 up-sell 與 cross-sell 提升 ARPU"
                )

        lines = [
            "💡 營收優化建議",
            "",
        ]
        if suggestions:
            for i, s in enumerate(suggestions, 1):
                lines.append(f"  {i}. {s}")
        else:
            lines.append("  （目前尚無足夠資料產出建議，請先新增營收流與支出記錄）")

        lines.extend([
            "",
            "📊 當前財務快照：",
            f"  MRR：${mrr:,.2f}",
            f"  本月支出：${total_expenses:,.2f}",
            f"  營收流數量：{len(self._revenue_streams)}",
            f"  支出項目數量：{len(self._expenses)}",
        ])
        return "\n".join(lines)

    @tool(name="add_expense", description="新增一筆支出記錄")
    def add_expense(self, name: str, amount: float, category: str = "一般") -> str:
        """新增一筆支出記錄

        Parameters
        ----------
        name : str
            支出項目名稱（唯一識別）
        amount : float
            金額
        category : str
            支出類別，如 行銷、人事、基礎設施、一般 等
        """
        if not name or not isinstance(name, str):
            return "❌ 支出名稱不可為空且必須是字串"
        if not isinstance(amount, (int, float)) or amount < 0:
            return "❌ 金額必須為非負數"
        if name in self._expenses:
            return f"❌ 支出項目「{name}」已存在，如需更新請先刪除"

        current_month = self._get_current_month_key()
        self._expenses[name] = {
            "name": name,
            "amount": float(amount),
            "category": category or "一般",
            "month": current_month,
            "added_at": datetime.now().isoformat(),
        }

        # 更新當月支出歷史
        total_exp = self._get_current_month_expenses()
        self._monthly_expense_history[current_month] = total_exp

        return (
            f"✅ 支出已記錄：{name}\n"
            f"  金額：${amount:,.2f}\n"
            f"  類別：{category}\n"
            f"  月份：{current_month}\n"
            f"  本月累計支出：${total_exp:,.2f}"
        )

    def _record_current_month(self) -> None:
        """將當月營收記錄到歷史中"""
        current_month = self._get_current_month_key()
        mrr = self._calculate_mrr()
        self._monthly_revenue_history[current_month] = mrr
