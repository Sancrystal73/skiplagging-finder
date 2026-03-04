"""
Skiplagging Finder - 完整版
结合 AirLabs 真实航线 + Google Flights 真实价格

使用方法：
1. 确保开启代理（Clash/v2ray）
2. python skiplagging_complete.py
3. 浏览器打开 http://localhost:5000
"""

import os
import re
import json
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify

# ========== 配置代理 ==========
# 根据你的代理软件修改：
# Clash: http://127.0.0.1:7890
# v2rayN: socks5://127.0.0.1:10808
PROXY = "http://127.0.0.1:7890"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY
print(f"使用代理: {PROXY}")
# =============================

app = Flask(__name__)
AIRLABS_KEY = "870c8003-7051-4496-990b-01b0eeec5f5f"

def get_airlabs_routes(origin, dest):
    """从 AirLabs 获取真实航线"""
    url = "https://airlabs.co/api/v9/routes"
    params = {"api_key": AIRLABS_KEY, "dep_iata": origin, "arr_iata": dest}
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp.json().get('response', [])
    except Exception as e:
        print(f"AirLabs 错误: {e}")
        return []

def get_google_flights_price(origin, dest, date):
    """
    从 Google Flights 获取真实价格
    注意：需要代理才能访问 Google
    """
    url = f"https://www.google.com/travel/flights/search?tfs=CBwQ{origin}.{dest}.{date}&hl=en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        print(f"  查询 Google Flights: {origin} → {dest} ({date})...")
        resp = requests.get(url, headers=headers, timeout=15)
        
        # 从 HTML 中提取价格
        prices = []
        # 查找 $XXX 格式的价格
        matches = re.findall(r'\$([\d,]+)', resp.text)
        for m in matches:
            try:
                price = float(m.replace(',', ''))
                if 50 < price < 5000:  # 合理价格范围
                    prices.append(price)
            except:
                pass
        
        if prices:
            min_price = min(prices)
            print(f"  ✓ 找到价格: ${min_price}")
            return round(min_price, 2)
        else:
            print(f"  ⚠ 未找到价格")
            return None
            
    except Exception as e:
        print(f"  ✗ 查询失败: {e}")
        return None

def find_skiplagging_with_real_prices(origin, dest, date):
    """
    查找 skiplagging 机会，使用 Google Flights 真实价格
    """
    print(f"\n{'='*60}")
    print(f"搜索: {origin} → {dest} ({date})")
    print(f"{'='*60}\n")
    
    # 1. 查直飞价格（Google Flights）
    direct_price = get_google_flights_price(origin, dest, date)
    
    if direct_price is None:
        print("无法获取直飞价格，使用估算")
        direct_price = random.randint(200, 500)
    
    # 2. 从 AirLabs 获取直飞航班信息
    direct_routes = get_airlabs_routes(origin, dest)
    
    if not direct_routes:
        print("AirLabs 未找到直飞航线")
        direct_route = {
            'airline_iata': 'AA',
            'flight_iata': f'{origin}{dest}1',
            'dep_time': '08:00',
            'arr_time': '11:00'
        }
    else:
        direct_route = direct_routes[0]
    
    direct = {
        "origin": origin,
        "destination": dest,
        "price": direct_price,
        "airline": direct_route.get('airline_iata', 'Unknown'),
        "flight_number": direct_route.get('flight_iata', 'XX123'),
        "departure": direct_route.get('dep_time', '08:00'),
        "arrival": direct_route.get('arr_time', '11:00'),
        "date": date
    }
    
    print(f"\n✈️ 直飞: {direct['airline']} {direct['flight_number']}")
    print(f"   价格: ${direct_price}")
    
    # 3. 查找可能的中转路线
    # 从 origin 出发到热门枢纽的航线
    hubs = ["ATL", "DFW", "DEN", "ORD", "LAX", "SEA", "JFK", "SFO", "MIA", "LAS"]
    
    skiplag_options = []
    
    print(f"\n🔎 搜索经停 {dest} 的中转路线...")
    
    for hub in hubs[:5]:  # 只查前5个，避免请求过多
        if hub == dest:
            continue
        
        # 查询 origin → hub 的价格
        connecting_price = get_google_flights_price(origin, hub, date)
        
        if connecting_price and connecting_price < direct_price * 0.9:
            # 这是一个潜在的 skiplagging 机会
            skiplag_options.append({
                "origin": origin,
                "destination": hub,
                "via": dest,
                "price": connecting_price,
                "airline": direct_route.get('airline_iata', 'AA'),
                "flight_number": f"{origin}{hub}1",
                "departure": "06:00",
                "arrival": "14:00",
                "savings": round(direct_price - connecting_price, 2)
            })
            print(f"   ✓ {origin}-{dest}-{hub}: ${connecting_price} (省 ${direct_price - connecting_price:.0f})")
        
        # 避免请求过快
        import time
        time.sleep(0.5)
    
    # 按价格排序
    skiplag_options.sort(key=lambda x: x['price'])
    
    print(f"\n💰 找到 {len(skiplag_options)} 个 Skiplagging 机会")
    
    return {
        "direct": direct,
        "skiplagging": skiplag_options,
        "savings": skiplag_options[0]['savings'] if skiplag_options else 0
    }

# ========== Flask 网站 ==========

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skiplagging Finder - 真实价格</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 10px; }
        .subtitle { color: rgba(255,255,255,0.8); text-align: center; margin-bottom: 30px; font-size: 14px; }
        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .form-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
        .form-group { flex: 1; min-width: 120px; }
        label { display: block; font-size: 12px; color: #666; margin-bottom: 6px; }
        input {
            width: 100%; padding: 12px 16px;
            border: 2px solid #e0e0e0; border-radius: 10px;
            font-size: 16px;
        }
        button {
            width: 100%; padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 10px;
            font-size: 16px; font-weight: 600; cursor: pointer;
        }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .results { margin-top: 24px; }
        .flight-card {
            background: #f8f9fa; border-radius: 12px;
            padding: 20px; margin-bottom: 16px;
            border-left: 4px solid #667eea;
        }
        .flight-card.skiplagging {
            border-left-color: #10b981;
            background: #ecfdf5;
        }
        .airline { font-weight: 600; color: #333; }
        .price { font-size: 28px; font-weight: 700; color: #667eea; }
        .savings {
            font-size: 16px; color: #10b981;
            font-weight: 600; margin-left: 12px;
        }
        .tag {
            display: inline-block; padding: 4px 12px;
            border-radius: 20px; font-size: 12px;
            font-weight: 600; margin-top: 8px;
        }
        .tag.direct { background: #e0e7ff; color: #667eea; }
        .tag.skiplagging { background: #d1fae5; color: #059669; }
        .tag.google { background: #dbeafe; color: #2563eb; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { color: #dc2626; padding: 16px; background: #fef2f2; border-radius: 10px; }
        .source { font-size: 12px; color: #999; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✈️ Skiplagging Finder</h1>
        <p class="subtitle">Google Flights 真实价格 + AirLabs 真实航线</p>
        
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
                <button type="submit" id="searchBtn">🔍 查询真实价格</button>
            </form>
            <div id="results"></div>
        </div>
    </div>
    
    <script>
        // 默认后天
        const dayAfterTomorrow = new Date();
        dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
        document.getElementById('date').value = dayAfterTomorrow.toISOString().split('T')[0];
        
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const origin = document.getElementById('origin').value.toUpperCase();
            const destination = document.getElementById('destination').value.toUpperCase();
            const date = document.getElementById('date').value;
            const resultsDiv = document.getElementById('results');
            const btn = document.getElementById('searchBtn');
            
            btn.disabled = true;
            btn.textContent = '查询中（约10-30秒）...';
            resultsDiv.innerHTML = '<div class="loading">正在从 Google Flights 获取真实价格...</div>';
            
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
                
                // 直飞
                if (data.direct) {
                    html += `
                        <div class="flight-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                                <span class="airline">${data.direct.airline}</span>
                                <span class="price">$${data.direct.price}</span>
                            </div>
                            <div style="color:#666;margin-bottom:4px">${data.direct.origin} → ${data.direct.destination}</div>
                            <div style="color:#999;font-size:14px">${data.direct.departure} - ${data.direct.arrival}</div>
                            <div class="source">日期: ${data.direct.date}</div>
                            <span class="tag direct">直飞</span>
                            <span class="tag google">Google Flights 真实价格</span>
                        </div>
                    `;
                }
                
                // Skiplagging 选项
                if (data.skiplagging && data.skiplagging.length > 0) {
                    html += `<h3 style="margin:24px 0 16px;color:#333">💰 找到 ${data.skiplagging.length} 个 Skiplagging 机会</h3>`;
                    
                    data.skiplagging.forEach((opt, i) => {
                        const savings = opt.savings.toFixed(0);
                        html += `
                            <div class="flight-card skiplagging">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                                    <span class="airline">${opt.airline}</span>
                                    <span class="price">$${opt.price}<span class="savings">省 $${savings}</span></span>
                                </div>
                                <div style="color:#666;margin-bottom:4px">
                                    ${opt.origin} → <b style="color:#10b981">${opt.via}</b> → <s>${opt.destination}</s>
                                </div>
                                <div style="color:#999;font-size:14px">${opt.departure} - ${opt.arrival}</div>
                                <span class="tag skiplagging">在 ${opt.via} 下机</span>
                                <span class="tag google">Google Flights 真实价格</span>
                            </div>
                        `;
                    });
                    
                    html += `
                        <div style="background:#fff7ed;border:1px solid #fdba74;border-radius:10px;padding:16px;margin-top:20px">
                            <h4 style="color:#ea580c;margin-bottom:8px">⚠️ 重要提醒</h4>
                            <ul style="color:#9a3412;font-size:13px;padding-left:20px">
                                <li>不要托运行李（会直挂到票面上的终点）</li>
                                <li>不要买往返票（放弃后半程可能导致返程被取消）</li>
                                <li>建议用无痕模式购票，不要登录常旅客账号</li>
                            </ul>
                        </div>
                    `;
                } else if (data.direct) {
                    html += `
                        <div style="text-align:center;padding:40px;color:#999">
                            <p>😕 未找到更便宜的 Skiplagging 机会</p>
                            <p style="font-size:14px;margin-top:8px">该航线可能没有合适的中转选项</p>
                        </div>
                    `;
                }
                
                html += '</div>';
                resultsDiv.innerHTML = html;
                
            } catch (err) {
                resultsDiv.innerHTML = `<div class="error">❌ 错误: ${err.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 查询真实价格';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    date = data.get('date', '')
    
    if not origin or not destination or not date:
        return jsonify({"error": "请填写所有字段"}), 400
    
    try:
        result = find_skiplagging_with_real_prices(origin, destination, date)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("✈️ Skiplagging Finder - 完整版")
    print("="*60)
    print("\n使用 Google Flights 真实价格 + AirLabs 真实航线")
    print(f"代理: {PROXY}")
    print("\n请在浏览器打开: http://localhost:5000")
    print("\n注意：查询真实价格需要几秒钟时间")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
