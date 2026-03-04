# Skiplagging Flight Finder - Demo Version
# 隐藏城市购票搜索工具

import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Flight:
    origin: str
    destination: str
    price: float
    airline: str
    flight_number: str
    departure: str
    arrival: str
    stops: int
    via: Optional[str] = None  # 中转城市

class SkiplaggingFinder:
    """
    Skiplagging 机票搜索工具
    
    核心逻辑：
    1. 搜索 A→B 直飞价格
    2. 搜索 A→C（经停 B）的价格
    3. 如果 A→B→C < A→B，就是潜在 skiplagging 机会
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # 这里使用 Amadeus API（需要申请免费 API key）
        # 或者使用 Google Flights 的非官方 API
        self.api_key = api_key
        self.session = requests.Session()
        
        # 热门中转枢纽机场（美国）
        self.us_hubs = [
            "ATL", "DFW", "DEN", "ORD", "LAX", "CLT", "MCO", "LAS",
            "PHX", "MIA", "SEA", "IAH", "JFK", "EWR", "SFO", "BOS",
            "MSP", "DTW", "PHL", "LGA", "FLL", "BWI", "IAD", "MDW"
        ]
    
    def search_direct_flight(self, origin: str, destination: str, 
                            date: str) -> Optional[Flight]:
        """
        搜索直飞航班价格（基准价）
        使用生成的数据库或模拟数据
        """
        # 尝试从数据库加载
        db = self._load_flight_database()
        key = f"{origin}_{destination}"
        
        if db and key in db:
            d = db[key]["direct"]
            return Flight(
                origin=d["origin"],
                destination=d["destination"],
                price=d["price"],
                airline=d["airline"],
                flight_number=d["flight_number"],
                departure=d["departure"],
                arrival=d["arrival"],
                stops=d["stops"],
                via=d.get("via"),
            )
        
        # 如果没有数据，生成随机直飞
        return self._generate_random_direct(origin, destination)
    
    def _load_flight_database(self) -> dict:
        """加载航班数据库"""
        import json
        import os
        
        db_path = os.path.join(os.path.dirname(__file__), "flight_database.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _generate_random_direct(self, origin: str, destination: str) -> Flight:
        """生成随机直飞航班"""
        import random
        
        airlines = ["American Airlines", "Delta", "United", "Southwest", "JetBlue", "Alaska Airlines"]
        price = float(random.randint(150, 500))
        
        return Flight(
            origin=origin,
            destination=destination,
            price=price,
            airline=random.choice(airlines),
            flight_number=f"XX{random.randint(100, 999)}",
            departure=f"{random.randint(6, 20):02d}:00",
            arrival=f"{random.randint(8, 22):02d}:30",
            stops=0
        )
    
    def search_connecting_flights(self, origin: str, destination: str, 
                                  date: str, 
                                  potential_hubs: List[str]) -> List[Flight]:
        """
        搜索 A→C 经停 B 的航班
        """
        opportunities = []
        db = self._load_flight_database()
        key = f"{origin}_{destination}"
        
        if db and key in db:
            # 从数据库加载 skiplagging 选项
            for opt in db[key].get("skiplagging", []):
                opportunities.append(Flight(
                    origin=opt["origin"],
                    destination=opt["destination"],
                    price=opt["price"],
                    airline=opt["airline"],
                    flight_number=opt["flight_number"],
                    departure=opt["departure"],
                    arrival=opt["arrival"],
                    stops=opt["stops"],
                    via=opt["via"],
                ))
        else:
            # 如果没有数据，使用旧版 mock 数据
            opportunities = self._get_legacy_mock_data(origin, destination)
        
        return opportunities
    
    def _get_legacy_mock_data(self, origin: str, destination: str) -> List[Flight]:
        """旧版模拟数据作为后备"""
        mock_data = {
            "AUS_DCA": [
                {"origin": "AUS", "destination": "JFK", "price": 150.0, "airline": "American Airlines", "flight_number": "AA567", "departure": "06:00", "arrival": "12:00", "stops": 1, "via": "DCA"},
                {"origin": "AUS", "destination": "BOS", "price": 180.0, "airline": "Delta", "flight_number": "DL123", "departure": "07:00", "arrival": "13:30", "stops": 1, "via": "DCA"},
            ],
        }
        
        key = f"{origin}_{destination}"
        flights = []
        if key in mock_data:
            for data in mock_data[key]:
                flights.append(Flight(**data))
        return flights
    
    def find_skiplagging_opportunities(self, origin: str, destination: str,
                                      date: str) -> dict:
        """
        主函数：查找 skiplagging 机会
        
        Returns:
            {
                "direct": Flight,  # 直飞选项
                "skiplagging": List[Flight],  # 更便宜的转机选项
                "savings": float,  # 最大节省金额
                "best_option": Flight  # 最优选项
            }
        """
        print(f"🔍 搜索 {origin} → {destination} 的机票...")
        print(f"📅 日期: {date}\n")
        
        # 1. 获取直飞价格
        direct = self.search_direct_flight(origin, destination, date)
        if not direct:
            return {"error": "未找到直飞航班"}
        
        print(f"✈️  直飞选项:")
        print(f"   {direct.airline} {direct.flight_number}")
        print(f"   价格: ${direct.price}")
        print(f"   时间: {direct.departure} - {direct.arrival}\n")
        
        # 2. 搜索可能的 skiplagging 路线
        # 策略：目的地通常是某个大枢纽，找从 origin 出发经停该枢纽的航班
        print(f"🔎 搜索经停 {destination} 的转机航班...")
        
        # 智能筛选：目的地如果是 hub，找从 origin 出发飞其他城市的航班
        # 目的地如果不是 hub，找飞附近大 hub 的航班
        search_hubs = self._get_search_hubs(destination)
        
        connecting = self.search_connecting_flights(
            origin, destination, date, search_hubs
        )
        
        # 3. 筛选出更便宜的选项
        cheaper_options = [
            f for f in connecting 
            if f.price < direct.price and f.via == destination
        ]
        
        result = {
            "direct": direct,
            "skiplagging": cheaper_options,
            "savings": 0.0,
            "best_option": None
        }
        
        if cheaper_options:
            # 按价格排序
            cheaper_options.sort(key=lambda x: x.price)
            best = cheaper_options[0]
            savings = direct.price - best.price
            
            result["savings"] = savings
            result["best_option"] = best
            
            print(f"💰 找到 {len(cheaper_options)} 个 Skiplagging 机会！")
            print(f"💵 最高可节省: ${savings:.2f}\n")
            
            for i, opt in enumerate(cheaper_options, 1):
                print(f"   选项 {i}:")
                print(f"   票面: {opt.origin} → {opt.destination} (经停 {opt.via})")
                print(f"   实际: {opt.origin} → {opt.via} (在 {opt.via} 下机)")
                print(f"   航班: {opt.airline} {opt.flight_number}")
                print(f"   价格: ${opt.price} (省 ${direct.price - opt.price})")
                print(f"   时间: {opt.departure} - {opt.arrival}")
                print()
            
            print("⚠️  提醒:")
            print("   - 不要托运行李（会直挂到终点）")
            print("   - 不要买往返票（返程可能被取消）")
            print("   - 不要用常用旅客账号（可能被封号）")
        else:
            print("❌ 未找到更便宜的 Skiplagging 机会")
            print("   建议:")
            print("   - 尝试其他日期")
            print("   - 尝试附近机场作为目的地")
        
        return result
    
    def _get_search_hubs(self, destination: str) -> List[str]:
        """
        根据目的地智能选择搜索的枢纽机场
        """
        # 如果目的地本身就是 hub，找从 origin 出发飞其他城市的航班
        if destination in self.us_hubs:
            return [hub for hub in self.us_hubs if hub != destination][:10]
        
        # 如果目的地不是 hub，找附近的大 hub
        nearby_hubs = {
            "DCA": ["JFK", "EWR", "BOS", "ATL", "ORD"],
            "AUS": ["DFW", "IAH", "ATL", "DEN"],
            "BWI": ["JFK", "EWR", "ATL", "ORD"],
        }
        
        return nearby_hubs.get(destination, self.us_hubs[:10])


# ============== 使用示例 ==============

def demo():
    """演示用法"""
    finder = SkiplaggingFinder()
    
    # 场景：想从奥斯汀(AUS)飞到华盛顿DCA
    # 但直飞太贵，找经停DCA的便宜机票
    
    result = finder.find_skiplagging_opportunities(
        origin="AUS",
        destination="DCA", 
        date="2026-03-15"
    )
    
    return result

if __name__ == "__main__":
    demo()
