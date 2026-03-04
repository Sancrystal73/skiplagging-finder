# skiplagging_api.py
# 使用 Amadeus API 的真实版本

import os
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass
from amadeus import Client, ResponseError
import json

@dataclass
class SkiplagOpportunity:
    direct_price: float
    direct_flight: str
    skiplag_price: float
    skiplag_flight: str
    final_destination: str  # 票面上的终点
    via_airport: str        # 你想下机的机场
    savings: float
    savings_percent: float

class AmadeusSkiplaggingFinder:
    """
    使用 Amadeus API 的 Skiplagging 搜索器
    
    免费额度：
    - Self-Service: 2,000 transactions/month (免费)
    - 需要注册：https://developers.amadeus.com/
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        # 从环境变量或参数读取 API key
        self.api_key = api_key or os.getenv('AMADEUS_API_KEY')
        self.api_secret = api_secret or os.getenv('AMADEUS_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "需要 Amadeus API Key\n"
                "1. 注册：https://developers.amadeus.com/\n"
                "2. 创建应用获取 API Key 和 Secret\n"
                "3. 设置环境变量：\n"
                "   export AMADEUS_API_KEY='your_key'\n"
                "   export AMADEUS_API_SECRET='your_secret'"
            )
        
        self.amadeus = Client(
            client_id=self.api_key,
            client_secret=self.api_secret
        )
    
    def search_flight_offers(self, origin: str, destination: str, 
                            date: str, adults: int = 1) -> List[Dict]:
        """
        搜索航班报价
        """
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date,
                adults=adults,
                max=20
            )
            return response.data
        except ResponseError as error:
            print(f"API Error: {error}")
            return []
    
    def find_skiplagging(self, origin: str, destination: str, 
                        date: str, 
                        potential_final_destinations: List[str] = None) -> List[SkiplagOpportunity]:
        """
        查找 skiplagging 机会
        
        策略：
        1. 搜索直飞 A→B 的价格
        2. 搜索 A→C（C 是枢纽，可能经停 B）
        3. 比较价格
        """
        opportunities = []
        
        # 1. 获取直飞价格
        print(f"🔍 搜索直飞 {origin} → {destination}...")
        direct_flights = self.search_flight_offers(origin, destination, date)
        
        if not direct_flights:
            print(f"❌ 未找到直飞航班")
            return []
        
        # 取最便宜的直飞
        direct_cheapest = min(direct_flights, 
                            key=lambda x: float(x['price']['total']))
        direct_price = float(direct_cheapest['price']['total'])
        
        print(f"✈️  直飞最低价格: ${direct_price}")
        
        # 2. 搜索可能的中转路线
        # 常见的大枢纽（可能经停 destination）
        hubs = potential_final_destinations or [
            "JFK", "LAX", "ORD", "ATL", "DFW", "DEN", "SEA", 
            "BOS", "SFO", "MIA", "LAS", "PHX"
        ]
        
        print(f"🔎 搜索经停 {destination} 的转机航班...")
        
        for hub in hubs:
            if hub == destination:
                continue
            
            # 搜索 origin → hub
            flights = self.search_flight_offers(origin, hub, date)
            
            for flight in flights:
                # 检查是否经停 destination
                if self._has_stop_at(flight, destination):
                    price = float(flight['price']['total'])
                    
                    if price < direct_price:
                        savings = direct_price - price
                        savings_pct = (savings / direct_price) * 100
                        
                        opp = SkiplagOpportunity(
                            direct_price=direct_price,
                            direct_flight=self._format_flight(direct_cheapest),
                            skiplag_price=price,
                            skiplag_flight=self._format_flight(flight),
                            final_destination=hub,
                            via_airport=destination,
                            savings=savings,
                            savings_percent=savings_pct
                        )
                        opportunities.append(opp)
        
        # 按节省金额排序
        opportunities.sort(key=lambda x: x.savings, reverse=True)
        return opportunities
    
    def _has_stop_at(self, flight_data: Dict, airport: str) -> bool:
        """
        检查航班是否经停特定机场
        """
        try:
            itineraries = flight_data.get('itineraries', [])
            for itinerary in itineraries:
                segments = itinerary.get('segments', [])
                # 如果有多个航段，检查经停点
                if len(segments) > 1:
                    for segment in segments[:-1]:  # 不包括最后一段
                        if segment.get('arrival', {}).get('iataCode') == airport:
                            return True
            return False
        except:
            return False
    
    def _format_flight(self, flight_data: Dict) -> str:
        """
        格式化航班信息
        """
        try:
            itineraries = flight_data.get('itineraries', [])
            if not itineraries:
                return "Unknown"
            
            segments = itineraries[0].get('segments', [])
            if not segments:
                return "Unknown"
            
            first_seg = segments[0]
            airline = first_seg.get('carrierCode', 'Unknown')
            flight_num = first_seg.get('number', '')
            
            return f"{airline} {flight_num}"
        except:
            return "Unknown"
    
    def print_opportunities(self, opportunities: List[SkiplagOpportunity]):
        """
        打印结果
        """
        if not opportunities:
            print("\n❌ 未找到 Skiplagging 机会")
            return
        
        print(f"\n💰 找到 {len(opportunities)} 个机会！\n")
        
        for i, opp in enumerate(opportunities[:5], 1):  # 只显示前5个
            print(f"选项 {i}:")
            print(f"  🎫 票面航班: {opp.skiplag_flight}")
            print(f"     路线: XXX → {opp.via_airport} → {opp.final_destination}")
            print(f"     价格: ${opp.skiplag_price:.2f}")
            print()
            print(f"  ✅ 实际使用: XXX → {opp.via_airport} (在 {opp.via_airport} 下机)")
            print(f"     节省: ${opp.savings:.2f} ({opp.savings_percent:.1f}%)")
            print()
        
        print("⚠️  重要提醒：")
        print("   • 不要托运行李（行李会直挂到票面上的终点）")
        print("   • 不要买往返票（放弃后半程可能导致返程被取消）")
        print("   • 建议用无痕模式搜索，不要用常旅客账号")
        print("   • 航班变动时航空公司可能改道，需自行承担风险")


# ============== 命令行界面 ==============

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Skiplagging 机票搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skiplagging_api.py AUS DCA 2026-03-15
  python skiplagging_api.py LAX JFK 2026-04-01 --hubs ORD ATL DFW
        """
    )
    
    parser.add_argument('origin', help='出发机场代码 (如 AUS)')
    parser.add_argument('destination', help='目的地机场代码 (如 DCA)')
    parser.add_argument('date', help='出发日期 (YYYY-MM-DD)')
    parser.add_argument('--hubs', nargs='+', 
                       help='额外搜索的枢纽机场 (可选)')
    parser.add_argument('--api-key', help='Amadeus API Key')
    parser.add_argument('--api-secret', help='Amadeus API Secret')
    
    args = parser.parse_args()
    
    try:
        finder = AmadeusSkiplaggingFinder(
            api_key=args.api_key,
            api_secret=args.api_secret
        )
        
        opportunities = finder.find_skiplagging(
            args.origin,
            args.destination,
            args.date,
            args.hubs
        )
        
        finder.print_opportunities(opportunities)
        
    except ValueError as e:
        print(e)
        print("\n或者使用演示模式（无需 API）：")
        print("  python skiplagging_finder.py")


if __name__ == "__main__":
    main()
