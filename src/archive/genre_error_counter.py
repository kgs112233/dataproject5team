import csv
from collections import Counter

INPUT_FILE = "result/game_and_publisher_revenue.csv"

def count_error_by_genre():
    error_count = Counter()

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            game_rev = row.get("game_revenue", "").strip()
            pub_rev = row.get("publisher_revenue", "").strip()
            genre = row.get("SampledGenre", "").strip()

            if game_rev == "ERROR" or pub_rev == "ERROR":
                error_count[genre] += 1

    print("=== 장르별 ERROR 개수 ===")
    for genre, count in error_count.items():
        print(f"{genre}: {count}")

if __name__ == "__main__":
    count_error_by_genre()
