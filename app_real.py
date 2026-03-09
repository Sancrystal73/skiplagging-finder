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
    
    # 搜索所有航班（直飞 + 转机）
    all_flights = []
    try:
        flight_data = finder.search_flight_offers(origin, destination, date)
        for f_data in flight_data:
            f = finder.parse_flight(f_data, date)
            if f:
                all_flights.append(f)
        # 按价格排序
        all_flights.sort(key=lambda x: x.price)
    except Exception as e:
        print(f"搜索错误: {e}")
    
    # 分离直飞和转机
    direct_flights = [f for f in all_flights if f.stops == 0]
    connecting_flights = [f for f in all_flights if f.stops > 0]
    
    print(f"找到 {len(direct_flights)} 个直飞, {len(connecting_flights)} 个转机")
    
    # 查找 skiplagging 机会
    # 策略：转机航班的目的地不是用户想要的，但经停点是
    opportunities = []
    
    if connecting_flights:
        # 如果没有直飞，用转机中最便宜的作为基准
        if direct_flights:
            baseline_price = direct_flights[0].price
        else:
            baseline_price = float('inf')
        
        for flight in connecting_flights:
            # 检查这个转机是否经停用户想要的目的地
            if flight.via == destination:
                # 转机价格应该比直飞便宜
                if flight.price < baseline_price:
                    savings = baseline_price - flight.price if direct_flights else 0
                    savings_pct = (savings / baseline_price * 100) if direct_flights and baseline_price > 0 else 0
                    
                    opportunities.append({
                        'flight': flight,
                        'savings': savings,
                        'savings_percent': savings_pct,
                        'final_destination': flight.destination  # 票面上的终点
                    })
                    print(f"Skiplag机会: {flight.flight_number} 省 ${savings:.2f}")
    
    # 按节省金额排序
    opportunities.sort(key=lambda x: x['savings'], reverse=True)
    
    # 如果没有直飞但有转机，把转机也显示在直飞列表里（但标记为转机）
    display_flights = direct_flights if direct_flights else all_flights[:5]
    
    return render_template('results.html',
                         origin=origin,
                         destination=destination,
                         date=date,
                         direct_flights=display_flights[:10],
                         opportunities=opportunities[:10])

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
