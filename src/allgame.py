#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
스팀 전체 게임을 수집해서 CSV로 저장하는 스크립트.
백업시스템은 copilot이 작성함
[출력]
./output/전체_게임_목록.csv
(추가로 장르별 CSV도 생성됨)
"""
import os
import re
import json
import time
import random
import asyncio
import aiohttp
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from getpass import getpass 

STORE_LANG = "english"  
STORE_CC   = "KR"


# 동시 요청 수(403 회피를 위해 적당히 조절)
CONCURRENCY_APPDETAILS = 16

# 요청 타임아웃(초)
REQ_TIMEOUT = 15

# 요청 간 랜덤 지연(초) 범위
DELAY_MIN = 0.25
DELAY_MAX = 0.5

# 출력 폴더
OUT_DIR = Path("./output")

# Steam Web API Key (환경변수에서 읽기)
STEAM_API_KEY = os.getenv("STEAM_API_KEY", None)


HEADERS = {
    # 봇 차단 회피용 브라우저 UA
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://store.steampowered.com/",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

STEAM_LIST_URL        = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
APPDETAILS_URL_TMPL   = "https://store.steampowered.com/api/appdetails?appids={appid}&cc={cc}&l={lang}"
STEAMSPY_APP_URL_TMPL = "https://steamspy.com/api.php?request=appdetails&appid={appid}"

GENRE_PATTERNS = {
    # 표준 장르명 : 정규식(영문/국문 혼용 대응)
    "Action": r"\bAction\b|액션|핵\s*앤\s*슬래시|격투|슈팅|1인칭\s*슈팅|3인칭\s*슈팅",
    "Adventure": r"\bAdventure\b|어드벤처",
    "RPG": r"\bRPG\b|롤\s*플레잉|JRPG|던전\s*RPG",
    "Strategy": r"\bStrategy\b|전략|실시간\s*전략|턴제\s*전략|군사\s*전략|4X|정착지|도시\s*건설",
    "Simulation": r"\bSimulation\b|시뮬레이션|생활|몰입형|건설|자동화|제작|농업|연애\s*시뮬레이션|샌드박스",
    "Sports": r"\bSports?\b|스포츠|팀\s*스포츠|스포츠\s*경영|레이싱\s*시뮬레이션",
    "Racing": r"\bRacing\b|레이싱",
    "Casual": r"\bCasual\b|캐주얼|퍼즐|풍부한\s*스토리",
    "Indie": r"\bIndie\b|인디",
    "Massively Multiplayer": r"\bMassively\s*Multiplayer\b|대규모\s*멀티플레이어|MMO",
    "Puzzle": r"\bPuzzle\b|퍼즐",
    "Platformer": r"\bPlatformer\b|플랫폼|러너",
    "Horror": r"\bHorror\b|공포",
    "Card & Board": r"\bCard\b|\bBoard\b|카드|보드",
    "Roguelike": r"\bRoguelike\b|\bRoguelite\b|로그라이크|로그라이트",
    "JRPG": r"\bJRPG\b|JRPG",
    "Survival": r"\bSurvival\b|생존",
    "Shooter": r"\bShooter\b|슈팅|총격",
    "Visual Novel": r"\bVisual\s*Novel\b|비주얼\s*노벨",
    "Metroidvania": r"\bMetroidvania\b|메트로배니아",
    "Fighting": r"\bFighting\b|격투|격투\s*및\s*무술",
    "Tower Defense": r"\bTower\s*Defense\b|타워\s*디펜스",
    "City Builder": r"\bCity\s*Builder\b|도시\s*건설|정착지",
    "4X": r"\b4X\b|4X",
}

class Throttler:
    def __init__(self, limit: int):
        self.sema = asyncio.Semaphore(limit)
    async def __aenter__(self):
        await self.sema.acquire()
    async def __aexit__(self, exc_type, exc, tb):
        self.sema.release()

async def get_json_with_retry(session: aiohttp.ClientSession, url: str,
                              params=None, timeout=REQ_TIMEOUT,
                              retries=3, backoff=1.5, delay_between=False):

    for i in range(retries):
        try:
            if delay_between:
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            async with session.get(url, params=params, timeout=timeout) as r:
                # 403 등은 별도 처리하고 싶을 수 있으나 여기서는 단순 반환
                if r.status == 403:
                    return {"__http_status__": 403}
                if r.status == 200:
                    # appdetails는 content_type 헤더가 없을 수 있어 None 허용
                    return await r.json(content_type=None)
                if r.status in (429, 500, 502, 503, 504):
                    await asyncio.sleep((backoff ** i))
                else:
                    return None
        except Exception:
            await asyncio.sleep((backoff ** i))
    return None

def match_genres(store_genres, steamspy_tags=None):
    """
    store_genres: appdetails의 genres 배열 [{"id":"1","description":"Action"}, ...]
    steamspy_tags: SteamSpy appdetails의 tags(dict) 키 목록
    반환: 매칭된 표준 장르 셋
    """
    texts = []
    if store_genres:
        texts += [g.get("description", "") for g in store_genres if isinstance(g, dict)]
    if steamspy_tags:
        texts += list(steamspy_tags)  

    if not texts:
        return set()

    text = " | ".join(map(str, texts))
    matched = set()
    for std_name, pattern in GENRE_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            matched.add(std_name)
    return matched

async def fetch_steamspy_details(session: aiohttp.ClientSession, appid: int):
    """
    SteamSpy appdetails 호출 (백업 플로우)
    반환 형식: info dict (appdetails와 유사하게 정규화)
    """
    url = STEAMSPY_APP_URL_TMPL.format(appid=appid)
    data = await get_json_with_retry(session, url, timeout=REQ_TIMEOUT, retries=2, backoff=1.5, delay_between=True)
    if not data or not isinstance(data, dict) or "name" not in data:
        return None

    # SteamSpy 필드 표준화
    tags = data.get("tags") or {}  # dict: {"Action": 12345, ...}
    developers = [d.strip() for d in (data.get("developer") or "").split(",") if d.strip()]
    publishers = [p.strip() for p in (data.get("publisher") or "").split(",") if p.strip()]
    year = data.get("release_year") or data.get("year") or ""
    

    info = {
        "appid": appid,
        "name": data.get("name"),
        "release_date": str(year) if year else None,
        "is_free": None,
        "price_overview": None,
        "developers": developers,
        "publishers": publishers,
        "genres": None,           # SteamSpy는 genres 필드가 없으므로 None
        "steamspy_tags": list(tags.keys()),  # 매칭에 활용
        "_source": "steamspy",
    }
    return info


async def fetch_appdetails(session: aiohttp.ClientSession, appid: int, throttler: Throttler, stats: dict):
    """
    Storefront appdetails 호출 → 실패/403 시 SteamSpy 백업
    반환: (appid, info|None)
    """
    url = APPDETAILS_URL_TMPL.format(appids=appid, appid=appid, cc=STORE_CC, lang=STORE_LANG)
    async with throttler:
        data = await get_json_with_retry(session, url, timeout=REQ_TIMEOUT, retries=3, backoff=1.7, delay_between=True)

    if data is None:
        stats["appdetails_fail"] += 1
        # 백업 시도
        info = await fetch_steamspy_details(session, appid)
        if info:
            stats["steamspy_used"] += 1
        return appid, info

    if isinstance(data, dict) and data.get("__http_status__") == 403:
        stats["appdetails_403"] += 1
        # 백업 시도
        info = await fetch_steamspy_details(session, appid)
        if info:
            stats["steamspy_used"] += 1
        return appid, info

    node = data.get(str(appid))
    if not node or not node.get("success"):
        stats["appdetails_unsuccess"] += 1
        # 백업 시도
        info = await fetch_steamspy_details(session, appid)
        if info:
            stats["steamspy_used"] += 1
        return appid, info

    dat = node.get("data", {})
    if dat.get("type") != "game":
        stats["non_game"] += 1
        return appid, None

    info = {
        "appid": appid,
        "name": dat.get("name"),
        "release_date": (dat.get("release_date") or {}).get("date"),
        "is_free": dat.get("is_free"),
        "price_overview": dat.get("price_overview", {}),
        "developers": dat.get("developers", []),
        "publishers": dat.get("publishers", []),
        "genres": dat.get("genres", []),
        "_source": "appdetails",
    }
    return appid, info

# -------------------- 전체 앱 목록(IStoreService) 수집 --------------------
async def fetch_all_steam_apps(api_key: str):
    """
    IStoreService.GetAppList/v1 를 사용해서
    have_more == False 가 될 때까지 전체 앱 목록을 페이지네이션으로 수집.
    반환: [(appid, name), ...]
    """
    all_apps = []
    params = {
        "key": api_key,
        "max_results": 50000,  # 한 번에 가져올 최대 개수
    }

    async with aiohttp.ClientSession(headers=HEADERS) as s:
        page = 1
        while True:
            print(f"[INFO] 앱 목록 페이지 {page} 수집 요청...")
            data = await get_json_with_retry(s, STEAM_LIST_URL, params=params,
                                             timeout=REQ_TIMEOUT, retries=3, backoff=1.5, delay_between=False)
            if not data or "response" not in data:
                print("[ERROR] 앱 목록 응답이 올바르지 않습니다. 중단합니다.")
                break

            resp = data["response"]
            apps = resp.get("apps", [])
            for x in apps:
                if "appid" in x:
                    all_apps.append((x["appid"], x.get("name", "")))

            print(f"  - 현재까지 누적 앱 수: {len(all_apps):,}")

            if not resp.get("have_more"):
                print("[INFO] 더 이상 가져올 앱이 없습니다. 전체 수집 완료.")
                break

            last_appid = resp.get("last_appid")
            if not last_appid:
                print("[WARN] have_more는 True인데 last_appid가 없습니다. 안전을 위해 중단합니다.")
                break

            params["last_appid"] = last_appid
            page += 1

    return all_apps

# -------------------- 메인 파이프라인 --------------------
async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 0) API 키 확보 (환경변수 → getpass 순)
    api_key = STEAM_API_KEY
    if not api_key:
        api_key = getpass("Steam Web API Key 입력 (입력 내용은 화면에 표시되지 않습니다): ").strip()

    if not api_key:
        raise RuntimeError("STEAM_API_KEY가 설정되지 않았습니다.")

    # 1) 전체 앱 목록
    print("[1/4] 전체 앱 목록 수집 (IStoreService.GetAppList)...")
    apps = await fetch_all_steam_apps(api_key)
    if not apps:
        raise RuntimeError("앱 목록 수집 실패")
    print(f"전체 앱 수: {len(apps):,}")

    # 2) appdetails/SteamSpy 수집 + 장르 매칭
    print("[2/4] 앱 상세 및 장르 매칭 중...")
    throttler = Throttler(CONCURRENCY_APPDETAILS)
    details = {}                # appid -> info
    genre_candidates = {}       # 표준장르 -> [appid, ...]
    for g in GENRE_PATTERNS.keys():
        genre_candidates[g] = []

    stats = {
        "non_game": 0,
        "appdetails_403": 0,
        "appdetails_fail": 0,
        "appdetails_unsuccess": 0,
        "steamspy_used": 0,
        "genre_unmatched": 0,
    }

    pbar = tqdm(total=len(apps), ncols=100, desc="details")
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async def handle(appid: int):
            appid_, info = await fetch_appdetails(session, appid, throttler, stats)
            pbar.update(1)
            if not info:
                return

            # 장르 판정(steamspy 태그 + appdetails 장르)
            matched = match_genres(info.get("genres"), steamspy_tags=info.get("steamspy_tags"))
            if not matched:
                # 🔹 이제는 '장르 미매칭'이어도 전체 리스트에는 포함시키고,
                #    다만 genre_candidates에는 안 넣음
                stats["genre_unmatched"] += 1
                details[appid_] = info
                return

            details[appid_] = info
            for g in matched:
                genre_candidates[g].append(appid_)

        tasks = [asyncio.create_task(handle(aid)) for aid, _ in apps]
        for f in asyncio.as_completed(tasks):
            await f
    pbar.close()

    for g, lst in genre_candidates.items():
        print(f" - 장르 후보 {g}: {len(lst):,}개")

    # 3) 전체 테이블 작성
    print("[3/4] 테이블 구성 및 저장...")
    rows_all = []
    for appid, info in details.items():
        matched = match_genres(info.get("genres"), steamspy_tags=info.get("steamspy_tags"))
        genre_str = ", ".join(sorted(matched)) if matched else ""
        price = None
        if info.get("price_overview"):
            price = info["price_overview"].get("final_formatted")

        rows_all.append({
            "appid": appid,
            "name": info.get("name"),
            "genres": genre_str,
            "release_date": info.get("release_date"),
            "is_free": info.get("is_free"),
            "price": price,
            "developers": ", ".join(info.get("developers") or []),
            "publishers": ", ".join(info.get("publishers") or []),
            "source": info.get("_source"),
        })

    df_all = pd.DataFrame(rows_all)
    if not df_all.empty:
        # 전체 게임 목록: 이름 기준 정렬
        df_all = df_all.sort_values(by=["name"], ascending=[True])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(OUT_DIR / "전체_게임_목록.csv", index=False, encoding="utf-8-sig")

    # 장르별 CSV (상한 없이 전체)
    for g, appids in genre_candidates.items():
        if not appids:
            continue
        rows = []
        for a in appids:
            info = details.get(a)
            if not info:
                continue
            price = None
            if info.get("price_overview"):
                price = info["price_overview"].get("final_formatted")
            rows.append({
                "appid": a,
                "name": info.get("name"),
                "release_date": info.get("release_date"),
                "is_free": info.get("is_free"),
                "price": price,
                "developers": ", ".join(info.get("developers") or []),
                "publishers": ", ".join(info.get("publishers") or []),
                "source": info.get("_source"),
            })
        df_g = pd.DataFrame(rows)
        if not df_g.empty:
            df_g = df_g.sort_values(by=["name"], ascending=[True])
            df_g.to_csv(OUT_DIR / f"{g}_전체.csv", index=False, encoding="utf-8-sig")

    # 4) 요약 로그
    print("[4/4] 완료")
    print("요약:")
    print(f" - appdetails 403: {stats['appdetails_403']:,}")
    print(f" - appdetails 실패: {stats['appdetails_fail']:,}")
    print(f" - appdetails success=false: {stats['appdetails_unsuccess']:,}")
    print(f" - 비게임 제외: {stats['non_game']:,}")
    print(f" - SteamSpy 백업 사용: {stats['steamspy_used']:,}")
    print(f" - 장르 미매칭(그래도 전체 리스트에는 포함): {stats['genre_unmatched']:,}")
    print(f" - 최종 전체 테이블 행 수: {len(df_all):,}")
    for g, appids in genre_candidates.items():
        if appids:
            print(f"   · {g}: {len(appids):,}개")

if __name__ == "__main__":
    # Windows 콘솔 한글 처리(가능한 경우)
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

    asyncio.run(main())
