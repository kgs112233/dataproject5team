import csv
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

publisher_list = []
with open("test_input.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        publisher_list.append(row["publishers"].strip())

# 중복 제거
publisher_list = list(set(publisher_list))

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=chrome_options)

output_rows = []

for pub in publisher_list:
    print(f"[INFO] Processing Publisher: {pub}")

    encoded = quote(pub)
    url = f"https://gamalytic.com/publisher/{encoded}"
    driver.get(url)

    try:
        overview_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Overview')]"))
        )

        text = overview_block.text.split("\n")

        total_rev = ""

        for line in text:
            if line.startswith("Total Lifetime Revenue:"):
                total_rev = line.replace("Total Lifetime Revenue:", "").strip()
                break

        if total_rev == "":
            raise Exception("Total Lifetime Revenue Not Found")

        output_rows.append([pub, total_rev])
        print(f"[SUCCESS] {pub}: {total_rev}")

    except Exception as e:
        print(f"[ERROR] {pub}: {e}")
        output_rows.append([pub, "ERROR"])

driver.quit()

with open("publisher_revenue_output.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["publishers", "Total_Lifetime_Revenue"])
    writer.writerows(output_rows)

print("=== ALL DONE ===")