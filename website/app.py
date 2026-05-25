"""AMPM-AIOPS.COM 付款註冊網頁伺服器"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, render_template, request, jsonify

from payment_verifier import verify_tx
from license_manager import generate_key

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/activate', methods=['POST'])
def activate():
    data = request.get_json()
    txid = (data.get('txid', '') if data else '').strip()
    if not txid:
        return jsonify({"success": False, "message": "❌ 請輸入 TXID"})

    result = verify_tx(txid)
    if not result.get("success"):
        return jsonify({"success": False, "message": result.get("message", "驗證失敗")})

    days = result.get("days", 30)
    tier = result.get("tier", "basic")
    plan = result.get("plan", "月方案")
    license_key = generate_key(0, days, tier)

    return jsonify({
        "success": True,
        "message": f"收到 {result['amount']:.2f} USDT，符合{plan}（{days} 天）",
        "license_key": license_key,
        "plan": plan,
        "days": days,
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5051))
    print(f"🌐 AMPM 註冊網站啟動：http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
