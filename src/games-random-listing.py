import pandas as pd
import random

def sample_games_by_genre(file_path):
    try:
        df = pd.read_csv(file_path)
    except:
        print("파일을 찾을 수 없습니다.")
        return None

    # 데이터 전처리
    df.columns = df.columns.str.strip()
    
    # peak_players가 100 이상인 게임만 필터링
    df['peak_players'] = pd.to_numeric(df['peak_players'], errors='coerce').fillna(0)
    qualified_games = df[df['peak_players'] >= 100].copy()

    # 장르 전처리
    qualified_games = qualified_games.dropna(subset=['genres'])
    
    # 여러 장르 분리
    # 게임 ID와 장르 리스트를 매핑
    genre_map = []
    for _, row in qualified_games.iterrows():
        g_list = [g.strip() for g in str(row['genres']).split(',')]
        for genre in g_list:
            genre_map.append({
                'genre': genre,
                'appid': row['appid'],
                'row_index': row.name  # 원본 데이터프레임의 인덱스
            })
    
    genre_df = pd.DataFrame(genre_map)

    # 장르별 수집 (중복 제외)
    final_results = []
    collected_game_ids = set() # 이미 수집된 게임 ID를 set에 저장

    # 존재하는 모든 장르 리스트 확보
    unique_genres = genre_df['genre'].unique()
    
    print(f"--- 총 {len(unique_genres)}개의 장르에 대해 수집을 시작합니다 ---")

    for genre in unique_genres:
        # 해당 장르이면서 아직 수집되지 않은 게임들 찾기
        candidates = genre_df[
            (genre_df['genre'] == genre) & 
            (~genre_df['appid'].isin(collected_game_ids))
        ]
        
        # 해당 장르의 후보군에서 중복된 게임ID 제거
        candidates = candidates.drop_duplicates(subset=['appid'])
        
        # 랜덤으로 100개 (혹은 그 이하) 추출
        sample_count = min(len(candidates), 100)
        
        if sample_count > 0:
            # 랜덤 샘플링
            selected = candidates.sample(n=sample_count) # random_state를 지정하지 않을 시 랜덤
            
            # 결과 저장 및 수집된 ID 등록
            for _, item in selected.iterrows():
                # 원본 데이터에서 해당 행의 모든 정보 가져오기
                original_row = df.loc[item['row_index']]
                
                # 원본 정보를 딕셔너리로 변환
                game_info = original_row.to_dict()
                
                # 어떤 장르 기준으로 뽑혔는지
                game_info['Selected_Genre'] = genre
                
                final_results.append(game_info)
                
                # 수집된 게임 set에 추가 
                collected_game_ids.add(item['appid'])
            
            print(f"[{genre}] 장르에서 {sample_count}개 수집 완료")
        else:
            print(f"[{genre}] 장르: 수집 가능한 새로운 게임이 없습니다 (조건 미달 혹은 이미 타 장르 선점)")

    # 결과 저장
    result_df = pd.DataFrame(final_results)
    
    # 컬럼 순서 정리: 'Selected_Genre'를 맨 앞으로 보내고 나머지는 그대로 유지
    if not result_df.empty:
        cols = ['Selected_Genre'] + [c for c in result_df.columns if c != 'Selected_Genre']
        result_df = result_df[cols]
        
        # 정렬 (장르별 -> 동접자순)
        result_df = result_df.sort_values(by=['Selected_Genre', 'peak_players'], ascending=[True, False])
    
    output_filename = '장르별_랜덤_게임목록.csv'
    result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n총 {len(result_df)}개의 게임이 선택되었습니다.")
    print(f"결과 파일 저장 완료: {output_filename}")
    
    return result_df

file_path = '게임목록+최고동시접속자.csv'
df_result = sample_games_by_genre(file_path)