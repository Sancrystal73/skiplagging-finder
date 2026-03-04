# Skiplagging Finder - 本地运行指南

## 快速开始

### 1. 安装依赖

```bash
pip install flask beautifulsoup4 selenium webdriver_manager requests
```

### 2. 配置代理（可选）

如果你在中国，需要配置代理才能访问 Google Flights：

**方法 A: 环境变量方式**
```bash
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
```

**方法 B: 修改代码**
在 `google_flights_scraper.py` 中取消代理相关的注释。

### 3. 运行

```bash
cd skiplagging_finder
python app.py
```

然后访问 http://localhost:5000

## 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | 主程序（Flask 网站） |
| `skiplagging_airlabs.py` | AirLabs API 版本 |
| `skiplagging_hybrid.py` | 混合版本（AirLabs + Google Flights） |
| `flight_database.json` | 本地航线数据库 |
| `requirements.txt` | Python 依赖 |

## API Keys

### AirLabs（已有）
```
870c8003-7051-4496-990b-01b0eeec5f5f
```

### Google Flights
无需 API Key，直接网页抓取

## 使用代理的完整示例

```bash
# 设置代理（根据你自己的代理配置修改）
export HTTP_PROXY="socks5://127.0.0.1:1080"
export HTTPS_PROXY="socks5://127.0.0.1:1080"

# 运行
python app.py
```

## 常见问题

**Q: 提示 ChromeDriver 错误？**  
A: 确保安装了 Chrome 浏览器，或者手动下载 chromedriver

**Q: Google Flights 连不上？**  
A: 需要配置代理，或者直接用 AirLabs 版本

**Q: AirLabs 额度用完了？**  
A: 免费版每月 1000 次调用，超了可以注册新账号
