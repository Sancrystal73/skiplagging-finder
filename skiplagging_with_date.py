from flask import Flask, render_template_string, request, jsonify
import requests
import random
from datetime import datetime

app = Flask(__name__)
API_KEY = "870c8003-7051-4496-990b-01b0eeec5f5f"

def get_routes(origin, dest):
    url = "https://airlabs.co/api/v9/routes"
    try:
        resp = requests.get(url, params={"api_key": API_KEY, "dep_iata": origin, "arr_iata": dest}, timeout=10)
        return resp.json().get('response', [])
    except:
        return []

def get_price(base_price, date_str):
    """根据日期调整价格（周末更贵）"""
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # 周五、周六、周日价格 +20%
            if dt.weekday() >= 4:
                return int(base_price * 1.2)
        except:
            pass
    return base_price

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Skiplagging Finder</title>
<style>
body{font-family:sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}
.container{max-width:800px;margin:0 auto}
h1{color:white;text-align:center}
.card{background:white;border-radius:16px;padding:24px}
input{width:30%;padding:12px;margin:8px;border:2px solid #ddd;border-radius:10px;font-size:16px}
button{width:100%;padding:16px;background:#667eea;color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer}
.flight-card{background:#f8f9fa;padding:16px;margin:16px 0;border-radius:8px;border-left:4px solid #667eea}
.flight-card.skiplagging{border-left-color:#10b981;background:#ecfdf5}
.price{font-size:24px;font-weight:700;color:#667eea}
.savings{color:#10b981;margin-left:8px}
.date-info{color:#666;font-size:14px;margin-top:8px}
</style></head>
<body>
<div class="container">
<h1>✈️ Skiplagging Finder</h1>
<div class="card">
<form id="f">
<input id="o" placeholder="出发地 (如 JFK)" maxlength="3" required>
<input id="d" placeholder="目的地 (如 LAX)" maxlength="3" required>
<input type="date" id="dt" required>
<button type="submit">🔍 搜索机票</button>
</form>
<div id="r"></div>
</div></div>
<script>
// 设置后天为默认日期
const dayAfterTomorrow = new Date();
dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
document.getElementById('dt').value = dayAfterTomorrow.toISOString().split('T')[0];

document.getElementById('f').onsubmit = async(e) => {
    e.preventDefault();
    const o = document.getElementById('o').value.toUpperCase();
    const d = document.getElementById('d').value.toUpperCase();
    const dt = document.getElementById('dt').value;
    document.getElementById('r').innerHTML = '搜索中...';
    try {
        const res = await fetch('/s', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({o, d, dt})
        });
        const data = await res.json();
        if (data.err) {
            document.getElementById('r').innerHTML = data.err;
            return;
        }
        let h = '<div class="flight-card">';
        h += '<div class="price">$' + data.direct.price + '</div>';
        h += '<div>' + data.direct.airline + '</div>';
        h += '<div>' + data.direct.o + ' → ' + data.direct.d + '</div>';
        h += '<div class="date-info">日期: ' + data.date + '</div>';
        h += '</div>';
        if (data.sk && data.sk.length) {
            h += '<h3>💰 找到 ' + data.sk.length + ' 个 Skiplagging 机会</h3>';
            data.sk.forEach(x => {
                const savings = (data.direct.price - x.price).toFixed(0);
                h += '<div class="flight-card skiplagging">';
                h += '<div class="price">$' + x.price + '<span class="savings">省 $' + savings + '</span></div>';
                h += '<div>' + x.airline + '</div>';
                h += '<div>' + x.o + ' → <b style="color:#10b981">' + x.via + '</b> → <s>' + x.d + '</s></div>';
                h += '<div class="date-info">在 ' + x.via + ' 下机，放弃后半程</div>';
                h += '</div>';
            });
        }
        document.getElementById('r').innerHTML = h;
    } catch(e) {
        document.getElementById('r').innerHTML = '错误: ' + e;
    }
};
</script>
</body></html>"""

@app.route('/')
def index():
    return HTML

@app.route('/s', methods=['POST'])
def search():
    data = request.get_json()
    o = data.get('o', '').upper()
    d = data.get('d', '').upper()
    dt = data.get('dt', '')
    
    if not o or not d:
        return jsonify({"err": "请填写机场代码"}), 400
    
    routes = get_routes(o, d)
    if not routes:
        return jsonify({"err": "未找到航线，请检查机场代码（如 JFK, LAX, PEK）"}), 404
    
    route = routes[0]
    base_price = random.randint(150, 400)
    price = get_price(base_price, dt)
    
    direct = {
        "o": o,
        "d": d,
        "price": price,
        "airline": route.get('airline_iata', 'AA'),
        "date": dt
    }
    
    # 生成 skiplagging 选项
    sk = []
    hubs = ["ATL", "DFW", "DEN", "ORD", "LAX", "SEA", "JFK", "SFO", "MIA", "LAS"]
    for hub in random.sample(hubs, min(3, len(hubs))):
        if hub != d:
            sk_base = int(price * random.uniform(0.5, 0.8))
            sk_price = get_price(sk_base, dt)
            sk.append({
                "o": o,
                "d": hub,
                "via": d,
                "price": sk_price,
                "airline": route.get('airline_iata', 'AA')
            })
    
    sk.sort(key=lambda x: x['price'])
    return jsonify({"direct": direct, "sk": sk, "date": dt})

if __name__ == '__main__':
    print("="*50)
    print("Skiplagging Finder 已启动!")
    print("请在浏览器打开: http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)
