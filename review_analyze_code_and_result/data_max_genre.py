import pandas as pd
import os
import re

# 키워드 카테고리 정의 (최고 수치 계산에 필요한 Ratio 컬럼을 식별하기 위해 필요)
GENRE_FACTORS = {
    "Action": ["Combat", "Controls", "Difficulty",
               "TechIssues", "Balance", "Blame"],
    "Strategy": ["StrategicVariety", "AIQuality", "InfoClarity",
                 "TechIssues", "Balance", "Blame"],
    "Indie": ["Originality", "Polish/Bugs", "Value",
              "TechIssues", "Balance", "Blame"],
    "RPG": ["Worldbuilding", "Rewards", "Freedom/Choice",
            "TechIssues", "Balance", "Blame"],
    "Simulation": ["SystemDepth", "UI/Interface", "Realism",
                   "TechIssues", "Balance", "Blame"],
    "Adventure": ["Story", "Exploration", "Atmosphere",
                  "TechIssues", "Balance", "Blame"],
    "Casual": ["Addictiveness", "Variety/LevelDesign", "Playtime/Pacing",
               "TechIssues", "Balance", "Blame"],
    "Puzzle": ["Logic/Intuition", "DifficultyCurve", "Novelty",
               "TechIssues", "Balance", "Blame"]
}

def calculate_genre_maximums():
    # 파일 경로 설정 (이전 스크립트와 동일)
    base_dir = "C:\\Users\\minjh\\Downloads\\dataproject5team-feature-kimguenseok-redit\\dataproject5team-feature-kimguenseok-redit\\review_analyze_code_and_result\\"
    
    ANALYSIS_RESULTS_PATH = os.path.join(base_dir, "final_analysis_results_3_categories.csv")
    TOP_GAMES_PATH = os.path.join(base_dir, "final_top_20_per_genre_fixed.csv")
    BOTTOM_GAMES_PATH = os.path.join(base_dir, "final_bottom_20_per_genre_fixed.csv")
    
    # 최고 수치 결과 저장 경로 변경
    GENRE_MAXIMUMS_PATH = os.path.join(base_dir, "genre_category_maximums.csv")

    try:
        # 1. 1단계 결과 파일 로드 (게임별 감성 및 키워드 비율)
        df_final = pd.read_csv(ANALYSIS_RESULTS_PATH)
        
        # 2. 장르 정보를 얻기 위해 상위/하위 게임 목록 로드 및 병합
        df_top_games = pd.read_csv(TOP_GAMES_PATH)
        df_bottom_games = pd.read_csv(BOTTOM_GAMES_PATH)
        df_game_list = pd.concat([df_top_games, df_bottom_games], ignore_index=True).drop_duplicates(subset=['appid'])
        
    except FileNotFoundError as e:
        print(f"오류: 필수 파일이 누락되었습니다: {e.filename}")
        print("1단계 분석 스크립트를 먼저 실행하여 필요한 CSV 파일을 생성하거나 경로를 확인하세요.")
        return
    
    # 3. 장르 정보 병합 (KeyError 방지를 위해 안전한 방식 사용)
    genre_map = df_game_list.set_index('appid')['Selected_Genre'].to_dict()
    df_final['Selected_Genre'] = df_final['appid'].map(genre_map)
    
    # 장르 정보가 없는 행은 제외하고 복사
    df_final_with_genre = df_final.dropna(subset=['Selected_Genre']).copy()

    # 4. 최고 수치를 계산할 컬럼 목록 동적 생성
    # 감성 분석 컬럼
    cols_to_maximize = ['sentiment_score', 'sentiment_magnitude']
    
    # 키워드 비율 컬럼 추가
    for genre, categories in GENRE_FACTORS.items():
        for category in categories:
            cols_to_maximize.append(f"{genre}_SUCCESS_{category}_Ratio")
            cols_to_maximize.append(f"{genre}_FAILURE_{category}_Ratio")
    
    # 실제로 df_final_with_genre에 존재하는 컬럼만 선택
    cols_to_maximize = [col for col in cols_to_maximize if col in df_final_with_genre.columns]
    
    # 5. 장르별 최고 수치 계산 (mean() 대신 max() 사용)
    print("장르별 카테고리 최고 수치 계산을 시작합니다...")
    df_genre_maximums = df_final_with_genre.groupby('Selected_Genre')[cols_to_maximize].max().reset_index()

    # 6. 결과 저장
    df_genre_maximums.to_csv(GENRE_MAXIMUMS_PATH, index=False, encoding='utf-8-sig')
    print(f"[2/2] 장르별 카테고리 최고 수치 결과가 다음 파일에 저장되었습니다: {GENRE_MAXIMUMS_PATH}")


if __name__ == '__main__':
    calculate_genre_maximums()
