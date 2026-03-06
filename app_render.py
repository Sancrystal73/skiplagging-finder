# app.py - Render 部署版本（带 FlightAPI 真实价格）
import os
import requests
import json
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)

# API Keys
AIRLABS_KEY = os.getenv('AIRLABS_API_KEY', '870c8003-7051-4496-990b-01b0eeec5f5f')
FLIGHTAPI_KEY = os.getenv('FLIGHTAPI_KEY', '')  # 从环境变量读取

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

def get_flightapi_price(origin, dest, date):
    """
    从 FlightAPI.io 获取真实价格
    URL格式: /onewaytrip/{api_key}/{from}/{to}/{date}/{adults}/{children}/{infants}
    """
    if not FLIGHTAPI_KEY:
        return None
    
    # 转换日期格式 yyyy-mm-dd 为 yyyymmdd
    date_clean = date.replace('-', '')
    
    url = f"https://api.flightapi.io/onewaytrip/{FLIGHTAPI_KEY}/{origin}/{dest}/{date_clean}/1/0/0"
    
    try:
        print(f"查询 FlightAPI: {origin} -> {dest} ({date})")
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                # 返回最便宜的航班
                cheapest = min(data, key=lambda x: x.get('price', float('inf')))
                return {
                    'price': cheapest.get('price'),
                    'airline': cheapest.get('airline'),
                    'flight_number': cheapest.get('flightNumber'),
                    'departure': cheapest.get('departureTime'),
                    'arrival': cheapest.get('arrivalTime'),
                }
        else:
            print(f"FlightAPI 错误: {resp.status_code}")
            
    except Exception as e:
        print(f"FlightAPI 请求失败: {e}")
    
    return None

def find_skiplagging(origin, dest, date):
    """
    查找 skiplagging 机会
    1. AirLabs 获取航线信息
    2. FlightAPI 获取真实价格
    3. 查找中转路线
    """
    print(f"\n搜索: {origin} -> {dest} ({date})")
    
    # 1. 获取直飞航线和价格
    direct_route = None
    direct_price = None
    
    # 先尝试 FlightAPI 真实价格
    flightapi_data = get_flightapi_price(origin, dest, date)
    
    if flightapi_data:
        direct_price = flightapi_data['price']
        direct_route = {
            'origin': origin,
            'destination': dest,
            'price': direct_price,
            'airline': flightapi_data['airline'],
            'flight_number': flightapi_data['flight_number'],
            'departure': flightapi_data['departure'],
            'arrival': flightapi_data['arrival'],
            'data_source': 'FlightAPI'
        }
        print(f"✅ FlightAPI 直飞价格: ${direct_price}")
    else:
        # Fallback: 用 AirLabs + 估算
        routes = get_airlabs_routes(origin, dest)
        if routes:
            route = routes[0]
            # 估算价格
            duration = route.get('duration', 300)
            direct_price = max(duration * 0.5, 150)  # 简单估算
            direct_route = {
                'origin': origin,
                'destination': dest,
                'price': round(direct_price, 2),
                'airline': route.get('airline_iata', 'Unknown'),
                'flight_number': route.get('flight_iata', 'XX123'),
                'departure': route.get('dep_time', '08:00'),
                'arrival': route.get('arr_time', '11:00'),
                'data_source': 'AirLabs (估算)'
            }
            print(f"⚠️ AirLabs 估算价格: ${direct_price}")
    
    if not direct_route:
        return {'error': '未找到直飞航线', 'direct': None, 'skiplagging': []}
    
    # 2. 查找 skiplagging 机会（中转路线）
    skiplag_options = []
    
    # 常见枢纽机场
    hubs = ['ATL', 'DFW', 'DEN', 'ORD', 'LAX', 'SEA', 'JFK', 'SFO', 'MIA', 'LAS', 'PHX', 'BOS']
    
    for hub in hubs[:5]:  # 限制数量，避免请求过多
        if hub == dest:
            continue
        
        # 查询 origin -> hub 的价格
        connecting = get_flightapi_price(origin, hub, date)
        
        if connecting and connecting['price'] < direct_route['price'] * 0.95:
            savings = direct_route['price'] - connecting['price']
            skiplag_options.append({
                'origin': origin,
                'destination': hub,
                'via': dest,
                'price': connecting['price'],
                'airline': connecting['airline'],
                'flight_number': connecting['flight_number'],
                'departure': connecting['departure'],
                'arrival': connecting['arrival'],
                'savings': round(savings, 2),
                'data_source': 'FlightAPI'
            })
            print(f"  ✅ Skiplag: {origin}-{dest}-{hub} ${connecting['price']} (省 ${savings:.0f})")
    
    # 按价格排序
    skiplag_options.sort(key=lambda x: x['price'])
    
    return {
        'direct': direct_route,
        'skiplagging': skiplag_options,
        'savings': skiplag_options[0]['savings'] if skiplag_options else 0
    }

# HTML 模板
HTML_TEMPLATE = '''
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
        .price { font-size: 28px; font-weight: 700; color: #667eea; }
        .savings { font-size: 16px; color: #10b981; margin-left: 12px; }
        .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 8px; margin-right: 8px; }
        .tag.direct { background: #e0e7ff; color: #667eea; }
        .tag.skiplagging { background: #d1fae5; color: #059669; }
        .tag.flightapi { background: #dbeafe; color: #2563eb; }
        .tag.airlabs { background: #fef3c7; color: #d97706; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { color: #dc2626; padding: 16px; background: #fef2f2; border-radius: 10px; }
        .source { font-size: 12px; color: #999; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✈️ Skiplagging Finder</h1>
        <p class="subtitle">FlightAPI.io 真实价格 + AirLabs 真实航线</p>
        
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
            btn.textContent = '查询中（约10-30秒）...';
            resultsDiv.innerHTML = '<div class="loading">正在从 FlightAPI.io 获取真实价格...</div>';
            
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
                    const sourceTag = data.direct.data_source === 'FlightAPI' ? 
                        '<span class="tag flightapi">FlightAPI 真实价格</span>' : 
                        '<span class="tag airlabs">AirLabs 估算</span>';
                    
                    html += `
                        <div class="flight-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                                <span class="airline">${data.direct.airline}</span>
                                <span class="price">$${data.direct.price}</span>
                            </div>
                            <div style="color:#666;margin-bottom:4px">${data.direct.origin} → ${data.direct.destination}</div>
                            <div style="color:#999;font-size:14px">${data.direct.departure} - ${data.direct.arrival}</div>
                            <div class="source">日期: ${date}</div>
                            <span class="tag direct">直飞</span>
                            ${sourceTag}
                        </div>
                    `;
                }
                
                // Skiplagging 选项
                if (data.skiplagging && data.skiplagging.length > 0) {
                    html += `<h3 style="margin:24px 0 16px;color:#333">💰 找到 ${data.skiplagging.length} 个 Skiplagging 机会</h3>`;
                    
                    data.skiplagging.forEach((opt) => {
                        const savings = opt.savings.toFixed(0);
                        const sourceTag = opt.data_source === 'FlightAPI' ? 
                            '<span class="tag flightapi">FlightAPI 真实价格</span>' : '';
                        
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
                                ${sourceTag}
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
        return jsonify({'error': '请填写所有字段'}), 400
    
    try:
        result = find_skiplagging(origin, destination, date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
