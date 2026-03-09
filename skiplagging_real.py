"""
Skiplagging Finder - Real Data Version
使用 Amadeus API 获取真实航班数据

Features:
- 真实航班价格（Amadeus API）
- 真实航班号、日期、时间
- 整个3月的价格追踪
- 缓存机制避免重复请求
- 自动查找 skiplagging 机会
"""

import os
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple
from amadeus import Client, ResponseError
import argparse

# Amadeus API Key (从 MEMORY.md 获取)
AMADEUS_API_KEY = "l6ROqlSPeeAsqtYI5hdGIsip80DIPatM"
AMADEUS_API_SECRET = "s0sFhjrxAPZ28JIV"

@dataclass
class Flight:
    """航班信息数据类"""
    flight_number: str
    airline_code: str
    airline_name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: float
    currency: str
    date: str
    stops: int
    via: Optional[str] = None
    duration: str = ""
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SkiplagOpportunity:
    """Skiplagging 机会数据类"""
    direct_flight: Flight
    skiplag_flight: Flight
    savings: float
    savings_percent: float
    final_destination: str  # 票面上的终点
    via_airport: str        # 实际下机点
    
    def to_dict(self):
        return {
            'direct_flight': self.direct_flight.to_dict(),
            'skiplag_flight': self.skiplag_flight.to_dict(),
            'savings': self.savings,
            'savings_percent': self.savings_percent,
            'final_destination': self.final_destination,
            'via_airport': self.via_airport
        }

class RealSkiplaggingFinder:
    """
    使用 Amadeus API 的真实 Skiplagging 搜索器
    
    Amadeus API 免费额度：每月 2,000 次调用
    需要注册：https://developers.amadeus.com/
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or AMADEUS_API_KEY
        self.api_secret = api_secret or AMADEUS_API_SECRET
        
        if not self.api_key or not self.api_secret:
            raise ValueError("需要 Amadeus API Key 和 Secret")
        
        self.amadeus = Client(
            client_id=self.api_key,
            client_secret=self.api_secret
        )
        
        # 缓存
        self.cache = {}
        self.cache_file = "amadeus_cache.json"
        self.load_cache()
        
    def load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"📦 已加载缓存: {len(self.cache)} 条记录")
            except:
                self.cache = {}
    
    def save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_cache_key(self, origin: str, dest: str, date: str) -> str:
        """生成缓存 key"""
        return f"{origin}_{dest}_{date}"
    
    def search_flight_offers(self, origin: str, destination: str, 
                            date: str, adults: int = 1,
                            force_refresh: bool = False) -> List[Dict]:
        """
        搜索航班报价（带缓存）
        
        Args:
            origin: 出发机场代码
            destination: 目的地机场代码
            date: 日期 (YYYY-MM-DD)
            adults: 成人数量
            force_refresh: 强制刷新缓存
        """
        cache_key = self.get_cache_key(origin, destination, date)
        
        if not force_refresh and cache_key in self.cache:
            print(f"  💾 使用缓存: {origin} → {destination} ({date})")
            return self.cache[cache_key]
        
        print(f"  🌐 查询 Amadeus: {origin} → {destination} ({date})")
        
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date,
                adults=adults,
                max=50,  # 最多50个结果
                currencyCode="USD"
            )
            
            data = response.data
            
            # 保存到缓存
            self.cache[cache_key] = data
            self.save_cache()
            
            # API 限制：每秒不超过 10 次
            time.sleep(0.2)
            
            return data
            
        except ResponseError as error:
            error_msg = str(error)
            if "Quota" in error_msg or "limit" in error_msg.lower():
                print(f"  ⚠️ API 额度限制，使用缓存数据")
                if cache_key in self.cache:
                    return self.cache[cache_key]
            print(f"  ❌ API Error: {error}")
            return []
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return []
    
    def parse_flight(self, flight_data: Dict, date: str) -> Optional[Flight]:
        """解析 Amadeus 返回的航班数据"""
        try:
            itineraries = flight_data.get('itineraries', [])
            if not itineraries:
                return None
            
            segments = itineraries[0].get('segments', [])
            if not segments:
                return None
            
            # 获取第一段和最后一段
            first_seg = segments[0]
            last_seg = segments[-1]
            
            # 航空公司信息
            airline_code = first_seg.get('carrierCode', 'Unknown')
            airline_name = self.get_airline_name(airline_code)
            flight_number = f"{airline_code}{first_seg.get('number', '')}"
            
            # 机场代码
            origin = first_seg.get('departure', {}).get('iataCode', '')
            destination = last_seg.get('arrival', {}).get('iataCode', '')
            
            # 时间
            dep_time = first_seg.get('departure', {}).get('at', '')
            arr_time = last_seg.get('arrival', {}).get('at', '')
            
            # 价格
            price = float(flight_data.get('price', {}).get('total', 0))
            currency = flight_data.get('price', {}).get('currency', 'USD')
            
            # 经停信息
            stops = len(segments) - 1
            via = None
            if stops > 0 and len(segments) > 1:
                via = segments[0].get('arrival', {}).get('iataCode', '')
            
            # 飞行时长
            duration = itineraries[0].get('duration', '')
            
            return Flight(
                flight_number=flight_number,
                airline_code=airline_code,
                airline_name=airline_name,
                origin=origin,
                destination=destination,
                departure_time=dep_time,
                arrival_time=arr_time,
                price=price,
                currency=currency,
                date=date,
                stops=stops,
                via=via,
                duration=duration
            )
            
        except Exception as e:
            print(f"  解析航班数据出错: {e}")
            return None
    
    def get_airline_name(self, code: str) -> str:
        """获取航空公司名称（简化版）"""
        airlines = {
            'AA': 'American Airlines',
            'DL': 'Delta Air Lines',
            'UA': 'United Airlines',
            'WN': 'Southwest Airlines',
            'AS': 'Alaska Airlines',
            'B6': 'JetBlue Airways',
            'F9': 'Frontier Airlines',
            'NK': 'Spirit Airlines',
            'G4': 'Allegiant Air',
            'HA': 'Hawaiian Airlines',
            'LH': 'Lufthansa',
            'BA': 'British Airways',
            'AF': 'Air France',
            'KL': 'KLM Royal Dutch Airlines',
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'SQ': 'Singapore Airlines',
            'CX': 'Cathay Pacific',
            'JL': 'Japan Airlines',
            'NH': 'All Nippon Airways',
        }
        return airlines.get(code, code)
    
    def get_march_dates(self, year: int = 2026) -> List[str]:
        """获取3月所有日期"""
        dates = []
        start_date = datetime(year, 3, 1)
        for i in range(31):  # 3月有31天
            date = start_date + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates
    
    def search_direct_flights(self, origin: str, destination: str, 
                              dates: List[str]) -> Dict[str, List[Flight]]:
        """
        搜索指定日期范围内的直飞航班
        
        Returns:
            Dict[date, List[Flight]]: 每个日期的航班列表
        """
        results = {}
        
        print(f"\n🔍 搜索 {origin} → {destination} 直飞航班（3月）")
        print("=" * 60)
        
        for date in dates:
            flights_data = self.search_flight_offers(origin, destination, date)
            
            flights = []
            for f_data in flights_data:
                flight = self.parse_flight(f_data, date)
                if flight:
                    flights.append(flight)
            
            # 按价格排序
            flights.sort(key=lambda x: x.price)
            
            results[date] = flights
            
            if flights:
                cheapest = flights[0]
                print(f"  {date}: {len(flights)} 个航班，最低 ${cheapest.price} ({cheapest.flight_number})")
            else:
                print(f"  {date}: 无航班")
        
        return results
    
    def search_skiplag_opportunities(self, origin: str, via_airport: str,
                                    dates: List[str],
                                    potential_hubs: List[str] = None) -> Dict[str, List[SkiplagOpportunity]]:
        """
        搜索 skiplagging 机会
        
        策略：
        1. 搜索 origin → via_airport 的直飞价格
        2. 搜索 origin → hub（经停 via_airport）的转机航班
        3. 找出转机比直飞便宜的选项
        """
        if potential_hubs is None:
            # 美国主要枢纽机场
            potential_hubs = [
                "JFK", "LAX", "ORD", "DFW", "DEN", "ATL", "SEA",
                "SFO", "MIA", "BOS", "PHX", "LAS", "PHL", "IAH",
                "CLT", "MCO", "DTW", "MSP", "BWI", "SLC"
            ]
        
        results = {}
        
        print(f"\n🔎 搜索 {origin} → {via_airport} Skiplagging 机会（3月）")
        print("=" * 60)
        
        for date in dates:
            print(f"\n📅 {date}:")
            
            # 1. 获取直飞价格
            direct_flights = self.search_flight_offers(origin, via_airport, date)
            if not direct_flights:
                print(f"  无直飞航班")
                results[date] = []
                continue
            
            # 解析直飞航班
            direct_parsed = []
            for f_data in direct_flights:
                f = self.parse_flight(f_data, date)
                if f:
                    direct_parsed.append(f)
            
            if not direct_parsed:
                results[date] = []
                continue
            
            # 取最便宜的直飞
            cheapest_direct = min(direct_parsed, key=lambda x: x.price)
            print(f"  直飞最低: ${cheapest_direct.price} ({cheapest_direct.flight_number})")
            
            opportunities = []
            
            # 2. 搜索转机航班
            for hub in potential_hubs:
                if hub == via_airport:
                    continue
                
                connecting_flights = self.search_flight_offers(origin, hub, date)
                
                for f_data in connecting_flights:
                    flight = self.parse_flight(f_data, date)
                    if not flight:
                        continue
                    
                    # 检查是否经停 via_airport
                    if flight.via == via_airport or self._check_stop_at(f_data, via_airport):
                        if flight.price < cheapest_direct.price:
                            savings = cheapest_direct.price - flight.price
                            savings_pct = (savings / cheapest_direct.price) * 100
                            
                            opp = SkiplagOpportunity(
                                direct_flight=cheapest_direct,
                                skiplag_flight=flight,
                                savings=savings,
                                savings_percent=savings_pct,
                                final_destination=hub,
                                via_airport=via_airport
                            )
                            opportunities.append(opp)
            
            # 按节省金额排序
            opportunities.sort(key=lambda x: x.savings, reverse=True)
            results[date] = opportunities
            
            if opportunities:
                best = opportunities[0]
                print(f"  💰 找到 {len(opportunities)} 个机会！")
                print(f"     最佳: 省 ${best.savings:.2f} ({best.savings_percent:.1f}%) - {best.skiplag_flight.flight_number}")
            else:
                print(f"  无 skiplagging 机会")
        
        return results
    
    def _check_stop_at(self, flight_data: Dict, airport: str) -> bool:
        """检查航班是否经停指定机场"""
        try:
            itineraries = flight_data.get('itineraries', [])
            for itinerary in itineraries:
                segments = itinerary.get('segments', [])
                if len(segments) > 1:
                    # 检查第一段的目的地是否是目标机场
                    first_seg = segments[0]
                    if first_seg.get('arrival', {}).get('iataCode') == airport:
                        return True
            return False
        except:
            return False
    
    def save_results(self, origin: str, destination: str, 
                    direct_flights: Dict, opportunities: Dict):
        """保存搜索结果到文件"""
        output = {
            'origin': origin,
            'destination': destination,
            'search_date': datetime.now().isoformat(),
            'direct_flights': {
                date: [f.to_dict() for f in flights]
                for date, flights in direct_flights.items()
            },
            'skiplagging_opportunities': {
                date: [o.to_dict() for o in opps]
                for date, opps in opportunities.items()
            }
        }
        
        filename = f"skiplagging_{origin}_{destination}_march2026.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 结果已保存到: {filename}")
        return filename
    
    def generate_report(self, origin: str, destination: str,
                       direct_flights: Dict, opportunities: Dict) -> str:
        """生成可读报告"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"Skiplagging 分析报告: {origin} → {destination} (2026年3月)")
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 统计信息
        total_dates = len(direct_flights)
        dates_with_flights = sum(1 for flights in direct_flights.values() if flights)
        dates_with_opps = sum(1 for opps in opportunities.values() if opps)
        
        lines.append(f"📊 统计:")
        lines.append(f"  查询日期数: {total_dates}")
        lines.append(f"  有航班的日期: {dates_with_flights}")
        lines.append(f"  有 skiplagging 机会的日期: {dates_with_opps}")
        lines.append("")
        
        # 每日详情
        lines.append("📅 每日详情:")
        lines.append("-" * 80)
        
        dates = sorted(direct_flights.keys())
        for date in dates:
            direct = direct_flights.get(date, [])
            opps = opportunities.get(date, [])
            
            lines.append(f"\n{date}:")
            
            if direct:
                cheapest = direct[0]
                lines.append(f"  直飞: ${cheapest.price} ({cheapest.flight_number}) {cheapest.departure_time[11:16]}")
            else:
                lines.append(f"  直飞: 无")
            
            if opps:
                best = opps[0]
                lines.append(f"  💡 Skiplag: ${best.skiplag_flight.price} → 省 ${best.savings:.0f} ({best.savings_percent:.1f}%)")
                lines.append(f"     航班: {best.skiplag_flight.flight_number} ({best.skiplag_flight.origin}→{best.via_airport}→{best.final_destination})")
            else:
                lines.append(f"  💡 Skiplag: 无机会")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("⚠️  风险提示:")
        lines.append("  • Skiplagging 违反大多数航空公司条款")
        lines.append("  • 可能被封号、里程清零、拒载")
        lines.append("  • 不要托运行李（行李会直挂到票面上的终点）")
        lines.append("  • 不要买往返票（放弃后半程可能导致返程被取消）")
        lines.append("  • 航班变动时航空公司可能改道")
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        # 保存报告
        report_file = f"report_{origin}_{destination}_march2026.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📝 报告已保存: {report_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description='真实航班数据 Skiplagging 搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skiplagging_real.py AUS DCA
  python skiplagging_real.py LAX JFK --hubs ORD ATL DFW
  python skiplagging_real.py SFO BOS --dates 2026-03-15 2026-03-20
        """
    )
    
    parser.add_argument('origin', help='出发机场代码 (如 AUS)')
    parser.add_argument('destination', help='目的地机场代码 (如 DCA)')
    parser.add_argument('--hubs', nargs='+', 
                       help='额外搜索的枢纽机场')
    parser.add_argument('--dates', nargs='+',
                       help='指定日期 (默认整个3月)')
    
    args = parser.parse_args()
    
    try:
        finder = RealSkiplaggingFinder()
        
        # 获取日期列表
        if args.dates:
            dates = args.dates
        else:
            dates = finder.get_march_dates(2026)
        
        print(f"\n{'='*80}")
        print(f"🛫 出发地: {args.origin}")
        print(f"🛬 目的地: {args.destination}")
        print(f"📅 查询日期: {len(dates)} 天 (2026年3月)")
        print(f"{'='*80}\n")
        
        # 搜索直飞航班
        direct_flights = finder.search_direct_flights(
            args.origin, args.destination, dates
        )
        
        # 搜索 skiplagging 机会
        opportunities = finder.search_skiplag_opportunities(
            args.origin, args.destination, dates, args.hubs
        )
        
        # 保存结果
        finder.save_results(args.origin, args.destination, 
                          direct_flights, opportunities)
        
        # 生成报告
        report = finder.generate_report(args.origin, args.destination,
                                       direct_flights, opportunities)
        
        print("\n" + report)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        raise


if __name__ == "__main__":
    main()
