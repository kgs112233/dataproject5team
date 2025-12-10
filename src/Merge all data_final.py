import pandas as pd
import numpy as np

# 데이터 가져오기
df = pd.read_csv('steam_games_final_data.csv') # steam_games_final_data.csv: 병합 후 스팀 평점, 리뷰 수, 다운로드 수 등이 포함된 데이터 but 정제 안됨.

# 평점 보정 (리뷰 수 500개 이하 페널티)
def apply_penalty(row):
    if row['Total_Reviews_Count'] <= 500: # 리뷰 수가 500개 이하라면 평점을 10% 깎음 
        return row['Steam_User_Score_Percent'] * 0.9
    else:
        return row['Steam_User_Score_Percent']

df['adjusted_rating'] = df.apply(apply_penalty, axis=1)

# Owners(소유자 수) 범위 -> 중간값 변환
def clean_owners(val):
    
    val_str = str(val).replace(',', '').strip()
    
    if '-' in val_str:
        parts = val_str.split('-')
    else:
        try: return float(val_str)
        except: return 0
            
    if len(parts) == 2:
        try:
            lower = float(parts[0].strip())
            upper = float(parts[1].strip())
            return (lower + upper) / 2
        except:
            return 0
    return 0

df['owners_midpoint'] = df['Owners_SteamSpy'].apply(clean_owners)


# 불필요한 컬럼 삭제 및 저장
cols_to_drop = [
    'Steam_User_Score_Percent', 
    'Total_Reviews_Count', 
    'Owners_SteamSpy', 
    'Total_Reviews_Count', 
    'Steam_User_Score_Percent'
]
df_simplified = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

# 결과 저장
output_filename = 'steam_games_final_simplified.csv'
df_simplified.to_csv(output_filename, index=False)

print("전처리 및 단순화된 파일 저장: {output_filename}")