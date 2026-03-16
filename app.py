#!/usr/bin/env python3
"""
Skiplagging Finder Web App - Pro Version
使用 skiplagging_pro 的智能算法
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
import json

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skiplagging_pro import HybridSkiplaggingFinder

app = Flask(__name__)
finder = HybridSkiplaggingFinder()

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
    
    try:
        # 使用 Pro 版本的搜索逻辑
        direct_flights, opportunities = finder.find_skiplagging(
            origin, destination, date
        )
        
        # 转换数据格式给模板
        direct_list = [f.to_dict() for f in direct_flights[:10]]
        opp_list = []
        for opp in opportunities[:10]:
            opp_list.append({
                'flight': opp.skiplag_flight.to_dict(),
                'savings': opp.savings,
                'savings_percent': opp.savings_percent,
                'final_destination': opp.final_destination,
                'via_airport': opp.via_airport
            })
        
        return render_template('results.html',
                             origin=origin,
                             destination=destination,
                             date=date,
                             direct_flights=direct_list,
                             opportunities=opp_list,
                             has_direct=len(direct_list) > 0)
                             
    except Exception as e:
        print(f"搜索错误: {e}")
        import traceback
        traceback.print_exc()
        return render_template('results.html',
                             error=f'搜索出错: {str(e)}',
                             origin=origin, destination=destination, date=date)

@app.route('/api/json/search')
def search_json():
    """搜索 API - 返回 JSON"""
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', '')
    
    if not origin or not destination or not date:
        return jsonify({'error': '需要提供 origin, destination 和 date'}), 400
    
    try:
        direct_flights, opportunities = finder.find_skiplagging(
            origin, destination, date
        )
        
        return jsonify({
            'origin': origin,
            'destination': destination,
            'date': date,
            'direct_flights': [f.to_dict() for f in direct_flights[:10]],
            'opportunities': [o.to_dict() for o in opportunities[:10]]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
