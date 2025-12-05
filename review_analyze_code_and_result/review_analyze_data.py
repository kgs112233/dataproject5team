import pandas as pd
import re
from google.cloud import language_v1
import os

GENRE_FACTORS = {
    "Action": {
        "Combat": {
            "SUCCESS": [r'fluid', r'fast-paced', r'responsive', r'satisfying', r'impact', r'smooth', r'precision', r'tight controls', r'combat is great'],
            "FAILURE": [r'clunky', r'slow', r'unresponsive', r'janky', r'awkward', r'hitbox', r'spam', r'repetitive', r'bad controls', r'feels stiff', r'no impact']
        },
        "Controls": {
            "SUCCESS": [r'precision', r'tight controls', r'responsive', r'smooth movement', r'quick reaction'],
            "FAILURE": [r'unresponsive controls', r'laggy', r'input delay', r'clunky movement', r'awkward controls', r'bad hit registration']
        },
        "Difficulty": {
            "SUCCESS": [r'challenging but fair', r'satisfying difficulty', r'great challenge', r'good balancing', r'hard but rewarding'],
            "FAILURE": [r'too easy', r'too hard', r'unfair difficulty', r'poorly balanced', r'frustrating difficulty', r'spikes in difficulty']
        }
    },
    "Strategy": {
        "StrategicVariety": {
            "SUCCESS": [r'strategic depth', r'diverse strategies', r'many ways to win', r'flexible tactics', r'complex decisions'],
            "FAILURE": [r'single strategy', r'one dominant path', r'boring choices', r'linear tactics', r'lack of depth']
        },
        "AIQuality": {
            "SUCCESS": [r'smart AI', r'challenging AI', r'clever opponent', r'AI is competitive'],
            "FAILURE": [r'dumb AI', r'stupid AI', r'AI cheats', r'predictable AI', r'no challenge from AI']
        },
        "InfoClarity": {
            "SUCCESS": [r'clear information', r'good feedback', r'intuitive interface', r'easy to understand data'],
            "FAILURE": [r'confusing data', r'unclear information', r'bad feedback', r'obscure mechanics', r'hard to read UI']
        }
    },
    "Indie": {
        "Originality": {
            "SUCCESS": [r'innovative', r'unique concept', r'original idea', r'fresh take', r'unseen'],
            "FAILURE": [r'generic', r'unoriginal', r'copied formula', r'stale concept']
        },
        "Polish/Bugs": {
            "SUCCESS": [r'highly polished', r'no crashes', r'stable performance', r'smooth experience', r'no bugs'],
            "FAILURE": [r'buggy', r'crashes constantly', r'technical issues', r'poor optimization', r'glitches', r'unstable']
        },
        "Value": {
            "SUCCESS": [r'great value for money', r'worth the price', r'cheap but amazing', r'huge amount of content'],
            "FAILURE": [r'overpriced', r'not worth the money', r'too short for price', r'lack of content']
        }
    },
    "RPG": {
        "Worldbuilding": {
            "SUCCESS": [r'rich world', r'deep lore', r'immersive setting', r'believable world', r'compelling atmosphere'],
            "FAILURE": [r'bland world', r'weak lore', r'generic setting', r'inconsistent worldbuilding']
        },
        "Rewards": {
            "SUCCESS": [r'satisfying progression', r'meaningful rewards', r'great loot', r'rewarding choices', r'feel powerful'],
            "FAILURE": [r'grindy', r'boring leveling', r'weak rewards', r'no excitement from loot', r'pointless progression']
        },
        "Freedom/Choice": {
            "SUCCESS": [r'high freedom', r'many choices', r'impactful decisions', r'multiple paths', r'open-ended'],
            "FAILURE": [r'linear path', r'no real choice', r'decisions dont matter', r'railroading', r'low freedom']
        }
    },
    "Simulation": {
        "SystemDepth": {
            "SUCCESS": [r'deep mechanics', r'complex systems', r'robust simulation', r'high fidelity', r'lots of detail'],
            "FAILURE": [r'shallow system', r'simplistic mechanics', r'no depth', r'fake depth', r'too easy']
        },
        "UI/Interface": {
            "SUCCESS": [r'intuitive UI', r'easy to navigate', r'clear interface', r'user-friendly', r'clean design'],
            "FAILURE": [r'clunky UI', r'confusing menus', r'bad interface', r'poor readability', r'unnecessary clicking']
        },
        "Realism": {
            "SUCCESS": [r'highly realistic', r'accurate simulation', r'authentic feel', r'true to life physics'],
            "FAILURE": [r'unrealistic', r'bad physics', r'feels arcadey', r'poor implementation of reality']
        }
    },
    "Adventure": {
        "Story": {
            "SUCCESS": [r'engaging story', r'well-written narrative', r'emotional plot', r'memorable characters', r'great plot'],
            "FAILURE": [r'weak story', r'plotholes', r'boring plot', r'bad writing', r'narrative falls apart']
        },
        "Exploration": {
            "SUCCESS": [r'satisfying exploration', r'strong exploration motive', r'rich world', r'fun to explore', r'discovery'],
            "FAILURE": [r'monotonous exploration', r'linear map', r'empty world', r'no reason to explore', r'tedious backtracking']
        },
        "Atmosphere": {
            "SUCCESS": [r'immersive atmosphere', r'stunning visuals', r'great sound design', r'world-building is excellent', r'mood'],
            "FAILURE": [r'dull atmosphere', r'generic setting', r'bad sound', r'not immersive', r'lack of mood']
        }
    },
    "Casual": {
        "Addictiveness": {
            "SUCCESS": [r'highly addictive', r'hard to put down', r'just one more round', r'compulsive gameplay', r'endless fun'],
            "FAILURE": [r'gets boring fast', r'no replay value', r'easily bored', r'repetitive gameplay']
        },
        "Variety/LevelDesign": {
            "SUCCESS": [r'diverse levels', r'high variety', r'creative stages', r'many mini-games', r'simple controls yet deep'],
            "FAILURE": [r'repetitive levels', r'low variety', r'too many similar stages', r'lack of innovation', r'too simple controls']
        },
        "Playtime/Pacing": {
            "SUCCESS": [r'perfect playtime', r'satisfying length', r'good pacing', r'easy to pick up and play'],
            "FAILURE": [r'too short', r'too long', r'bad pacing', r'feels like a chore', r'time commitment is high']
        }
    },
    "Puzzle": {
        "Logic/Intuition": {
            "SUCCESS": [r'logical puzzles', r'intuitive solutions', r'clear rules', r'well-designed puzzles', r'makes sense'],
            "FAILURE": [r'illogical puzzles', r'unreasonable solutions', r'guesswork puzzles', r'makes no sense', r'frustrating puzzle']
        },
        "DifficultyCurve": {
            "SUCCESS": [r'smooth difficulty curve', r'natural progression', r'ramps up perfectly', r'fair challenges'],
            "FAILURE": [r'erratic difficulty', r'sudden spikes', r'badly balanced puzzles', r'too easy then too hard']
        },
        "Novelty": {
            "SUCCESS": [r'novel puzzle mechanics', r'creative elements', r'fresh ideas', r'never seen before', r'innovative puzzles'],
            "FAILURE": [r'generic puzzles', r'reused mechanics', r'stale puzzles', r'too simple', r'unoriginal elements']
        }
    }
}

def analyze_sentiment_api(client, text):
    try:
        if not text or pd.isna(text):
            return 0.0, 0.0

        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT, language='en')
        response = client.analyze_sentiment(document=document)
        
        score = response.document_sentiment.score
        magnitude = response.document_sentiment.magnitude
        
        return score, magnitude
    
    except Exception as e:
        return 0.0, 0.0

def analyze_keywords_vectorized(df_reviews, df_game_list, genre_factors_dict):

    df_results = df_reviews[['appid', 'review']].copy()
    
    appid_to_genre = df_game_list.set_index('appid')['Selected_Genre'].to_dict()
    appid_to_group = df_game_list.set_index('appid')['Group'].to_dict()
    
    df_results['genre'] = df_results['appid'].map(appid_to_genre)
    df_results['group'] = df_results['appid'].map(appid_to_group)
    
    all_keyword_cols = []
    
    df_list = []
    
    for genre, factors in genre_factors_dict.items():
        
        df_genre = df_results[df_results['genre'] == genre].copy()
        
        if df_genre.empty:
            continue
            
        genre_keyword_cols = []

        for category, factor_dict in factors.items():
            
            success_patterns = '|'.join(factor_dict.get('SUCCESS', []))
            success_col_name = f"{genre}_SUCCESS_{category}"
            if success_patterns:
                df_genre[success_col_name] = df_genre['review'].str.lower().str.count(success_patterns, flags=re.IGNORECASE).fillna(0)
                genre_keyword_cols.append(success_col_name)

            failure_patterns = '|'.join(factor_dict.get('FAILURE', []))
            failure_col_name = f"{genre}_FAILURE_{category}"
            if failure_patterns:
                df_genre[failure_col_name] = df_genre['review'].str.lower().str.count(failure_patterns, flags=re.IGNORECASE).fillna(0)
                genre_keyword_cols.append(failure_col_name)

        top_mask = df_genre['group'] == 'Top'
        bottom_mask = df_genre['group'] == 'Bottom'
        
        for col in genre_keyword_cols:
            if '_FAILURE_' in col:
                df_genre.loc[top_mask, col] = 0
            elif '_SUCCESS_' in col:
                df_genre.loc[bottom_mask, col] = 0
                
        df_list.append(df_genre)
        all_keyword_cols.extend(genre_keyword_cols)

    if not df_list:
        return pd.DataFrame()
        
    df_combined = pd.concat(df_list, ignore_index=True)
    
    df_keyword_counts = df_combined.groupby('appid', dropna=False)[list(set(all_keyword_cols))].sum().reset_index()
    
    return df_keyword_counts

def calculate_keyword_ratios(df_game_list, df_keyword_counts):
    
    df_results = pd.merge(df_game_list[['appid', 'Review_Count']], df_keyword_counts, on='appid', how='left')
    df_results = df_results.fillna(0)
    
    keyword_cols = [col for col in df_results.columns if col not in ['appid', 'Review_Count']]
    
    for col in keyword_cols:
        ratio_col = f'{col}_Ratio'
        df_results[ratio_col] = df_results.apply(
            lambda row: row[col] / row['Review_Count'] if row['Review_Count'] > 0 else 0.0, axis=1
        )
        
    ratio_cols = [col for col in df_results.columns if col.endswith('_Ratio')]
    
    df_final = df_results[['appid'] + ratio_cols]
    
    return df_final

def calculate_sentiment_averages(df_game_list, df_reviews_sentiment):
    
    sentiment_averages = df_reviews_sentiment.groupby('appid')[['sentiment_score', 'sentiment_magnitude']].mean().reset_index()
    
    df_final = pd.merge(df_game_list, sentiment_averages, on='appid', how='left')
    
    df_final[['sentiment_score', 'sentiment_magnitude']] = df_final[['sentiment_score', 'sentiment_magnitude']].fillna(0.0)
    
    return df_final


if __name__ == '__main__':
    BASE_PATH = "C:\\Users\\minjh\\OneDrive\\문서\\데분프 과제\\팀플\\dataproject5team\\collect_steam_review\\"
    
    REVIEWS_FILE_PATH = BASE_PATH + "steam_reviews_top50_each_game.csv" 
    
    TOP_GAMES_PATH = BASE_PATH + "final_top_20_per_genre_fixed.csv"
    BOTTOM_GAMES_PATH = BASE_PATH + "final_bottom_20_per_genre_fixed.csv"
    
    OUTPUT_FILE_PATH = BASE_PATH + "final_analysis_results_3_categories.csv"
    GENRE_AVERAGES_PATH = BASE_PATH + "genre_category_averages.csv"

    try:
        df_reviews = pd.read_csv(REVIEWS_FILE_PATH)
    except FileNotFoundError:
        print(f"오류: 리뷰 파일 '{REVIEWS_FILE_PATH}'을(를) 찾을 수 없습니다.")
        print("경로를 확인하거나, 'steam_reviews_top50_each_game.csv' 파일을 해당 경로에 놓아주세요.")
        exit()

    try:
        df_top_games = pd.read_csv(TOP_GAMES_PATH)
        df_bottom_games = pd.read_csv(BOTTOM_GAMES_PATH)
    except FileNotFoundError as e:
        print(f"오류: 상위/하위 게임 목록 파일 중 하나를 찾을 수 없습니다: {e.filename}")
        print("해당 파일을 BASE_PATH에 놓아주세요.")
        exit()

    df_top_games['Group'] = 'Top'
    df_bottom_games['Group'] = 'Bottom'
    
    df_game_list = pd.concat([df_top_games, df_bottom_games], ignore_index=True).drop_duplicates(subset=['appid'])
    
    target_genres = list(GENRE_FACTORS.keys())
    df_game_list = df_game_list[df_game_list['Selected_Genre'].isin(target_genres)].copy()
    
    target_appids = df_game_list['appid'].unique()
    df_reviews_filtered = df_reviews[df_reviews['appid'].isin(target_appids)].copy()
    
    actual_review_counts = df_reviews_filtered.groupby('appid').size().reset_index(name='Review_Count')
    df_game_list = df_game_list.drop(columns=['Review_Count'], errors='ignore')
    df_game_list = pd.merge(df_game_list, actual_review_counts, on='appid', how='left')
    df_game_list['Review_Count'] = df_game_list['Review_Count'].fillna(0).astype(int)

    total_reviews_count = len(df_reviews_filtered)
    print(f"--- 8개 장르 전체 분석을 시작합니다. ---")
    print(f"분석 대상 게임 수: {len(df_game_list)}개. 총 리뷰 수: {total_reviews_count}개")

    client = language_v1.LanguageServiceClient()
    
    sentiment_data = []

    print("감성 분석을 시작합니다 (시간이 오래 걸릴 수 있습니다)...")
    
    for index, row in df_reviews_filtered.iterrows():
        score, magnitude = analyze_sentiment_api(client, row['review'])
        sentiment_data.append({
            'appid': row['appid'],
            'sentiment_score': score,
            'sentiment_magnitude': magnitude
        })
        
        current_count = index + 1
        if current_count % 1000 == 0 or current_count == total_reviews_count:
            progress = (current_count / total_reviews_count) * 100
            print(f"처리된 리뷰: {current_count}/{total_reviews_count} ({progress:.2f}%)", end='\r')
            
    print(f"\n처리된 리뷰: {total_reviews_count}/{total_reviews_count} (100.00%)")
    df_reviews_sentiment = pd.DataFrame(sentiment_data)
    
    print("감성 분석 완료.")

    print("키워드 분석 (3개 카테고리, 벡터화)을 시작합니다...")
    df_keyword_counts = analyze_keywords_vectorized(df_reviews_filtered, df_game_list, GENRE_FACTORS)
    print("키워드 분석 완료.")
    
    df_final_sentiment = calculate_sentiment_averages(df_game_list, df_reviews_sentiment)
    
    df_final_keywords_ratios = calculate_keyword_ratios(df_game_list, df_keyword_counts)
    
    df_final = pd.merge(df_final_sentiment, df_final_keywords_ratios, on='appid', how='left')

    df_final.to_csv(OUTPUT_FILE_PATH, index=False, encoding='utf-8-sig')
    print(f"\n[1/2] 게임별 분석 결과가 다음 파일에 저장되었습니다: {OUTPUT_FILE_PATH}")

    df_final_with_genre = pd.merge(df_final, df_game_list[['appid', 'Selected_Genre']], on='appid', how='left')

    ratio_cols = [col for col in df_final_with_genre.columns if col.endswith('_Ratio')]
    
    cols_to_average = ['sentiment_score', 'sentiment_magnitude'] + ratio_cols
    df_genre_averages = df_final_with_genre.groupby('Selected_Genre')[cols_to_average].mean().reset_index()

    df_genre_averages.to_csv(GENRE_AVERAGES_PATH, index=False, encoding='utf-8-sig')
    print(f"[2/2] 장르별 카테고리 평균 결과가 다음 파일에 저장되었습니다: {GENRE_AVERAGES_PATH}")