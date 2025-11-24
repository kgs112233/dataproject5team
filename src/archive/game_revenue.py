import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

game_ids = []
with open("test_input.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        game_ids.append(row["appid"])

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=chrome_options)

output_rows = []

for game_id in game_ids:
    url = f"https://gamalytic.com/game/{game_id}"
    print(f"[INFO] Processing {game_id} ...")

    driver.get(url)

    try:
        stats_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Stats')]"))
        )

        all_text = stats_block.text

        def extract_by_prefix(prefix: str) -> str:
            for line in all_text.split("\n"):
                if line.startswith(prefix):
                    return line.replace(prefix, "").strip()
            return ""

        gross_normal = extract_by_prefix("Gross revenue:")

        gross_base = ""
        if not gross_normal:
            gross_base = extract_by_prefix("Gross revenue (base game):")

        if gross_normal:
            final = gross_normal
            print(f"[SUCCESS NORMAL] {game_id}: {gross_normal}")
        elif gross_base:
            final = gross_base
            print(f"[SUCCESS BASE]   {game_id}: {gross_base}")
        else:
            final = "ERROR"
            print(f"[ERROR] {game_id}: Gross revenue not found (normal/base)")

        output_rows.append([game_id, gross_normal, gross_base, final])

    except Exception as e:
        print(f"[ERROR EXCEPTION] {game_id}: {e}")
        output_rows.append([game_id, "", "", "ERROR"])

driver.quit()

with open("game_revenue_output.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "appid",
        "Gross_Revenue_Normal",
        "Gross_Revenue_Base_Game",
        "Gross_Revenue_Final"
    ])
    writer.writerows(output_rows)

print("=== ALL DONE ===")