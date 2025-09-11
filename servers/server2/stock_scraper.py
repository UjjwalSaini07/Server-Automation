import requests
from bs4 import BeautifulSoup
import json
import time
import os
import schedule
from datetime import datetime
from pymongo import MongoClient
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "investiqdb"
COLLECTION_NAME = "Stocks"

if not MONGO_URI:
    raise ValueError("MONGO_URI not set in .env")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

current_dir = os.path.dirname(os.path.abspath(__file__))
ticker_file_path = os.path.join(current_dir, 'IndianStockTicker.json')

if not os.path.exists(ticker_file_path):
    raise FileNotFoundError("IndianStockTicker.json not found in current directory")

with open(ticker_file_path, 'r') as f:
    tickers = json.load(f)

def is_within_allowed_hours():
    """Return True if current IST time is Mon-Fri 9:30 → 16:00."""
    ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    return ist.weekday() < 5 and 9 <= ist.hour <= 16

def fetch_stock_data(ticker, exchange):
    try:
        url = f'https://www.screener.in/company/{ticker}/'
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": f"Failed to fetch data. Status code: {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')

        def get_text(selector):
            element = soup.select_one(selector)
            return element.text.strip() if element else None

        def parse_numeric(value):
            try:
                return float(value.replace(',', '').strip('₹').strip('%')) if value else None
            except ValueError:
                return None

        market_cap = get_text("li:-soup-contains('Market Cap') .number")
        current_price = get_text("li:-soup-contains('Current Price') .number")
        high_low = get_text("li:-soup-contains('High / Low') .nowrap.value")
        stock_pe = get_text("li:-soup-contains('Stock P/E') .number")
        dividend_yield = get_text("li:-soup-contains('Dividend Yield') .number")
        roce = get_text("li:-soup-contains('ROCE') .number")
        roe = get_text("li:-soup-contains('ROE') .number")
        face_value = get_text("li:-soup-contains('Face Value') .number")

        high, low = None, None
        if high_low and ' / ' in high_low:
            high, low = map(parse_numeric, high_low.split(' / '))

        return {
            "ticker": ticker,
            "exchange": exchange,
            "market_cap": parse_numeric(market_cap),
            "current_price": parse_numeric(current_price),
            "high": high,
            "low": low,
            "stock_pe": parse_numeric(stock_pe),
            "dividend_yield": parse_numeric(dividend_yield),
            "roce": parse_numeric(roce),
            "roe": parse_numeric(roe),
            "face_value": parse_numeric(face_value)
        }

    except Exception as e:
        return {"error": str(e)}

def scrape_stocks():
    if not is_within_allowed_hours():
        print("Skipping stock scraping (outside allowed hours).")
        return

    batch_size = 20
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        for ticker in batch:
            stock_data = fetch_stock_data(ticker, "NSE")
            if "error" not in stock_data:
                collection.update_one({"ticker": ticker}, {"$set": stock_data}, upsert=True)
            else:
                print(f"Error fetching {ticker}: {stock_data['error']}")
            time.sleep(2)
        print(f"Batch {i // batch_size + 1} processed")
    print("Stock scraping completed.")

def start():
    schedule.every(15).minutes.do(scrape_stocks)
    print("Server : Stock scraper service started (Mon-Fri 9:30 → 16:00 IST).")
    while True:
        schedule.run_pending()
        time.sleep(1)
