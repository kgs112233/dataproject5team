import pandas as pd
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings('ignore')
# 이미지 생성 테스트 및 결과 확인용 코드
# 분석 대상 장르와 핵심 카테고리 정의
# - 각 장르마다 원래 3개 핵심 카테고리 + 공통 3개(TechIssues, Balance, Blame)를 사용
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


def plot_genre_ratios(df_maximums):
    """
    장르별 최고 비율 데이터를 받아서
    SUCCESS / FAILURE 각각에 대해 8개 장르의 파이차트를 그리는 함수
    """
    # 한글 폰트 설정 (윈도우 기준)
    plt.rcParams['font.family'] = 'Malgun Gothic'

    all_genres = list(GENRE_FACTORS.keys())

    # 4x4 레이아웃으로 16개의 서브플롯 설정 (장르 8개 x 성공/실패 2종)
    fig, axes = plt.subplots(4, 4, figsize=(25, 25))
    axes = axes.flatten()

    print("모든 장르에 대한 성공 및 실패 비율 원형 그래프를 생성 중...")

    plot_index = 0

    # ratio_type: SUCCESS / FAILURE 두 가지를 각각 그림
    for ratio_type in ["SUCCESS", "FAILURE"]:
        for target_genre in all_genres:
            ax = axes[plot_index]

            # 해당 장르의 행 추출
            genre_data = df_maximums[df_maximums['Selected_Genre'] == target_genre]

            if genre_data.empty:
                ax.set_title(f"{target_genre} ({ratio_type}) 데이터 없음", fontsize=12)
                ax.axis('off')
                plot_index += 1
                continue

            genre_row = genre_data.iloc[0]
            categories = GENRE_FACTORS.get(target_genre, [])

            core_ratios = []
            labels = []

            # 1. 정의된 카테고리들에 대한 비율을 추출
            for category in categories:
                column_name = f"{target_genre}_{ratio_type}_{category}_Ratio"
                if column_name in genre_row:
                    ratio_value = genre_row[column_name]
                    # 0~1 사이 비율을 0~100 퍼센트로 변환
                    core_ratios.append(ratio_value * 100.0)
                    labels.append(category)

            # 데이터가 있고, 합계가 0보다 큰 경우에만 파이차트 그림
            if core_ratios and sum(core_ratios) > 0:
                # 2. 기타 비율 계산 (총합 100%를 기준으로 부족분을 기타로 처리)
                sum_core = sum(core_ratios)
                other_ratio = max(0.0, 100.0 - sum_core)

                final_ratios = core_ratios + [other_ratio]
                final_labels = labels + ["기타"]

                # 3. 조각 개수에 맞춰 동적으로 explode 값 생성
                num_slices = len(final_ratios)

                if target_genre == 'Casual':
                    # Casual 장르는 전체적으로 조금 더 강하게 강조
                    # 마지막 조각(기타)을 약간 더 튀어나오게 설정
                    explode_values = [0.15] * (num_slices - 1) + [0.2]
                else:
                    # 일반 장르는 전체적으로 약하게 강조
                    explode_values = [0.05] * (num_slices - 1) + [0.08]

                # 4. 원형 그래프 생성
                ax.pie(
                    final_ratios,
                    labels=final_labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=True,
                    explode=explode_values,
                    textprops={'fontsize': 10},
                    pctdistance=0.7,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
                )

                title_korean = f"{target_genre} 장르 ({'성공' if ratio_type == 'SUCCESS' else '실패'})"
                ax.set_title(title_korean, fontsize=14, pad=10)
                ax.axis('equal')
            else:
                ax.set_title(f"{target_genre} ({ratio_type}) (데이터 부족)", fontsize=14)
                ax.axis('off')

            plot_index += 1

    fig.suptitle(
        "8개 주요 장르별 핵심 카테고리 및 기타 키워드 언급 비율 (최대값 기준)",
        fontsize=24,
        y=1.00
    )
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.show()


if __name__ == '__main__':
    # 2단계 분석 후 생성된 장르별 최고 수치 파일 경로
    # 실제 사용 경로에 맞게 수정해서 사용하세요.
    base_dir = "C:\\Users\\minjh\\Downloads\\dataproject5team-feature-kimguenseok-redit\\dataproject5team-feature-kimguenseok-redit\\review_analyze_code_and_result\\"
    GENRE_MAXIMUMS_PATH = os.path.join(base_dir, "genre_category_maximums.csv")

    try:
        df_genre_maximums = pd.read_csv(GENRE_MAXIMUMS_PATH)
        print(f"'{GENRE_MAXIMUMS_PATH}' 파일을 성공적으로 로드했습니다.")
    except FileNotFoundError:
        print(f"오류: 파일 '{GENRE_MAXIMUMS_PATH}'을(를) 찾을 수 없습니다.")
        print("경로를 확인하거나, 'data_max_genre.py' 스크립트를 먼저 실행하여 파일을 생성하세요.")
        exit()
    except pd.errors.EmptyDataError:
        print(f"오류: 파일 '{GENRE_MAXIMUMS_PATH}'이(가) 비어 있습니다.")
        exit()

    plot_genre_ratios(df_genre_maximums)

