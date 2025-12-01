import pandas as pd
import numpy as np
import re

# 데이터 가져오기
df = pd.read_csv('steam_games_final_simplified.csv') # steam_games_final_simplified.csv: 전처리가 끝난 데이터 파일

# 2. 금액($) 문자열 -> 숫자 변환
def clean_money(val):
    val = str(val)
    val = re.sub(r'\s*\(.*\)', '', val) # 괄호 제거
    val = val.replace('$', '').replace(',', '')
    
    multiplier = 1
    if 'k' in val.lower(): #단위 따라서 곱셈
        multiplier = 1000
        val = val.lower().replace('k', '')
    elif 'm' in val.lower():
        multiplier = 1000000
        val = val.lower().replace('m', '')
    elif 'b' in val.lower():
        multiplier = 1000000000
        val = val.lower().replace('b', '')
        
    try:
        return float(val) * multiplier
    except:
        return 0

df['clean_game_revenue'] = df['game_revenue'].apply(clean_money)
df['clean_publisher_revenue'] = df['publisher_revenue'].apply(clean_money)


# 무료 게임 여부 확인
df['is_free'] = df['clean_game_revenue'] == 0

# 로그 변환
df['log_game_rev'] = np.log1p(df['clean_game_revenue'])
df['log_pub_rev'] = np.log1p(df['clean_publisher_revenue'])
df['log_peak_players'] = np.log1p(df['peak_players'])
df['log_owners_midpoint'] = np.log1p(df['owners_midpoint'])

# Min-Max 정규화 (0~1 사이 값으로 변환)
def min_max(series):
    return (series - series.min()) / (series.max() - series.min())

df['norm_rev'] = min_max(df['log_game_rev'])
df['norm_pub'] = min_max(df['log_pub_rev'])
df['norm_peak_players'] = min_max(df['log_peak_players'])
df['norm_owners_midpoint'] = min_max(df['log_owners_midpoint'])
df['norm_adjusted_rating'] = min_max(df['adjusted_rating'])


# 가중치 적용 및 최종 점수 계산
score_paid = ( # 유료 게임 공식: 수익(30) + 동접(30) + 다운(20) + 평점(10) + 배급사(10)
    df['norm_rev'] * 0.30 + 
    df['norm_peak_players'] * 0.30 +
    df['norm_owners_midpoint'] * 0.20 +
    df['adjusted_rating'] * 0.10 +
    df['norm_pub'] * 0.10
)
score_free = ( # 무료 게임 공식: 수익(0) + 동접(45) + 다운(35) + 평점(10) + 배급사(10)
    df['norm_rev'] * 0.00 +
    df['norm_peak_players'] * 0.45 +
    df['norm_owners_midpoint'] * 0.35 +
    df['adjusted_rating'] * 0.10 +
    df['norm_pub'] * 0.10
)

# 조건에 따라 점수 합치기
df['total_score'] = np.where(df['is_free'], score_free, score_paid)


# 5. 결과 저장: 원래 있던 컬럼들에 'total_score'만 추가해서 저장
original_cols = ['appid', 'name', 'publisher_main', 'Selected_Genre', 'game_revenue', 'publisher_revenue', 'peak_players', 'adjusted_rating', 'owners_midpoint']
final_cols = original_cols + ['total_score']

df_final = df[final_cols]

output_filename = 'steam_games_with_score.csv'
df_final.to_csv(output_filename, index=False)

print(f"점수가 포함된 파일 저장: {output_filename}")