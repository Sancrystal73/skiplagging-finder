# google_flights_scraper.py
# 使用 Selenium 查询 Google Flights 价格 - 支持代理

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os

class GoogleFlightsScraper:
    """Google Flights 价格查询器"""
    
    def __init__(self, headless=True, proxy=None):
        self.headless = headless
        self.proxy = proxy or os.getenv('HTTP_PROXY')
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化浏览器"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # 配置代理
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
            print(f"使用代理: {self.proxy}")
        
        # 禁用图片加速
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
        })
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def search_price(self, origin: str, destination: str, date: str) -> float:
        """查询单程航班价格"""
        url = f"https://www.google.com/travel/flights/search?tfs=CBwQ{origin}.{destination}.{date}&hl=en"
        
        print(f"   🌐 Google Flights: {origin} → {destination}")
        self.driver.get(url)
        time.sleep(5)
        
        try:
            # 查找价格
            price_selectors = [
                "[class*='price']",
                "[class*=' Price']",
                "[jsname*='price']",
            ]
            
            prices = []
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        match = re.search(r'\$[\d,]+', text)
                        if match:
                            price_str = match.group().replace('$', '').replace(',', '')
                            price = float(price_str)
                            if 50 < price < 5000:
                                prices.append(price)
                except:
                    continue
            
            if prices:
                min_price = min(prices)
                print(f"   ✓ 价格: ${min_price}")
                return min_price
            else:
                print(f"   ⚠ 未找到价格")
                return None
                
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()


def get_google_flights_price(origin: str, destination: str, date: str) -> float:
    """快速查询 Google Flights 价格"""
    # 使用 requests + BeautifulSoup（更快）
    import requests
    from bs4 import BeautifulSoup
    
    # 从环境变量获取代理
    proxies = {}
    http_proxy = os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('HTTPS_PROXY')
    
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy
    
    url = f"https://www.google.com/travel/flights/search?tfs=CBwQ{origin}.{destination}.{date}&hl=en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 提取价格
        prices = []
        for elem in soup.find_all(text=re.compile(r'\$[\d,]+')):
            match = re.search(r'\$([\d,]+)', elem)
            if match:
                price = float(match.group(1).replace(',', ''))
                if 50 < price < 5000:
                    prices.append(price)
        
        if prices:
            return min(prices)
        
        return None
        
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
        return None


if __name__ == "__main__":
    # 测试
    print("Testing Google Flights...")
    
    # 检查代理
    proxy = os.getenv('HTTP_PROXY')
    if proxy:
        print(f"使用代理: {proxy}")
    else:
        print("无代理，直连")
    
    price = get_google_flights_price("JFK", "LAX", "2026-03-07")
    print(f"Price: ${price}")
