# variflight_scraper.py
# 使用 Selenium 爬取飞常准航线数据

import json
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class VariFlightScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://map.variflight.com"
        
    def init_driver(self):
        """初始化 Chrome 浏览器"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 禁用图片加载，加快速度
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
        })
        
        try:
            # 使用 webdriver-manager 自动管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✓ Chrome 浏览器已启动")
        except Exception as e:
            print(f"✗ 启动浏览器失败: {e}")
            raise
    
    def login(self, username, password):
        """登录飞常准"""
        print("正在登录...")
        self.driver.get(f"{self.base_url}/login")
        time.sleep(2)
        
        try:
            # 查找用户名和密码输入框
            username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[name='username'], input[placeholder*='邮箱'], input[placeholder*='手机']")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            
            username_input.clear()
            username_input.send_keys(username)
            time.sleep(0.5)
            
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(0.5)
            
            # 点击登录按钮
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn, button:contains('登录')")
            login_btn.click()
            
            time.sleep(3)
            
            # 检查是否登录成功
            if "login" not in self.driver.current_url:
                print("✓ 登录成功")
                return True
            else:
                print("✗ 登录失败")
                return False
                
        except Exception as e:
            print(f"登录过程出错: {e}")
            return False
    
    def search_route(self, dep_code, arr_code, date_str):
        """
        搜索特定航线
        返回航班列表
        """
        url = f"{self.base_url}/?dep={dep_code}&arr={arr_code}&date={date_str}"
        print(f"搜索: {dep_code} -> {arr_code} ({date_str})")
        
        self.driver.get(url)
        time.sleep(3)  # 等待页面加载
        
        flights = []
        
        try:
            # 等待航班列表加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-item, .flight-list, [class*='flight']"))
            )
            
            # 解析航班数据
            # 注意：这里的选择器需要根据实际网页结构调整
            flight_elements = self.driver.find_elements(By.CSS_SELECTOR, ".flight-item, .flight-row")
            
            for elem in flight_elements:
                try:
                    flight = self._parse_flight_element(elem)
                    if flight:
                        flights.append(flight)
                except Exception as e:
                    continue
            
            print(f"  找到 {len(flights)} 个航班")
            
        except Exception as e:
            print(f"  未找到航班数据: {e}")
        
        return flights
    
    def _parse_flight_element(self, elem):
        """解析单个航班元素"""
        flight = {}
        
        try:
            # 这里的选择器需要根据实际网页结构调整
            # 尝试多种可能的选择器
            
            # 航班号
            try:
                flight_no = elem.find_element(By.CSS_SELECTOR, ".flight-no, .flight-number, .num").text
                flight['flight_number'] = flight_no
            except:
                pass
            
            # 航空公司
            try:
                airline = elem.find_element(By.CSS_SELECTOR, ".airline, .company").text
                flight['airline'] = airline
            except:
                pass
            
            # 出发时间
            try:
                dep_time = elem.find_element(By.CSS_SELECTOR, ".dep-time, .departure-time").text
                flight['departure'] = dep_time
            except:
                pass
            
            # 到达时间
            try:
                arr_time = elem.find_element(By.CSS_SELECTOR, ".arr-time, .arrival-time").text
                flight['arrival'] = arr_time
            except:
                pass
            
            # 价格
            try:
                price = elem.find_element(By.CSS_SELECTOR, ".price, .fare").text
                flight['price'] = self._extract_price(price)
            except:
                flight['price'] = None
            
            # 经停信息
            try:
                stops = elem.find_element(By.CSS_SELECTOR, ".stop, .via").text
                flight['stops'] = 1 if '经停' in stops or 'stop' in stops.lower() else 0
            except:
                flight['stops'] = 0
            
        except Exception as e:
            return None
        
        return flight if flight.get('flight_number') else None
    
    def _extract_price(self, price_text):
        """从价格文本中提取数字"""
        import re
        numbers = re.findall(r'[\d,]+', price_text.replace(',', ''))
        if numbers:
            return float(numbers[0])
        return None
    
    def scrape_multiple_routes(self, routes, date_str):
        """
        批量爬取多条航线
        routes: [(dep, arr), ...]
        """
        all_data = {}
        
        for i, (dep, arr) in enumerate(routes):
            print(f"\n[{i+1}/{len(routes)}] 正在爬取 {dep} -> {arr}")
            
            flights = self.search_route(dep, arr, date_str)
            
            if flights:
                key = f"{dep}_{arr}"
                all_data[key] = {
                    "date": date_str,
                    "flights": flights,
                }
            
            # 随机延迟，避免被封
            delay = random.uniform(2, 5)
            time.sleep(delay)
        
        return all_data
    
    def scrape_popular_routes(self, date_str, max_routes=50):
        """
        爬取热门航线
        """
        # 美国主要机场的热门组合
        popular_routes = [
            # 东西海岸
            ("JFK", "LAX"), ("LAX", "JFK"),
            ("EWR", "SFO"), ("SFO", "EWR"),
            ("BOS", "LAX"), ("LAX", "BOS"),
            ("JFK", "SEA"), ("SEA", "JFK"),
            
            # 南部到东西海岸
            ("ATL", "LAX"), ("LAX", "ATL"),
            ("DFW", "JFK"), ("JFK", "DFW"),
            ("IAH", "LAX"), ("LAX", "IAH"),
            ("MIA", "LAX"), ("LAX", "MIA"),
            
            # 中西部
            ("ORD", "LAX"), ("LAX", "ORD"),
            ("DEN", "JFK"), ("JFK", "DEN"),
            ("MSP", "LAX"), ("LAX", "MSP"),
            
            # 短途热门
            ("JFK", "DCA"), ("DCA", "JFK"),
            ("JFK", "BOS"), ("BOS", "JFK"),
            ("LAX", "SFO"), ("SFO", "LAX"),
            ("LAX", "SAN"), ("SAN", "LAX"),
            ("JFK", "ORD"), ("ORD", "JFK"),
            ("DFW", "ORD"), ("ORD", "DFW"),
            
            # 更多组合
            ("ATL", "MIA"), ("MIA", "ATL"),
            ("ATL", "JFK"), ("JFK", "ATL"),
            ("DFW", "MIA"), ("MIA", "DFW"),
            ("DEN", "SEA"), ("SEA", "DEN"),
            ("PHX", "LAX"), ("LAX", "PHX"),
            ("LAS", "LAX"), ("LAX", "LAS"),
        ][:max_routes]
        
        return self.scrape_multiple_routes(popular_routes, date_str)
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("✓ 浏览器已关闭")


def main():
    # 计算后天日期
    target_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"目标日期: {target_date}")
    
    # 初始化爬虫
    scraper = VariFlightScraper(headless=True)
    
    try:
        scraper.init_driver()
        
        # 登录（如果需要）
        # scraper.login("henrym73@163.com", "69Quoll！")
        
        # 爬取热门航线
        print(f"\n开始爬取 {target_date} 的航线数据...")
        data = scraper.scrape_popular_routes(target_date, max_routes=30)
        
        # 保存数据
        output_file = f"variflight_data_{target_date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 数据已保存到 {output_file}")
        print(f"共爬取 {len(data)} 条航线")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
