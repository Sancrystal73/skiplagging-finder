from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 启动浏览器
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("正在访问 AirLabs 注册页面...")
driver.get("https://airlabs.co/signup")
time.sleep(3)

print("正在填写表单...")

# 填写各个字段
try:
    # Full name
    driver.find_element(By.NAME, "name").send_keys("Henry")
    print("✓ Name")
    
    # Website
    driver.find_element(By.NAME, "website").send_keys("https://shaw-input-vegetables-aerospace.trycloudflare.com")
    print("✓ Website")
    
    # Company
    driver.find_element(By.NAME, "company").send_keys("Personal Project")
    print("✓ Company")
    
    # Activity - 下拉选择
    activity_select = Select(driver.find_element(By.NAME, "activity"))
    activity_select.select_by_value("Personal")
    print("✓ Activity")
    
    # Description
    driver.find_element(By.NAME, "description").send_keys(
        "Flight price comparison and route analysis tool for educational purposes. "
        "Helps users find cheaper flight options by analyzing hidden city ticketing opportunities."
    )
    print("✓ Description")
    
    # Email
    driver.find_element(By.NAME, "email").send_keys("2006.henry.mao@gmail.com")
    print("✓ Email")
    
    # Password
    password = "Sk!pLag2024$Secure"
    driver.find_element(By.NAME, "password").send_keys(password)
    print("✓ Password")
    
    # 同意条款
    driver.find_element(By.NAME, "terms").click()
    print("✓ Terms")
    
    # 保存密码
    with open("/root/.openclaw/workspace/airlabs_credentials.txt", "w") as f:
        f.write(f"Email: 2006.henry.mao@gmail.com\n")
        f.write(f"Password: {password}\n")
    print("\n凭证已保存到 airlabs_credentials.txt")
    
    # 点击注册按钮
    print("\n正在提交...")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    submit_btn.click()
    
    # 等待结果
    time.sleep(5)
    
    # 检查页面内容
    page_text = driver.find_element(By.TAG_NAME, "body").text
    print(f"\n页面状态: {driver.title}")
    
    if "success" in page_text.lower() or "check" in page_text.lower() or "email" in page_text.lower():
        print("✓ 注册成功！请检查邮箱收取验证邮件")
    elif "error" in page_text.lower():
        print(f"✗ 注册可能失败，页面内容: {page_text[:500]}")
    else:
        print("? 注册状态不确定，请检查邮箱")
        print(f"页面片段: {page_text[:500]}")
    
    # 截图保存
    driver.save_screenshot("/tmp/airlabs_signup_result.png")
    print("\n截图已保存: /tmp/airlabs_signup_result.png")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    driver.quit()
    print("\n浏览器已关闭")
