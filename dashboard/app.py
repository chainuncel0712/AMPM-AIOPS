"""
量子機械控制台 - AMPM-AIOPS 神經核心監控面板 v5
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
_brain = None

def set_brain(brain: Any):
    global _brain
    _brain = brain

# ===== 量子機械控制台 HTML 模板 =====
TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚙️ AMPM-AIOPS 量子機械控制台 v5</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #050510;
            color: #00f0ff;
            font-family: 'Courier New', 'Consolas', monospace;
            padding: 20px;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        body::after {
            content: "";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 240, 255, 0.02) 0px,
                rgba(0, 240, 255, 0.02) 1px,
                transparent 1px,
                transparent 3px
            );
            pointer-events: none;
            z-index: 9999;
            animation: scanlines 0.1s linear infinite;
        }
        @keyframes scanlines {
            0% { transform: translateY(0); }
            100% { transform: translateY(3px); }
        }
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 5px #00f0ff, 0 0 10px rgba(0,240,255,0.3); }
            50% { box-shadow: 0 0 15px #00f0ff, 0 0 30px rgba(0,240,255,0.5); }
        }
        @keyframes flicker-text {
            0%, 100% { opacity: 1; }
            92% { opacity: 1; }
            93% { opacity: 0.8; }
            94% { opacity: 1; }
            96% { opacity: 0.9; }
            97% { opacity: 1; }
        }
        @keyframes neon-flicker {
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
                border-color: #00f0ff;
                box-shadow: 0 0 5px #00f0ff, inset 0 0 5px rgba(0,240,255,0.1);
            }
            20%, 24%, 55% {
                border-color: #0ff;
                box-shadow: 0 0 20px #00f0ff, 0 0 40px rgba(0,240,255,0.3), inset 0 0 10px rgba(0,240,255,0.15);
            }
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            font-size: 2em;
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid #00f0ff;
            margin-bottom: 30px;
            text-shadow: 0 0 15px #00f0ff, 0 0 30px rgba(0,240,255,0.5);
            animation: flicker-text 4s infinite;
            letter-spacing: 3px;
        }
        h2 {
            text-shadow: 0 0 8px #00f0ff;
            letter-spacing: 2px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #0a0a14;
            border: 1px solid #00f0ff;
            border-radius: 4px;
            padding: 15px;
            transition: all 0.3s;
            position: relative;
            box-shadow: 0 0 3px rgba(0,240,255,0.2), inset 0 0 3px rgba(0,240,255,0.05);
        }
        .card::before {
            content: "";
            position: absolute;
            top: -1px; left: -1px; right: -1px; bottom: -1px;
            border: 1px solid transparent;
            border-radius: 4px;
            pointer-events: none;
        }
        .card:hover {
            animation: pulse-glow 1.5s ease-in-out infinite;
            transform: translateY(-2px);
            border-color: #0ff;
        }
        .card h3 {
            color: #00f0ff;
            font-size: 1.1em;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(0,240,255,0.2);
            padding-bottom: 5px;
            text-shadow: 0 0 5px rgba(0,240,255,0.5);
            letter-spacing: 1px;
        }
        .card .value {
            font-size: 1.5em;
            color: #e0f7ff;
            margin: 10px 0;
            text-shadow: 0 0 8px rgba(0,240,255,0.4);
        }
        .card .label {
            color: rgba(0,240,255,0.5);
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        .status-ok { color: #00f0ff; text-shadow: 0 0 8px rgba(0,240,255,0.6); }
        .status-warn { color: #fbbf24; text-shadow: 0 0 8px rgba(251,191,36,0.5); }
        .status-err { color: #ef4444; text-shadow: 0 0 8px rgba(239,68,68,0.5); }
        .log-area {
            background: #03030a;
            border: 1px solid rgba(0,240,255,0.3);
            border-radius: 4px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 0.85em;
            line-height: 1.5;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        }
        .log-area::-webkit-scrollbar {
            width: 6px;
        }
        .log-area::-webkit-scrollbar-track {
            background: #050510;
        }
        .log-area::-webkit-scrollbar-thumb {
            background: rgba(0,240,255,0.3);
            border-radius: 3px;
        }
        .log-area::-webkit-scrollbar-thumb:hover {
            background: rgba(0,240,255,0.6);
        }
        .log-area .timestamp { color: rgba(0,240,255,0.4); }
        .log-area .info { color: #00f0ff; }
        .log-area .warn { color: #fbbf24; text-shadow: 0 0 4px rgba(251,191,36,0.3); }
        .log-area .error { color: #ef4444; text-shadow: 0 0 4px rgba(239,68,68,0.4); }
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(0,240,255,0.4);
            font-size: 0.8em;
            letter-spacing: 2px;
            text-shadow: 0 0 5px rgba(0,240,255,0.2);
        }
        .refresh-btn {
            background: #00f0ff;
            color: #050510;
            border: 1px solid #0ff;
            padding: 10px 20px;
            border-radius: 3px;
            cursor: pointer;
            font-family: 'Courier New', 'Consolas', monospace;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: none;
            box-shadow: 0 0 10px rgba(0,240,255,0.4);
            transition: all 0.3s;
            letter-spacing: 2px;
        }
        .refresh-btn:hover {
            background: #0ff;
            box-shadow: 0 0 20px rgba(0,240,255,0.7), 0 0 40px rgba(0,240,255,0.3);
            transform: scale(1.02);
        }
        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .progress-bar {
            height: 8px;
            background: rgba(0,240,255,0.08);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
            border: 1px solid rgba(0,240,255,0.15);
            box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0088aa, #00f0ff);
            border-radius: 4px;
            transition: width 0.5s;
            box-shadow: 0 0 10px rgba(0,240,255,0.6), inset 0 0 5px rgba(255,255,255,0.2);
            animation: progress-glow 2s ease-in-out infinite;
        }
        @keyframes progress-glow {
            0%, 100% { box-shadow: 0 0 8px rgba(0,240,255,0.5), inset 0 0 5px rgba(255,255,255,0.1); }
            50% { box-shadow: 0 0 18px rgba(0,240,255,0.8), inset 0 0 8px rgba(255,255,255,0.2); }
        }
        .sync-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00f0ff;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulse-dot 1.5s ease-in-out infinite;
            box-shadow: 0 0 6px rgba(0,240,255,0.7);
        }
        @keyframes pulse-dot {
            0%, 100% { opacity: 0.4; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.2); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ AMPM-AIOPS 量子機械控制台 v5</h1>
        <div style="text-align: center; margin-bottom: 20px;">
            <button class="refresh-btn" onclick="location.reload()">⟳ 系統同步</button>
            <span style="color: rgba(0,240,255,0.4); margin-left: 10px;">
                <span class="sync-indicator"></span>最後同步: {{ now }}
            </span>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🔩 機械組件</h3>
                <div class="value">{{ stats.total_organs }}</div>
                <div class="label">已載入組件單元</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ stats.organ_percent }}%"></div>
                </div>
            </div>
            <div class="card">
                <h3>🛠️ 工具協議</h3>
                <div class="value">{{ stats.tools_count }}</div>
                <div class="label">已註冊工具模組</div>
            </div>
            <div class="card">
                <h3>✅ 正常組件</h3>
                <div class="value status-ok">{{ stats.alive_count }}</div>
                <div class="label">運作中</div>
            </div>
            <div class="card">
                <h3>❌ 異常組件</h3>
                <div class="value status-err">{{ stats.dead_count }}</div>
                <div class="label">需維修</div>
            </div>
        </div>
        
        <h2 style="color: #00f0ff; margin-bottom: 15px;">📋 組件掃描</h2>
        <div class="grid">
            {% for organ in stats.organs %}
            <div class="card">
                <h3>{{ organ.display_name }}</h3>
                <div class="stats-row">
                    <span class="label">類別</span>
                    <span>{{ organ.type }}</span>
                </div>
                <div class="stats-row">
                    <span class="label">狀態</span>
                    <span class="{% if organ.alive %}status-ok{% else %}status-err{% endif %}">
                        {{ '✅ 正常' if organ.alive else '❌ 異常' }}
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <h2 style="color: #00f0ff; margin-bottom: 15px;">📜 核心日誌</h2>
        <div class="log-area">
            {% for log in logs %}
            <div>
                <span class="timestamp">{{ log.timestamp }}</span>
                <span class="{{ log.level }}">{{ log.message }}</span>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            AMPM-AIOPS Neural Core | 開源版 | 連線穩定
        </div>
    </div>
</body>
</html>
"""

def get_stats() -> Dict:
    """取得系統統計資料"""
    global _brain
    stats = {
        "total_organs": 0,
        "tools_count": 0,
        "alive_count": 0,
        "dead_count": 0,
        "organ_percent": 0,
        "organs": [],
    }
    
    if _brain is None:
        return stats
    
    # 取得器官資料
    organs = getattr(_brain, "organs", {})
    stats["total_organs"] = len(organs)
    
    # 取得工具數量
    langgraph = getattr(_brain, "langgraph", None)
    if langgraph:
        try:
            tools = langgraph.list_tools()
            stats["tools_count"] = len(tools)
        except:
            stats["tools_count"] = 0
    
    # 量子機械組件代號對應表
    organ_display_names = {
        "memory": "神經記憶矩陣 v3",
        "evolution": "進化演算核心 EVO-7",
        "self_learn": "自主學習陣列 SLA-5",
        "planner": "量子任務排程器 QTP-9",
        "web_search": "全域掃描陣列 GSA-X",
        "market_analyzer": "市場波動解析器 MWA-8",
        "customer_persona": "客戶神經畫像 CNP-4",
        "email_marketer": "量子通訊協議 QCP-2",
        "portfolio_tracker": "資產追蹤矩陣 PTM-6",
        "revenue_optimizer": "營收最大化引擎 RME-3",
        "auto_content_creator": "內容合成工廠 CSF-7",
        "seo_optimizer": "搜尋秩優化器 SRO-X",
        "social_media_manager": "社群訊號陣列 SSA-5",
        "smart_contract_auditor": "合約漏洞掃描器 CVS-4",
        "daily_growth_report": "每日成長分析儀 DGA-2",
        "nose": "分子嗅覺偵測器 MSD-1",
        "breath": "循環換氣單元 CVU-3",
        "cortex": "量子運算核心 QPU-9",
        "hypothalamus": "時序同步引擎 TS-7",
        "thalamus": "量子訊號中繼器 QSR-4",
        "self_repair": "奈米修復矩陣 NRM-2",
        "self_review": "自我審計引擎 SAE-5",
        "circuit_breaker": "量子斷路柵 QBG-3",
        "contradiction_detector": "邏輯矛盾掃描器 LCS-6",
        "health_checker": "系統診斷核心 SDC-8",
        "compass": "量子導航模組 QNM-1",
        "task_tracker": "任務狀態監控器 TSM-4",
        "tool_system": "工具協定矩陣 TPM-7",
        "plugin_loader": "插件注入引擎 PIE-2",
        "web_search_plugin": "搜尋協議擴展 SPE-X",
        "voice_ear": "聲波解析陣列 SPA-3",
        "vision_eye": "光學感測陣列 OSA-5",
        "nose_system": "氣味分子掃描器 OMS-1",
        "auto_grow": "自主進化引擎 AGE-4",
        "fallback_chain": "冗餘路徑協議 RPP-6",
        "registry": "組件註冊矩陣 CRM-2",
        "face": "全息顯示面板 HDP-1",
        "skin": "奈米裝甲外殼 NAH-3",
        "blood": "液冷循環系統 LCS-5",
        "muscle": "伺服驅動陣列 SDA-2",
        "womb": "組件製造艙 CMB-4",
        "waste": "廢熱回收單元 WRU-1",
        "bag": "量子儲存矩陣 QSM-3",
        "nerve": "光纖神經網路 FNN-7",
        "immune": "入侵防禦柵 IDG-5",
        "circuit": "量子電路系統 QCS-2",
        "brain": "神經核心矩陣 NCM-9",
        "self_awareness": "自我意識核心 SAC-1",
        "rebirth": "系統重生協議 SRP-3",
        "evolution_cycle": "進化週期引擎 ECE-5",
        "inheritance": "基因繼承矩陣 GIM-2",
        "crash_recovery": "崩潰復原協議 CRP-4",
        "input_guard": "輸入防火牆模組 IFM-7",
        "conversation": "對話神經網路 DNN-3",
        "feedback_learn": "反饋學習迴路 FLL-2",
        "task_planner": "任務規劃核心 TPC-5",
        "performance_profiler": "效能分析陣列 PPA-4",
        "crypto_wallet": "加密錢包模組 CWM-1",
        "gas_tracker": "燃料追蹤器 GTR-3",
        "cross_chain_bridge": "跨鏈橋接協議 CBP-2",
        "nft_sniper": "NFT 狙擊陣列 NSA-4",
        "nft_floor_scanner": "NFT 底價掃描器 NFS-5",
        "nft_whale_tracker": "NFT 鯨魚追蹤器 NWT-2",
        "nft_market_maker": "NFT 做市引擎 NME-3",
        "nft_airdrop_checker": "NFT 空投驗證器 NAC-1",
        "nft_manager": "NFT 管理矩陣 NFM-5",
        "market_data": "市場資料饋送 MDF-2",
        "ad_manager": "廣告投放引擎 ADE-4",
        "landing_page_crm": "著陸頁管理系統 LPM-2",
        "auto_learning": "自動學習迴路 ALL-3",
        "auto_job_system": "自動任務系統 AJS-2",
        "plugin_manager": "插件管理核心 PMC-5",
        "vision_analyzer": "視覺分析引擎 VAE-2",
        "vision_designer": "視覺設計核心 VDC-4",
        "domain_identity": "域身份協議 DIP-1",
        "social_promoter": "社群推廣引擎 SPE-3",
        "ebook_publisher": "電子書發布器 EBP-2",
        "crypto_hunter": "加密獵手陣列 CHA-4",
        "wealth_manager": "財富管理核心 WMC-3",
        "proactive_learner": "主動學習引擎 PLE-5",
        "nft_platform_manager": "NFT 平台管理器 NPM-2",
    }
    
    for name, organ in organs.items():
        if organ:
            display_name = organ_display_names.get(name, name)
            try:
                alive = organ.is_alive() if hasattr(organ, 'is_alive') else True
            except:
                alive = True
            stats["organs"].append({
                "name": name,
                "display_name": display_name,
                "type": type(organ).__name__,
                "alive": alive,
            })
            if alive:
                stats["alive_count"] += 1
            else:
                stats["dead_count"] += 1
    
    # 計算百分比
    if stats["total_organs"] > 0:
        stats["organ_percent"] = round(stats["alive_count"] / stats["total_organs"] * 100)
    
    return stats

def get_logs() -> List[Dict]:
    """取得系統日誌"""
    logs = []
    log_file = Path("data/startup_diagnosis.json")
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logs.append({
                "timestamp": data.get("timestamp", "?")[:19],
                "level": "info",
                "message": f"啟動自檢完成，組件數: {data.get('total_organs', 0)}"
            })
        except:
            pass
    
    # 加入 hypothalamus 日誌
    if _brain:
        hypothalamus = getattr(_brain, "hypothalamus", None)
        if hypothalamus:
            logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "info",
                "message": "時序同步引擎運作中"
            })
    
    # 加入 langgraph 日誌
    if _brain:
        langgraph = getattr(_brain, "langgraph", None)
        if langgraph:
            try:
                tools = langgraph.list_tools()
                logs.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "info",
                    "message": f"量子思考引擎就緒，已註冊 {len(tools)} 個工具模組"
                })
            except:
                pass
    
    # 加入記憶系統日誌
    memory_file = Path("data/long_term_memory.json")
    if memory_file.exists():
        try:
            import json
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logs.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "info",
                "message": f"神經記憶矩陣就緒，共 {len(data)} 筆記錄"
            })
        except:
            pass
    
    return logs[-50:]  # 只顯示最近 50 筆

@app.route("/")
def index():
    """主頁面"""
    stats = get_stats()
    logs = get_logs()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(TEMPLATE, stats=stats, logs=logs, now=now)

@app.route("/api/stats")
def api_stats():
    """API - 取得統計資料"""
    return jsonify(get_stats())

@app.route("/api/logs")
def api_logs():
    """API - 取得日誌"""
    return jsonify(get_logs())

@app.route("/api/organs")
def api_organs():
    """API - 取得組件清單"""
    stats = get_stats()
    return jsonify(stats["organs"])

@app.route("/health")
def health():
    """健康檢查端點"""
    stats = get_stats()
    alive = stats["alive_count"]
    total = stats["total_organs"]
    status_code = 200 if total > 0 and alive > 0 else 503
    return jsonify({
        "status": "ok" if status_code == 200 else "degraded",
        "organs": f"{alive}/{total}",
        "tools": stats["tools_count"],
        "brain": "alive",
    }), status_code

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
