import os
import re
import asyncio
import random
from pathlib import Path
from getpass import getpass  

import aiohttp
import pandas as pd
from tqdm import tqdm

# ==================== 설정 ====================

STORE_LANG = "english"
STORE_CC   = "KR"

SAMPLE_APP_COUNT = 500
CONCURRENCY_APPDETAILS = 12
REQ_TIMEOUT = 15
DELAY_MIN = 0.1
DELAY_MAX = 0.25

OUT_DIR = Path("./output_fast")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://store.steampowered.com/",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

STEAM_LIST_URL      = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
APPDETAILS_URL_TMPL = "https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}&l={lang}"

GENRE_PATTERNS = {
    "Action": r"\bAction\b|액션|격투|슈팅",
    "Adventure": r"\bAdventure\b|어드벤처",
    "RPG": r"\bRPG\b|롤\s*플레잉|JRPG",
}

# ==================== 비동기 유틸 ====================

class SemaphorePool:
    def __init__(self, max_concurrency):
        self._sema = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self):
        await self._sema.acquire()

    async def __aexit__(self, exc, exc2, tb):
        self._sema.release()


async def fetch_json(session, url, params=None):
    await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    try:
        async with session.get(url, params=params, timeout=REQ_TIMEOUT) as resp:
            print(f"[DEBUG] GET {resp.url} -> status {resp.status}")
            if resp.status != 200:
                text = await resp.text()
                print("[DEBUG] 응답 일부:", text[:300])
                return None
            return await resp.json(content_type=None)
    except Exception as e:
        print(f"[ERROR] 요청 실패: {e}")
        return None


def match_genres(genres):
    if not genres:
        return ""
    joined = " | ".join(g.get("description", "") for g in genres if isinstance(g, dict))
    matched = {name for name, pattern in GENRE_PATTERNS.items()
               if re.search(pattern, joined, re.IGNORECASE)}
    return ", ".join(sorted(matched))


async def fetch_appdetails(session, appid, limiter):
    url = APPDETAILS_URL_TMPL.format(appid=appid, cc=STORE_CC, lang=STORE_LANG)

    async with limiter:
        data = await fetch_json(session, url)
    if not data:
        return None

    node = data.get(str(appid))
    if not node or not node.get("success"):
        return None

    d = node["data"]
    if d.get("type") != "game":
        return None

    return {
        "appid": appid,
        "name": d.get("name"),
        "genres": match_genres(d.get("genres")),
        "release_date": (d.get("release_date") or {}).get("date"),
        "is_free": d.get("is_free"),
        "price": (d.get("price_overview") or {}).get("final_formatted"),
        "developers": ", ".join(d.get("developers", [])),
        "publishers": ", ".join(d.get("publishers", [])),
    }


# ==================== 메인 실행 ====================

async def main():
    #api_key 환경변수에서 가져오기
    api_key = os.environ.get("STEAM_API_KEY")
    #api_key 입력받기
    if not api_key:
        api_key = getpass("Steam Web API Key 입력 (입력 내용은 화면에 표시되지 않습니다): ").strip()

    if not api_key:
        print("[FATAL] API Key가 없습니다.")
        return

    OUT_DIR.mkdir(exist_ok=True)
    print("[1/3] 앱 리스트 수집 중...")

    async with aiohttp.ClientSession(headers=HEADERS) as sess:
        data = await fetch_json(
            sess,
            STEAM_LIST_URL,
            params={"key": api_key, "max_results": 50000},
        )

    if not data or "response" not in data:
        print("[FATAL] 앱 목록 수집 실패")
        return

    apps = data["response"].get("apps", [])
    print(f"  - 전체 앱 수: {len(apps):,}")

    if not apps:
        print("[FATAL] apps 리스트가 비어 있습니다.")
        return

    sampled = random.sample(apps, min(SAMPLE_APP_COUNT, len(apps)))
    print(f"  - 샘플링 수: {len(sampled):,}")

    limiter = SemaphorePool(CONCURRENCY_APPDETAILS)
    results = []

    print("[2/3] appdetails 수집중...")
    async with aiohttp.ClientSession(headers=HEADERS) as sess:
        tasks = []
        pbar = tqdm(total=len(sampled), desc="appdetails", ncols=100)

        async def handle(appid):
            info = await fetch_appdetails(sess, appid, limiter)
            if info:
                results.append(info)
            pbar.update(1)

        for x in sampled:
            tasks.append(asyncio.create_task(handle(x["appid"])))

        await asyncio.gather(*tasks)
        pbar.close()

    print("[3/3] CSV 저장...")
    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "sample_games.csv", index=False, encoding="utf-8-sig")

    print(f" 저장된 게임 수: {len(df)}")


if __name__ == "__main__":
    asyncio.run(main())
