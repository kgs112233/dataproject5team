import csv
import time
from urllib.parse import quote
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=chrome_options)


# 게임 수익 수집 함수
def process_game(game):
    """
    game = { 'appid': str, 'name': str, 'publishers': str }
    반환값 = { 'appid', 'name', 'publishers', 'game_revenue' }
    """

    appid = game["appid"]
    name = game["name"]
    publishers = game["publishers"]

    driver = create_driver()
    url = f"https://gamalytic.com/game/{appid}"

    result = {
        "appid": appid,
        "name": name,
        "publishers": publishers,
        "game_revenue": "ERROR"
    }

    try:
        driver.get(url)

        stats_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Stats')]"))
        )

        all_text = stats_block.text.split("\n")

        gross_normal = ""
        gross_base = ""

        for line in all_text:
            if line.startswith("Gross revenue:"):
                gross_normal = line.replace("Gross revenue:", "").strip()
            if line.startswith("Gross revenue (base game):"):
                gross_base = line.replace("Gross revenue (base game):", "").strip()

        # 최종 수익 결정
        if gross_normal:
            result["game_revenue"] = gross_normal
        elif gross_base:
            result["game_revenue"] = gross_base

    except Exception:
        pass  # ERROR 상태 그대로 둠

    finally:
        driver.quit()

    return result


# 배급사 수익 수집 함수
def process_publisher(pub):
    """
    pub = publisher name (string)
    반환값 = { publisher: str, revenue: str }
    """

    driver = create_driver()
    encoded = quote(pub)
    url = f"https://gamalytic.com/publisher/{encoded}"

    result = { "publisher": pub, "revenue": "ERROR" }

    try:
        driver.get(url)

        overview_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Overview')]"))
        )

        lines = overview_block.text.split("\n")

        for line in lines:
            if line.startswith("Total Lifetime Revenue:"):
                result["revenue"] = line.replace("Total Lifetime Revenue:", "").strip()
                break

    except Exception:
        pass

    finally:
        driver.quit()

    return result


# 메인 실행부
if __name__ == "__main__":

    # 병렬 프로세스 수 설정
    POOL_SIZE = min(8, cpu_count())

    # 입력 데이터 읽기
    games = []
    publishers = []

    with open("test_input.csv", "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            games.append({
                "appid": row["appid"],
                "name": row["name"],
                "publishers": row["publishers"]
            })
            publishers.append(row["publishers"])

    # 퍼블리셔 중복 제거
    unique_publishers = list(set(publishers))

    print(f"[INFO] 총 게임 수: {len(games)}개")
    print(f"[INFO] 총 배급사 수: {len(unique_publishers)}개")
    print(f"[INFO] 병렬 프로세스 수: {POOL_SIZE}")

    print("\n=== 게임 수익 수집 시작 ===")
    game_results = []
    with Pool(processes=POOL_SIZE) as pool:
        for res in tqdm(pool.imap_unordered(process_game, games), total=len(games)):
            game_results.append(res)

    print("\n=== 배급사 수익 수집 시작 ===")
    pub_results = []
    with Pool(processes=POOL_SIZE) as pool:
        for res in tqdm(pool.imap_unordered(process_publisher, unique_publishers), total=len(unique_publishers)):
            pub_results.append(res)

    pub_dict = { item["publisher"]: item["revenue"] for item in pub_results }

    output_rows = []
    for g in game_results:
        pub_rev = pub_dict.get(g["publishers"], "ERROR")
        output_rows.append([
            g["appid"],
            g["name"],
            g["publishers"],
            g["game_revenue"],
            pub_rev
        ])

    # csv 저장
    with open("game_and_publisher_revenue_output.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["appid", "name", "publishers", "game_revenue", "publisher_revenue"])
        writer.writerows(output_rows)

    print("\n=== 작업 완료 ===")