# Skiplagging Flight Finder ✈️

> 隐藏城市购票搜索工具 - 帮你找到更便宜的机票

## 什么是 Skiplagging？

**例子：**
- 直飞：奥斯汀 (AUS) → 华盛顿 (DCA) = **$280**
- 转机：奥斯汀 (AUS) → 纽约 (JFK)，**经停华盛顿** = **$150**

你在华盛顿下机，放弃后半段，省了 $130！

⚠️ **风险提示**：航空公司不喜欢这种方式，可能导致：
- 返程票被取消
- 常旅客账号被封
- 行李直挂到终点无法取出

**适合**：单程、无托运行李、能承担风险

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `skiplagging_finder.py` | 演示版本（无需 API，用模拟数据） |
| `skiplagging_api.py` | 真实版本（需要 Amadeus API Key） |
| `requirements.txt` | 依赖包 |

---

## 快速开始

### 1. 演示版本（无需 API）

```bash
cd skiplagging_finder
python skiplagging_finder.py
```

输出示例：
```
🔍 搜索 AUS → DCA 的机票...
📅 日期: 2026-03-15

✈️  直飞选项:
   American Airlines AA1234
   价格: $280
   时间: 08:00 - 11:30

🔎 搜索经停 DCA 的转机航班...
💰 找到 2 个 Skiplagging 机会！
💵 最高可节省: $130.00

   选项 1:
   票面: AUS → JFK (经停 DCA)
   实际: AUS → DCA (在 DCA 下机)
   航班: American Airlines AA567
   价格: $150 (省 $130)
   时间: 06:00 - 12:00
```

### 2. 真实版本（使用 Amadeus API）

#### 申请 API Key
1. 访问 https://developers.amadeus.com/
2. 注册账号（免费）
3. 创建应用，获取 API Key 和 Secret
4. 每月 2,000 次免费调用（足够个人使用）

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 使用方法

**方式 1：环境变量**
```bash
export AMADEUS_API_KEY='your_api_key_here'
export AMADEUS_API_SECRET='your_api_secret_here'

python skiplagging_api.py AUS DCA 2026-03-15
```

**方式 2：命令行参数**
```bash
python skiplagging_api.py AUS DCA 2026-03-15 \
    --api-key 'your_key' \
    --api-secret 'your_secret'
```

**方式 3：Python 调用**
```python
from skiplagging_api import AmadeusSkiplaggingFinder

finder = AmadeusSkiplaggingFinder()
opportunities = finder.find_skiplagging(
    origin="AUS",
    destination="DCA",
    date="2026-03-15"
)
finder.print_opportunities(opportunities)
```

---

## 工作原理

```
用户输入: AUS → DCA, 2026-03-15

├─ 步骤 1: 搜索 AUS → DCA 直飞
│  └─ 最便宜直飞: $280 (AA1234)
│
├─ 步骤 2: 搜索 AUS → [各大枢纽]
│  ├─ AUS → JFK: $150 ✓ (经停 DCA)
│  ├─ AUS → BOS: $180 ✓ (经停 DCA)
│  └─ AUS → LAX: $320 ✗ (不经停 DCA)
│
├─ 步骤 3: 比较价格
│  └─ AUS → JFK ($150) < AUS → DCA ($280)
│     └─ 找到机会！节省 $130
│
└─ 输出: 推荐 AUS → JFK 经停 DCA 的航班
          在 DCA 下机，放弃 JFK 段
```

---

## 使用技巧

### 1. 选择合适的目的地
- **大枢纽**更容易有 skiplagging 机会
- 如：DCA 附近的大枢纽有 JFK、EWR、BOS、ATL

### 2. 搜索策略
```bash
# 基本搜索
python skiplagging_api.py AUS DCA 2026-03-15

# 指定额外搜索的枢纽
python skiplagging_api.py AUS DCA 2026-03-15 --hubs JFK BOS EWR

# 测试不同日期（通常周二周三最便宜）
python skiplagging_api.py AUS DCA 2026-03-18
```

### 3. 实际购票注意事项
1. **不要托运行李** - 行李会直挂到票面上的终点
2. **不要买往返票** - 放弃后半程可能导致返程被取消
3. **不要用常用账号** - 建议使用无痕模式，不登录常旅客账号
4. **航班变动** - 如果航班取消/改道，航空公司可能安排直飞或其他路线，需自行承担风险
5. **提前值机** - 有些航司对 skiplagging 乘客可能限制值机，建议提前在线值机

---

## 扩展功能（TODO）

- [ ] 多日期批量搜索
- [ ] 附近机场搜索（如 DCA/IAD/BWI 都算作华盛顿地区）
- [ ] 历史价格追踪
- [ ] 邮件/通知提醒
- [ ] Web 界面
- [ ] 移动端 App

---

## 常见问题

**Q: 这是违法的吗？**  
A: 不违法，但违反航空公司条款。可能被罚（如取消返程），但不会进监狱。

**Q: 为什么 API 需要信用卡？**  
A: Amadeus 免费额度 2,000 次/月，超出后才收费。通常个人使用不会超。

**Q: 可以找到国际航班的 skiplagging 吗？**  
A: 可以，但要注意：
- 国际航班涉及签证问题（需要终点国家的签证）
- 海关和边检可能在出发地检查签证

---

## 免责声明

此工具仅供学习研究，使用 Skiplagging 需自行承担风险。航空公司可能采取措施（如取消机票、封号等）。

---

Made with ❤️ by OpenClaw
