import time
import re
import requests
import pandas as pd

# ============================================================
# 1) CSV 로드 및 상위 200개 선택
# ============================================================

# CSV 파일 경로 (네 환경에 맞게 수정)
TOP_PATH = "final_top_20_per_genre_fixed.csv"
BOTTOM_PATH = "final_bottom_20_per_genre_fixed.csv"

df_top = pd.read_csv(TOP_PATH)
df_bottom = pd.read_csv(BOTTOM_PATH)

# 여기서는 "위에서부터 200개"를 사용
# 원하면 특정 장르/조건으로 필터해서 200개를 만드는 방식으로 바꿔도 됨
df_top_200 = df_top.head(200).copy()
df_bottom_200 = df_bottom.head(200).copy()

df_top_200["list_type"] = "top"      # 어디에서 온 데이터인지 표시
df_bottom_200["list_type"] = "bottom"

df_all = pd.concat([df_top_200, df_bottom_200], ignore_index=True)

print("Top 200 개:", len(df_top_200))
print("Bottom 200 개:", len(df_bottom_200))
print("총 조사 대상:", len(df_all))  # 400 예상


# ============================================================
# 2) 이름 정규화 / 시리즈 매핑 유틸 함수
# ============================================================

def normalize_name(name: str) -> str:
    """
    서브레딧 검색에 사용할 문자열을 정규화합니다.
    - 소문자로 변환
    - 알파벳/숫자/공백 이외의 문자는 공백으로 치환
    - 연속된 공백을 하나로 합침
    """
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# 시리즈/프랜차이즈 단위로 운영되는 대표 서브레딧 매핑
# 필요할 때 직접 계속 추가하면 정확도가 올라갑니다.
SERIES_MAP = {
    "Europa Universalis IV": "r/eu4",
    "Europa Universalis 4": "r/eu4",
    "Crusader Kings III": "r/CrusaderKings",
    "Crusader Kings II": "r/CrusaderKings",
    "Sid Meier's Civilization VI": "r/civ",
    "Sid Meier's Civilization V": "r/civ",
    "Sid Meier's Civilization VII": "r/civ",
    "Stellaris": "r/Stellaris",
    "Manor Lords": "r/ManorLords",
    # 여기 아래로 계속 추가 가능
}


# ============================================================
# 3) Reddit 서브레딧 검색 함수
# ============================================================

BASE_URL = "https://www.reddit.com/subreddits/search.json"

# User-Agent는 본인 Reddit 계정 아이디 등으로 바꾸는 것을 추천
HEADERS = {
    "User-Agent": "GameSubredditScanner/0.1 by YOUR_REDDIT_ID"
}


def search_representative_subreddit(game_name: str, sleep_sec: float = 1.0):
    """
    주어진 게임 이름에 대해 '대표 서브레딧'을 찾습니다.

    우선순위:
    1) SERIES_MAP에 매핑이 등록되어 있으면 그걸 바로 사용
    2) 그렇지 않으면 Reddit 서브레딧 검색 API를 사용하여 후보를 찾고,
       게임 이름과의 매칭 정도를 간단한 점수로 계산해
       가장 점수가 높은 서브레딧을 대표 서브레딧 후보로 선택

    반환:
    - (has_subreddit: bool, subreddit_name: str or None)
    """
    # 1) 시리즈 매핑 우선 적용
    if game_name in SERIES_MAP:
        return True, SERIES_MAP[game_name]

    norm = normalize_name(game_name)

    params = {
        "q": game_name,
        "limit": 10,   # 상위 10개의 서브레딧만 사용
    }

    try:
        resp = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=10
        )
    except Exception as e:
        print(f"[ERROR] 요청 실패: {game_name} -> {e}")
        time.sleep(sleep_sec)
        return False, None

    if resp.status_code != 200:
        print(f"[WARN] HTTP {resp.status_code} for: {game_name}")
        time.sleep(sleep_sec)
        return False, None

    children = resp.json().get("data", {}).get("children", [])
    candidates = []

    for child in children:
        sub = child.get("data", {})
        display_name = sub.get("display_name", "")  # 예: "CivVI"
        title = sub.get("title", "")                # 예: "Sid Meier's Civilization"
        public_desc = sub.get("public_description", "")

        # 서브레딧 이름/제목/설명을 합쳐서 텍스트 하나로 만든다.
        text_blob = " ".join([display_name, title, public_desc]).lower()

        tokens = norm.split()
        match_score = 0

        # 아주 단순한 매칭 점수 계산 (필요하면 고도화 가능)
        if tokens:
            # 첫 단어가 들어가면 +1
            if tokens[0] in text_blob:
                match_score += 1
        if len(tokens) >= 2:
            # 첫 두 단어가 같이 들어가면 +1
            key2 = " ".join(tokens[:2])
            if key2 in text_blob:
                match_score += 1
        # 전체 정규화 문자열이 통째로 들어가면 +2
        if norm and norm in text_blob:
            match_score += 2

        # 점수가 1 이상이면 "게임 관련일 가능성이 있다"고 보고 후보에 추가
        if match_score > 0:
            candidates.append((match_score, display_name))

    # Reddit API에 부담을 줄이기 위해 요청 사이에 딜레이
    time.sleep(sleep_sec)

    if not candidates:
        # 게임 전용 서브레딧을 못 찾았다고 판단
        return False, None

    # 점수가 높은 순으로 정렬해서 가장 높은 후보를 선택
    candidates.sort(reverse=True, key=lambda x: x[0])
    best = candidates[0][1]  # display_name
    return True, f"r/{best}"


# ============================================================
# 4) 전체 400개 루프 돌리면서 결과 수집
# ============================================================

results = []

for idx, row in df_all.iterrows():
    game_name = row["name"]
    list_type = row["list_type"]          # top / bottom
    genre = row.get("Selected_Genre", "") # 있으면 같이 저장

    print(f"[{idx+1}/{len(df_all)}] 검색 중: {game_name} ({list_type}) ...")

    has_sub, sub_name = search_representative_subreddit(
        game_name,
        sleep_sec=1.0   # Reddit에 과도한 요청 방지용
    )

    results.append({
        "name": game_name,
        "list_type": list_type,
        "Selected_Genre": genre,
        "has_representative_subreddit": has_sub,
        "subreddit": sub_name,
    })

result_df = pd.DataFrame(results)


# ============================================================
# 5) Top / Bottom 별 서브레딧 보유 비율 계산
# ============================================================

summary = (
    result_df.groupby("list_type")["has_representative_subreddit"]
    .mean()
    .mul(100)
    .reset_index()
    .rename(columns={"has_representative_subreddit": "ratio_with_subreddit_percent"})
)

print("\n[Top / Bottom 대표 서브레딧 보유 비율 요약]")
print(summary)


# ============================================================
# 6) CSV로 저장
# ============================================================

result_df.to_csv("top_bottom_200_subreddits_result.csv", index=False)
summary.to_csv("top_bottom_200_subreddits_summary.csv", index=False)

print("\n세부 결과: top_bottom_200_subreddits_result.csv")
print("요약 결과: top_bottom_200_subreddits_summary.csv")
