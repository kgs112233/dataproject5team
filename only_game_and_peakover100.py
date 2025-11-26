import pandas as pd
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. CSV 불러오기
df = pd.read_csv("steam_peak_players_output.csv")

# peak_players가 100 이상인 게임만 남기기
df_target = df[df["peak_players"] >= 100].copy()

print("동시 접속자 100 이상 대상:", len(df_target))

# 대상 appid만 API 조회 (중복 제거)
unique_appids = df_target["appid"].dropna().unique()


# 2. 세션 + 자동 재시도 설정 (API 안정화)
session = requests.Session()

retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

session.mount("https://", HTTPAdapter(max_retries=retries))


# 3. 단일 게임의 type 조회 함수
def get_app_type(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    
    try:
        response = session.get(url, timeout=6)
        data = response.json()

        app_data = data.get(str(appid), {})
        
        if not app_data.get("success", False):
            return None
        
        app_info = app_data.get("data", {})
        return app_info.get("type", None)

    except Exception:
        return None


# 4. 모든 대상 appid에 대해 type 조회
appid_to_type = {}

for i, appid in enumerate(unique_appids):
    app_type = get_app_type(appid)
    appid_to_type[appid] = app_type

    if i % 50 == 0:
        print(f"{i}/{len(unique_appids)} 조회 중...")

    time.sleep(0.3)  # rate limit 방지


# 5. type 값을 원본 df_target에 추가
df_target["type"] = df_target["appid"].map(appid_to_type)

# 6. 정식 게임만 남기기 (type='game')
games_df = df_target[df_target["type"] == "game"].copy()

# 7. 결과 저장
games_df.to_csv("steam_games_only_peak100.csv", index=False)

print("---------------------------------------------------")
print("최종 게임 수:", len(games_df))
print("steam_games_only_peak100.csv 파일 생성됨.")
