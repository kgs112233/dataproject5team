import pandas as pd
import time
import os
from googleapiclient.discovery import build
from youtube_search import YoutubeSearch

# 유튜브 API 키 입력
YOUTUBE_API_KEY = ""

# 파일 가져오기 및 게임 리스트 생성
def load_game_names():
    print("게임 리스트 파일을 읽어오는 중...")
    try:
        # 파일 가져오기
        df_top = pd.read_csv('final_top_20_per_genre_fixed.csv')
        df_bottom = pd.read_csv('final_bottom_20_per_genre_fixed.csv')
        
        # 두 데이터 합치기
        df_all = pd.concat([df_top, df_bottom])
        
        # 'name' 컬럼만 리스트로 변환 (중복 제거)
        game_list = df_all['name'].dropna().unique().tolist()
        
        print(f"총 {len(game_list)}개의 게임을 찾았습니다.")
        return game_list
    except Exception as e:
        print(f"파일 읽기 실패: {e}")
        return []

# 영상 검색 함수 (Review 단어 포함 여부만 확인)
def get_video_id_by_search(game_name):
    # 검색어: 게임이름 + Review
    query = f"{game_name} Review"
    
    try:
        # 검색 결과 상위 5개 영상 가져오기
        results = YoutubeSearch(query, max_results=5).to_dict()
        
        if not results:
            print(f"검색 결과 없음")
            return None, None
            
        # 상위 5개 영상을 순서대로 확인
        for result in results:
            video_title = result['title']
            
            # 영상 제목에 'review'가 포함되어 있는지 확인
            if "review" in video_title.lower():
                print(f"영상 선택: {video_title[:40]}...")
                return result['id'], video_title
        
        # 5개를 다 봤는데 제목에 'Review'가 들어간 게 하나도 없으면 스킵
        print(f"[Skip] 제목에 'Review'가 포함된 영상이 없음.")
        return None, None
            
    except Exception as e:
        print(f"검색 에러: {e}")
        return None, None

# 유튜브 알고리즘으로 댓글 20개씩 수집 함수
def get_top_20_comments(youtube, video_id, game_name):
    collected_data = []
    
    try:
        # 인기순(relevance)으로 넉넉하게 30개 요청
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=30, 
            textFormat="plainText",
            order="relevance" 
        ).execute()

        items = response.get('items', [])
        
        # 최대 20개까지만 수집
        target_count = 20
        
        for i, item in enumerate(items):
            if i >= target_count: 
                break
                
            comment = item['snippet']['topLevelComment']['snippet']
            
            collected_data.append({
                'Game_Name': game_name,
                'Video_ID': video_id,
                'Video_Title': item.get('video_title', ''),
                'Author': comment['authorDisplayName'],
                'Comment': comment['textDisplay'],
                'Likes': comment['likeCount'],
                'Date': comment['publishedAt'][:10]
            })
            
        return collected_data

    except Exception as e:
        # 댓글이 막혀있거나 오류 발생 시
        return []

# 메인 함수 실행
def main():
    # 게임 리스트 로드
    game_names = load_game_names()
    if not game_names:
        return

    # 유튜브 API 연결
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    except Exception as e:
        print(f"API 키 오류: {e}")
        return

    all_comments = []
    
    print(f"\n{len(game_names)}개 게임에 대한 데이터 수집을 시작합니다.")

    # 반복문 실행
    for i, game in enumerate(game_names):
        print(f"[{i+1}/{len(game_names)}] {game} 처리 중...", end=" ")
        
        # 영상 찾기
        video_id, video_title = get_video_id_by_search(game)
        
        # 댓글 20개 수집
        if video_id:
            comments = get_top_20_comments(youtube, video_id, game)
            
            if comments:
                all_comments.extend(comments)
                print(f"-> 댓글 {len(comments)}개 수집 완료")
            else:
                print("-> 댓글 없음/수집 불가")
        else:
            pass

        # 1초 대기 (차단 방지)
        time.sleep(1)
        
        # 중간 저장: 100개 게임마다 저장하기
        if (i + 1) % 100 == 0:
            temp_df = pd.DataFrame(all_comments)
            temp_df.to_csv(f"temp_comments_saved_{i+1}.csv", index=False, encoding='utf-8-sig')
            print(f"중간 저장 완료 ({i+1}번째 게임까지)")

    # 최종
    if all_comments:
        df = pd.DataFrame(all_comments)
        filename = "steam_960_games_comments_review_20_each.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"모든 수집이 완료되었습니다!")
        print(f"저장된 파일명: {filename}")
        print(f"총 수집된 댓글 수: {len(df)}개")
    else:
        print("수집된 데이터가 하나도 없습니다.")

if __name__ == "__main__":
    main()