import pandas as pd
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1) CSV 불러오기
df = pd.read_csv("steam_peak_players_output.csv")

# peak_players 100 이상만 대상
df_target = df[df["peak_players"] >= 100].copy()

print("API 조회 대상 게임 수:", len(df_target))

# 중복 appid 제거
unique_appids = df_target["appid"].dropna().unique()


# 2) 세션 + 재시도 설정
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retries))


# 3) appdetails에서 type 가져오는 함수
def fetch_type(appid):
    """
    각 스레드가 독립적으로 실행하는 함수
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"

    try:
        response = session.get(url, timeout=6)
        data = response.json()

        app_block = data.get(str(appid), {})
        if not app_block.get("success", False):
            return appid, None

        app_data = app_block.get("data", {})
        app_type = app_data.get("type", None)

    except Exception:
        return appid, None
    
    # 스레드별 0.25초 지연 (초당 약 4 요청)
    time.sleep(0.25)
    return appid, app_type


# 4) 멀티스레드 실행
THREAD_COUNT = 6  # 차단 없이 가장 안정적인 갯수

appid_to_type = {}

print(f"멀티스레드 실행 (스레드 {THREAD_COUNT}개)...")

with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    futures = {executor.submit(fetch_type, appid): appid for appid in unique_appids}

    for i, future in enumerate(as_completed(futures)):
        appid, app_type = future.result()
        appid_to_type[appid] = app_type

        if i % 100 == 0:
            print(f"{i}/{len(unique_appids)} 완료...")


# 5) type을 df에 추가
df_target["type"] = df_target["appid"].map(appid_to_type)

# 6) 정식 게임(type='game')만 남기기
games_df = df_target[df_target["type"] == "game"].copy()

# 7) 저장
games_df.to_csv("steam_games_only_peak100_multithread.csv", index=False)

print("--------------------------------------------------------")
print("완료! 멀티스레드 + 정식 게임 필터링 완료.")
print("최종 게임 개수:", len(games_df))
print("저장 파일: steam_games_only_peak100_multithread.csv")
