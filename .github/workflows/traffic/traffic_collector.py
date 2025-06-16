import requests
import csv
import os
from datetime import datetime

# 配置信息
TOKEN = os.environ['GH_TOKEN']
OWNER = os.environ['REPO_OWNER']
REPO = os.environ['REPO_NAME']
CSV_FILE = os.path.join(os.path.dirname(__file__), 'traffic_data.csv')

def get_traffic_data():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 获取流量数据
    views_url = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic/views"
    clones_url = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic/clones"
    
    # 发送请求
    views_res = requests.get(views_url, headers=headers)
    clones_res = requests.get(clones_url, headers=headers)
    
    # 检查响应
    views_res.raise_for_status()
    clones_res.raise_for_status()
    
    views_data = views_res.json().get('views', [])
    clones_data = clones_res.json().get('clones', [])
    
    # 合并数据
    combined = {}
    for view in views_data:
        date = view['timestamp'][:10]  # 保留日期部分
        combined.setdefault(date, {}).update({
            'views': view['count'],
            'unique_visitors': view['uniques']
        })
    
    for clone in clones_data:
        date = clone['timestamp'][:10]
        combined.setdefault(date, {}).update({
            'clones': clone['count'],
            'unique_cloners': clone['uniques']
        })
    
    return combined

def save_to_csv(data):
    # 文件存在时读取已有日期
    existing_dates = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_dates.add(row['date'])
    
    # 追加新数据
    with open(CSV_FILE, 'a', newline='') as f:
        fieldnames = ['date', 'views', 'unique_visitors', 'clones', 'unique_cloners']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # 如果是新文件，写入表头
        if not existing_dates:
            writer.writeheader()
        
        # 按日期排序（从旧到新）
        sorted_dates = sorted(data.keys())
        for date in sorted_dates:
            if date not in existing_dates:
                row = {'date': date}
                row.update(data[date])
                writer.writerow(row)
                print(f"Added data for {date}")

if __name__ == "__main__":
    print(f"Starting traffic collection for {OWNER}/{REPO}")
    traffic_data = get_traffic_data()
    print(f"Retrieved {len(traffic_data)} days of data")
    save_to_csv(traffic_data)
    print(f"Data saved to {CSV_FILE}")
