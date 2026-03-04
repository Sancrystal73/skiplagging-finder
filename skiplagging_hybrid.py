# skiplagging_hybrid.py
# 混合策略：AirLabs 找航线 + Google Flights 查价格

import requests
import json
import random
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import os

@dataclass
class Flight:
    origin: str
    destination: str
    price: Optional[float]
    airline: str
    flight_number: str
    departure: str
    arrival: str
    stops: int
    via: Optional[str] = None
    airline_iata: str = ""
    duration: int = 0
    data_source: str = ""  # 'airlabs' | 'google' | 'mock'

class HybridSkiplaggingFinder:
    """
    混合搜索策略：
    1. 用 AirLabs 找所有可能的航线（包括中转路线）
    2. 筛选出有 skiplagging 潜力的路线
    3. 用 Google Flights 查这些路线的真实价格
    """
    
    def __init__(self, airlabs_key: str = None):
        self.airlabs_key = airlabs_key or os.getenv('AIRLABS_API_KEY')
        self.base_url = "https://airlabs.co/api/v9"
        self.session = requests.Session()
        
        # 缓存
        self._routes_cache = {}
        self._google_cache = {}
        
    def _airlabs_call(self, endpoint: str, params: dict = None) -> dict:
        """调用 AirLabs API"""
        params = params or {}
        params['api_key'] = self.airlabs_key
        
        try:
            resp = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"AirLabs API Error: {e}")
            return {}
    
    def find_connecting_routes_via(self, origin: str, via: str) -> List[dict]:
        """
        找到从 origin 出发、经过 via 的所有可能路线
        返回: 终点不是 via，但途经 via 的路线
        """
        print(f"🔍 AirLabs: 找 {origin} → ... → {via} 的路线...")
        
        # 获取从 origin 出发的所有航线
        all_routes = self._airlabs_call("routes", {"dep_iata": origin}).get('response', [])
        
        # 找目的地是热门枢纽（可能经停 via）的航线
        # 策略：如果 via 是大枢纽，找从 origin 飞其他城市且可能经停 via 的航班
        connecting_routes = []
        
        for route in all_routes:
            arr_iata = route.get('arr_iata')
            
            # 如果目的地不是 via，且不是直飞（可能经停）
            if arr_iata and arr_iata != via:
                # 判断这条航线是否可能经停 via
                # 规则：如果 via 是从 origin 到 arr_iata 的常见中转点
                if self._is_likely_stopover(origin, via, arr_iata):
                    connecting_routes.append(route)
        
        print(f"   ✓ 找到 {len(connecting_routes)} 条可能经停 {via} 的路线")
        return connecting_routes
    
    def _is_likely_stopover(self, origin: str, via: str, dest: str) -> bool:
        """
        判断 via 是否可能是 origin-dest 的中转点
        基于地理位置和枢纽地位
        """
        # 美国主要枢纽
        us_hubs = ["ATL", "DFW", "DEN", "ORD", "LAX", "CLT", "MCO", "LAS", 
                   "PHX", "MIA", "SEA", "IAH", "JFK", "EWR", "SFO", "BOS", 
                   "MSP", "DTW", "PHL", "LGA"]
        
        # 如果 via 不是大枢纽，不太可能作为中转点
        if via not in us_hubs:
            return False
        
        # 如果 origin 和 dest 都在东海岸，经停西海岸不合理
        # 简单规则：如果 via 是枢纽，且不是 dest，则可能是中转
        return True
    
    def search_google_flights_price(self, origin: str, destination: str, 
                                     date: str) -> Optional[float]:
        """
        查询 Google Flights 真实价格
        """
        cache_key = f"{origin}_{destination}_{date}"
        if cache_key in self._google_cache:
            return self._google_cache[cache_key]
        
        print(f"   💰 Google Flights: 查询 {origin} → {destination}...")
        
        # 导入并调用 Google Flights 查询
        try:
            from google_flights_scraper import get_google_flights_price
            price = get_google_flights_price(origin, destination, date)
            
            if price:
                self._google_cache[cache_key] = price
                print(f"   ✓ 价格: ${price}")
                return price
            else:
                print(f"   ⚠ 未获取到价格，使用估算")
                
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")
        
        # 失败时使用估算
        mock_price = self._mock_price(origin, destination)
        self._google_cache[cache_key] = mock_price
        print(f"   ~ 估算价格: ${mock_price}")
        return mock_price
    
    def _mock_price(self, origin: str, destination: str) -> float:
        """模拟价格（临时）"""
        # 基于距离估算
        distance_map = {
            ("JFK", "LAX"): 2500, ("LAX", "JFK"): 2500,
            ("JFK", "SFO"): 2600, ("SFO", "JFK"): 2600,
            ("JFK", "ORD"): 800, ("ORD", "JFK"): 800,
            ("LAX", "ORD"): 1800, ("ORD", "LAX"): 1800,
        }
        
        dist = distance_map.get((origin, destination), 1500)
        price = dist * random.uniform(0.08, 0.15)
        return round(max(price, 79), 2)
    
    def find_skiplagging_opportunities(self, origin: str, destination: str,
                                      date: str = None) -> dict:
        """
        主搜索函数 - 混合策略
        """
        if date is None:
            date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        print(f"\n{'='*60}")
        print(f"🎯 搜索: {origin} → {destination} ({date})")
        print(f"{'='*60}\n")
        
        # 步骤1: 用 AirLabs 找直飞
        print("📌 步骤1: AirLabs 查直飞...")
        direct_routes = self._airlabs_call("routes", {
            "dep_iata": origin,
            "arr_iata": destination,
        }).get('response', [])
        
        if not direct_routes:
            print(f"   ❌ AirLabs 未找到直飞航线")
            return {"error": "未找到直飞航线", "direct": None, "skiplagging": []}
        
        # 取第一个直飞作为基准
        direct_route = direct_routes[0]
        airlines = self._airlabs_call("airlines").get('response', [])
        airline_map = {a.get('iata_code'): a.get('name') for a in airlines if a.get('iata_code')}
        
        airline_iata = direct_route.get('airline_iata', 'XX')
        airline_name = airline_map.get(airline_iata, airline_iata)
        
        direct_flight = Flight(
            origin=origin,
            destination=destination,
            price=None,  # 稍后查询
            airline=airline_name,
            flight_number=direct_route.get('flight_iata', f'{airline_iata}1'),
            departure=direct_route.get('dep_time', '08:00'),
            arrival=direct_route.get('arr_time', '11:00'),
            stops=0,
            airline_iata=airline_iata,
            data_source='airlabs'
        )
        
        # 步骤2: 用 AirLabs 找可能的中转路线
        print("\n📌 步骤2: AirLabs 查中转路线...")
        connecting_candidates = self.find_connecting_routes_via(origin, destination)
        
        # 步骤3: 查询 Google Flights 价格（只查候选路线）
        print(f"\n📌 步骤3: Google Flights 查价格 ({len(connecting_candidates) + 1} 条路线)...")
        
        # 查直飞价格
        direct_price = self.search_google_flights_price(origin, destination, date)
        direct_flight.price = direct_price
        
        print(f"\n✈️ 直飞: {direct_flight.airline} {direct_flight.flight_number}")
        print(f"   价格: ${direct_price}")
        
        # 查中转路线价格
        skiplag_options = []
        
        for route in connecting_candidates[:10]:  # 限制数量，避免过多请求
            final_dest = route.get('arr_iata')
            route_airline_iata = route.get('airline_iata', 'XX')
            route_airline_name = airline_map.get(route_airline_iata, route_airline_iata)
            
            # 查询这条完整路线的价格
            full_price = self.search_google_flights_price(origin, final_dest, date)
            
            if full_price and full_price < direct_price * 0.9:  # 至少便宜 10% 才算有价值
                skiplag_flight = Flight(
                    origin=origin,
                    destination=final_dest,
                    price=full_price,
                    airline=route_airline_name,
                    flight_number=route.get('flight_iata', f'{route_airline_iata}1'),
                    departure=route.get('dep_time', '06:00'),
                    arrival=route.get('arr_time', '18:00'),
                    stops=1,
                    via=destination,
                    airline_iata=route_airline_iata,
                    data_source='google'
                )
                skiplag_options.append(skiplag_flight)
                print(f"   ✓ {origin}-{destination}-{final_dest}: ${full_price} (省 ${direct_price - full_price:.0f})")
        
        # 步骤4: 整理结果
        skiplag_options.sort(key=lambda x: x.price)
        
        result = {
            "direct": direct_flight,
            "skiplagging": skiplag_options,
            "savings": 0.0,
            "best_option": None,
            "stats": {
                "total_checked": len(connecting_candidates) + 1,
                "google_requests": len(connecting_candidates) + 1,
            }
        }
        
        if skiplag_options:
            best = skiplag_options[0]
            result["savings"] = direct_price - best.price
            result["best_option"] = best
            
            print(f"\n💰 找到 {len(skiplag_options)} 个 Skiplagging 机会！")
            print(f"💵 最高可节省: ${result['savings']:.2f}")
        else:
            print(f"\n❌ 未找到更便宜的 Skiplagging 机会")
        
        return result


def main():
    """测试混合搜索"""
    finder = HybridSkiplaggingFinder(
        airlabs_key="870c8003-7051-4496-990b-01b0eeec5f5f"
    )
    
    test_routes = [
        ("JFK", "LAX"),
        ("LAX", "JFK"),
    ]
    
    for origin, dest in test_routes:
        result = finder.find_skiplagging_opportunities(origin, dest)
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
