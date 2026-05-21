"""DailyGrowthReportOrgan - 每日成長報告器官

負責產生每日成長報告，追蹤系統指標（器官數、進化分數、任務完成數、錯誤數、上線時間）
與業務指標（營收、用戶數、互動率），並以時間戳儲存每日報告，
支援 KPI 與目標值的對比分析。
"""
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from skeleton.brain_component import BrainComponent
from tools import tool


class DailyGrowthReportOrgan(BrainComponent):
    """每日成長報告器官

    每日產出完整報告，涵蓋系統健康與業務成長兩個維度，
    支援歷史查詢、KPI 摘要與目標對比。
    """

    def __init__(self, dna: Optional[dict] = None):
        """初始化每日成長報告器官

        Parameters
        ----------
        dna : dict, optional
            器官的 DNA 設定
        """
        super().__init__(dna)
        self._reports: List[Dict[str, Any]] = []
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._created_at = datetime.now().isoformat()

        # 初始化預設指標與目標
        self._init_default_metrics()

    def _init_default_metrics(self) -> None:
        """初始化預設的指標與目標值"""
        defaults = {
            # 系統指標
            "organ_count": {"value": 0, "target": 30, "category": "系統", "unit": "個"},
            "evolution_score": {"value": 0, "target": 85, "category": "系統", "unit": "分"},
            "tasks_completed": {"value": 0, "target": 100, "category": "系統", "unit": "個"},
            "errors": {"value": 0, "target": 5, "category": "系統", "unit": "次"},
            "uptime": {"value": 0, "target": 99.9, "category": "系統", "unit": "%"},
            # 業務指標
            "revenue": {"value": 0, "target": 5000, "category": "業務", "unit": "USD"},
            "users": {"value": 0, "target": 1000, "category": "業務", "unit": "人"},
            "engagement": {"value": 0, "target": 60, "category": "業務", "unit": "%"},
        }
        self._metrics = defaults

    def status(self) -> dict:
        """回報器官狀態"""
        report_count = len(self._reports)
        last_report_date = self._reports[-1]["date"] if self._reports else None
        return {
            "name": "DailyGrowthReportOrgan",
            "alive": True,
            "report_count": report_count,
            "last_report_date": last_report_date,
            "metrics_tracked": len(self._metrics),
            "system_metrics": self._get_metrics_by_category("系統"),
            "business_metrics": self._get_metrics_by_category("業務"),
        }

    def _get_metrics_by_category(self, category: str) -> Dict[str, float]:
        """取得指定類別的所有指標值"""
        return {
            k: v["value"]
            for k, v in self._metrics.items()
            if v.get("category") == category
        }

    @tool(name="generate_report", description="產生每日成長報告並儲存")
    def generate_report(self) -> str:
        """產生當日的完整成長報告

        報告涵蓋系統指標與業務指標，包含 KPI 達成率分析與建議。
        報告會自動儲存到歷史記錄中。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        now_iso = datetime.now().isoformat()

        # 產生報告資料
        system_metrics = self._get_metrics_by_category("系統")
        business_metrics = self._get_metrics_by_category("業務")

        # KPI 達成率
        kpi_details = {}
        for k, v in self._metrics.items():
            target = v["target"]
            value = v["value"]
            if target > 0:
                achievement = min(round(value / target * 100, 1), 999.9)
            else:
                achievement = 100.0 if value == 0 else 200.0
            kpi_details[k] = {
                "value": value,
                "target": target,
                "achievement": achievement,
                "status": "達標" if achievement >= 100 else ("接近" if achievement >= 80 else "落後"),
                "category": v["category"],
                "unit": v["unit"],
            }

        # 異常檢測
        anomalies = []
        if kpi_details.get("errors", {}).get("value", 0) > kpi_details.get("errors", {}).get("target", 5):
            anomalies.append("⚠️ 錯誤數超過目標值，建議檢查系統穩定性")
        if kpi_details.get("uptime", {}).get("achievement", 100) < 99:
            anomalies.append("⚠️ 上線時間低於 99%，建議排查當機原因")
        if kpi_details.get("revenue", {}).get("achievement", 100) < 80:
            anomalies.append("⚠️ 營收未達目標的 80%，建議檢視營收策略")

        # 與昨日對比（若有歷史記錄）
        prev_comparison = {}
        if self._reports:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            for historic in reversed(self._reports):
                if historic.get("date") == yesterday:
                    for k in self._metrics:
                        prev_val = historic.get("metrics", {}).get(k, {}).get("value", 0)
                        curr_val = kpi_details.get(k, {}).get("value", 0)
                        if prev_val != curr_val:
                            delta = curr_val - prev_val
                            prev_comparison[k] = {
                                "prev": prev_val,
                                "curr": curr_val,
                                "delta": delta,
                                "delta_pct": round(delta / prev_val * 100, 1) if prev_val else 0,
                            }
                    break

        # 儲存報告
        report = {
            "date": today,
            "generated_at": now_iso,
            "metrics": kpi_details,
            "anomalies": anomalies,
            "prev_comparison": prev_comparison,
        }
        self._reports.append(report)

        # 組裝輸出
        lines = [
            f"📊 每日成長報告 — {today}",
            "",
            "🤖 系統指標：",
        ]
        for k, v in kpi_details.items():
            if v["category"] == "系統":
                status_icon = {"達標": "✅", "接近": "🟡", "落後": "🔴"}.get(v["status"], "⚪")
                lines.append(
                    f"  {status_icon} {k}: {v['value']}{v['unit']} / 目標 {v['target']}{v['unit']} "
                    f"({v['achievement']}%)"
                )

        lines.append("")
        lines.append("💼 業務指標：")
        for k, v in kpi_details.items():
            if v["category"] == "業務":
                status_icon = {"達標": "✅", "接近": "🟡", "落後": "🔴"}.get(v["status"], "⚪")
                lines.append(
                    f"  {status_icon} {k}: {v['value']}{v['unit']} / 目標 {v['target']}{v['unit']} "
                    f"({v['achievement']}%)"
                )

        # 與昨日對比
        if prev_comparison:
            lines.append("")
            lines.append("📈 與昨日對比：")
            for k, comp in prev_comparison.items():
                arrow = "↑" if comp["delta"] > 0 else "↓" if comp["delta"] < 0 else "→"
                metric_def = self._metrics.get(k, {})
                unit = metric_def.get("unit", "")
                lines.append(
                    f"  {arrow} {k}: {comp['curr']}{unit} "
                    f"({comp['delta']:+}{unit}, {comp['delta_pct']:+.1f}%)"
                )

        # 異常警示
        if anomalies:
            lines.append("")
            lines.append("⚠️ 異常警示：")
            for a in anomalies:
                lines.append(f"  {a}")

        # 建議
        lines.append("")
        lines.append("💡 今日建議：")
        poor_kpis = [
            (k, v) for k, v in kpi_details.items() if v["status"] == "落後"
        ]
        if poor_kpis:
            for k, v in poor_kpis[:3]:
                suggestion_map = {
                    "organ_count": "建議使用 learn_from_user 擴充器官功能",
                    "evolution_score": "建議執行一次進化循環提升分數",
                    "tasks_completed": "建議檢查排程任務是否正常執行",
                    "errors": "建議使用 self_repair 修復已知錯誤",
                    "uptime": "建議檢查 crash_recovery 機製是否正常",
                    "revenue": "建議使用 revenue_optimizer 優化營收策略",
                    "users": "建議加強行銷活動吸引新用戶",
                    "engagement": "建議優化內容策略提升用戶互動",
                }
                lines.append(f"  - {suggestion_map.get(k, f'檢討 {k} 落後原因並製定改善計畫')}")
        else:
            lines.append("  🎉 所有指標目前達標或接近目標，繼續保持！")

        return "\n".join(lines)

    @tool(name="get_report_history", description="取得過去指定天數的報告歷史")
    def get_report_history(self, days: int = 7) -> str:
        """取得過去 N 天的報告歷史摘要

        Parameters
        ----------
        days : int
            欲查詢的天數
        """
        if not self._reports:
            return "📭 尚未產生任何報告，請先使用 generate_report"

        if not isinstance(days, int) or days <= 0:
            days = 7

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [r for r in self._reports if r["date"] >= cutoff]

        if not filtered:
            return f"📭 過去 {days} 天內無報告記錄"

        lines = [
            f"📋 過去 {days} 天報告歷史（共 {len(filtered)} 筆）",
            "",
        ]

        for r in sorted(filtered, key=lambda x: x["date"], reverse=True):
            total_kpis = len(r.get("metrics", {}))
            anomalies = len(r.get("anomalies", []))
            line = f"  {r['date']} — {total_kpis} 項 KPI"
            if anomalies:
                line += f"，⚠️ {anomalies} 項異常"
            else:
                line += "，✅ 無異常"
            lines.append(line)

        return "\n".join(lines)

    @tool(name="get_kpi_summary", description="取得 KPI 摘要，含目標達成率總覽")
    def get_kpi_summary(self) -> str:
        """取得所有 KPI 的摘要總覽，含達成率與趨勢"""
        if not self._reports:
            return "📭 尚未產生任何報告，請先使用 generate_report"

        lines = [
            "📊 KPI 摘要總覽",
            "",
        ]

        # 計算每個指標的近期趨勢與平均達成率
        for k, v in self._metrics.items():
            # 從歷史報告中擷取該指標的資料
            history_values = []
            for r in self._reports[-30:]:  # 最近 30 筆
                val = r.get("metrics", {}).get(k, {}).get("value", 0)
                history_values.append(val)

            current = v["value"]
            target = v["target"]
            achievement = round(current / target * 100, 1) if target > 0 else 100.0

            # 趨勢計算
            if len(history_values) >= 3:
                recent_3 = history_values[-3:]
                if recent_3[0] < recent_3[-1]:
                    trend = "↗ 上升"
                elif recent_3[0] > recent_3[-1]:
                    trend = "↘ 下降"
                else:
                    trend = "→ 持平"
            else:
                trend = "— 無歷史"

            unit = v.get("unit", "")
            lines.append(
                f"  {k}: {current}{unit} / {target}{unit} "
                f"({achievement}%) {trend}"
            )

        # 整體 KPI 健康度
        if self._reports:
            latest = self._reports[-1]
            metrics = latest.get("metrics", {})
            if metrics:
                avg_achievement = sum(
                    m["achievement"] for m in metrics.values()
                ) / len(metrics)
                if avg_achievement >= 95:
                    health = "🟢 優秀"
                elif avg_achievement >= 75:
                    health = "🟡 良好"
                else:
                    health = "🔴 需改善"

                lines.append("")
                lines.append(f"📈 整體 KPI 達成率：{avg_achievement:.1f}% — {health}")

        return "\n".join(lines)

    @tool(name="add_metric", description="新增或更新一項指標及其目標值")
    def add_metric(self, name: str, value: float, target: float) -> str:
        """新增或更新一項追蹤指標

        Parameters
        ----------
        name : str
            指標名稱
        value : float
            目前數值
        target : float
            目標數值
        """
        if not name or not isinstance(name, str):
            return "❌ 指標名稱不可為空且必須是字串"
        if not isinstance(value, (int, float)):
            return "❌ 數值必須為數字"
        if not isinstance(target, (int, float)) or target < 0:
            return "❌ 目標值必須為非負數"

        is_new = name not in self._metrics
        prev_value = self._metrics.get(name, {}).get("value", 0)

        self._metrics[name] = {
            "value": float(value),
            "target": float(target),
            "category": self._metrics.get(name, {}).get("category", "自訂"),
            "unit": self._metrics.get(name, {}).get("unit", ""),
        }

        achievement = round(value / target * 100, 1) if target > 0 else 100.0
        delta_str = ""
        if not is_new:
            delta = value - prev_value
            delta_str = f" (變化 {delta:+})"

        return (
            f"{'🆕' if is_new else '✏️'} 指標{'已新增' if is_new else '已更新'}：{name}\n"
            f"  目前值：{value}{delta_str}\n"
            f"  目標值：{target}\n"
            f"  達成率：{achievement}%"
        )

    @tool(name="list_metrics", description="列出所有追蹤中的指標")
    def list_metrics(self) -> str:
        """列出所有追蹤中的指標，按類別分組顯示"""
        if not self._metrics:
            return "📭 尚未追蹤任何指標"

        by_category: Dict[str, List[Tuple[str, Dict]]] = {}
        for k, v in self._metrics.items():
            cat = v.get("category", "未分類")
            by_category.setdefault(cat, []).append((k, v))

        lines = ["📋 指標總覽（按類別）", ""]
        for cat in sorted(by_category.keys()):
            lines.append(f"  ── {cat} ──")
            for k, v in sorted(by_category[cat], key=lambda x: x[0]):
                value = v["value"]
                target = v["target"]
                achievement = round(value / target * 100, 1) if target > 0 else 100.0
                unit = v.get("unit", "")
                status = "✅" if achievement >= 100 else "🟡" if achievement >= 80 else "🔴"
                lines.append(
                    f"  {status} {k}: {value}{unit} / {target}{unit} ({achievement}%)"
                )
            lines.append("")

        return "\n".join(lines)
