import pandas as pd

# 데이터 가져오기
df_target = pd.read_csv('output_after.csv') # output_after.csv: 장르별로 선정된 2,400개 게임 리스트
df_source = pd.read_csv('steam_peak_players_output.csv') # steam_peak_players_output.csv: 게임별 최대 동시 접속자 수 데이터


df_source_subset = df_source[['appid', 'peak_players']].copy() # 동접자 데이터에서 필요한 정보('appid', 'peak_players')만 추출

df_target['appid'] = df_target['appid'].astype(str)  # 'appid'를 기준으로 합쳐야 하므로, 두 파일의 appid 타입을 문자열(str)로 통일
df_source_subset['appid'] = df_source_subset['appid'].astype(str)


# 데이터 합치기
df_merged = pd.merge(df_target, df_source_subset, on='appid', how='left') #'appid'를 기준으로 병합, 원래 파일 형식 유지를 위해 df_target 기준으로 Left Join 사용


# 결과 저장
output_filename = 'steam_games_with_peak_players.csv'
df_merged.to_csv(output_filename, index=False)

print(f"파일이 저장되었습니다: {output_filename}")
print(f"최종 데이터 크기: {len(df_merged)}개")