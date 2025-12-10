import csv
import time
import requests
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

INPUT_CSV  = "test_input.csv"
OUTPUT_CSV = "steam_peak_players_output.csv"
LOG_FILE   = "time_log.txt"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def get_peak(appid):
    if not appid.isdigit():
        return None
    url = f"https://steamcharts.com/app/{appid}"
    try:
        time.sleep(random.uniform(0.18, 0.33))
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser', from_encoding='utf-8')
        for div in soup.find_all('div', class_='app-stat'):
            if 'all-time peak' in div.get_text().lower():
                sib = div.find_next_sibling()
                if sib:
                    n = sib.get_text(strip=True).replace(',', '')
                    if n.isdigit():
                        return int(n)
        nums = [int(s.get_text(strip=True).replace(',', '')) 
                for s in soup.find_all('span', class_='num') 
                if s.get_text(strip=True).replace(',', '').isdigit()]
        return max(nums) if nums else None
    except:
        return None

with open(INPUT_CSV, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
print(f"로그 시작 총 {total:,}개")

def process_row(item):
    i, row = item
    appid = row["appid"].strip()
    name = row.get("name", "Unknown")[:35]
    peak = get_peak(appid)
    row["peak_players"] = peak if peak else ""
    
    # 실시간 로그 저장
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{i:>5}/{total}] {name:<35} → {peak if peak else '없음'}\n")
    
    if i <= 20 or i % 2000 == 0:
        print(f"[{i:>5}/{total}] {name:<35} → {peak if peak else '없음'}")
    return row

# 병렬 3개 실행
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_row, enumerate(rows, 1)))

# 원본 순서 그대로 저장
keys = results[0].keys()
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(results)

print("완료")
