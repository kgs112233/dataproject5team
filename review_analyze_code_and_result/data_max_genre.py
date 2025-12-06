import pandas as pd
import os
import re


BASE_GENRE_FACTORS = {
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


NEW_GENRE_FACTORS = {
    "Racing": [
        "Vehicle Handling", "Track Variety", "Graphics & Immersion",
        "Vehicle Variety", "TechIssues", "Balance", "Blame"
    ],
    "JRPG": [
        "Character Appeal", "World Atmosphere", "Level Flow & Fatigue",
        "TechIssues", "Balance", "Blame"
    ],
    "Massively Multiplayer": [
        "Content Volume", "Service Stability",
        "TechIssues", "Balance", "Blame"
    ],
    "Tower Defense": [
        "Information Display", "Strategic Options", "Accessibility & Engagement",
        "TechIssues", "Balance", "Blame"
    ],
    "City Builder": [
        "Freedom & Map Scale", "Simulation Depth", "City UI Usability",
        "TechIssues", "Balance", "Blame"
    ],
    "Metroidvania": [
        "Map Connectivity", "Ability Unlock Impact", "Boss Battles",
        "TechIssues", "Balance", "Blame"
    ],
    "Fighting": [
        "Hit Feel & Flow", "Character Balance", "Combo Depth",
        "Online Infrastructure", "TechIssues", "Balance", "Blame"
    ],
    "4X": [
        "AI Behavior", "Session Depth", "Accessibility & Depth",
        "TechIssues", "Balance", "Blame"
    ],

    "Platformer": ["Control", "Level Design", "Difficulty"],
    "Horror": ["Atmosphere", "Jumpscare", "Presentation"],
    "Shooter": ["Optimization", "Cheaters", "Gunplay"],
    "Survival": ["Resource", "Exploration", "Progression"],
    "Visual Novel": ["Character", "Story", "Choice"],
    "Sports": ["Physics", "AI", "Game Flow"],
    "Roguelike": ["RNG", "Replayability", "Synergy"],
    "Card & Board": ["Strategy", "Accessibility", "Luck"]
}


GENRE_FACTORS = {}
GENRE_FACTORS.update(BASE_GENRE_FACTORS)

for genre, categories in NEW_GENRE_FACTORS.items():
    GENRE_FACTORS[genre] = categories 


def calculate_genre_maximums():
    base_dir = (
        "C:\\Users\\minjh\\Downloads\\dataproject5team-feature-kimguenseok-redit\\"
        "dataproject5team-feature-kimguenseok-redit\\review_analyze_code_and_result\\"
    )

    ANALYSIS_RESULTS_PATH = os.path.join(base_dir, "final_analysis_results_3_categories.csv")
    TOP_GAMES_PATH = os.path.join(base_dir, "final_top_20_per_genre_fixed.csv")
    BOTTOM_GAMES_PATH = os.path.join(base_dir, "final_bottom_20_per_genre_fixed.csv")
    GENRE_MAXIMUMS_PATH = os.path.join(base_dir, "genre_category_maximums.csv")

    try:
        df_final = pd.read_csv(ANALYSIS_RESULTS_PATH)
        df_top = pd.read_csv(TOP_GAMES_PATH)
        df_bottom = pd.read_csv(BOTTOM_GAMES_PATH)

        df_games = (
            pd.concat([df_top, df_bottom], ignore_index=True)
            .drop_duplicates(subset=["appid"])
        )
    except FileNotFoundError as e:
        print(f"파일 누락: {e.filename}")
        return

    genre_map = df_games.set_index("appid")["Selected_Genre"].to_dict()
    df_final["Selected_Genre"] = df_final["appid"].map(genre_map)
    df_final = df_final.dropna(subset=["Selected_Genre"])

    cols_to_maximize = ["sentiment_score", "sentiment_magnitude"]

    for genre, categories in GENRE_FACTORS.items():
        for category in categories:
            cols_to_maximize.append(f"{genre}_SUCCESS_{category}_Ratio")
            cols_to_maximize.append(f"{genre}_FAILURE_{category}_Ratio")

    cols_to_maximize = [c for c in cols_to_maximize if c in df_final.columns]

    df_max = (
        df_final
        .groupby("Selected_Genre")[cols_to_maximize]
        .max()
        .reset_index()
    )

    df_max.to_csv(GENRE_MAXIMUMS_PATH, index=False, encoding="utf-8-sig")
    print(f"완료: {GENRE_MAXIMUMS_PATH}")


if __name__ == "__main__":
    calculate_genre_maximums()
