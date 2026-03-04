# flight_data_generator.py
# 生成扩展的模拟航班数据用于 skiplagging 演示

import random
import json
from datetime import datetime, timedelta

# 主要机场数据 (IATA代码, 城市, 国家, 区域)
AIRPORTS = [
    # 美国主要机场
    ("ATL", "Atlanta", "USA", "US"),
    ("LAX", "Los Angeles", "USA", "US"),
    ("ORD", "Chicago", "USA", "US"),
    ("DFW", "Dallas", "USA", "US"),
    ("DEN", "Denver", "USA", "US"),
    ("JFK", "New York", "USA", "US"),
    ("SFO", "San Francisco", "USA", "US"),
    ("SEA", "Seattle", "USA", "US"),
    ("LAS", "Las Vegas", "USA", "US"),
    ("MCO", "Orlando", "USA", "US"),
    ("MIA", "Miami", "USA", "US"),
    ("PHX", "Phoenix", "USA", "US"),
    ("IAH", "Houston", "USA", "US"),
    ("BOS", "Boston", "USA", "US"),
    ("MSP", "Minneapolis", "USA", "US"),
    ("DTW", "Detroit", "USA", "US"),
    ("PHL", "Philadelphia", "USA", "US"),
    ("CLT", "Charlotte", "USA", "US"),
    ("EWR", "Newark", "USA", "US"),
    ("BWI", "Baltimore", "USA", "US"),
    ("MDW", "Chicago Midway", "USA", "US"),
    ("SLC", "Salt Lake City", "USA", "US"),
    ("IAD", "Washington DC", "USA", "US"),
    ("DCA", "Washington DC", "USA", "US"),
    ("SAN", "San Diego", "USA", "US"),
    ("TPA", "Tampa", "USA", "US"),
    ("PDX", "Portland", "USA", "US"),
    ("AUS", "Austin", "USA", "US"),
    ("BNA", "Nashville", "USA", "US"),
    ("STL", "St. Louis", "USA", "US"),
    ("HNL", "Honolulu", "USA", "US"),
    ("RDU", "Raleigh", "USA", "US"),
    ("MSY", "New Orleans", "USA", "US"),
    ("SAT", "San Antonio", "USA", "US"),
    ("PIT", "Pittsburgh", "USA", "US"),
    ("CLE", "Cleveland", "USA", "US"),
    ("CMH", "Columbus", "USA", "US"),
    ("IND", "Indianapolis", "USA", "US"),
    ("MCI", "Kansas City", "USA", "US"),
    ("OAK", "Oakland", "USA", "US"),
    ("SJC", "San Jose", "USA", "US"),
    ("SMF", "Sacramento", "USA", "US"),
    ("SNA", "Santa Ana", "USA", "US"),
    ("FLL", "Fort Lauderdale", "USA", "US"),
    ("RSW", "Fort Myers", "USA", "US"),
    ("MKE", "Milwaukee", "USA", "US"),
    ("BUF", "Buffalo", "USA", "US"),
    ("PVD", "Providence", "USA", "US"),
    ("MHT", "Manchester", "USA", "US"),
    ("ALB", "Albany", "USA", "US"),
    ("SYR", "Syracuse", "USA", "US"),
    ("ROC", "Rochester", "USA", "US"),
    
    # 欧洲主要机场
    ("LHR", "London", "UK", "EU"),
    ("CDG", "Paris", "France", "EU"),
    ("AMS", "Amsterdam", "Netherlands", "EU"),
    ("FRA", "Frankfurt", "Germany", "EU"),
    ("MAD", "Madrid", "Spain", "EU"),
    ("BCN", "Barcelona", "Spain", "EU"),
    ("FCO", "Rome", "Italy", "EU"),
    ("MUC", "Munich", "Germany", "EU"),
    ("ZUR", "Zurich", "Switzerland", "EU"),
    ("VIE", "Vienna", "Austria", "EU"),
    ("CPH", "Copenhagen", "Denmark", "EU"),
    ("ARN", "Stockholm", "Sweden", "EU"),
    ("OSL", "Oslo", "Norway", "EU"),
    ("HEL", "Helsinki", "Finland", "EU"),
    ("DUB", "Dublin", "Ireland", "EU"),
    ("BRU", "Brussels", "Belgium", "EU"),
    ("MXP", "Milan", "Italy", "EU"),
    ("ATH", "Athens", "Greece", "EU"),
    ("LIS", "Lisbon", "Portugal", "EU"),
    ("WAW", "Warsaw", "Poland", "EU"),
    ("PRG", "Prague", "Czech Republic", "EU"),
    ("BUD", "Budapest", "Hungary", "EU"),
    
    # 亚洲主要机场
    ("HKG", "Hong Kong", "China", "AS"),
    ("NRT", "Tokyo Narita", "Japan", "AS"),
    ("HND", "Tokyo Haneda", "Japan", "AS"),
    ("ICN", "Seoul", "South Korea", "AS"),
    ("SIN", "Singapore", "Singapore", "AS"),
    ("BKK", "Bangkok", "Thailand", "AS"),
    ("KUL", "Kuala Lumpur", "Malaysia", "AS"),
    ("CGK", "Jakarta", "Indonesia", "AS"),
    ("MNL", "Manila", "Philippines", "AS"),
    ("TPE", "Taipei", "Taiwan", "AS"),
    ("PEK", "Beijing", "China", "AS"),
    ("PVG", "Shanghai", "China", "AS"),
    ("CAN", "Guangzhou", "China", "AS"),
    ("SZX", "Shenzhen", "China", "AS"),
    ("CTU", "Chengdu", "China", "AS"),
    ("HGH", "Hangzhou", "China", "AS"),
    ("XIY", "Xi'an", "China", "AS"),
    ("CKG", "Chongqing", "China", "AS"),
    ("KIX", "Osaka", "Japan", "AS"),
    ("NGO", "Nagoya", "Japan", "AS"),
    ("FUK", "Fukuoka", "Japan", "AS"),
    ("DEL", "New Delhi", "India", "AS"),
    ("BOM", "Mumbai", "India", "AS"),
    ("MAA", "Chennai", "India", "AS"),
    ("BLR", "Bangalore", "India", "AS"),
    ("HYD", "Hyderabad", "India", "AS"),
    ("CCU", "Kolkata", "India", "AS"),
    ("DXB", "Dubai", "UAE", "AS"),
    ("DOH", "Doha", "Qatar", "AS"),
    ("AUH", "Abu Dhabi", "UAE", "AS"),
    ("RUH", "Riyadh", "Saudi Arabia", "AS"),
    ("JED", "Jeddah", "Saudi Arabia", "AS"),
    ("TLV", "Tel Aviv", "Israel", "AS"),
    
    # 其他国际
    ("SYD", "Sydney", "Australia", "OC"),
    ("MEL", "Melbourne", "Australia", "OC"),
    ("BNE", "Brisbane", "Australia", "OC"),
    ("PER", "Perth", "Australia", "OC"),
    ("AKL", "Auckland", "New Zealand", "OC"),
    ("GRU", "Sao Paulo", "Brazil", "SA"),
    ("GIG", "Rio de Janeiro", "Brazil", "SA"),
    ("EZE", "Buenos Aires", "Argentina", "SA"),
    ("SCL", "Santiago", "Chile", "SA"),
    ("LIM", "Lima", "Peru", "SA"),
    ("BOG", "Bogota", "Colombia", "SA"),
    ("MEX", "Mexico City", "Mexico", "NA"),
    ("CUN", "Cancun", "Mexico", "NA"),
    ("YYZ", "Toronto", "Canada", "NA"),
    ("YVR", "Vancouver", "Canada", "NA"),
    ("YUL", "Montreal", "Canada", "NA"),
    ("YYC", "Calgary", "Canada", "NA"),
    ("JNB", "Johannesburg", "South Africa", "AF"),
    ("CPT", "Cape Town", "South Africa", "AF"),
    ("CAI", "Cairo", "Egypt", "AF"),
    ("NBO", "Nairobi", "Kenya", "AF"),
    ("ADD", "Addis Ababa", "Ethiopia", "AF"),
    ("LOS", "Lagos", "Nigeria", "AF"),
    ("CMN", "Casablanca", "Morocco", "AF"),
    ("TUN", "Tunis", "Tunisia", "AF"),
]

# 主要航空公司
AIRLINES = {
    "US": [
        ("AA", "American Airlines"),
        ("DL", "Delta Air Lines"),
        ("UA", "United Airlines"),
        ("WN", "Southwest Airlines"),
        ("AS", "Alaska Airlines"),
        ("B6", "JetBlue Airways"),
        ("F9", "Frontier Airlines"),
        ("NK", "Spirit Airlines"),
        ("HA", "Hawaiian Airlines"),
    ],
    "EU": [
        ("AF", "Air France"),
        ("LH", "Lufthansa"),
        ("BA", "British Airways"),
        ("KL", "KLM"),
        ("IB", "Iberia"),
        ("AZ", "ITA Airways"),
        ("TP", "TAP Air Portugal"),
        ("AY", "Finnair"),
        ("SK", "SAS"),
        ("OS", "Austrian Airlines"),
        ("LX", "Swiss"),
        ("SN", "Brussels Airlines"),
    ],
    "AS": [
        ("JL", "Japan Airlines"),
        ("NH", "ANA"),
        ("KE", "Korean Air"),
        ("OZ", "Asiana Airlines"),
        ("CX", "Cathay Pacific"),
        ("SQ", "Singapore Airlines"),
        ("TG", "Thai Airways"),
        ("MH", "Malaysia Airlines"),
        ("GA", "Garuda Indonesia"),
        ("PR", "Philippine Airlines"),
        ("CI", "China Airlines"),
        ("BR", "EVA Air"),
        ("CA", "Air China"),
        ("MU", "China Eastern"),
        ("CZ", "China Southern"),
        ("HU", "Hainan Airlines"),
        ("AI", "Air India"),
        ("EK", "Emirates"),
        ("QR", "Qatar Airways"),
        ("EY", "Etihad Airways"),
        ("SV", "Saudia"),
        ("LY", "El Al"),
    ],
    "OC": [
        ("QF", "Qantas"),
        ("VA", "Virgin Australia"),
        ("NZ", "Air New Zealand"),
        ("JQ", "Jetstar"),
    ],
    "SA": [
        ("LA", "LATAM Airlines"),
        ("G3", "GOL"),
        ("AR", "Aerolineas Argentinas"),
        ("AV", "Avianca"),
        ("AM", "Aeromexico"),
    ],
    "NA": [
        ("AC", "Air Canada"),
        ("WS", "WestJet"),
        ("TS", "Air Transat"),
    ],
    "AF": [
        ("SA", "South African Airways"),
        ("MS", "EgyptAir"),
        ("ET", "Ethiopian Airlines"),
        ("KQ", "Kenya Airways"),
        ("AT", "Royal Air Maroc"),
    ],
}

# 枢纽机场 (更容易有skiplagging机会)
HUBS = {
    "US": ["ATL", "DFW", "DEN", "ORD", "LAX", "CLT", "MCO", "LAS", "PHX", "MIA", "SEA", "IAH", "JFK", "EWR", "SFO", "BOS", "MSP", "DTW", "PHL", "LGA", "FLL", "BWI", "IAD", "MDW", "SLC"],
    "EU": ["LHR", "CDG", "AMS", "FRA", "MAD", "BCN", "FCO", "MUC", "ZUR", "VIE", "CPH", "ARN", "OSL", "HEL", "DUB", "BRU"],
    "AS": ["HKG", "NRT", "HND", "ICN", "SIN", "BKK", "KUL", "DXB", "DOH", "AUH", "PEK", "PVG", "CAN"],
}

def get_airline_for_route(origin_region, dest_region):
    """根据航线区域选择合适的航空公司"""
    if origin_region == dest_region:
        return random.choice(AIRLINES.get(origin_region, AIRLINES["US"]))
    else:
        # 国际航线，混合选择
        all_airlines = []
        for region, airlines in AIRLINES.items():
            all_airlines.extend(airlines)
        return random.choice(all_airlines)

def generate_flight_number(airline_code):
    """生成航班号"""
    return f"{airline_code}{random.randint(1, 9999)}"

def generate_time():
    """生成随机时间"""
    hour = random.randint(5, 23)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"

def add_hours(time_str, hours):
    """时间加法"""
    h, m = map(int, time_str.split(':'))
    new_h = (h + hours) % 24
    return f"{new_h:02d}:{m:02d}"

def calculate_distance(origin, dest):
    """
    简化版距离计算
    实际应该使用经纬度计算，这里用随机值模拟
    """
    return random.randint(200, 3000)

def generate_direct_price(origin, dest, distance=None):
    """
    生成直飞价格
    基于距离和市场需求
    """
    if distance is None:
        distance = calculate_distance(origin, dest)
    
    # 基础价格：每英里 0.1-0.3 美元
    base_price = distance * random.uniform(0.08, 0.25)
    
    # 添加随机波动
    price = base_price * random.uniform(0.8, 1.5)
    
    # 确保最低价格
    price = max(price, 79)
    
    return round(price, 2)

def generate_skiplagging_opportunities(origin_code, dest_code, origin_region, dest_region):
    """
    生成 skiplagging 机会
    逻辑：找从 origin 出发经停 dest 飞往更远目的地的航班
    """
    opportunities = []
    
    # 获取同区域的其他机场作为潜在终点
    if origin_region in HUBS:
        potential_hubs = [h for h in HUBS[origin_region] if h != dest_code]
    else:
        potential_hubs = HUBS.get("US", [])[:15]  # 默认用美国枢纽
    
    # 随机选择 2-5 个可能的终点
    selected_hubs = random.sample(potential_hubs, min(random.randint(2, 5), len(potential_hubs)))
    
    for hub in selected_hubs:
        # 决定这个路线是否有 skiplagging 机会 (70% 概率)
        if random.random() < 0.7:
            # 生成直飞价格
            direct_dist = calculate_distance(origin_code, dest_code)
            direct_price = generate_direct_price(origin_code, dest_code, direct_dist)
            
            # 生成转机价格 (通常更便宜)
            full_dist = direct_dist + calculate_distance(dest_code, hub)
            
            # skiplagging 价格通常是直飞的 40-80%
            skiplag_ratio = random.uniform(0.4, 0.85)
            skiplag_price = round(direct_price * skiplag_ratio, 2)
            
            # 确保节省金额合理
            savings = direct_price - skiplag_price
            if savings > 20:  # 至少节省 $20 才算有价值
                airline_code, airline_name = get_airline_for_route(origin_region, origin_region)
                
                dep_time = generate_time()
                # 转机航班通常更长
                flight_hours = random.randint(3, 8)
                arr_time = add_hours(dep_time, flight_hours)
                
                opportunities.append({
                    "origin": origin_code,
                    "destination": hub,  # 票面终点
                    "price": skiplag_price,
                    "airline": airline_name,
                    "flight_number": generate_flight_number(airline_code),
                    "departure": dep_time,
                    "arrival": arr_time,
                    "stops": 1,
                    "via": dest_code,  # 实际下机点
                    "direct_price": direct_price,
                    "savings": round(savings, 2),
                    "savings_percent": round((savings / direct_price) * 100, 1),
                })
    
    return opportunities

def generate_route_data(origin_code, dest_code):
    """
    生成一条航线的完整数据（直飞 + skiplagging 选项）
    """
    # 查找机场信息
    origin_info = next((a for a in AIRPORTS if a[0] == origin_code), None)
    dest_info = next((a for a in AIRPORTS if a[0] == dest_code), None)
    
    if not origin_info or not dest_info:
        return None
    
    origin_region = origin_info[3]
    dest_region = dest_info[3]
    
    # 生成直飞航班
    distance = calculate_distance(origin_code, dest_code)
    direct_price = generate_direct_price(origin_code, dest_code, distance)
    airline_code, airline_name = get_airline_for_route(origin_region, dest_region)
    
    dep_time = generate_time()
    flight_hours = max(1, distance // 500)  # 粗略估算飞行时间
    arr_time = add_hours(dep_time, flight_hours)
    
    direct_flight = {
        "origin": origin_code,
        "destination": dest_code,
        "price": direct_price,
        "airline": airline_name,
        "flight_number": generate_flight_number(airline_code),
        "departure": dep_time,
        "arrival": arr_time,
        "stops": 0,
        "via": None,
    }
    
    # 生成 skiplagging 机会
    skiplag_options = generate_skiplagging_opportunities(
        origin_code, dest_code, origin_region, dest_region
    )
    
    # 只保留确实比直飞便宜的选项
    valid_skiplag = [s for s in skiplag_options if s["price"] < direct_price]
    
    return {
        "direct": direct_flight,
        "skiplagging": valid_skiplag,
    }

def generate_all_route_data(output_file="flight_database.json"):
    """
    生成所有航线的数据库
    """
    database = {}
    
    # 重点生成美国国内航线 (skiplagging 最常见的场景)
    us_airports = [a[0] for a in AIRPORTS if a[3] == "US"]
    
    print(f"生成美国国内航线数据 ({len(us_airports)} 个机场)...")
    count = 0
    for i, origin in enumerate(us_airports):
        for dest in us_airports[i+1:]:
            if origin != dest:
                key = f"{origin}_{dest}"
                data = generate_route_data(origin, dest)
                if data and data["skiplagging"]:
                    database[key] = data
                    count += 1
    
    print(f"生成了 {count} 条有 skiplagging 机会的航线")
    
    # 添加一些热门国际航线
    print("生成热门国际航线...")
    international_routes = [
        ("JFK", "LHR"), ("LAX", "NRT"), ("SFO", "HKG"),
        ("MIA", "GRU"), ("LAX", "SYD"), ("JFK", "CDG"),
        ("ORD", "FRA"), ("DFW", "NRT"), ("SEA", "ICN"),
    ]
    
    for origin, dest in international_routes:
        key = f"{origin}_{dest}"
        data = generate_route_data(origin, dest)
        if data:
            database[key] = data
    
    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"数据已保存到 {output_file}")
    return database

if __name__ == "__main__":
    # 生成数据
    db = generate_all_route_data()
    
    # 显示一些示例
    print("\n示例航线数据:")
    for key in list(db.keys())[:5]:
        data = db[key]
        direct = data["direct"]
        print(f"\n{key}: 直飞 ${direct['price']} ({direct['airline']})")
        for opt in data["skiplagging"][:2]:
            print(f"  → Skiplag: {opt['origin']}-{opt['via']}-{opt['destination']} "
                  f"${opt['price']} (省 ${opt['savings']:.0f})")
