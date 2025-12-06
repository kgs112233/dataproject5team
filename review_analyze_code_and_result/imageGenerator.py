import pandas as pd
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings('ignore')


GENRE_FACTORS = {
    "Action": ["Combat", "Controls", "Difficulty", "TechIssues", "Balance", "Blame"],
    "Strategy": ["StrategicVariety", "AIQuality", "InfoClarity", "TechIssues", "Balance", "Blame"],
    "Indie": ["Originality", "Polish/Bugs", "Value", "TechIssues", "Balance", "Blame"],
    "RPG": ["Worldbuilding", "Rewards", "Freedom/Choice", "TechIssues", "Balance", "Blame"],
    "Simulation": ["SystemDepth", "UI/Interface", "Realism", "TechIssues", "Balance", "Blame"],
    "Adventure": ["Story", "Exploration", "Atmosphere", "TechIssues", "Balance", "Blame"],
    "Casual": ["Addictiveness", "Variety/LevelDesign", "Playtime/Pacing", "TechIssues", "Balance", "Blame"],
    "Puzzle": ["Logic/Intuition", "DifficultyCurve", "Novelty", "TechIssues", "Balance", "Blame"],

    "Racing": ["Vehicle Handling", "Track Variety", "Graphics & Immersion",
               "Vehicle Variety", "TechIssues", "Balance", "Blame"],
    "JRPG": ["Character Appeal", "World Atmosphere", "Level Flow & Fatigue",
             "TechIssues", "Balance", "Blame"],
    "Massively Multiplayer": ["Content Volume", "Service Stability",
                              "TechIssues", "Balance", "Blame"],
    "Tower Defense": ["Information Display", "Strategic Options",
                      "Accessibility & Engagement", "TechIssues", "Balance", "Blame"],
    "City Builder": ["Freedom & Map Scale", "Simulation Depth",
                     "City UI Usability", "TechIssues", "Balance", "Blame"],
    "Metroidvania": ["Map Connectivity", "Ability Unlock Impact",
                     "Boss Battles", "TechIssues", "Balance", "Blame"],
    "Fighting": ["Hit Feel & Flow", "Character Balance", "Combo Depth",
                 "Online Infrastructure", "TechIssues", "Balance", "Blame"],
    "4X": ["AI Behavior", "Session Depth",
           "Accessibility & Depth", "TechIssues", "Balance", "Blame"],

    "Platformer": ["Control", "Level Design", "Difficulty",
               "TechIssues", "Balance", "Blame"],
    "Horror": ["Atmosphere", "Jumpscare", "Presentation",
               "TechIssues", "Balance", "Blame"],
    "Shooter": ["Optimization", "Cheaters", "Gunplay",
               "TechIssues", "Balance", "Blame"],
    "Survival": ["Resource", "Exploration", "Progression",
               "TechIssues", "Balance", "Blame"],
    "Visual Novel": ["Character", "Story", "Choice",
               "TechIssues", "Balance", "Blame"],
    "Sports": ["Physics", "AI", "Game Flow",
               "TechIssues", "Balance", "Blame"],
    "Roguelike": ["RNG", "Replayability", "Synergy",
               "TechIssues", "Balance", "Blame"],
    "Card & Board": ["Strategy", "Accessibility", "Luck",
               "TechIssues", "Balance", "Blame"]
}


def plot_and_save_per_genre(df_maximums, output_dir):
    plt.rcParams['font.family'] = 'Malgun Gothic'
    os.makedirs(output_dir, exist_ok=True)

    for genre, categories in GENRE_FACTORS.items():
        genre_data = df_maximums[df_maximums['Selected_Genre'] == genre]

        if genre_data.empty:
            print(f"⚠️ {genre}: 데이터 없음 → 스킵")
            continue

        genre_row = genre_data.iloc[0]

        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle(f"{genre} 장르 성공 / 실패 비율", fontsize=16)

        for idx, ratio_type in enumerate(["SUCCESS", "FAILURE"]):
            ax = axes[idx]
            ratios, labels = [], []

            for category in categories:
                col = f"{genre}_{ratio_type}_{category}_Ratio"
                if col in genre_row and genre_row[col] > 0:
                    ratios.append(genre_row[col] * 100)
                    labels.append(category)

            if ratios and sum(ratios) > 0:
                other = max(0, 100 - sum(ratios))
                ratios.append(other)
                labels.append("기타")

                explode = [0.05] * (len(ratios) - 1) + [0.08]

                ax.pie(
                    ratios,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    explode=explode,
                    shadow=True,
                    pctdistance=0.7,
                    textprops={'fontsize': 9}
                )
                ax.set_title("성공" if ratio_type == "SUCCESS" else "실패")
                ax.axis('equal')
            else:
                ax.set_title(f"{ratio_type} 데이터 부족")
                ax.axis('off')

        save_path = os.path.join(
            output_dir,
            f"genre_{genre.replace(' ', '_').replace('&', 'and')}_success_failure.png"
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=200)
        plt.close()
        print(f"✅ 저장 완료: {save_path}")


if __name__ == '__main__':
    base_dir = (
        "C:\\Users\\minjh\\Downloads\\dataproject5team-feature-kimguenseok-redit\\"
        "dataproject5team-feature-kimguenseok-redit\\review_analyze_code_and_result\\"
    )

    GENRE_MAXIMUMS_PATH = os.path.join(base_dir, "genre_category_maximums.csv")
    OUTPUT_DIR = os.path.join(base_dir, "genre_pie_results")

    df_genre_maximums = pd.read_csv(GENRE_MAXIMUMS_PATH)
    plot_and_save_per_genre(df_genre_maximums, OUTPUT_DIR)
