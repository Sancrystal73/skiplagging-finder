# Skiplagging Finder - Real Data Version 🛫

使用 **Amadeus API** 获取真实航班数据，不再使用模拟数据！

## 🆕 新版本特性

- ✅ **真实航班价格** - 来自 Amadeus GDS 的真实报价
- ✅ **真实航班号** - 实际运营的航班编号
- ✅ **真实日期时间** - 实际起降时间
- ✅ **整月价格追踪** - 查询整个3月的价格趋势
- ✅ **缓存机制** - 避免重复 API 调用，节省额度
- ✅ **自动查找机会** - 自动搜索 skiplagging 机会

## 🔑 API Key

Amadeus API Key 已内置（免费额度：每月 2,000 次调用）

如需使用自己的 Key：
```bash
export AMADEUS_API_KEY='your_key'
export AMADEUS_API_SECRET='your_secret'
```

## 🚀 使用方法

### 命令行版本

```bash
# 搜索单个日期
python skiplagging_real.py AUS DCA

# 指定日期范围
python skiplagging_real.py LAX JFK --dates 2026-03-15 2026-03-20

# 指定枢纽机场
python skiplagging_real.py SFO BOS --hubs ORD ATL DFW
```

### Web 版本

```bash
pip install -r requirements.txt
python app_real.py
```

访问 http://localhost:5000

## 📊 输出示例

```
================================================================================
🛫 出发地: AUS
🛬 目的地: DCA
📅 查询日期: 31 天 (2026年3月)
================================================================================

🔍 搜索 AUS → DCA 直飞航班（3月）
============================================================
  2026-03-01: 12 个航班，最低 $189.50 (AA1234)
  2026-03-02: 15 个航班，最低 $195.00 (AA5678)
  ...

🔎 搜索 AUS → DCA Skiplagging 机会（3月）
============================================================

📅 2026-03-15:
  直飞最低: $189.50 (AA1234)
  💡 Skiplag: $145.00 → 省 $44.50 (23.5%)
     航班: AA5678 (AUS→ORD→BOS)
```

## 🗂️ 文件说明

| 文件 | 说明 |
|------|------|
| `skiplagging_real.py` | 主程序，使用真实 Amadeus API |
| `app_real.py` | Flask Web 版本 |
| `requirements.txt` | Python 依赖 |
| `amadeus_cache.json` | API 缓存（自动生成） |

## ⚠️ 重要提示

- Skiplagging 违反大多数航空公司条款
- 可能被封号、里程清零、拒载
- 不要托运行李（行李会直挂到票面上的终点）
- 不要买往返票（放弃后半程可能导致返程被取消）
- 航班变动时航空公司可能改道

## 🌐 部署

### Render 部署

1. Fork 此仓库
2. 在 Render 创建新的 Web Service
3. 选择 Python 环境
4. 设置启动命令：`python app_real.py`
5. 部署完成

## 📄 许可证

MIT License

---

**注意**: 此工具仅供研究和学习使用。使用 skiplagging 策略可能违反航空公司条款，请自行承担风险。
