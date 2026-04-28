from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Set up headless Chrome
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

#product_name = "Armed Neos"
#product_type = "card"

product_name = "Battles of Legend: Monstrous Revenge Booster Box"
product_type = "booster box"

rarity_keyword = "Quarter Century Secret Rare"

# Step 1: Search for the card
search_url = f"https://www.tcgplayer.com/search/yugioh/product?q={product_name.replace(' ', '+')}"
driver.get(search_url)
time.sleep(3)

# Step 2: Find the correct product link
product_link = None

products = driver.find_elements(By.CSS_SELECTOR, "a[data-testid^='product-card__image--']")
if product_type == "card":
    for card in products:
        if rarity_keyword.lower() in card.text.lower():
            product_link = card.get_attribute('href')
            break
    if not product_link:
        driver.quit()
        raise Exception("Card with desired rarity not found.")
elif product_type == "booster box":
    breakpoint()
    for product in products:
        if "booster-box" in product.get_attribute('href'):
            product_link = product.get_attribute('href')
            break
        if not product_link:
            driver.quit()
            raise Exception("Booster box not found.")

print("Found product:", product_link)
###################################DONE TILL HERE ####################################
# Step 3: Open product page
driver.get(product_link)
time.sleep(5)  # Wait for JS to load chart

# Step 4: Extract chart data from JavaScript
chart_data_script = None
scripts = driver.find_elements(By.TAG_NAME, "script")
for script in scripts:
    if "priceChartData" in script.get_attribute("innerHTML"):
        chart_data_script = script.get_attribute("innerHTML")
        break

if not chart_data_script:
    driver.quit()
    raise Exception("Could not find price chart script.")

# Step 5: Extract JSON from script content
start = chart_data_script.find('priceChartData:') + len('priceChartData:')
end = chart_data_script.find('}', start) + 1

raw_json = chart_data_script[start:end]
try:
    price_data = json.loads(raw_json)
except:
    driver.quit()
    raise Exception("Failed to parse price chart JSON.")

driver.quit()

# Step 6: Convert to DataFrame and analyze
df = pd.DataFrame(price_data['market'])
df['date'] = pd.to_datetime(df['date'])
df['price'] = df['value']

# Plot price history
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['price'], label='Market Price')
plt.title(f"{card_name} - {rarity_keyword}")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Step 7: Calculate % change
today_price = df.iloc[-1]['price']
today_date = df.iloc[-1]['date']

def get_change(target_delta):
    target_date = today_date - target_delta
    closest = df.iloc[(df['date'] - target_date).abs().argsort()[:1]]
    if closest.empty:
        return None
    old_price = closest.iloc[0]['price']
    return round((today_price - old_price) / old_price * 100, 2)

changes = {
    "2 Weeks": get_change(timedelta(weeks=2)),
    "2 Months": get_change(timedelta(weeks=8)),
    "2 Years": get_change(timedelta(weeks=104))
}

print("Price Change Summary:")
for label, change in changes.items():
    print(f"{label}: {change if change is not None else 'N/A'}%")
