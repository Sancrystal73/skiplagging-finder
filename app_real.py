#!/usr/bin/env python3
"""
Skiplagging Finder Web App - Real Data Version
使用 Amadeus API 获取真实航班数据
"""

from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
from skiplagging_real import RealSkiplaggingFinder

app = Flask(__name__)
finder = RealSkiplaggingFinder()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/search')
def search():
    """搜索 API - 返回 HTML 页面"""
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', '')
    
    if not origin or not destination or not date:
        return render_template('results.html', 
                             error='请填写出发地、目的地和日期',
                             origin=origin, destination=destination, date=date)
    
    print(f"搜索: {origin} -> {destination}, 日期: {date}")
    
    # 1. 搜索到目标地的所有航班（直飞+转机）
    all_flights_to_dest = []
    try:
        flight_data = finder.search_flight_offers(origin, destination, date)
        for f_data in flight_data:
            f = finder.parse_flight(f_data, date)
            if f:
                all_flights_to_dest.append(f)
        all_flights_to_dest.sort(key=lambda x: x.price)
    except Exception as e:
        print(f"搜索到目的地错误: {e}")
    
    # 分离直飞和转机
    direct_flights = [f for f in all_flights_to_dest if f.stops == 0]
    connecting_to_dest = [f for f in all_flights_to_dest if f.stops > 0]
    
    print(f"到{destination}: {len(direct_flights)} 直飞, {len(connecting_to_dest)} 转机")
    
    # 2. 搜索到其他枢纽城市的航班（找 skiplagging 机会）
    # 这些航班可能经停用户想要的目的地
    hubs = ["JFK", "LGA", "EWR", "BOS", "PHL", "BWI", "ATL", "ORD", "DFW", "DEN", "LAX", "SEA"]
    skiplag_candidates = []
    
    for hub in hubs:
        if hub == destination:
            continue
        try:
            print(f"搜索 {origin} -> {hub}...")
            hub_flights_data = finder.search_flight_offers(origin, hub, date)
            
            for f_data in hub_flights_data[:5]:  # 每个hub只看前5个
                f = finder.parse_flight(f_data, date)
                if f and f.stops > 0:  # 只关心转机航班
                    # 检查是否经停用户想要的目的地
                    if f.via == destination:
                        skiplag_candidates.append(f)
                        print(f"  找到候选: {f.flight_number} 经停 {f.via} 到 {f.destination} 价格 ${f.price}")
        except Exception as e:
            print(f"搜索{hub}错误: {e}")
    
    # 3. 计算 skiplagging 机会
    opportunities = []
    
    if skiplag_candidates:
        # 基准价格：直飞价格 或 到目的地的转机价格
        if direct_flights:
            baseline_price = direct_flights[0].price
            baseline_flight = direct_flights[0]
        elif connecting_to_dest:
            baseline_price = connecting_to_dest[0].price
            baseline_flight = connecting_to_dest[0]
        else:
            baseline_price = float('inf')
            baseline_flight = None
        
        print(f"基准价格: ${baseline_price}")
        
        for flight in skiplag_candidates:
            # 如果经停航班比直接到目的地便宜
            if flight.price < baseline_price:
                savings = baseline_price - flight.price
                savings_pct = (savings / baseline_price * 100) if baseline_price > 0 else 0
                
                opportunities.append({
                    'flight': flight,
                    'savings': savings,
                    'savings_percent': savings_pct,
                    'final_destination': flight.destination,
                    'via_airport': destination
                })
                print(f"✅ Skiplag机会: {flight.flight_number} 省 ${savings:.2f}")
    
    # 按节省金额排序
    opportunities.sort(key=lambda x: x['savings'], reverse=True)
    
    # 如果没有直飞但有转机到目的地，显示转机
    display_flights = direct_flights if direct_flights else connecting_to_dest[:5]
    
    return render_template('results.html',
                         origin=origin,
                         destination=destination,
                         date=date,
                         direct_flights=display_flights[:10],
                         opportunities=opportunities[:10],
                         has_direct=len(direct_flights) > 0)

@app.route('/api/json/search')
def search_json():
    """搜索 API - 返回 JSON"""
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', '')
    
    if not origin or not destination:
        return jsonify({'error': '需要提供 origin 和 destination'}), 400
    
    direct_data = finder.search_flight_offers(origin, destination, date)
    direct_flights = []
    for f_data in direct_data[:10]:
        f = finder.parse_flight(f_data, date)
        if f:
            direct_flights.append(f.to_dict())
    
    return jsonify({
        'direct_flights': direct_flights,
        'origin': origin,
        'destination': destination,
        'date': date
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
