import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------
# CONFIG
# -----------------------
HEADLESS = True

# Card Info
TCG = "yugioh"
SET_NAME = "The Lost Millennium"
CARD_NAME = "Elemental Hero Flame Wingman"
PRODUCT_TYPE = "Cards"
PRINTING = "1st Edition"
CONDITION = "Near Mint"
RARITY = "Ultimate Rare"

# -----------------------
# DATABASE SETUP
# -----------------------
conn = sqlite3.connect("cards.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_name TEXT,
    price REAL,
    condition TEXT,
    listing_title TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


# -----------------------
# DRIVER SETUP
# -----------------------
def create_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    return driver


# -----------------------
# SCRAPE FUNCTION
# -----------------------
def scrape_card(card_name, tcg, set_name, product_type, printing, condition, rarity):
    driver = create_driver()

    try:
        # Create the URL
        search_url = f"https://www.tcgplayer.com/search/"
        if tcg is None:
            search_url += "all/product?"
        else:
            search_url += f"{tcg.replace(' ', '-')}/product?productLineName={tcg.replace(' ', '-')}"

        if card_name is None:
            print("Need at least the card name to search for and add a card.")
            return
        else:
            search_url += f"&q={card_name.replace(' ', '+')}"

        if set_name is not None:
            search_url += f"&setName={set_name.replace(' ', '-')}"

        if product_type is not None:
            search_url += f"&ProductTypeName={product_type.replace(' ', '+')}"

        if printing is not None:
            search_url += f"&Printing={printing.replace(' ', '+')}"

        if condition is not None:
            search_url += f"&Condition={condition.replace(' ', '+')}"

        if rarity is not None:
            search_url += f"&RarityName={rarity.replace(' ', '+')}"

        driver.get(search_url)

        time.sleep(5)  # let JS load

        # click first product
        # list-view-product-card__image--1
        products = driver.find_elements(By.CSS_SELECTOR, "section.search-results a")
        if not products:
            print("No products found")
            return

        products[0].click()
        time.sleep(5)

        # grab market data
        market_price = driver.find_elements(By.CSS_SELECTOR, "span.price-points__upper__price")[0]
################-----------------
        # grab listing rows
        rows = driver.find_elements(By.CSS_SELECTOR, ".listing-item")

        results = []

        for row in rows[:20]:  # limit for MVP
            try:
                price_el = row.find_element(By.CSS_SELECTOR, ".listing-item__price")
                title_el = row.find_element(By.CSS_SELECTOR, ".listing-item__title")
                condition_el = row.find_element(By.CSS_SELECTOR, ".listing-item__condition")

                price_text = price_el.text.replace("$", "").strip()
                price = float(price_text)

                title = title_el.text
                condition = condition_el.text

                results.append({
                    "price": price,
                    "title": title,
                    "condition": condition
                })

            except Exception:
                continue

        return results

    finally:
        driver.quit()


# -----------------------
# STORE DATA
# -----------------------
def store_results(card_name, results):
    for r in results:
        cur.execute("""
            INSERT INTO listings (card_name, price, condition, listing_title)
            VALUES (?, ?, ?, ?)
        """, (card_name, r["price"], r["condition"], r["title"]))

    conn.commit()


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    data = scrape_card(CARD_NAME)

    if data:
        store_results(CARD_NAME, data)
        print(f"Stored {len(data)} listings")
        print(data[:5])
    else:
        print("No data scraped")
