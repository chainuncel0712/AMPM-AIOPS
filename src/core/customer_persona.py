"""CustomerPersonaOrgan - 客戶畫像器官

負責建立、分析與比較客戶畫像，提供基於行為評分的行銷建議。
每個畫像包含年齡、地點、收入、興趣、痛點、目標、偏好管道等屬性，
透過行為分析計算多維度分數，並產出可執行的行銷推薦。
"""
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from skeleton.brain_component import BrainComponent
from src.tools import tool


class CustomerPersonaOrgan(BrainComponent):
    """客戶畫像器官

    管理客戶畫像的生命週期，包含建立、行為分析、行銷建議與畫像比較。
    """

    def __init__(self, dna: Optional[dict] = None):
        """初始化客戶畫像器官

        Parameters
        ----------
        dna : dict, optional
            器官的 DNA 設定
        """
        super().__init__(dna)
        self._personas: Dict[str, Dict[str, Any]] = {}

    def status(self) -> dict:
        """回報器官狀態"""
        return {
            "name": "CustomerPersonaOrgan",
            "alive": True,
            "persona_count": len(self._personas),
            "persona_names": list(self._personas.keys()),
        }

    @tool(name="create_persona", description="建立客戶畫像，包含人口統計、行為模式與目標")
    def create_persona(
        self,
        name: str,
        demographics: Optional[Dict[str, Any]] = None,
        behaviors: Optional[Dict[str, Any]] = None,
        goals: Optional[Dict[str, Any]] = None,
    ) -> str:
        """建立一個新的客戶畫像

        Parameters
        ----------
        name : str
            畫像名稱（唯一識別）
        demographics : dict, optional
            人口統計資訊，可包含 age, location, income, interests
        behaviors : dict, optional
            行為模式記錄，可包含 purchase_frequency, avg_order_value, preferred_channels, last_purchase
        goals : dict, optional
            客戶目標，可包含 primary_goal, secondary_goals
        """
        if not name or not isinstance(name, str):
            return "❌ 畫像名稱不可為空且必須是字串"

        demographics = demographics or {}
        behaviors = behaviors or {}
        goals = goals or {}

        persona = {
            "name": name,
            "age": demographics.get("age", 0),
            "location": demographics.get("location", "未知"),
            "income": demographics.get("income", 0.0),
            "interests": demographics.get("interests", []),
            "pain_points": demographics.get("pain_points", []),
            "channels": demographics.get("channels", []),
            "behaviors": {
                "purchase_frequency": behaviors.get("purchase_frequency", 0),
                "avg_order_value": behaviors.get("avg_order_value", 0.0),
                "preferred_channels": behaviors.get("preferred_channels", []),
                "last_purchase": behaviors.get("last_purchase", "無"),
            },
            "goals": {
                "primary": goals.get("primary", "未設定"),
                "secondary": goals.get("secondary", []),
            },
            "created_at": datetime.now().isoformat(),
            "score": 0,
        }

        self._personas[name] = persona

        lines = [
            f"👤 客戶畫像已建立：{name}",
            "",
            "📋 基本資訊：",
            f"  年齡：{persona['age'] if persona['age'] > 0 else '未設定'}",
            f"  地點：{persona['location']}",
            f"  收入：${persona['income']:,.0f}/年" if persona['income'] > 0 else "  收入：未設定",
            f"  興趣：{', '.join(persona['interests']) if persona['interests'] else '未設定'}",
            f"  痛點：{', '.join(persona['pain_points']) if persona['pain_points'] else '未設定'}",
            f"  偏好管道：{', '.join(persona['channels']) if persona['channels'] else '未設定'}",
            "",
            "🎯 客戶目標：",
            f"  主要：{persona['goals']['primary']}",
            f"  次要：{', '.join(persona['goals']['secondary']) if persona['goals']['secondary'] else '無'}",
        ]
        return "\n".join(lines)

    @tool(name="analyze_behavior", description="根據行為資料對指定畫像進行多維度行為分析與評分")
    def analyze_behavior(self, persona_name: str, data: Optional[Dict[str, Any]] = None) -> str:
        """分析指定畫像的行為資料，計算行為分數

        分析維度包含：互動頻率、轉換率、最近活躍度、購買頻率與消費價值。
        各維度以加權平均方式計算總分。

        Parameters
        ----------
        persona_name : str
            欲分析的畫像名稱
        data : dict, optional
            行為資料，可包含 engagement_rate, conversion_rate,
            days_since_last_activity, purchase_count, total_spent
        """
        if persona_name not in self._personas:
            return f"❌ 找不到畫像「{persona_name}」，請先使用 create_persona 建立"

        data = data or {}
        persona = self._personas[persona_name]

        # 計算各維度分數 (0-100)
        scores = {}

        # 互動率 (engagement_rate, 0-100)
        engagement = data.get("engagement_rate", 0)
        scores["互動率"] = min(float(engagement), 100)

        # 轉換率 (conversion_rate, 0-100)
        conversion = data.get("conversion_rate", 0)
        scores["轉換率"] = min(float(conversion), 100)

        # 最近活躍度 (天數越短分數越高)
        days_since = data.get("days_since_last_activity", 90)
        if days_since <= 1:
            scores["活躍度"] = 100
        elif days_since <= 7:
            scores["活躍度"] = 80
        elif days_since <= 30:
            scores["活躍度"] = 50
        elif days_since <= 90:
            scores["活躍度"] = 20
        else:
            scores["活躍度"] = 5

        # 購買頻率 (相對分數)
        purchase_count = data.get("purchase_count", 0)
        if purchase_count >= 20:
            scores["購買頻率"] = 100
        elif purchase_count >= 10:
            scores["購買頻率"] = 75
        elif purchase_count >= 5:
            scores["購買頻率"] = 50
        elif purchase_count >= 1:
            scores["購買頻率"] = 25
        else:
            scores["購買頻率"] = 0

        # 消費價值 (total_spent 相對分數)
        total_spent = data.get("total_spent", 0)
        if total_spent >= 10000:
            scores["消費價值"] = 100
        elif total_spent >= 5000:
            scores["消費價值"] = 75
        elif total_spent >= 1000:
            scores["消費價值"] = 50
        elif total_spent >= 100:
            scores["消費價值"] = 25
        else:
            scores["消費價值"] = 0

        # 加權計算總分
        weights = {
            "互動率": 0.15,
            "轉換率": 0.25,
            "活躍度": 0.20,
            "購買頻率": 0.20,
            "消費價值": 0.20,
        }
        overall_score = sum(scores[k] * weights[k] for k in scores)
        overall_score = round(overall_score, 1)

        # 判定客戶等級
        if overall_score >= 80:
            tier = "🏆 高價值客戶"
        elif overall_score >= 50:
            tier = "⭐ 中等價值客戶"
        else:
            tier = "📌 低價值客戶"

        # 更新畫像分數
        persona["score"] = overall_score
        persona["behavior_data"] = data
        persona["analyzed_at"] = datetime.now().isoformat()

        lines = [
            f"🔍 行為分析：{persona_name}",
            "",
            "📊 行為分數明細：",
        ]
        for dim, sc in scores.items():
            bar = "█" * int(sc / 10) + "░" * (10 - int(sc / 10))
            lines.append(f"  {dim}：{bar} {sc:.1f}/100")

        lines.extend([
            "",
            f"📈 綜合評分：{overall_score}/100",
            f"📌 客戶等級：{tier}",
            "",
            "📋 行為摘要：",
            f"  互動率：{engagement}%",
            f"  轉換率：{conversion}%",
            f"  最近活躍：{days_since} 天前",
            f"  購買次數：{purchase_count} 次",
            f"  總消費額：${total_spent:,.0f}",
        ])
        return "\n".join(lines)

    @tool(name="get_recommendations", description="根據客戶畫像產出可執行的行銷建議")
    def get_recommendations(self, persona_name: str) -> str:
        """根據畫像屬性與行為分數，產出針對性的行銷建議

        Parameters
        ----------
        persona_name : str
            欲取得建議的畫像名稱
        """
        if persona_name not in self._personas:
            return f"❌ 找不到畫像「{persona_name}」，請先使用 create_persona 建立"

        persona = self._personas[persona_name]
        recommendations = []
        score = persona.get("score", 0)

        # 根據痛點產生建議
        for pain in persona.get("pain_points", []):
            rec_map = {
                "價格敏感": "推出限時折扣與分期付款方案，降低購買門檻",
                "時間不足": "提供一鍵再訂購與自動補貨服務，節省客戶時間",
                "資訊缺乏": "建立教育型內容行銷（部落格、教學影片）建立信任",
                "選擇困難": "提供個人化推薦引擎與 AI 購物助手",
                "服務不佳": "導入 24/7 客服聊天機器人，提升服務體驗",
                "信任不足": "展示真實客戶評價、案例研究與第三方認證",
            }
            matched = False
            for keyword, rec in rec_map.items():
                if keyword in pain:
                    recommendations.append(rec)
                    matched = True
                    break
            if not matched:
                recommendations.append(f"針對「{pain}」設計專屬解決方案")

        # 根據偏好管道產生建議
        channels = persona.get("channels", [])
        behaviors = persona.get("behaviors", {})
        preferred = behaviors.get("preferred_channels", [])
        all_channels = channels + preferred
        if all_channels:
            channel_strategies = {
                "社群媒體": "加強 Facebook/IG 廣告投放，發布互動型內容提高參與",
                "電子郵件": "發送個人化電子報與自動化 drip campaign",
                "簡訊": "推送限時優惠簡訊，提高即時轉換率",
                "網站": "優化 Landing Page 與 SEO，提升自然流量轉換",
                "線下活動": "舉辦 VIP 專屬體驗活動，強化品牌忠誠度",
                "App": "發送推播通知與 App 內專屬優惠",
            }
            for ch in all_channels:
                if ch in channel_strategies:
                    recommendations.append(channel_strategies[ch])

        # 根據分數產生建議
        if score >= 80:
            recommendations.append("啟動 VIP 忠誠計畫，提供專屬客服與搶先體驗權益")
            recommendations.append("邀請參與使用者訪談，深化關係並收集高品質回饋")
        elif score >= 50:
            recommendations.append("透過再行銷廣告重新吸引，提供專屬升級優惠")
            recommendations.append("發送 NPS 調查，了解滿意度瓶頸並改善")
        else:
            recommendations.append("發送歡迎回歸優惠券，降低流失門檻")
            recommendations.append("進行 A/B 測試找出最佳溝通方式與內容")

        # 去重
        seen = set()
        unique_recs = []
        for r in recommendations:
            if r not in seen:
                unique_recs.append(r)
                seen.add(r)

        lines = [
            f"💡 {persona_name} 行銷建議",
            "",
        ]
        if unique_recs:
            for i, rec in enumerate(unique_recs, 1):
                lines.append(f"  {i}. {rec}")
        else:
            lines.append("  （尚無足夠資料產出建議，請先完善畫像資訊）")

        lines.extend([
            "",
            "📊 參考依據：",
            f"  綜合評分：{score:.0f}/100",
            f"  痛點：{', '.join(persona.get('pain_points', [])) or '未設定'}",
            f"  偏好管道：{', '.join(persona.get('channels', [])) or '未設定'}",
        ])
        return "\n".join(lines)

    @tool(name="list_personas", description="列出所有已建立的客戶畫像")
    def list_personas(self) -> str:
        """列出所有已建立的客戶畫像及其摘要"""
        if not self._personas:
            return "📭 尚未建立任何客戶畫像"

        lines = [f"📋 客戶畫像總覽（共 {len(self._personas)} 筆）", ""]
        for name, p in self._personas.items():
            lines.append(f"  ── {name} ──")
            lines.append(
                f"  {'👤':<1} 年齡：{p['age'] if p['age'] > 0 else '未設定'}  "
                f"地點：{p['location']}  "
                f"收入：${p['income']:,.0f}" if p['income'] > 0 else "  收入：未設定"
            )
            lines.append(f"  📊 評分：{p.get('score', 0):.0f}/100")
            lines.append(f"  🎯 目標：{p['goals']['primary']}")
            lines.append("")
        return "\n".join(lines)

    @tool(name="compare_personas", description="比較兩個客戶畫像的異同")
    def compare_personas(self, p1: str, p2: str) -> str:
        """比較兩個客戶畫像，突顯差異與共同點

        Parameters
        ----------
        p1 : str
            第一個畫像名稱
        p2 : str
            第二個畫像名稱
        """
        missing = []
        if p1 not in self._personas:
            missing.append(p1)
        if p2 not in self._personas:
            missing.append(p2)
        if missing:
            return f"❌ 找不到畫像：{', '.join(missing)}"

        a = self._personas[p1]
        b = self._personas[p2]

        def _compare_field(field_a, field_b, label):
            if field_a == field_b:
                return f"  {label}：{field_a} （一致）"
            return f"  {label}：{p1} → {field_a} ｜ {p2} → {field_b}"

        def _compare_list(list_a, list_b, label):
            shared = set(list_a) & set(list_b)
            only_a = set(list_a) - set(list_b)
            only_b = set(list_b) - set(list_a)
            parts = []
            if shared:
                parts.append(f"共同：{', '.join(sorted(shared))}")
            if only_a:
                parts.append(f"{p1} 特有：{', '.join(sorted(only_a))}")
            if only_b:
                parts.append(f"{p2} 特有：{', '.join(sorted(only_b))}")
            return f"  {label}：{' ｜ '.join(parts)}" if parts else f"  {label}：（均未設定）"

        lines = [
            f"⚖️ 畫像比較：{p1} vs {p2}",
            "",
        ]

        lines.append(_compare_field(a.get("age", 0) or "未設定", b.get("age", 0) or "未設定", "年齡"))
        lines.append(_compare_field(a.get("location", "未知"), b.get("location", "未知"), "地點"))
        lines.append(
            _compare_field(
                f"${a['income']:,.0f}" if a.get("income") else "未設定",
                f"${b['income']:,.0f}" if b.get("income") else "未設定",
                "收入",
            )
        )
        lines.append(_compare_list(a.get("interests", []), b.get("interests", []), "興趣"))
        lines.append(_compare_list(a.get("pain_points", []), b.get("pain_points", []), "痛點"))
        lines.append(_compare_list(a.get("channels", []), b.get("channels", []), "偏好管道"))
        lines.append(_compare_field(a.get("score", 0), b.get("score", 0), "行為評分"))
        lines.append(_compare_field(a["goals"]["primary"], b["goals"]["primary"], "主要目標"))

        return "\n".join(lines)
