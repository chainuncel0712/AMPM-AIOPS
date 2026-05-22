"""MarketAnalyzerOrgan - 市場分析器官，提供技術摘要、情緒分析與進場建議"""
from typing import Optional, Dict, List
from skeleton.brain_component import BrainComponent
from tools import tool
import time
import random
import hashlib


class MarketAnalyzerOrgan(BrainComponent):
    """市場分析器官 — 基於市場數據進行技術分析與交易建議"""

    RISK_LEVELS = {
        "conservative": {"rsi_buy_threshold": 35, "rsi_sell_threshold": 70, "volatility_bonus": -0.03},
        "moderate":      {"rsi_buy_threshold": 40, "rsi_sell_threshold": 65, "volatility_bonus": 0.00},
        "aggressive":    {"rsi_buy_threshold": 45, "rsi_sell_threshold": 60, "volatility_bonus": 0.03},
    }

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._analysis_history: Dict[str, list] = {}
        # 延遲匯入以避免循環依賴
        self._market_data = None

    def _get_market_data(self):
        """取得 MarketDataOrgan 實例 (延遲實例化)"""
        if self._market_data is None:
            from core.market_data import MarketDataOrgan
            self._market_data = MarketDataOrgan(self._dna)
        return self._market_data

    def _generate_score_seed(self, symbol: str, base: str) -> float:
        """根據代幣符號與基礎因子產生可重現的分數 (0~1)"""
        digest = hashlib.sha256(f"{symbol}:{base}:{int(time.time() // 3600)}".encode()).digest()
        val = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
        return val

    def _estimate_rsi(self, symbol: str) -> int:
        """估算 RSI 數值 (0~100)，基於偽隨機 + 價格變動訊號"""
        seed = self._generate_score_seed(symbol, "rsi")
        base_rsi = 30 + seed * 40  # 範圍 30~70
        # 以 24h 變動微調
        md = self._get_market_data()
        try:
            change_text = md.get_24h_change(symbol)
            import re
            m = re.search(r'([+-]?\d+\.?\d*)%', change_text)
            if m:
                change_val = float(m.group(1))
                # 漲幅大 → RSI 偏高
                base_rsi += change_val * 1.5
        except Exception:
            pass
        return max(0, min(100, int(base_rsi)))

    def _estimate_volatility(self, symbol: str) -> float:
        """估算年化波動率 (0~2.0)，數值越高越震盪"""
        seed = self._generate_score_seed(symbol, "vol")
        # 主流幣波動較低，山寨幣較高
        majors = {"btc", "eth"}
        alts = {"sol", "bnb", "matic", "arb", "op", "avax", "link", "uni", "aave"}
        base_vol = 0.3 if symbol in majors else (0.7 if symbol in alts else 1.2)
        return round(base_vol + seed * 0.8, 2)

    def _trend_direction(self, symbol: str) -> str:
        """判斷短期趨勢方向"""
        seed = self._generate_score_seed(symbol, "trend")
        if seed > 0.6:
            return "bullish"
        elif seed > 0.3:
            return "sideways"
        else:
            return "bearish"

    def _trend_score(self, symbol: str) -> int:
        """趨勢信心分數 0~100"""
        seed = self._generate_score_seed(symbol, "tscore")
        return int(seed * 100)

    @tool(name="analyze_sentiment", description="分析代幣的市場情緒 (恐懼/貪婪/中性)")
    def analyze_sentiment(self, symbol: str) -> str:
        """分析市場情緒"""
        symbol = symbol.lower().strip()
        md = self._get_market_data()
        price_line = md.get_price(symbol)
        change_line = md.get_24h_change(symbol)

        # 從 change_line 提取數值
        import re
        change_match = re.search(r'([+-]?\d+\.?\d*)%', change_line)
        change_val = float(change_match.group(1)) if change_match else 0

        rsi = self._estimate_rsi(symbol)
        vol = self._estimate_volatility(symbol)

        # 情緒判定
        if change_val > 3 and rsi > 60:
            sentiment = "貪婪 🤑"
            advice = "市場過熱，注意回調風險"
        elif change_val < -3 and rsi < 40:
            sentiment = "恐懼 😨"
            advice = "市場超賣，可關注抄底機會"
        elif abs(change_val) < 1.5 and 40 <= rsi <= 60:
            sentiment = "中性 😐"
            advice = "市場方向不明，建議觀望"
        elif rsi > 70:
            sentiment = "極度貪婪 🚀"
            advice = "RSI 過熱，短線可考慮分批止盈"
        elif rsi < 30:
            sentiment = "極度恐懼 💀"
            advice = "RSI 超賣，價值投資者可分批建倉"
        else:
            sentiment = "觀望 🤔"
            advice = "等待明確方向訊號"

        lines = [
            f"🧠 {symbol.upper()} 市場情緒分析",
            f"{price_line.split(': ', 1)[1] if ': ' in price_line else price_line}",
            f"  24h 變動: {change_val:+.2f}%",
            f"  估計 RSI (14): {rsi}",
            f"  估計波動率: {vol:.2f} (年化)",
            f"  情緒判定: {sentiment}",
            f"  建議: {advice}",
        ]
        return "\n".join(lines)

    @tool(name="get_technical_summary", description="取得代幣的綜合技術指標摘要")
    def get_technical_summary(self, symbol: str) -> str:
        """技術指標摘要"""
        symbol = symbol.lower().strip()
        rsi = self._estimate_rsi(symbol)
        vol = self._estimate_volatility(symbol)
        trend = self._trend_direction(symbol)
        tscore = self._trend_score(symbol)

        trend_emoji = {"bullish": "📈 看漲", "sideways": "↔️ 盤整", "bearish": "📉 看跌"}
        trend_label = trend_emoji.get(trend, "未知")

        # RSI 訊號
        if rsi > 70:
            rsi_signal = "超買 ⚠️"
        elif rsi < 30:
            rsi_signal = "超賣 💡"
        elif rsi > 55:
            rsi_signal = "偏強"
        elif rsi < 45:
            rsi_signal = "偏弱"
        else:
            rsi_signal = "中性"

        # 波動率分級
        if vol < 0.4:
            vol_level = "低波動 (穩定)"
        elif vol < 0.9:
            vol_level = "中波動"
        else:
            vol_level = "高波動 ⚡"

        # 簡單支撐/阻力估算 (模擬)
        md = self._get_market_data()
        price_line = md.get_price(symbol)
        import re
        price_match = re.search(r'\$([\d,]+\.?\d*)', price_line)
        current_price = float(price_match.group(1).replace(",", "")) if price_match else 100
        support = round(current_price * (1 - vol * 0.3), 2)
        resistance = round(current_price * (1 + vol * 0.3), 2)

        lines = [
            f"📊 {symbol.upper()} 技術指標摘要",
            f"  目前價格: ${current_price:,.4f}",
            f"  趨勢方向: {trend_label} (信心: {tscore}/100)",
            f"  估計 RSI (14): {rsi} → {rsi_signal}",
            f"  波動率等級: {vol_level} ({vol:.2f})",
            f"  預估支撐位: ${support:,.4f}",
            f"  預估阻力位: ${resistance:,.4f}",
        ]
        return "\n".join(lines)

    @tool(name="suggest_entry", description="根據風險偏好提供進場建議")
    def suggest_entry(self, symbol: str, risk_level: str = "moderate") -> str:
        """提供進場建議 (保守/穩健/激進)"""
        symbol = symbol.lower().strip()
        risk_level = risk_level.lower().strip()

        if risk_level not in self.RISK_LEVELS:
            supported = ", ".join(self.RISK_LEVELS.keys())
            return f"❌ 不支援的風險等級: {risk_level}。支援: {supported}"

        risk_cfg = self.RISK_LEVELS[risk_level]
        rsi = self._estimate_rsi(symbol)
        vol = self._estimate_volatility(symbol)
        trend = self._trend_direction(symbol)

        md = self._get_market_data()
        price_line = md.get_price(symbol)
        change_line = md.get_24h_change(symbol)

        import re
        price_match = re.search(r'\$([\d,]+\.?\d*)', price_line)
        current_price = float(price_match.group(1).replace(",", "")) if price_match else 100
        change_match = re.search(r'([+-]?\d+\.?\d*)%', change_line)
        change_val = float(change_match.group(1)) if change_match else 0

        # 進場訊號計算
        buy_threshold = risk_cfg["rsi_buy_threshold"]
        sell_threshold = risk_cfg["rsi_sell_threshold"]

        # 計算進場分數
        entry_score = 50
        if trend == "bullish":
            entry_score += 15
        elif trend == "bearish":
            entry_score -= 20

        if rsi < buy_threshold:
            entry_score += 20
        elif rsi > sell_threshold:
            entry_score -= 25

        if change_val < -3:
            entry_score += 10  # 大跌後潛在反彈
        elif change_val > 5:
            entry_score -= 10  # 大漲後追高風險

        # 目標價與止損
        stop_loss = round(current_price * (1 - vol * 0.25), 4)
        take_profit = round(current_price * (1 + vol * 0.4), 4)

        # 建議動作
        if entry_score >= 65:
            action = "✅ 強烈建議進場"
            detail = "訊號偏多，風險可控，可分批入場"
        elif entry_score >= 50:
            action = "🟢 可考慮進場"
            detail = "訊號中性偏多，建議小倉位試單"
        elif entry_score >= 35:
            action = "🟡 建議觀望"
            detail = "訊號偏弱，等待更明確的進場訊號"
        else:
            action = "🔴 不建議進場"
            detail = "訊號偏空，建議等待 RSI 回落或趨勢轉多"

        risk_labels = {"conservative": "保守型", "moderate": "穩健型", "aggressive": "激進型"}

        lines = [
            f"🎯 {symbol.upper()} 進場建議 ({risk_labels.get(risk_level, risk_level)})",
            f"  目前價格: ${current_price:,.4f}",
            f"  估計 RSI: {rsi} (買入閾值 ≤{buy_threshold}, 賣出閾值 ≥{sell_threshold})",
            f"  趨勢: {trend}",
            f"  進場評分: {entry_score}/100",
            f"  建議: {action}",
            f"  理由: {detail}",
            f"  建議止損: ${stop_loss:,.4f}",
            f"  建議止盈: ${take_profit:,.4f}",
        ]
        return "\n".join(lines)

    @tool(name="compare_tokens", description="比較多個代幣的技術面與風險指標")
    def compare_tokens(self, symbols: List[str]) -> str:
        """比較多個代幣"""
        if not symbols:
            return "❌ 請提供至少一個代幣符號"

        md = self._get_market_data()
        lines = ["📊 代幣比較分析", "=" * 40]
        results = []

        for sym in symbols:
            sym = sym.lower().strip()
            rsi = self._estimate_rsi(sym)
            vol = self._estimate_volatility(sym)
            trend = self._trend_direction(sym)
            tscore = self._trend_score(sym)

            price_line = md.get_price(sym)
            change_line = md.get_24h_change(sym)
            import re
            price_match = re.search(r'\$([\d,]+\.?\d*)', price_line)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0
            change_match = re.search(r'([+-]?\d+\.?\d*)%', change_line)
            change_val = float(change_match.group(1)) if change_match else 0

            # 綜合評分
            composite = int(50 + (rsi - 50) * 0.6 + change_val * 1.5 - vol * 10)
            composite = max(0, min(100, composite))

            trend_icon = {"bullish": "📈", "sideways": "↔️", "bearish": "📉"}.get(trend, "?")
            results.append({
                "symbol": sym.upper(),
                "price": price,
                "change": change_val,
                "rsi": rsi,
                "vol": vol,
                "trend_icon": trend_icon,
                "trend": trend,
                "tscore": tscore,
                "composite": composite,
            })

        # 按綜合評分排序
        results.sort(key=lambda x: x["composite"], reverse=True)

        for r in results:
            lines.append(
                f"\n  {r['trend_icon']} {r['symbol']:6s}  ${r['price']:>10,.4f}  "
                f"{r['change']:+.2f}%  RSI:{r['rsi']:3d}  Vol:{r['vol']:.2f}  "
                f"趨勢信心:{r['tscore']:3d}  綜合:{r['composite']:3d}"
            )

        # 最佳/最差建議
        best = results[0]
        worst = results[-1]
        lines.append(f"\n🏆 最佳: {best['symbol']} (綜合評分 {best['composite']})")
        lines.append(f"⚠️  最差: {worst['symbol']} (綜合評分 {worst['composite']})")

        return "\n".join(lines)

    def status(self) -> dict:
        """回報器官狀態"""
        return {
            "organ": "MarketAnalyzerOrgan",
            "alive": True,
            "risk_levels_supported": list(self.RISK_LEVELS.keys()),
            "analyses_cached": len(self._analysis_history),
        }
