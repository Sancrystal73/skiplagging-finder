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
    
    # 搜索直飞航班
    direct_flights = []
    try:
        direct_data = finder.search_flight_offers(origin, destination, date)
        for f_data in direct_data[:10]:  # 最多10个
            f = finder.parse_flight(f_data, date)
            if f:
                direct_flights.append(f)
        direct_flights.sort(key=lambda x: x.price)
    except Exception as e:
        print(f"直飞搜索错误: {e}")
    
    # 搜索 skiplagging 机会
    opportunities = []
    if direct_flights:
        cheapest_direct = direct_flights[0]
        hubs = ["JFK", "LAX", "ORD", "DFW", "DEN", "ATL", "SEA", "SFO", "MIA", "BOS"]
        
        for hub in hubs:
            if hub == destination:
                continue
            try:
                connecting_data = finder.search_flight_offers(origin, hub, date)
                for f_data in connecting_data[:5]:
                    flight = finder.parse_flight(f_data, date)
                    if flight and flight.via == destination:
                        if flight.price < cheapest_direct.price:
                            savings = cheapest_direct.price - flight.price
                            opportunities.append({
                                'flight': flight,
                                'savings': savings,
                                'savings_percent': (savings / cheapest_direct.price) * 100,
                                'final_destination': hub
                            })
            except Exception as e:
                print(f"转机搜索错误 {hub}: {e}")
        
        # 按节省金额排序
        opportunities.sort(key=lambda x: x['savings'], reverse=True)
    
    return render_template('results.html',
                         origin=origin,
                         destination=destination,
                         date=date,
                         direct_flights=direct_flights[:5],
                         opportunities=opportunities[:5])

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
    for f_data in direct_data[:5]:
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
    app.run(host='0.0.0.0', port=port)
