#!/usr/bin/env python3
"""
Skiplagging Finder Web App - Real Data Version
使用 Amadeus API 获取真实航班数据

部署到 Render:
1. 创建 Render 账号
2. 新建 Web Service
3. 选择此 GitHub 仓库
4. 设置环境变量（可选）
5. 部署完成
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, timedelta
from skiplagging_real import RealSkiplaggingFinder, Flight, SkiplagOpportunity

app = Flask(__name__)

# 初始化 finder
finder = RealSkiplaggingFinder()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/search')
def search():
    """搜索 API"""
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', '')
    
    if not origin or not destination:
        return jsonify({'error': '需要提供 origin 和 destination'}), 400
    
    # 搜索直飞
    direct = finder.search_flight_offers(origin, destination, date)
    direct_flights = []
    for f_data in direct[:5]:  # 最多5个
        f = finder.parse_flight(f_data, date)
        if f:
            direct_flights.append(f.to_dict())
    
    # 搜索 skiplagging
    opportunities = []
    hubs = ["JFK", "LAX", "ORD", "DFW", "DEN", "ATL"]
    for hub in hubs:
        if hub == destination:
            continue
        connecting = finder.search_flight_offers(origin, hub, date)
        for f_data in connecting:
            flight = finder.parse_flight(f_data, date)
            if flight and flight.via == destination:
                if direct_flights and flight.price < direct_flights[0]['price']:
                    savings = direct_flights[0]['price'] - flight.price
                    opportunities.append({
                        'direct': direct_flights[0],
                        'skiplag': flight.to_dict(),
                        'savings': savings,
                        'savings_percent': (savings / direct_flights[0]['price']) * 100
                    })
    
    return jsonify({
        'direct_flights': direct_flights,
        'opportunities': opportunities[:3]
    })

@app.route('/api/march/<origin>/<destination>')
def march_prices(origin, destination):
    """获取整个3月的价格"""
    origin = origin.upper()
    destination = destination.upper()
    
    dates = finder.get_march_dates(2026)
    results = []
    
    for date in dates[:7]:  # 限制查询数量避免 API 限制
        direct = finder.search_flight_offers(origin, destination, date)
        if direct:
            f = finder.parse_flight(direct[0], date)
            if f:
                results.append({
                    'date': date,
                    'price': f.price,
                    'flight_number': f.flight_number,
                    'airline': f.airline_name
                })
    
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
