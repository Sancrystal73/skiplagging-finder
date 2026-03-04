from flask import Flask, render_template_string, request, jsonify
from skiplagging_airlabs import AirLabsSkiplaggingFinder
import os

app = Flask(__name__)

# AirLabs API Key
AIRLABS_API_KEY = "870c8003-7051-4496-990b-01b0eeec5f5f"

# HTML 模板 - 极简风格
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skiplagging Finder - 隐藏城市机票搜索</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2rem;
        }
        .subtitle {
            color: rgba(255,255,255,0.8);
            text-align: center;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .form-row {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .form-group {
            flex: 1;
            min-width: 120px;
        }
        label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .results {
            margin-top: 24px;
        }
        .flight-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid #667eea;
        }
        .flight-card.skiplagging {
            border-left-color: #10b981;
            background: #ecfdf5;
        }
        .flight-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .airline {
            font-weight: 600;
            color: #333;
        }
        .price {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        .price .savings {
            font-size: 14px;
            color: #10b981;
            font-weight: 600;
            margin-left: 8px;
        }
        .flight-route {
            display: flex;
            align-items: center;
            gap: 12px;
            color: #666;
            margin-bottom: 8px;
        }
        .arrow {
            color: #999;
        }
        .flight-time {
            color: #999;
            font-size: 14px;
        }
        .tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
        }
        .tag.direct {
            background: #e0e7ff;
            color: #667eea;
        }
        .tag.skiplagging {
            background: #d1fae5;
            color: #059669;
        }
        .warning {
            background: #fff7ed;
            border: 1px solid #fdba74;
            border-radius: 10px;
            padding: 16px;
            margin-top: 20px;
        }
        .warning h3 {
            color: #ea580c;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .warning ul {
            color: #9a3412;
            font-size: 13px;
            padding-left: 20px;
        }
        .warning li {
            margin-bottom: 4px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #e0e0e0;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 16px;
            border-radius: 10px;
            margin-top: 16px;
        }
        .empty {
            text-align: center;
            padding: 40px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✈️ Skiplagging Finder</h1>
        <p class="subtitle">隐藏城市机票搜索工具</p>
        
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
        // 设置默认日期为明天
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById('date').value = tomorrow.toISOString().split('T')[0];
        
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const origin = document.getElementById('origin').value.toUpperCase();
            const destination = document.getElementById('destination').value.toUpperCase();
            const date = document.getElementById('date').value;
            const resultsDiv = document.getElementById('results');
            const btn = document.getElementById('searchBtn');
            
            btn.disabled = true;
            btn.textContent = '搜索中...';
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>正在搜索机票...</div>';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ origin, destination, date })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                    return;
                }
                
                let html = '<div class="results">';
                
                // 直飞选项
                if (data.direct) {
                    html += `
                        <div class="flight-card">
                            <div class="flight-header">
                                <span class="airline">${data.direct.airline} ${data.direct.flight_number}</span>
                                <span class="price">$${data.direct.price}</span>
                            </div>
                            <div class="flight-route">
                                <span>${data.direct.origin}</span>
                                <span class="arrow">→</span>
                                <span>${data.direct.destination}</span>
                            </div>
                            <div class="flight-time">${data.direct.departure} - ${data.direct.arrival}</div>
                            <span class="tag direct">直飞</span>
                        </div>
                    `;
                }
                
                // Skiplagging 选项
                if (data.skiplagging && data.skiplagging.length > 0) {
                    html += `<h3 style="margin: 24px 0 16px; color: #333;">💰 找到 ${data.skiplagging.length} 个隐藏城市购票机会</h3>`;
                    
                    data.skiplagging.forEach((opt, i) => {
                        const savings = (data.direct.price - opt.price).toFixed(0);
                        html += `
                            <div class="flight-card skiplagging">
                                <div class="flight-header">
                                    <span class="airline">${opt.airline} ${opt.flight_number}</span>
                                    <span class="price">$${opt.price}<span class="savings">省 $${savings}</span></span>
                                </div>
                                <div class="flight-route">
                                    <span>${opt.origin}</span>
                                    <span class="arrow">→</span>
                                    <span style="color: #10b981; font-weight: 600;">${opt.via}</span>
                                    <span class="arrow">→</span>
                                    <span style="color: #999; text-decoration: line-through;">${opt.destination}</span>
                                </div>
                                <div class="flight-time">${opt.departure} - ${opt.arrival}</div>
                                <span class="tag skiplagging">💡 在 ${opt.via} 下机</span>
                            </div>
                        `;
                    });
                    
                    html += `
                        <div class="warning">
                            <h3>⚠️ 重要提醒</h3>
                            <ul>
                                <li>不要托运行李 - 行李会直挂到票面上的终点</li>
                                <li>不要买往返票 - 放弃后半程可能导致返程被取消</li>
                                <li>建议用无痕模式购票，不要登录常旅客账号</li>
                                <li>提前在线值机，避免柜台问题</li>
                            </ul>
                        </div>
                    `;
                } else if (data.direct) {
                    html += `
                        <div class="empty">
                            <p>😕 未找到更便宜的隐藏城市购票机会</p>
                            <p style="font-size: 14px; margin-top: 8px;">建议尝试其他日期或附近机场</p>
                        </div>
                    `;
                }
                
                html += '</div>';
                resultsDiv.innerHTML = html;
                
            } catch (err) {
                resultsDiv.innerHTML = `<div class="error">❌ 搜索出错: ${err.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 搜索机票';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    date = data.get('date', '')
    
    if not origin or not destination or not date:
        return jsonify({"error": "请填写所有字段"}), 400
    
    if len(origin) != 3 or len(destination) != 3:
        return jsonify({"error": "机场代码必须是3个字母（如 JFK, LAX）"}), 400
    
    try:
        finder = AirLabsSkiplaggingFinder(api_key=AIRLABS_API_KEY)
        result = finder.find_skiplagging_opportunities(origin, destination, date)
        
        # 转换结果为 JSON 可序列化格式
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
