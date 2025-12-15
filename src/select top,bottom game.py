import pandas as pd

# 데이터 가져오기
df = pd.read_csv('final data with score.csv')

# 2. 장르별 상위 20개 / 하위 20개 리스트
final_top_list = []
final_bottom_list = []

genres = df['Selected_Genre'].unique()

# 장르별로 가져오기
for genre in genres: 
    g_df = df[df['Selected_Genre'] == genre].sort_values('total_score', ascending=False) # 장르마다 데이터 추출 및 점수 내림차순 정렬
    
    top20 = g_df.head(20) # 상위 20개 (점수 높은 순)
    final_top_list.append(top20)
    
    bottom20 = g_df.tail(20) # 하위 20개 (점수 낮은 순)
    final_bottom_list.append(bottom20)

# 리스트 합치기
df_top_final = pd.concat(final_top_list)
df_bottom_final = pd.concat(final_bottom_list)

# 파일 저장
df_top_final.to_csv('final_top_20_per_genre_fixed.csv', index=False)
df_bottom_final.to_csv('final_bottom_20_per_genre_fixed.csv', index=False)

print(f"Top 20 파일 생성 완료: {len(df_top_final)}개")
print(f"Bottom 20 파일 생성 완료: {len(df_bottom_final)}개")