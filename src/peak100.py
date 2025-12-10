import pandas as pd
from pathlib import Path

# ----------------------------------------------------------
# 경로 설정
# ----------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_DIR = PROJECT_ROOT / "input"

INPUT_FILE = INPUT_DIR / "only_games.csv"
OUTPUT_FILE = INPUT_DIR / "only_games_peak100.csv"

# ----------------------------------------------------------
# peak ≥ 100 필터링 함수
# ----------------------------------------------------------

def filter_peak_100(input_path: Path, output_path: Path):

    if not input_path.exists():
        raise FileNotFoundError(f"[에러] 입력 파일을 찾지 못했습니다: {input_path}")

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    # peak_players 숫자로 변환
    df["peak_players"] = pd.to_numeric(df["peak_players"], errors="coerce").fillna(0)

    before = len(df)
    df_filtered = df[df["peak_players"] >= 100].copy()
    after = len(df_filtered)

    # 저장
    df_filtered.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[INFO] 전체 {before}개 중 peak_players ≥ 100 : {after}개")
    print(f"[INFO] 저장 완료 → {output_path}")


# ----------------------------------------------------------
# main
# ----------------------------------------------------------

def main():
    filter_peak_100(INPUT_FILE, OUTPUT_FILE)


if __name__ == "__main__":
    main()
