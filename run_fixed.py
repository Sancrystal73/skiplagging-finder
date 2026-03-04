# run.py - 完整的 Flask 启动脚本（修复版）
import os
import sys

# ========== 修改这里：你的代理地址 ==========
# Clash 用户用: http://127.0.0.1:7890
# v2rayN 用户用: socks5://127.0.0.1:10808
PROXY = "http://127.0.0.1:7890"  # ← 改成你的

os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY
# ==========================================

print("="*50)
print("Skiplagging Finder 启动中...")
print(f"代理: {PROXY}")
print("="*50)

# 检查依赖
try:
    from flask import Flask, render_template_string, request, jsonify
    import requests
except ImportError:
    print("请先安装依赖：pip install flask requests")
    sys.exit(1)

# ========== AirLabs API Key ==========
AIRLABS_API_KEY = "870c8003-7051-4496-990b-01b0eeec5f5f"
# =====================================

# ========== 简化版 HTML 模板 ==========
HTML_PAGE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skiplagging Finder</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 10px; }
        .subtitle { color: rgba(255,255,255,0.8); text-align: center; margin-bottom: 30px; }
        .card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        .form-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
        .form-group { flex: 1; min-width: 120px; }
        label { display: block; font-size: 12px; color: #666; margin-bottom: 6px; }
        input { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 16px; }
        button { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; }
        button:disabled { opacity: 0.6; }
        .results { margin-top: 24px; }
        .flight-card { background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 16px; border-left: 4px solid #667eea; }
        .flight-card.skiplagging { border-left-color: #10b981; background: #ecfdf5; }
        .airline { font-weight: 600; color: #333; }
        .price { font-size: 24px; font-weight: 700; color: #667eea; }
        .savings { font-size: 14px; color: #10b981; margin-left: 8px; }
        .tag { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 8px; }
        .tag.direct { background: #e0e7ff; color: #667eea; }
        .tag.skiplagging { background: #d1fae5; color: #059669; }
        .loading { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✈️ Skiplagging Finder</h1>
        <p class="subtitle">AirLabs 真实航线 + Google Flights 价格</p>
        
        <div class="card">
            <form id="searchForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>出发地</label>
                        <input type="text" id="origin" placeholder="如: JFK" maxlength="3" required>
                    </div>
                    <div class="form-group">
                        <label>目的地</label>
                        <input type="text" id="destination" placeholder="如: LAX" maxlength="3" required>
                    </div>
                    <div class="form-group">
                        <label>日期</label>
                        <input type="date" id="date" required>
                    </div>
                </div>
                <button type="submit" id="searchBtn">🔍 搜索机票</button>
            </form>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById("date").value = tomorrow.toISOString().split("T")[0];
        
        document.getElementById("searchForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            const origin = document.getElementById("origin").value.toUpperCase();
            const destination = document.getElementById("destination").value.toUpperCase();
            const date = document.getElementById("date").value;
            const resultsDiv = document.getElementById("results");
            const btn = document.getElementById("searchBtn");
            
            btn.disabled = true;
            btn.textContent = "搜索中...";
            resultsDiv.innerHTML = '<div class="loading">正在搜索...</div>';
            
            try {
                const response = await fetch("/search", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ origin, destination, date })
                });
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div style="color:red">❌ ${data.error}</div>`;
                    return;
                }
                
                let html = '<div class="results">';
                if (data.direct) {
                    html += `
                        <div class="flight-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                <span class="airline">${data.direct.airline}</span>
                                <span class="price">$${data.direct.price}</span>
                            </div>
                            <div style="color:#666;margin-bottom:4px;">${data.direct.origin} → ${data.direct.destination}</div>
                            <div style="color:#999;font-size:14px;">${data.direct.departure} - ${data.direct.arrival}</div>
                            <span class="tag direct">直飞</span>
                        </div>
                    `;
                }
                
                if (data.skiplagging && data.skiplagging.length > 0) {
                    html += `<h3 style="margin:24px 0 16px;color:#333;">💰 找到 ${data.skiplagging.length} 个机会</h3>`;
                    data.skiplagging.forEach((opt) => {
                        const savings = (data.direct.price - opt.price).toFixed(0);
                        html += `
                            <div class="flight-card skiplagging">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                    <span class="airline">${opt.airline}</span>
                                    <span class="price">$${opt.price}<span class="savings">省 $${savings}</span></span>
                                </div>
                                <div style="color:#666;margin-bottom:4px;">
                                    ${opt.origin} → <b style="color:#10b981">${opt.via}</b> → <s>${opt.destination}</s>
                                </div>
                                <div style="color:#999;font-size:14px;">${opt.departure} - ${opt.arrival}</div>
                                <span class="tag skiplagging">在 ${opt.via} 下机</span>
                            </div>
                        `;
                    });
                }
                html += "</div>";
                resultsDiv.innerHTML = html;
            } catch (err) {
                resultsDiv.innerHTML = `<div style="color:red">错误: ${err.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = "🔍 搜索机票";
            }
        });
    </script>
</body>
</html>
'''
# =====================================

# ========== 创建 Flask 应用 ==========
app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    date = data.get('date', '')
    
    if not origin or not destination or not date:
        return jsonify({"error": "请填写所有字段"}), 400
    
    try:
        # 使用 AirLabs + 智能估算
        from skiplagging_airlabs import AirLabsSkiplaggingFinder
        finder = AirLabsSkiplaggingFinder(api_key=AIRLABS_API_KEY)
        result = finder.find_skiplagging_opportunities(origin, destination, date)
        
        response = {
            "direct": None,
            "skiplagging": [],
            "savings": result.get("savings", 0),
        }
        
        if result.get("direct"):
            d = result["direct"]
            response["direct"] = {
                "origin": d.origin,
                "destination": d.destination,
                "price": d.price,
                "airline": d.airline,
                "flight_number": d.flight_number,
                "departure": d.departure,
                "arrival": d.arrival,
            }
        
        if result.get("skiplagging"):
            for f in result["skiplagging"]:
                response["skiplagging"].append({
                    "origin": f.origin,
                    "destination": f.destination,
                    "price": f.price,
                    "airline": f.airline,
                    "flight_number": f.flight_number,
                    "departure": f.departure,
                    "arrival": f.arrival,
                    "via": f.via,
                })
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("✓ 服务器启动成功！")
    print("请在浏览器打开: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
