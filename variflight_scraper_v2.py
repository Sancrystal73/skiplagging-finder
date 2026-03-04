# variflight_scraper_v2.py
# 爬取飞常准航线数据 - 处理弹窗

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import json
import time
import re

target_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
print(f"目标日期: {target_date}")

# 启动浏览器
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
print("浏览器已启动")

# 先访问首页关闭弹窗
print("访问首页关闭弹窗...")
driver.get("https://map.variflight.com")
time.sleep(3)

# 尝试关闭弹窗
try:
    # 查找关闭按钮 (X)
    close_btn = driver.find_element(By.CSS_SELECTOR, ".modal-close, .close-btn, button[aria-label='close'], .el-dialog__close")
    close_btn.click()
    print("已关闭弹窗")
    time.sleep(1)
except:
    print("没有找到弹窗或弹窗已关闭")

# 热门国内航线
routes = [
    ("PEK", "SHA"), ("SHA", "PEK"),
    ("CAN", "PEK"), ("PEK", "CAN"),
    ("PVG", "SZX"), ("SZX", "PVG"),
    ("CTU", "PVG"), ("PVG", "CTU"),
    ("HGH", "PEK"), ("PEK", "HGH"),
    ("CKG", "PEK"), ("PEK", "CKG"),
    ("XIY", "PEK"), ("PEK", "XIY"),
    ("CAN", "SHA"), ("SHA", "CAN"),
    ("SZX", "CTU"), ("CTU", "SZX"),
    ("KMG", "PEK"), ("PEK", "KMG"),
]

all_data = {}

for dep, arr in routes:
    print(f"\n[{len(all_data)+1}/{len(routes)}] 搜索: {dep} -> {arr}")
    
    try:
        # 访问航线页面
        url = f"https://map.variflight.com/?dep={dep}&arr={arr}&date={target_date}"
        driver.get(url)
        time.sleep(4)
        
        # 尝试关闭可能出现的弹窗
        try:
            close_btns = driver.find_elements(By.CSS_SELECTOR, ".modal-close, .close, .el-dialog__close, button[class*='close']")
            for btn in close_btns:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(0.5)
        except:
            pass
        
        # 查找航线数据
        page_source = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        flights = []
        
        # 尝试多种方式提取航班数据
        # 方法1: 查找航班列表元素
        try:
            flight_items = driver.find_elements(By.CSS_SELECTOR, ".flight-item, .route-item, [class*='flight']")
            print(f"  找到 {len(flight_items)} 个航班元素")
            
            for item in flight_items[:5]:  # 只取前5个
                try:
                    text = item.text
                    if text and len(text) > 10:
                        flights.append({"raw_text": text})
                except:
                    pass
        except Exception as e:
            print(f"  提取元素失败: {e}")
        
        # 方法2: 从页面文本中提取
        if not flights:
            # 保存页面文本用于分析
            all_data[f"{dep}_{arr}"] = {
                "date": target_date,
                "page_text_sample": page_text[:1000] if len(page_text) > 1000 else page_text,
                "flights": []
            }
        else:
            all_data[f"{dep}_{arr}"] = {
                "date": target_date,
                "flights": flights
            }
        
        print(f"  ✓ 已获取数据")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
    
    time.sleep(2)

driver.quit()
print("\n浏览器已关闭")

# 保存数据
output_file = f"variflight_raw_{target_date}.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ 数据已保存到 {output_file}")
print(f"共 {len(all_data)} 条航线")

# 显示样本
print("\n数据样本:")
for key, data in list(all_data.items())[:3]:
    print(f"\n{key}:")
    sample = data.get('page_text_sample', '')[:200]
    print(f"  {sample}...")
