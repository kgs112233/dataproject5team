import csv
import time
import random
from urllib.parse import quote
from multiprocessing import Pool
from tqdm import tqdm

import pyautogui

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 사전 설정
INPUT_FILE = "input/RandomListByGenres.csv"
OUTPUT_FILE = "output/output.csv"
ERROR_LIST_FILE = "output/error_list.csv"
ERROR_GENRE_COUNT_FILE = "output/error_genre_count.csv"

CHUNK_SIZE = 500
POOL_GAME = 3
POOL_PUB = 3


# VPN 서버 변경
def vpn_click(img, desc, timeout=8):
    print(f"[VPN] '{desc}' 찾는 중")
    end = time.time() + timeout
    while time.time() < end:
        pos = pyautogui.locateOnScreen(img, confidence=0.8)
        if pos:
            center = pyautogui.center(pos)
            pyautogui.moveTo(center, duration=0.2)
            pyautogui.click()
            print(f"[VPN] '{desc}' 클릭 완료")
            return True
        time.sleep(0.4)
    print(f"[VPN] '{desc}' 찾지 못함")
    return False


def auto_change_vpn():
    print("\n===== VPN 서버 변경 시작 =====")

    changed = vpn_click("image/vpn_change_server.png", "Change Server")

    if changed:
        print("VPN 서버 변경 완료. 재연결까지 10초 대기...")
        time.sleep(10)
    else:
        print("VPN Change Server 버튼 찾지 못함")

    print("===== VPN 서버 변경 완료 =====\n")


# 셀레니움 설정
def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(options=options)


# 차단 방지
def safe_get(driver, url, retries=3):
    for _ in range(retries):
        try:
            driver.get(url)
            return True
        except:
            time.sleep(random.uniform(1.0, 2.0))
    return False


# Publisher 추출
def get_first_publisher(driver):
    try:
        overview_block = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Overview')]"))
        )

        lines = [l.strip() for l in overview_block.text.split("\n") if l.strip()]

        publisher_line = None

        for i, line in enumerate(lines):
            if line.startswith("Publishers:") or line.startswith("Publisher:"):
                after = line.split(":", 1)[1].strip()
                if after:
                    publisher_line = after
                else:
                    if i + 1 < len(lines):
                        publisher_line = lines[i+1].strip()
                break

        if not publisher_line:
            return None

        tokens = [t.strip() for t in publisher_line.split(",") if t.strip()]
        if not tokens:
            return None

        suffixes = {
            "inc.", "inc",
            "ltd.", "ltd",
            "co.", "co",
            "corp.", "corp",
            "llc", "llp",
            "lp",
            "gmbh", "ag", "ug", "ohg", "kg",
            "s.a.", "s.a", "sas", "sarl", "sae", "s.l.", "s.l",
            "s.r.l", "s.r.l.", "s.p.a", "s.p.a.",
            "bv",
            "co., ltd.", "co. ltd.", "co ltd",
        }

        first = tokens[0]
        idx = 1

        while idx < len(tokens):
            t = tokens[idx].lower()
            if t in suffixes:
                first += ", " + tokens[idx]
                idx += 1
            else:
                break

        return first

    except:
        return None


# 게임 수익 수집
def process_game(game):
    time.sleep(random.uniform(1.0, 2.0))

    appid = game["appid"]
    name = game["name"]
    genre = game["Selected_Genre"]

    driver = create_driver()
    url = f"https://gamalytic.com/game/{appid}"

    result = {
        "appid": appid,
        "name": name,
        "publisher_main": None,
        "Selected_Genre": genre,
        "game_revenue": "0"
    }

    try:
        if not safe_get(driver, url):
            return result

        # Publisher 수집
        publisher = get_first_publisher(driver)
        result["publisher_main"] = publisher

        # Gross revenue 수집
        stats_block = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Stats')]"))
        )

        lines = stats_block.text.split("\n")

        gross_normal = ""
        gross_base = ""

        for line in lines:
            if line.startswith("Gross revenue:"):
                gross_normal = line.replace("Gross revenue:", "").strip()

            if line.startswith("Gross revenue (base game):"):
                gross_base = line.replace("Gross revenue (base game):", "").strip()

        if gross_normal:
            result["game_revenue"] = gross_normal
        elif gross_base:
            result["game_revenue"] = gross_base
        else:
            result["game_revenue"] = "0"

    except:
        result["game_revenue"] = "0"

    finally:
        driver.quit()

    return result


# 배급사 수익 수집
def process_publisher(pub):
    time.sleep(random.uniform(0.8, 1.5))

    driver = create_driver()
    encoded = quote(pub)
    url = f"https://gamalytic.com/publisher/{encoded}"

    result = {"publisher": pub, "revenue": "ERROR"}

    try:
        if not safe_get(driver, url):
            return result

        block = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Overview')]"))
        )

        for line in block.text.split("\n"):
            if line.startswith("Total Lifetime Revenue:"):
                result["revenue"] = line.replace("Total Lifetime Revenue:", "").strip()
                break

    except:
        pass

    finally:
        driver.quit()

    return result


# 청크 나누개
def chunk_list(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


# 메인 실행부
if __name__ == "__main__":

    games = []
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            games.append({
                "appid": row["appid"],
                "name": row["name"],
                "Selected_Genre": row["Selected_Genre"]
            })

    print(f"[INFO] 총 게임 {len(games)}개")

    output_rows = []
    error_rows = []
    genre_count = {}
    publisher_cache = {}

    total_chunks = (len(games) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for chunk_idx, games_chunk in enumerate(chunk_list(games, CHUNK_SIZE), start=1):

        if chunk_idx > 1:
            auto_change_vpn()

        print(f"\n===== CHUNK {chunk_idx}/{total_chunks} 시작 =====")

        # 1. 게임 수집
        game_results = []
        with Pool(processes=POOL_GAME) as pool:
            for res in tqdm(pool.imap_unordered(process_game, games_chunk), total=len(games_chunk)):
                game_results.append(res)

        # 2. 배급사 캐시 수집
        pubs_to_fetch = sorted({
            g["publisher_main"]
            for g in game_results
            if g["publisher_main"] and g["publisher_main"] not in publisher_cache
        })

        print(f"[INFO] 새 publisher: {len(pubs_to_fetch)}개")

        if pubs_to_fetch:
            pub_results = []
            with Pool(processes=POOL_PUB) as pool:
                for res in tqdm(pool.imap_unordered(process_publisher, pubs_to_fetch),
                                total=len(pubs_to_fetch)):
                    pub_results.append(res)

            for p in pub_results:
                publisher_cache[p["publisher"]] = p["revenue"]

        # 3. 저장
        for g in game_results:
            pub_rev = publisher_cache.get(g["publisher_main"], "ERROR")

            row = [
                g["appid"],
                g["name"],
                g["publisher_main"],
                g["Selected_Genre"],
                g["game_revenue"],
                pub_rev
            ]
            output_rows.append(row)

            if g["game_revenue"] == "ERROR" or pub_rev == "ERROR":
                error_rows.append(row)
                genre_count[g["Selected_Genre"]] = genre_count.get(g["Selected_Genre"], 0) + 1

    # 4. CSV 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["appid", "name", "publisher_main", "Selected_Genre",
                    "game_revenue", "publisher_revenue"])
        w.writerows(output_rows)

    if error_rows:
        with open(ERROR_LIST_FILE, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["appid", "name", "publisher_main", "Selected_Genre",
                        "game_revenue", "publisher_revenue"])
            w.writerows(error_rows)

        with open(ERROR_GENRE_COUNT_FILE, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Selected_Genre", "Error_Count"])
            for genre, count in genre_count.items():
                w.writerow([genre, count])

    print("\n===== 전체 완료 =====")
    print(f"[SAVE] {OUTPUT_FILE}")
    print(f"[SAVE] {ERROR_LIST_FILE}")
    print(f"[SAVE] {ERROR_GENRE_COUNT_FILE}")
