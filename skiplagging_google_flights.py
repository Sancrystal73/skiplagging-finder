# skiplagging_google_flights.py
# 使用 Selenium 爬取 Google Flights 真实数据（含转机航班）

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import re
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FlightOption:
    origin: str
    destination: str
    price: float
    airline: str
    duration: str
    stops: int
    layover_airport: Optional[str] = None
    layover_duration: Optional[str] = None
    is_skiplag_candidate: bool = False


class GoogleFlightsSkiplaggingFinder:
    """
    基于 Google Flights 的真实 Skiplagging 搜索器
    """
    
    HUBS = ['ATL', 'DFW', 'DEN', 'ORD', 'LAX', 'JFK', 'EWR', 'SFO', 'SEA', 'MIA', 'YYZ', 'YVR']
    
    def __init__(self, headless=True, proxy=None):
        self.headless = headless
        self.proxy = proxy or os.getenv('HTTP_PROXY')
        self.driver = None
        
    def _init_driver(self):
        """初始化 Chrome 浏览器"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
            print(f"🌐 使用代理: {self.proxy}")
        
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
        })
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(15)
          def _parse_duration(self, duration_text: str) -> int:
        """解析飞行时长（分钟）"""
        hours = re.search(r'(\d+)\s*hr', duration_text)
        mins = re.search(r'(\d+)\s*min', duration_text)
        total = 0
        if hours:
            total += int(hours.group(1)) * 60
        if mins:
            total += int(mins.group(1))
        return total
    
    def search_flights(self, origin: str, destination: str, date: str) -> List[FlightOption]:
        """搜索 Google Flights，返回所有航班选项（含转机）"""
        if not self.driver:
            self._init_driver()
        
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
        url = f"https://www.google.com/travel/flights/search?tfs=CBwQ{origin}.{destination}.{formatted_date}&hl=en&curr=USD"
        
        print(f"   🔍 搜索 {origin} → {destination}...")
        self.driver.get(url)
        time.sleep(8)
        
        flights = []
        
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[role='listitem']"))
            )
            
            flight_cards = self.driver.find_elements(By.CSS_SELECTOR, "[role='listitem']")
            
            for card in flight_cards[:10]:
                try:
                    flight = self._parse_flight_card(card, origin, destination)
                    if flight:
                        flights.append(flight)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"   ⚠️ 获取航班失败: {e}")
        
        return flights
    
    def _parse_flight_card(self, card, origin: str, destination: str) -> Optional[FlightOption]:
        """解析单个航班卡片"""
        try:
            price_elem = card.find_element(By.CSS_SELECTOR, "[aria-label*='$']")
            price_text = price_elem.get_attribute("aria-label")
            price_match = re.search(r'\$([\d,]+)', price_text)
            if not price_match:
                return None
            price = float(price_match.group(1).replace(',', ''))
            
            try:
                airline_elem = card.find_element(By.CSS_SELECTOR, "[class*='airline'], [class*='Airline']")
                airline = airline_elem.text
            except:
                airline = "Unknown"
            
            stops = 0
            layover_airport = None
            layover_duration = None
            
            try:
                stops_elem = card.find_element(By.CSS_SELECTOR, "[class*='stop'], [class*='Stop']")
                stops_text = stops_elem.text.lower()
                
                if 'nonstop' in stops_text or 'non-stop' in stops_text:
                    stops = 0
                elif '1 stop' in stops_text:
                    stops = 1
                elif '2 stops' in stops_text:
                    stops = 2
                
                layover_match = re.search(r'(\d+)\s*stop\s*(?:in|at)\s*([A-Z]{3})', stops_text, re.IGNORECASE)
                if layover_match:
                    layover_airport = layover_match.group(2).upper()
                    
            except:
                pass
            
            try:
                duration_elem = card.find_element(By.CSS_SELECTOR, "[class*='duration'], [class*='Duration']")
                duration = duration_elem.text
            except:
                duration = "Unknown"
            
            return FlightOption(
                origin=origin,
                destination=destination,
                price=price,
                airline=airline,
                duration=duration,
                stops=stops,
                layover_airport=layover_airport,
                layover_duration=layover_duration
            )
            
        except Exception as e:
            return None
def find_skiplagging_opportunities(self, origin: str, real_destination: str, 
                                       date: str, max_hubs: int = 5) -> dict:
        """查找真实的 Skiplagging 机会"""
        print(f"\n{'='*60}")
        print(f"🔍 Google Flights 真实数据搜索")
        print(f"   {origin} → {real_destination} | {date}")
        print(f"{'='*60}\n")
        
        if not self.driver:
            self._init_driver()
        
        print("📍 步骤 1: 搜索直飞航班...")
        direct_flights = self.search_flights(origin, real_destination, date)
        
        if not direct_flights:
            print("   ❌ 未找到直飞航班")
            return {"error": "No direct flights found"}
        
        direct_flights.sort(key=lambda x: x.price)
        cheapest_direct = direct_flights[0]
        
        print(f"\n✈️  直飞选项:")
        print(f"   {cheapest_direct.airline}")
        print(f"   价格: ${cheapest_direct.price}")
        print(f"   时长: {cheapest_direct.duration}")
        print(f"   经停: {'无' if cheapest_direct.stops == 0 else cheapest_direct.stops}")
        print()
        
        print("📍 步骤 2: 搜索经停航班...")
        skiplag_options = []
        
        relevant_hubs = [h for h in self.HUBS if h != origin and h != real_destination]
        checked = 0
        
        for hub in relevant_hubs:
            if checked >= max_hubs:
                break
                
            connecting_flights = self.search_flights(origin, hub, date)
            checked += 1
            
            for flight in connecting_flights:
                if flight.stops > 0 and flight.layover_airport == real_destination:
                    if flight.price < cheapest_direct.price:
                        flight.is_skiplag_candidate = True
                        skiplag_options.append(flight)
                        print(f"   ✓ 发现机会: {origin} → {hub} 经停 {real_destination} | ${flight.price}")
        
        print(f"\n   检查了 {checked} 个枢纽，找到 {len(skiplag_options)} 个真实机会")
        
        result = {
            "direct": cheapest_direct,
            "skiplagging": skiplag_options,
            "savings": 0,
            "best_option": None
        }
        
        if skiplag_options:
            skiplag_options.sort(key=lambda x: x.price)
            best = skiplag_options[0]
            savings = cheapest_direct.price - best.price
            result["savings"] = savings
            result["best_option"] = best
            
            print(f"\n{'='*60}")
            print(f"💰 找到 {len(skiplag_options)} 个真实 Skiplagging 机会！")
            print(f"💵 最高节省: ${savings:.2f}")
            print(f"{'='*60}\n")
            
            for i, opt in enumerate(skiplag_options[:3], 1):
                print(f"选项 {i}:")
                print(f"   票面行程: {opt.origin} → {opt.destination}")
                print(f"   实际下机: {opt.origin} → {opt.layover_airport}")
                print(f"   航空公司: {opt.airline}")
                print(f"   价格: ${opt.price} (比直飞省 ${cheapest_direct.price - opt.price:.0f})")
                print(f"   总时长: {opt.duration}")
                print(f"   经停时间: {opt.layover_duration or '未知'}")
                print()
            
            print("⚠️  重要提醒:")
            print("   • 这是真实 Google Flights 数据")
            print("   • 不要托运行李（会直挂到票面终点）")
            print("   • 不要买往返票（返程可能被取消）")
            print("   • 提前在线值机，避免柜台检查")
            
        else:
            print(f"\n{'='*60}")
            print("❌ 未找到更便宜的 Skiplagging 机会")
            print("   直飞价格已经是最优")
            print(f"{'='*60}")
        
        return result
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


def main():
    """测试真实 Google Flights 搜索"""
    proxy = os.getenv('HTTP_PROXY')
    if proxy:
        print(f"🌐 检测到代理: {proxy}\n")
    else:
        print("⚠️  无代理设置，直连 Google Flights（可能连接失败）\n")
    
    finder = GoogleFlightsSkiplaggingFinder(headless=True, proxy=proxy)

    try:
        result = finder.find_skiplagging_opportunities(
            origin="AUS",
            real_destination="YYZ",
            date="2026-03-26",
            max_hubs=5
        )
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        finder.close()


if __name__ == "__main__":
    main()
