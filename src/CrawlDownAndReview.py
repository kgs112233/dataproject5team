import pandas as pd
import requests
import time
import random

def get_steam_data(appid):
    """
    Steam 공식 Store API: 평점 및 리뷰 수 수집
    """
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            summary = data.get('query_summary', {})
            total_reviews = summary.get('total_reviews', 0)
            positive = summary.get('total_positive', 0)
            
            # 긍정 리뷰 비율 계산
            if total_reviews > 0:
                score = round((positive / total_reviews) * 100, 2)
            else:
                score = 0
            
            return {
                'Steam_Score': score,
                'Total_Reviews': total_reviews
            }
    except:
        pass
    return {'Steam_Score': 0, 'Total_Reviews': 0}

def get_steamspy_data(appid):
    """
    SteamSpy API: 사이트에 명시된 보유자 수(Owners) 구간 수집
    """
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # SteamSpy에서 제공하는 'owners' 문자열 
            owners_str = data.get('owners', "N/A")
            # 시인성 향상을 위한 처리
            owners_clean = owners_str.replace("..", "-").replace(",", "")
            return owners_clean
    except:
        pass
    return "Error"

def main():
    input_filename = 'steam_games_with_peak_players.csv'
    output_filename = 'steam_games_final_data.csv'
    
    print(f"Reading {input_filename}...")
    try:
        df = pd.read_csv(input_filename)
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다. 파일명을 확인해주세요.")
        return

    print(f"Collecting data for {len(df)} games... (Estimated time: 30-60 mins)")
    print("API 호출 제한을 피하기 위해 천천히 수집합니다.")

    scores = []
    reviews_count = []
    owners_data = []

    # 데이터 수집 루프
    for idx, row in df.iterrows():
        appid = row['appid']
        name = row['name']
        
        # 스팀 공식 평점 가져오기
        steam_info = get_steam_data(appid)
        scores.append(steam_info['Steam_Score'])
        reviews_count.append(steam_info['Total_Reviews'])
        
        # SteamSpy 보유자 수 가져오기
        owners = get_steamspy_data(appid)
        owners_data.append(owners)
        
        # 진행 상황 표시 
        if (idx + 1) % 10 == 0:
            print(f"[{idx + 1}/{len(df)}] {name} -> Owners: {owners}, Score: {steam_info['Steam_Score']}%")
        
        # API 차단 방지를 위한 대기 시간 
        time.sleep(1.5) 

    # 결과 저장
    df['Steam_User_Score_Percent'] = scores
    df['Total_Reviews_Count'] = reviews_count
    df['Owners_SteamSpy'] = owners_data 

    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n모든 데이터가 '{output_filename}'에 저장되었습니다.")

if __name__ == "__main__":
    main()