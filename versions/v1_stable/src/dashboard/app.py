"""
簡單儀表板 - 網頁介面查看黑曜狀態
"""

from flask import Flask, jsonify, render_template_string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from brain import Obsidian

app = Flask(__name__)

# 初始化黑曜（只做一次）
print("🧠 載入黑曜大腦...")
brain = Obsidian()
print("✅ 儀表板就緒")

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>黑曜儀表板</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #0d1117; color: #c9d1d9; }
        h1 { color: #58a6ff; }
        .card { background: #161b22; border-radius: 10px; padding: 15px; margin: 10px 0; border: 1px solid #30363d; }
        .stat { display: inline-block; margin: 10px 20px; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2ea043; }
        .stat-label { font-size: 12px; color: #8b949e; }
        .warning { color: #f85149; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #30363d; }
        th { color: #58a6ff; }
    </style>
</head>
<body>
    <h1>🧠 黑曜大腦儀表板</h1>
    <p>最後更新: {{ time }}</p>
    
    <div class="card">
        <h3>📊 核心統計</h3>
        <div class="stat"><span class="stat-value">{{ stats.tools }}</span><br><span class="stat-label">工具數</span></div>
        <div class="stat"><span class="stat-value">{{ stats.memories }}</span><br><span class="stat-label">記憶數</span></div>
        <div class="stat"><span class="stat-value">{{ stats.agents }}</span><br><span class="stat-label">代理數</span></div>
        <div class="stat"><span class="stat-value">{{ stats.models }}</span><br><span class="stat-label">模型數</span></div>
        <div class="stat"><span class="stat-value">{{ stats.version }}</span><br><span class="stat-label">版本</span></div>
    </div>
    
    <div class="card">
        <h3>🔄 循環監控</h3>
        <div>檢查次數: {{ circuit.total_checks }}</div>
        <div>阻擋次數: {{ circuit.blocks }}</div>
        <div>迴圈計數: {{ circuit.breaker.loop_count }}</div>
    </div>
    
    <div class="card">
        <h3>💾 最近記憶</h3>
        <table>
            <tr><th>內容</th><th>重要性</th></tr>
            {% for fact in recent_facts %}
            <tr>
                <td>{{ fact.fact[:80] }}{% if fact.fact|length > 80 %}...{% endif %}</td>
                <td>{{ fact.importance }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="card">
        <h3>📋 待辦任務</h3>
        <table>
            <tr><th>任務</th><th>優先級</th><th>狀態</th></tr>
            {% for task in tasks %}
            <tr>
                <td>{{ task.title }}</td>
                <td>{{ task.priority }}</td>
                <td>{{ task.status }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="card">
        <h3>🛠️ 可用工具</h3>
        <table>
            <tr><th>名稱</th><th>描述</th><th>使用次數</th></tr>
            {% for name, info in tools %}
            <tr>
                <td>{{ name }}</td>
                <td>{{ info.description[:50] }}</td>
                <td>{{ info.use_count }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    from datetime import datetime
    
    # 取得統計
    stats = {
        "tools": len(brain.tools.list_all()),
        "memories": len(brain.memory.get_all_facts()),
        "agents": brain.agents.get_agent_status()['total'],
        "models": len(brain.models.switcher.registry.models),
        "version": brain.evolution.version['number']
    }
    
    # 循環監控狀態
    circuit_status = brain.circuit.get_status()
    
    # 最近記憶
    recent_facts = brain.memory.semantic[-10:]
    
    # 待辦任務
    tasks = brain.tasks.list_pending()
    
    # 工具列表
    tools_list = list(brain.tools.list_all().items())
    
    return render_template_string(
        HTML_TEMPLATE,
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stats=stats,
        circuit=circuit_status,
        recent_facts=recent_facts,
        tasks=tasks,
        tools=tools_list
    )

@app.route('/api/status')
def api_status():
    """JSON API 給其他程式呼叫"""
    return jsonify({
        "stats": {
            "tools": len(brain.tools.list_all()),
            "memories": len(brain.memory.get_all_facts()),
            "agents": brain.agents.get_agent_status()['total'],
        },
        "circuit": brain.circuit.get_status(),
        "health": brain.circuit.health.check_system()
    })

def main():
    print("🌐 啟動儀表板: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
