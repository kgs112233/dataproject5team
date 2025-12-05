import pandas as pd
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings('ignore')

# 분석 대상 장르와 핵심 카테고리 정의
GENRE_FACTORS = {
    "Action": ["Combat", "Controls", "Difficulty"],
    "Strategy": ["StrategicVariety", "AIQuality", "InfoClarity"],
    "Indie": ["Originality", "Polish/Bugs", "Value"],
    "RPG": ["Worldbuilding", "Rewards", "Freedom/Choice"],
    "Simulation": ["SystemDepth", "UI/Interface", "Realism"],
    "Adventure": ["Story", "Exploration", "Atmosphere"],
    "Casual": ["Addictiveness", "Variety/LevelDesign", "Playtime/Pacing"],
    "Puzzle": ["Logic/Intuition", "DifficultyCurve", "Novelty"]
}

def plot_genre_ratios(df_maximums):
    # 주어진 장르 최고 수치 데이터프레임을 기반으로 모든 장르의 성공 및 실패 비율을 시각화
    plt.rcParams['font.family'] = 'Malgun Gothic' 

    all_genres = list(GENRE_FACTORS.keys())
    
    # 4x4 레이아웃으로 16개의 서브플롯 설정
    fig, axes = plt.subplots(4, 4, figsize=(25, 25)) 
    axes = axes.flatten()

    # 일반 장르에 적용할 explode 패턴 (4개 조각: [Core1, Core2, Core3, 기타])
    EXPLODE_PATTERN = [0.10, 0.03, 0.07, 0.05] 
    
    # Casual 장르 전용 explode 패턴 (더 벌어지게 설정)
    CASUAL_EXPLODE_PATTERN = [0.25, 0.15, 0.20, 0.10] 
    
    print("모든 장르에 대한 성공 및 실패 비율 원형 그래프를 생성 중...")
    
    plot_index = 0
    
    for ratio_type in ["SUCCESS", "FAILURE"]:
        for target_genre in all_genres:
            ax = axes[plot_index]
            
            # 해당 장르의 데이터 행을 필터링
            genre_data = df_maximums[df_maximums['Selected_Genre'] == target_genre]
            
            if genre_data.empty:
                ax.set_title(f"{target_genre} ({ratio_type}) 데이터 없음", fontsize=12)
                ax.axis('off')
                plot_index += 1
                continue
                
            genre_row = genre_data.iloc[0]
            categories = GENRE_FACTORS.get(target_genre)
            
            core_ratios = []
            labels = []
            
            # 1. 3개 핵심 카테고리 비율 추출
            for category in categories:
                column_name = f"{target_genre}_{ratio_type}_{category}_Ratio"
                if column_name in genre_row:
                    ratio_value = genre_row[column_name]
                    # CSV 파일의 수치를 퍼센트(0~100)로 변환
                    core_ratios.append(ratio_value * 100)
                    labels.append(category)

            # 데이터가 있고 합계가 0보다 큰 경우에만 플로팅
            if core_ratios and sum(core_ratios) > 0:
                
                # 2. '기타' 비율 계산 (총합 100% 가정)
                sum_core_ratios = sum(core_ratios)
                other_ratio = max(0, 100.0 - sum_core_ratios)

                final_ratios = core_ratios + [other_ratio]
                final_labels = labels + ["기타"]
                
                # 3. Explode 패턴 적용
                if target_genre == 'Casual':
                    explode_values = CASUAL_EXPLODE_PATTERN
                else:
                    explode_values = EXPLODE_PATTERN
                
                # 원형 그래프 생성 (5% 미만도 모두 표시)
                ax.pie(final_ratios, labels=final_labels, autopct='%1.1f%%', startangle=90, 
                       shadow=True, explode=explode_values,
                       textprops={'fontsize': 10},
                       pctdistance=0.7, 
                       wedgeprops={'linewidth': 1, 'edgecolor': 'white'})

                title_korean = f"{target_genre} 장르 ({'성공' if ratio_type == 'SUCCESS' else '실패'})"
                ax.set_title(title_korean, fontsize=14, pad=10)
                ax.axis('equal')
            else:
                ax.set_title(f"{target_genre} ({ratio_type}) (데이터 부족)", fontsize=14)
                ax.axis('off')
                
            plot_index += 1

    fig.suptitle("8개 주요 장르별 핵심 카테고리 및 기타 키워드 언급 비율 (최대값 기준)", fontsize=24, y=1.00)
    plt.tight_layout(rect=[0, 0, 1, 0.99]) 
    plt.show()

if __name__ == '__main__':
    # 파일 경로 설정 (장르별 최고 수치 파일 사용)
    base_dir = "C:\\Users\\minjh\\OneDrive\\문서\\데분프 과제\\팀플\\dataproject5team\\collect_steam_review"
    GENRE_MAXIMUMS_PATH = os.path.join(base_dir, "genre_category_maximums.csv")

    try:
        # 2단계 분석 후 생성된 최종 최고 수치 파일 로드
        df_genre_maximums = pd.read_csv(GENRE_MAXIMUMS_PATH)
        print(f"'{GENRE_MAXIMUMS_PATH}' 파일을 성공적으로 로드했습니다.")
    except FileNotFoundError:
        print(f"오류: 평균 파일 '{GENRE_MAXIMUMS_PATH}'을(를) 찾을 수 없습니다.")
        print("경로를 확인하거나, 'calculate_genre_maximums.py' 스크립트를 먼저 실행하여 파일을 생성하세요.")
        exit()
    except pd.errors.EmptyDataError:
        print(f"오류: 파일 '{GENRE_MAXIMUMS_PATH}'이(가) 비어 있습니다.")
        exit()

    plot_genre_ratios(df_genre_maximums)