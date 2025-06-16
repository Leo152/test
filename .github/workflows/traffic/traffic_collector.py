import os
import sys
import requests
import csv
from datetime import datetime

# 添加路径验证
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(SCRIPT_DIR, 'traffic_data.csv')

print(f"脚本目录: {SCRIPT_DIR}")
print(f"CSV 文件路径: {CSV_FILE}")

# 确保文件存在
if not os.path.exists(CSV_FILE):
    print(f"创建新的 CSV 文件: {CSV_FILE}")
    with open(CSV_FILE, 'w') as f:
        pass  # 创建空文件

# 配置信息
TOKEN = os.environ['GH_TOKEN']
OWNER = os.environ['REPO_OWNER']
REPO = os.environ['REPO_NAME']

def get_traffic_data():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    print(f"获取仓库流量数据: {OWNER}/{REPO}")
    
    # API 端点
    views_url = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic/views"
    clones_url = f"https://api.github.com/repos/{OWNER}/{REPO}/traffic/clones"
    
    try:
        # 发送请求
        views_res = requests.get(views_url, headers=headers)
        clones_res = requests.get(clones_url, headers=headers)
        
        # 检查响应状态
        views_res.raise_for_status()
        clones_res.raise_for_status()
        
        views_data = views_res.json().get('views', [])
        clones_data = clones_res.json().get('clones', [])
        
        print(f"获取到 {len(views_data)} 天访问数据, {len(clones_data)} 天克隆数据")
        
        # 合并数据
        combined = {}
        for view in views_data:
            date = view['timestamp'][:10]
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
    
    except requests.exceptions.RequestException as e:
        print(f"API 请求错误: {e}")
        print(f"访问量 API 响应: {views_res.status_code} {views_res.text}")
        print(f"克隆量 API 响应: {clones_res.status_code} {clones_res.text}")
        return {}
    except Exception as e:
        print(f"处理数据时出错: {e}")
        return {}

def save_to_csv(data):
    print(f"保存数据到 CSV: {CSV_FILE}")
    
    # 收集已有日期
    existing_dates = set()
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                existing_dates = {row['date'] for row in reader}
    
    # 追加新数据
    with open(CSV_FILE, 'a', newline='') as f:
        fieldnames = ['date', 'views', 'unique_visitors', 'clones', 'unique_cloners']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # 如果是新文件或空文件，写入表头
        if not existing_dates:
            writer.writeheader()
        
        # 按日期排序（从旧到新）
        sorted_dates = sorted(data.keys())
        new_entries = 0
        
        for date in sorted_dates:
            if date not in existing_dates:
                row = {'date': date}
                row.update(data[date])
                writer.writerow(row)
                print(f"添加新数据: {date}")
                new_entries += 1
        
        print(f"总共添加 {new_entries} 条新记录")

if __name__ == "__main__":
    print("=== 开始收集 GitHub 流量数据 ===")
    traffic_data = get_traffic_data()
    
    if traffic_data:
        save_to_csv(traffic_data)
        print("=== 数据收集完成 ===")
    else:
        print("!!! 未获取到数据，请检查错误信息 !!!")
        sys.exit(1)  # 失败退出
