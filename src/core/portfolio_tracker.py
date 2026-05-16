"""PortfolioTrackerOrgan - 投資組合追蹤器官，管理持倉、計算損益與再平衡建議"""
from typing import Optional, Dict, List
from skeleton.brain_component import BrainComponent
from src.tools import tool
import time
import uuid
import re


class PortfolioTrackerOrgan(BrainComponent):
    """投資組合追蹤器官 — 追蹤持倉成本、計算未實現損益、提供再平衡建議"""

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._positions: Dict[str, dict] = {}
        self._position_counter: int = 0
        self._market_data = None

    def _get_market_data(self):
        """延遲取得 MarketDataOrgan 實例"""
        if self._market_data is None:
            from core.market_data import MarketDataOrgan
            self._market_data = MarketDataOrgan(self.dna)
        return self._market_data

    def _parse_price(self, price_output: str) -> float:
        """從 MarketDataOrgan 價格輸出字串中提取數值"""
        m = re.search(r'\$([\d,]+\.?\d*)', price_output)
        if m:
            return float(m.group(1).replace(",", ""))
        return 0.0

    def _generate_position_id(self) -> str:
        """產生唯一持倉 ID"""
        self._position_counter += 1
        ts = int(time.time() * 1000)
        return f"pos_{ts}_{self._position_counter:04d}"

    @tool(name="add_position", description="新增一筆持倉記錄")
    def add_position(self, symbol: str, amount: float, buy_price: float) -> str:
        """新增持倉位置"""
        symbol = symbol.lower().strip()
        if amount <= 0:
            return "❌ 持倉數量必須大於 0"
        if buy_price <= 0:
            return "❌ 買入價格必須大於 0"

        pos_id = self._generate_position_id()
        self._positions[pos_id] = {
            "symbol": symbol,
            "amount": amount,
            "buy_price": buy_price,
            "cost_basis": amount * buy_price,
            "timestamp": time.time(),
        }

        return (
            f"✅ 已新增持倉 #{pos_id}\n"
            f"  代幣: {symbol.upper()}\n"
            f"  數量: {amount:,.6f}\n"
            f"  買入價: ${buy_price:,.4f}\n"
            f"  成本: ${amount * buy_price:,.2f}"
        )

    @tool(name="remove_position", description="根據持倉 ID 移除一筆持倉記錄")
    def remove_position(self, position_id: str) -> str:
        """移除持倉"""
        if position_id not in self._positions:
            return f"❌ 找不到持倉 ID: {position_id}"

        pos = self._positions.pop(position_id)
        return (
            f"✅ 已移除持倉 #{position_id}\n"
            f"  代幣: {pos['symbol'].upper()}\n"
            f"  數量: {pos['amount']:,.6f}\n"
            f"  成本: ${pos['cost_basis']:,.2f}"
        )

    @tool(name="get_portfolio_value", description="計算當前投資組合總市值與總損益")
    def get_portfolio_value(self) -> str:
        """計算投資組合總價值"""
        if not self._positions:
            return "📭 目前沒有任何持倉"

        md = self._get_market_data()
        total_cost = 0.0
        total_value = 0.0
        lines = ["📊 投資組合總覽", "=" * 50]

        for pos_id, pos in sorted(self._positions.items()):
            symbol = pos["symbol"]
            amount = pos["amount"]
            cost = pos["cost_basis"]
            buy_price = pos["buy_price"]

            price_output = md.get_price(symbol)
            current_price = self._parse_price(price_output)
            current_value = amount * current_price
            pnl = current_value - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0

            total_cost += cost
            total_value += current_value

            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(
                f"\n  {emoji} [{pos_id}] {symbol.upper():6s}  "
                f"數量: {amount:>10,.4f}  "
                f"買入價: ${buy_price:>12,.4f}  "
                f"現價: ${current_price:>12,.4f}\n"
                f"       成本: ${cost:>12,.2f}  "
                f"市值: ${current_value:>12,.2f}  "
                f"損益: {pnl:+,.2f} ({pnl_pct:+.2f}%)"
            )

        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        lines.append(f"\n{'=' * 50}")
        lines.append(f"  總成本: ${total_cost:,.2f}")
        lines.append(f"  總市值: ${total_value:,.2f}")
        lines.append(f"  總損益: {total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")

        return "\n".join(lines)

    @tool(name="get_pnl", description="查詢單一持倉的未實現損益")
    def get_pnl(self, position_id: str) -> str:
        """查詢特定持倉的損益"""
        if position_id not in self._positions:
            return f"❌ 找不到持倉 ID: {position_id}"

        pos = self._positions[position_id]
        symbol = pos["symbol"]
        amount = pos["amount"]
        cost = pos["cost_basis"]
        buy_price = pos["buy_price"]

        md = self._get_market_data()
        price_output = md.get_price(symbol)
        current_price = self._parse_price(price_output)
        current_value = amount * current_price
        pnl = current_value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0

        emoji = "📈" if pnl >= 0 else "📉"
        return (
            f"{emoji} 持倉 #{position_id} 損益明細\n"
            f"  代幣: {symbol.upper()}\n"
            f"  數量: {amount:,.6f}\n"
            f"  買入價: ${buy_price:,.4f}\n"
            f"  現價: ${current_price:,.4f}\n"
            f"  成本: ${cost:,.2f}\n"
            f"  市值: ${current_value:,.2f}\n"
            f"  未實現損益: {pnl:+,.2f} ({pnl_pct:+.2f}%)"
        )

    @tool(name="rebalance_suggestion", description="根據持倉權重提供再平衡建議")
    def rebalance_suggestion(self) -> str:
        """提供投資組合再平衡建議"""
        if not self._positions:
            return "📭 目前沒有任何持倉，無法提供再平衡建議"

        md = self._get_market_data()
        positions_list = []
        total_value = 0.0

        for pos_id, pos in self._positions.items():
            symbol = pos["symbol"]
            amount = pos["amount"]
            cost = pos["cost_basis"]

            price_output = md.get_price(symbol)
            current_price = self._parse_price(price_output)
            current_value = amount * current_price

            positions_list.append({
                "id": pos_id,
                "symbol": symbol,
                "amount": amount,
                "cost": cost,
                "current_price": current_price,
                "current_value": current_value,
            })
            total_value += current_value

        if total_value <= 0:
            return "⚠️ 投資組合總市值為 0，無法提供建議"

        # 計算每個持倉的市值占比
        num_positions = len(positions_list)
        target_weight = 1.0 / num_positions  # 等權重為目標

        lines = ["⚖️ 投資組合再平衡建議", f"  目標權重: 等權重分配 ({target_weight:.1%} 每部位)", ""]
        suggestions = []

        for p in positions_list:
            current_weight = p["current_value"] / total_value
            deviation = current_weight - target_weight
            p["weight"] = current_weight
            p["deviation"] = deviation

            status = "🟢 適中" if abs(deviation) < 0.1 else ("🔴 偏高" if deviation > 0 else "🟡 偏低")
            lines.append(
                f"  {status} [{p['id']}] {p['symbol'].upper():6s}  "
                f"市值: ${p['current_value']:>10,.2f}  權重: {current_weight:.1%}  "
                f"(偏離目標: {deviation:+.1%})"
            )

            if abs(deviation) >= 0.1:
                if deviation > 0:
                    # 權重過高 → 建議減倉
                    trim_value = deviation * total_value
                    trim_amount = trim_value / p["current_price"] if p["current_price"] > 0 else 0
                    suggestions.append(
                        f"  📤 減倉 {p['symbol'].upper()}: 賣出約 {trim_amount:,.4f} 單位 (約 ${trim_value:,.2f})"
                    )
                else:
                    # 權重過低 → 建議加倉
                    add_value = abs(deviation) * total_value
                    add_amount = add_value / p["current_price"] if p["current_price"] > 0 else 0
                    suggestions.append(
                        f"  📥 加倉 {p['symbol'].upper()}: 買入約 {add_amount:,.4f} 單位 (約 ${add_value:,.2f})"
                    )

        if suggestions:
            lines.append(f"\n📋 建議操作 ({len(suggestions)} 筆):")
            lines.extend(suggestions)
        else:
            lines.append("\n✅ 投資組合權重已接近目標，無需調整")

        return "\n".join(lines)

    def status(self) -> dict:
        """回報器官狀態"""
        return {
            "organ": "PortfolioTrackerOrgan",
            "alive": True,
            "positions_count": len(self._positions),
            "position_ids": list(self._positions.keys()),
            "total_positions": self._position_counter,
        }
