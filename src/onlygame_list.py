import pandas as pd
import re
from pathlib import Path


# 이 스크립트 파일 위치 (예: ~/dataproject5team/src/onlygame_list.py)
SCRIPT_DIR = Path(__file__).resolve().parent
# 프로젝트 루트: src의 상위 (~/dataproject5team)
PROJECT_ROOT = SCRIPT_DIR.parent
# input 디렉터리: ~/dataproject5team/input
INPUT_DIR = PROJECT_ROOT / "input"

# 정리 대상 원본 파일 (필요하면 파일명만 바꾸면 됨)
INPUT_FILE = INPUT_DIR / "게임목록+최고동시접속자.csv"

# 출력: 게임만 남긴 파일 / 비게임 의심 목록 파일
OUTPUT_GAMES = INPUT_DIR / "genre_random100_only_games.csv"
OUTPUT_NON_GAMES = INPUT_DIR / "genre_random100_non_game_suspects.csv"


# ============================================================
# 1. 게임이 아닌 패턴 (DLC, OST, Tool, Demo 등)
#    정규식으로 한 번에 처리
# ============================================================

NON_GAME_KEYWORDS = [
    # OST / 음악 계열
    r"soundtrack", r"\bost\b", r"bgm", r"sound track",

    # DLC / 확장팩 / 추가 콘텐츠
    r"\bdlc\b", r"expansion", r"season pass", r"content pack",

    # 체험판 / 프로로그 / 베타 / 알파 / 테스트 빌드
    r"demo", r"prologue", r"\balpha\b", r"\bbeta\b",
    r"preview", r"playtest", r"test build", r"prototype",

    # 툴 / 편집기 / 유틸리티
    r"editor", r"level editor", r"tool", r"tools", r"utility",

    # 영상 계열
    r"movie", r"trailer", r"cutscenes", r"animation",

    # 아트북 / 이미지 계열
    r"wallpaper", r"artbook", r"concept art", r"sketchbook",
    r"fan kit", r"avatars",

    # 스킨, 코스튬 등
    r"skin", r"costume", r"cosmetic",

    # 기타 비게임 항목
    r"benchmark", r"manual", r"guide"
]

NON_GAME_REGEX = re.compile("|".join(NON_GAME_KEYWORDS), re.IGNORECASE)


def is_non_game(name: str) -> bool:
    """게임이 아닌(또는 비게임 가능성이 높은) 항목인지 여부를 판별"""
    if not isinstance(name, str):
        return False
    return bool(NON_GAME_REGEX.search(name))


# ============================================================
# 2. 전체 CSV에서 비게임/게임 분리 후 파일로 저장
# ============================================================

def split_games_and_non_games(input_path: Path,
                              output_games: Path,
                              output_non_games: Path):
    """전체 리스트를 읽어서
       - 비게임 의심 항목: 별도 CSV로 저장
       - 나머지(게임으로 추정): 다른 CSV로 저장
    """

    if not input_path.exists():
        raise FileNotFoundError(f"[에러] 입력 파일을 찾을 수 없습니다: {input_path}")

    # 원본 데이터 읽기
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    if "name" not in df.columns:
        raise ValueError("[에러] CSV에 'name' 컬럼이 없습니다. 제목 컬럼 이름을 확인해 주세요.")

    # 비게임 여부 판별
    df["is_non_game"] = df["name"].apply(is_non_game)

    # 비게임 의심 목록
    non_game_df = df[df["is_non_game"]].copy()
    # 게임으로 보는 목록
    game_df = df[~df["is_non_game"]].copy()

    # is_non_game 컬럼은 정리 결과 파일에서는 빼도 되고, 남겨도 됨
    non_game_df.to_csv(output_non_games, index=False, encoding="utf-8-sig")
    game_df.to_csv(output_games, index=False, encoding="utf-8-sig")

    print(f"[INFO] 전체 행 수: {len(df)}")
    print(f"[INFO] 비게임 의심 항목: {len(non_game_df)} → {output_non_games.name}")
    print(f"[INFO] 게임으로 분류된 항목: {len(game_df)} → {output_games.name}")


# ============================================================
# 3. main
# ============================================================

def main():
    print(f"[INFO] 입력 파일: {INPUT_FILE}")
    split_games_and_non_games(INPUT_FILE, OUTPUT_GAMES, OUTPUT_NON_GAMES)


if __name__ == "__main__":
    main()
