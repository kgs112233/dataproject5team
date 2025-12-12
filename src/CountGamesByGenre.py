import pandas as pd

file_path = 'only_games.csv'
df = pd.read_csv(file_path)

# dropna(): 정보가 없는 행 제거
# str.split(','): , 기준 분리
# explode(): 별도의 행으로 분리
# str.strip(): 공백 제거
# value_counts(): 개수 세기
genre_counts = df['genres'].dropna().str.split(',').explode().str.strip().value_counts()

# 변환 
result_df = genre_counts.reset_index()
result_df.columns = ['Genre', 'Count']

# CSV 파일로 저장
result_df.to_csv('CountGamesByGenre.csv', index=False)
