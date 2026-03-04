# skiplagging_minimal.py - 最小可用版本
from flask import Flask, render_template_string, request, jsonify
import requests
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# AirLabs API Key
API_KEY = "870c8003-7051-4496-990b-01b0eeec5f5f"

def get_airlabs_routes(origin, destination):
    """从 AirLabs 获取航线"""
    url = "https://airlabs.co/api/v9/routes"
    params = {
        "api_key": API_KEY,
        "dep_iata": origin,
        "arr_iata": destination,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return data.get('response', [])
    except:
        return []

def generate_price(origin, dest, duration):
    """基于飞行时间生成价格"""
    if not duration:
        duration = 180
    base = duration * random.uniform(0.3, 0.8)
    return round(max(base, 79), 2)

HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Skiplagging Finder</title>
<style>
body{font-family:sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}
.container{max-width:800px;margin:0 auto}
h1{color:white;text-align:center}
.card{background:white;border-radius:16px;padding:24px}
.form-row{display:flex;gap:12px;margin-bottom:16px}
.form-group{flex:1}
label{display:block;font-size:12px;color:#666;margin-bottom:6px}
input{width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:16px}
button{width:100%;padding:16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer}
button:disabled{opacity:0.6}
.results{margin-top:24px}
.flight-card{background:#f8f9fa;border-radius:12px;padding:20px;margin-bottom:16px;border-left:4px solid #667eea}
.flight-card.skiplagging{border-left-color:#10b981;background:#ecfdf5}
.airline{font-weight:600}
.price{font-size:24px;font-weight:700;color:#667eea}
.savings{color:#10b981;margin-left:8px}
.tag{display:inline-block;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;margin-top:8px}
.tag.direct{background:#e0e7ff;color:#667eea}
.tag.skiplagging{background:#d1fae5;color:#059669}
.loading{text-align:center;padding:40px;color:#666}
.error{color:red;padding:16px;background:#fef2f2;border-radius:10px}
</style></head>
<body>
<div class="container">
<h1>✈️ Skiplagging Finder</h1>
<div class="card">
<form id="f">
<div class="form-row">
<div class="form-group"><label>出发地</label><input id="o" placeholder="JFK" maxlength="3" required></div>
<div class="form-group"><label>目的地</label><input id="d" placeholder="LAX" maxlength="3" required></div>
<div class="form-group"><label>日期</label><input type="date" id="dt" required></div>
</div>
<button type="submit" id="btn">🔍 搜索</button>
</form>
<div id="r"></div>
</div></div>
<script>
document.getElementById('dt').value=new Date().toISOString().split('T')[0];
document.getElementById('f').onsubmit=async(e)=>{e.preventDefault();
const o=document.getElementById('o').value.toUpperCase(),d=document.getElementById('d').value.toUpperCase(),dt=document.getElementById('dt').value;
document.getElementById('btn').disabled=true;document.getElementById('r').innerHTML='<div class="loading">搜索中...</div>';
try{const res=await fetch('/s',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({o,d,dt})});
const data=await res.json();
if(data.err){document.getElementById('r').innerHTML='<div class="error">'+data.err+'</div>';return;}
let h='';if(data.direct){h+='<div class="flight-card"><div style="display:flex;justify-content:space-between"><span class="airline">'+data.direct.airline+'</span><span class="price">$'+data.direct.price+'</span></div><div>'+data.direct.o+' → '+data.direct.d+'</div><div style="color:#999">'+data.direct.dep+' - '+data.direct.arr+'</div><span class="tag direct">直飞</span></div>';}
if(data.sk&&data.sk.length){h+='<h3 style="margin:24px 0 16px">💰 找到 '+data.sk.length+' 个机会</h3>';
data.sk.forEach(x=>{const sv=(data.direct.price-x.price).toFixed(0);h+='<div class="flight-card skiplagging"><div style="display:flex;justify-content:space-between"><span class="airline">'+x.airline+'</span><span class="price">$'+x.price+'<span class="savings">省 $'+sv+'</span></span></div><div>'+x.o+' → <b style="color:#10b981">'+x.via+'</b> → <s>'+x.d+'</s></div><span class="tag skiplagging">在 '+x.via+' 下机</span></div>';});}
document.getElementById('r').innerHTML=h;
}catch(e){document.getElementById('r').innerHTML='<div class="error">'+e+'</div>';}
document.getElementById('btn').disabled=false;};
</script>
</body></html>'''

@app.route('/')
def index():
    return HTML

@app.route('/s', methods=['POST'])
def search():
    data = request.get_json()
    o = data.get('o', '').upper()
    d = data.get('d', '').upper()
    if not o or not d:
        return jsonify({"err": "请填写机场代码"}), 400
    
    # 获取直飞
    direct_routes = get_airlabs_routes(o, d)
    if not direct_routes:
        return jsonify({"err": "未找到直飞航线"}), 404
    
    route = direct_routes[0]
    dur = route.get('duration') or 180
    price = generate_price(o, d, dur)
    
    direct = {
        "o": o, "d": d, "price": price,
        "airline": route.get('airline_iata', 'Unknown'),
        "dep": route.get('dep_time', '08:00'),
        "arr": route.get('arr_time', '11:00')
    }
    
    # 模拟 skiplagging 选项
    sk = []
    if random.random() > 0.3:
        hubs = ["ATL","DFW","DEN","ORD","LAX","SEA","JFK"]
        for hub in random.sample(hubs, min(3, len(hubs))):
            if hub != d:
                sk_price = price * random.uniform(0.5, 0.85)
                sk.append({
                    "o": o, "d": hub, "via": d,
                    "price": round(sk_price, 2),
                    "airline": route.get('airline_iata', 'XX'),
                    "dep": "06:00", "arr": "14:00"
                })
    
    sk.sort(key=lambda x: x['price'])
    return jsonify({"direct": direct, "sk": sk})

if __name__ == '__main__':
    print("\n服务器: http://localhost:5000")
    print("按 Ctrl+C 停止\n")
    app.run(port=5000)
