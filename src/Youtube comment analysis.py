import pandas as pd
import re

# 데이터 불러오기 및 전처리
df_comments = pd.read_csv('steam_960_games_comments_with_appid_and_genre.csv')
df_top = pd.read_csv('final_top_20_per_genre_fixed.csv')
df_bottom = pd.read_csv('final_bottom_20_per_genre_fixed.csv')

# appid 문자열 변환
df_comments['appid'] = df_comments['appid'].astype(str)
df_top['appid'] = df_top['appid'].astype(str)
df_bottom['appid'] = df_bottom['appid'].astype(str)

# 그룹 매핑 (Top/Bottom)
top_ids = set(df_top['appid'])
bottom_ids = set(df_bottom['appid'])

df_comments['Group'] = df_comments['appid'].apply(
    lambda x: 'Top' if x in top_ids else ('Bottom' if x in bottom_ids else 'Other')
)

# 분석 대상 필터링
df_target = df_comments[df_comments['Group'].isin(['Top', 'Bottom'])].copy()


# 분석 키워드 정리

# (1) 명작 찬양 키워드 (Masterpiece)
masterpiece_keywords = [
    r"masterpiece", r"underrated", r"gem", r"beautiful", r"art", 
    r"legend", r"classic", r"perfect", r"goat"
]

# (2) 부정적 평가 키워드 (Negative)
negative_keywords = [
    r"\bbad\b", r"\bworst\b", r"\bhate\b", r"\bboring\b", r"\bterrible\b", 
    r"\bsucks?\b", r"\bawful\b", r"\btrash\b", r"\bgarbage\b", r"\bdisappoint\b"
]


# 분석 함수
def analyze_specific_keywords(group_name):
    comments = df_target[df_target['Group'] == group_name]['Comment'].astype(str).tolist()
    total = len(comments)
    
    # 명작 찬양 분석
    masterpiece_count = 0
    for c in comments:
        c_lower = c.lower()
        if any(w in c_lower for w in masterpiece_keywords): # 단순 포함 여부 (substring)
            masterpiece_count += 1
            
    # 부정 평가 분석
    negative_count = 0
    for c in comments:
        for pattern in negative_keywords:
            if re.search(pattern, c, re.IGNORECASE): # 정규식 매칭 (단어 경계)
                negative_count += 1
                break
    
    return total, masterpiece_count, negative_count


# 실행 및 결과 출력
top_total, top_master, top_neg = analyze_specific_keywords('Top')
bot_total, bot_master, bot_neg = analyze_specific_keywords('Bottom')

print("유튜브 댓글 핵심 지표 분석 결과")
print(f"총 댓글 수 - Top: {top_total}, Bottom: {bot_total}\n")

# 명작 찬양 비율 비교
top_master_rate = (top_master / top_total) * 100
bot_master_rate = (bot_master / bot_total) * 100

print("명작 찬양")
print(f"Top Games: {top_master_rate:.2f}% ({top_master}개)")
print(f"Bottom Games: {bot_master_rate:.2f}% ({bot_master}개)")

print("\n")

# 부정 평가 비율 비교
top_neg_rate = (top_neg / top_total) * 100
bot_neg_rate = (bot_neg / bot_total) * 100

print("부정적 평가")
print(f"Top Games: {top_neg_rate:.2f}% ({top_neg}개)")
print(f"Bottom Games: {bot_neg_rate:.2f}% ({bot_neg}개)")