import time
import urllib.parse
import re
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# =========================
# 0. 설정값
# =========================

# 상위 20%, 하위 20% 게임 CSV 경로
TOP_CSV_PATH = r"final_top_20_per_genre_fixed (1).csv"
BOTTOM_CSV_PATH = r"final_bottom_20_per_genre_fixed (1).csv"

# 출력 CSV 경로
OUTPUT_CSV_PATH = r"reddit_comments_by_genre_top_bottom.csv"

# 크롬 드라이버 경로 (PATH에 있으면 None으로 두면 됨)
CHROME_DRIVER_PATH = r"C:\chromedriver.exe"   # 실제 chromedriver 위치로 수정

# 서브레딧 하나에서 가져올 게시글/댓글 개수
MAX_POSTS_PER_SUBREDDIT = 10     # hot 글 10개
MAX_COMMENTS_PER_POST = 10       # 글당 댓글 10개

# 테스트 모드: True면 앞에서 일부 게임만 실행
TEST_MODE = False                 # 전체 돌릴 때는 False
TEST_GAME_LIMIT = 2               # TEST_MODE=True일 때만 의미 있음


# =========================
# 1. Selenium WebDriver 초기화
# =========================

def create_driver():
    """Selenium Chrome WebDriver를 초기화하는 함수"""
    chrome_options = Options()
    # 화면 없이 실행하려면 주석 해제
    # chrome_options.add_argument("--headless=new")

    # 봇 탐지 완화용 옵션
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    if CHROME_DRIVER_PATH:
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    # 기본 암묵적 대기
    driver.implicitly_wait(5)
    return driver


# =========================
# 2. CSV에서 게임 리스트 읽기
# =========================

def load_game_list(top_csv_path, bottom_csv_path):
    """
    상위 20%, 하위 20% CSV를 읽어서
    [ {appid, name, genre, tier}, ... ] 형태 리스트로 반환
    tier: 'top' 또는 'bottom'
    """
    top_df = pd.read_csv(top_csv_path)
    bottom_df = pd.read_csv(bottom_csv_path)

    games = []

    for _, row in top_df.iterrows():
        games.append({
            "appid": int(row["appid"]),
            "name": str(row["name"]),
            "genre": str(row["Selected_Genre"]),
            "tier": "top"
        })

    for _, row in bottom_df.iterrows():
        games.append({
            "appid": int(row["appid"]),
            "name": str(row["name"]),
            "genre": str(row["Selected_Genre"]),
            "tier": "bottom"
        })

    return games


# =========================
# 3. 게임 이름으로 서브레딧 검색
# =========================

def normalize_text(s: str) -> str:
    """문자열을 유사도 비교용으로 정규화하는 함수 (소문자 + 영숫자 + 공백만)"""
    s = s.lower()
    s = s.replace("’", "'")
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def find_subreddit_for_game(driver, game_name):
    """
    게임 이름으로 Reddit 서브레딧 검색.

    old.reddit.com/subreddits/search?q= 로 이동한 뒤
    잠깐 기다리고,
    검색 결과 블록 div.thing.subreddit 안의 첫 번째 a.title 을 찾아
    클릭한 후 서브레딧 이름을 반환한다.
    """
    base_url = "https://old.reddit.com/subreddits/search"
    query = urllib.parse.quote_plus(game_name)
    url = f"{base_url}?q={query}"

    print(f"[DEBUG] 서브레딧 검색 URL: {url}")
    driver.get(url)

    # old.reddit 렌더링 여유 시간
    time.sleep(3)

    # 검색 결과: div.thing.subreddit 안의 a.title만 대상으로 선택
    links = driver.find_elements(By.CSS_SELECTOR, "div.thing.subreddit a.title")

    # 혹시 위 셀렉터가 안 잡히면, a.title 중에서 /r/ 를 포함하는 것만 필터
    if not links:
        print(f"[INFO] div.thing.subreddit a.title 없음, 전체 a.title에서 필터링 시도: {game_name}")
        candidates = driver.find_elements(By.CSS_SELECTOR, "a.title")
        links = [a for a in candidates if "/r/" in (a.get_attribute("href") or "")]
        if not links:
            print(f"[INFO] 서브레딧 후보 링크를 찾지 못함: {game_name}")
            return None

    first_link = links[0]
    href = first_link.get_attribute("href") or ""
    if "/r/" not in href:
        print(f"[INFO] '/r/'를 포함하지 않는 href: {href}")
        return None

    # 예: https://old.reddit.com/r/CivVI/
    part = href.split("/r/")[1]
    subreddit = part.split("/")[0].strip()
    if not subreddit:
        print(f"[INFO] 서브레딧 이름 파싱 실패: href={href}")
        return None

    try:
        first_link.click()
        print(f"[OK] '{game_name}' → r/{subreddit} 클릭 완료")
        time.sleep(1)  # 서브레딧 페이지 로딩 여유
    except Exception as e:
        print(f"[WARN] 서브레딧 링크 클릭 실패: {e}")

    return subreddit


# =========================
# 4. 서브레딧에서 핫 게시글 가져오기
# =========================

def get_top_posts_from_subreddit(driver, subreddit, max_posts=10, wait_sec=10):
    """
    특정 서브레딧에서 hot 게시글 상위 max_posts개를 가져온다.

    - https://old.reddit.com/r/{subreddit}/hot 기준
    - 각 게시글에서 'comments' 링크(a.comments)의 href를 댓글 페이지 URL로 사용한다.

    반환: [ {title, url(=comments_url)}, ... ]
    """
    url = f"https://old.reddit.com/r/{subreddit}/hot"
    driver.get(url)

    try:
        WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.thing.link"))
        )
    except TimeoutException:
        print(f"[WARN] 서브레딧 로딩 실패: r/{subreddit}")
        return []

    posts = []
    elements = driver.find_elements(By.CSS_SELECTOR, "div.thing.link")

    for el in elements:
        try:
            # 게시글 제목 (기록용)
            title_el = el.find_element(By.CSS_SELECTOR, "a.title")
            title = title_el.text.strip()

            # 댓글 페이지 링크
            comments_link = el.find_element(By.CSS_SELECTOR, "a.comments")
            comments_url = comments_link.get_attribute("href")

            if comments_url:
                posts.append({
                    "title": title,
                    "url": comments_url
                })

        except NoSuchElementException:
            continue

        if len(posts) >= max_posts:
            break

    print(f"[INFO] r/{subreddit} hot 게시글 {len(posts)}개 선택")
    return posts


# =========================
# 5. 게시글에서 댓글 크롤링
# =========================

def to_old_reddit_url(url):
    """www.reddit.com 형식을 old.reddit.com 으로 바꿔서 파싱하기 쉽게 만드는 함수"""
    if "old.reddit.com" in url:
        return url
    return url.replace("https://www.reddit.com", "https://old.reddit.com") \
              .replace("https://reddit.com", "https://old.reddit.com")


def get_comments_from_post(driver, post_url, max_comments=100, wait_sec=10):
    """
    특정 게시글 URL에서 댓글 크롤링.
    old.reddit.com 기준, 댓글 div.thing[data-type='comment'] 대상.

    반환: [ {author, score, body}, ... ]
    """
    url = to_old_reddit_url(post_url)
    driver.get(url)

    try:
        WebDriverWait(driver, wait_sec).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.thing"))
        )
    except TimeoutException:
        print(f"[WARN] 게시글 로딩 실패: {url}")
        return []

    comment_elements = driver.find_elements(By.CSS_SELECTOR, "div.thing[data-type='comment']")
    comments = []

    for el in comment_elements:
        try:
            # 작성자
            try:
                author = el.get_attribute("data-author")
                if not author:
                    author_el = el.find_element(By.CSS_SELECTOR, "a.author")
                    author = author_el.text.strip()
            except NoSuchElementException:
                author = "[deleted]"

            # 점수
            try:
                score_el = el.find_element(By.CSS_SELECTOR, "span.score.unvoted")
                score_text = score_el.get_attribute("title") or score_el.text
                score_text = score_text.replace("points", "").replace("point", "").strip()
                score = int(score_text) if score_text else 0
            except Exception:
                score = 0

            # 댓글 본문
            try:
                body_el = el.find_element(By.CSS_SELECTOR, "div.entry div.usertext-body div.md")
                body = body_el.text.strip()
            except NoSuchElementException:
                body = ""

            if not body:
                continue

            comment_id = el.get_attribute("data-fullname")  # 예: t1_xxxxx
            comments.append({
                "comment_id": comment_id,
                "author": author,
                "score": score,
                "body": body
            })

        except Exception:
            continue

        if len(comments) >= max_comments:
            break

    print(f"[INFO] 댓글 {len(comments)}개 수집 완료: {url}")
    return comments


# =========================
# 6. 전체 파이프라인 실행 (게임 단위 자동 저장 포함)
# =========================

def main():
    games = load_game_list(TOP_CSV_PATH, BOTTOM_CSV_PATH)
    print(f"[INFO] CSV 기준 전체 게임 수: {len(games)}")

    # 테스트 모드일 경우 앞에서 일부 게임만 사용
    if TEST_MODE:
        games = games[:TEST_GAME_LIMIT]
        print(f"[INFO] 테스트 모드: 상위 {TEST_GAME_LIMIT}개 게임만 처리합니다.")

    # 기존 결과 파일이 있으면 삭제 후 헤더만 먼저 생성
    if os.path.exists(OUTPUT_CSV_PATH):
        os.remove(OUTPUT_CSV_PATH)
        print(f"[INFO] 기존 결과 파일 삭제: {OUTPUT_CSV_PATH}")

    header_df = pd.DataFrame(columns=[
        "appid", "game_name", "genre", "tier", "subreddit",
        "post_title", "post_url",
        "comment_id", "comment_author", "comment_score", "comment_body"
    ])
    header_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[INFO] 결과 파일 헤더 생성: {OUTPUT_CSV_PATH}")

    driver = create_driver()
    result_rows = []

    for idx, game in enumerate(games, start=1):
        appid = game["appid"]
        name = game["name"]
        genre = game["genre"]
        tier = game["tier"]

        print(f"\n========== [{idx}/{len(games)}] 게임 처리: {name} ({genre}, {tier}) ==========")

        # 1) 게임 이름으로 서브레딧 검색
        subreddit = find_subreddit_for_game(driver, name)
        if not subreddit:
            print(f"[SKIP] 서브레딧 없음: {name}")
            continue

        # 2) 서브레딧에서 hot 게시글 가져오기
        posts = get_top_posts_from_subreddit(
            driver,
            subreddit,
            max_posts=MAX_POSTS_PER_SUBREDDIT
        )
        if not posts:
            print(f"[SKIP] 게시글 없음: r/{subreddit}")
            continue

        # 3) 각 게시글에서 댓글 수집
        for post in posts:
            post_title = post["title"]
            post_url = post["url"]

            comments = get_comments_from_post(
                driver,
                post_url,
                max_comments=MAX_COMMENTS_PER_POST
            )
            if not comments:
                continue

            for c in comments:
                result_rows.append({
                    "appid": appid,
                    "game_name": name,
                    "genre": genre,
                    "tier": tier,
                    "subreddit": subreddit,
                    "post_title": post_title,
                    "post_url": post_url,
                    "comment_id": c["comment_id"],
                    "comment_author": c["author"],
                    "comment_score": c["score"],
                    "comment_body": c["body"]
                })

        # 4) 게임 하나 처리 끝날 때마다 자동 저장
        if result_rows:
            df = pd.DataFrame(result_rows)
            df.sort_values(by=["genre", "tier", "appid"], inplace=True)
            df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
            print(f"[AUTO-SAVE] {idx}/{len(games)}개 게임 처리 완료 - 현재까지 댓글 수: {len(df)}")

        # Reddit / Cloudflare에 너무 안 찍히게 약간 휴식
        time.sleep(2)

    driver.quit()

    print(f"\n[DONE] 전체 처리 완료. 최종 결과 파일: {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
