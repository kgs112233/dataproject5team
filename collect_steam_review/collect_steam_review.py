import requests
import pandas as pd
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def write_log(message, log_file="progress_log.txt"):
    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        f.write(f"{timestamp} {message}\n")

def safe_get(url, params, max_retry=5):
    for attempt in range(1, max_retry + 1):
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            return res
        except requests.exceptions.HTTPError as e:
            if res.status_code == 429:
                delay = 5 + attempt * 2
                write_log(f"Rate limit (429) encountered. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            elif res.status_code in (404, 403):
                return {"error": f"HTTP Error {res.status_code} (Not Found or Forbidden)", "status_code": res.status_code}
            elif attempt == max_retry:
                return {"error": f"HTTP Error {res.status_code} after {max_retry} tries: {e}", "status_code": res.status_code}
            
            time.sleep(1 + attempt * 0.5)
        except Exception as e:
            if attempt == max_retry:
                return {"error": f"Connection error after {max_retry} tries: {e}", "status_code": 0}
            
            time.sleep(1 + attempt * 0.5)
    return {"error": "Unknown critical error", "status_code": 0}

def fetch_top_50_reviews(appid):
    write_log(f"Start fetching → AppID {appid}")

    url = f"https://store.steampowered.com/appreviews/{appid}"
    params = {
        "json": 1,
        "language": "english", 
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": 100,
        "day_range": 9223372036854775807,
        "cursor": "*",
        "filter": "all",
        "sort": "helpful"
    }

    collected = []
    total_reviews_available = None

    while len(collected) < 50:
        current_cursor = params.get("cursor", "*")
        response = safe_get(url, params)

        if isinstance(response, dict) and "error" in response:
            write_log(f"[ERROR] AppID {appid} req fail: {response['error']} (Status: {response.get('status_code', 'N/A')})")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            write_log(f"[ERROR] AppID {appid} JSON decode fail: {e} (Status: {response.status_code})")
            return []

        if total_reviews_available is None and "query_summary" in data:
            total_reviews_available = data["query_summary"].get("total_reviews", "N/A")
            write_log(f"AppID {appid} total ENGLISH reviews available: {total_reviews_available}")
            
            if total_reviews_available == 0:
                write_log(f"[INFO] AppID {appid}: 0 English reviews available, stopping early.")
                break


        if "reviews" not in data or not data["reviews"]:
            if "reviews" not in data:
                 write_log(f"[WARN] AppID {appid}: 'reviews' field missing in response. Status code: {response.status_code}. Total English reviews: {total_reviews_available}")
            break

        reviews_in_page = 0
        for r in data["reviews"]:
            if len(collected) < 50: 
                collected.append({
                    "appid": appid,
                    "review_id": r.get("recommendationid"),
                    "author": r.get("author", {}).get("steamid"),
                    "review": r.get("review"),
                    "rating": "positive" if r.get("voted_up") else "negative",
                    "votes_helpful": r.get("votes_helpful"),
                    "votes_funny": r.get("votes_funny"),
                    "weighted_vote_score": r.get("weighted_vote_score"),
                    "written_date": r.get("timestamp_created"),
                    "reaction_counts": json.dumps(r.get("reactions", {}), ensure_ascii=False)
                })
                reviews_in_page += 1
            else:
                break
        
        if len(collected) >= 50:
            break

        cursor = data.get("cursor")
        if not cursor or cursor == current_cursor: 
            break
        
        if reviews_in_page == 0:
            break

        params["cursor"] = cursor
        time.sleep(0.5)

    return collected

def load_appids_from_csv(files):
    appids = set()
    for file in files:
        df = pd.read_csv(file)
        if "appid" in df.columns:
            appids.update(df["appid"].astype(int).tolist())
    return list(appids)

def collect_reviews_from_csv(csv_files, output_file="collected_reviews.csv"):
    appids = load_appids_from_csv(csv_files)
    total = len(appids)

    print(f"총 {total}개의 AppID로 리뷰 수집 시작")

    all_reviews = []
    completed = 0

    max_workers = 5

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_appid = {executor.submit(fetch_top_50_reviews, appid): appid for appid in appids}

        for future in as_completed(future_to_appid):
            appid = future_to_appid[future]
            completed += 1

            try:
                reviews = future.result()

                all_reviews.extend(reviews)

                msg = f"[{completed}/{total}] AppID {appid} 리뷰 {len(reviews)}개 수집 완료."
                print(msg)
                write_log(msg)

            except Exception as e:
                msg = f"[{completed}/{total}] AppID {appid} 처리 중 에러: {e}"
                print(msg)
                write_log(msg)

    df = pd.DataFrame(all_reviews)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    write_log("===== 수집 완료 =====")
    print(f"\n완료, 결과 {output_file}")

    return df

base = r"C:\Users\minjh\OneDrive\문서\데분프 과제\팀플\dataproject5team\test_score"

csv_files = [
    os.path.join(base, "final_top_20_per_genre_fixed.csv"),
    os.path.join(base, "final_bottom_20_per_genre_fixed.csv")
]

collect_reviews_from_csv(csv_files, "steam_reviews_top50_each_game.csv")