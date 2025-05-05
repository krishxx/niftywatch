import os
import pandas as pd
import datetime
import time
from pathlib import Path
from nselib import capital_market as cm
from nsepython import nse_get_index_quote, nse_get_index_list
import yfinance as yf
import datetime

# NSE indices
NSE_INDEX_LIST = ["NIFTY BANK", "NIFTY 50"]
# BSE index mapping
BSE_INDEX_TICKERS = {
    "SENSEX": "^BSESN"
}

DATA_DIR = "..\\data"


def get_today_file():
    today = datetime.date.today()
    filename = f"nse_data_{today}.csv"
    return os.path.join(DATA_DIR, filename)

def is_market_open():
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    market_open = datetime.time(9, 15)
    market_close = datetime.time(15, 30)
    return market_open <= now.time() <= market_close

def fetch_index_data():
    records = []
    available_nse_indices = nse_get_index_list()

    # NSE indices
    for index in NSE_INDEX_LIST:
        if index not in available_nse_indices:
            print(f"Index {index} not found in NSE index list. Skipping.")
            continue

        try:
            quote = nse_get_index_quote(index)
            if quote and 'last' in quote:
                records.append({
                    'datetime': datetime.datetime.now(),
                    'index': index,
                    'last_price': float(quote['last'].replace(',', '')),
                    'change': float(quote['last'].replace(',', '')) - float(quote['previousClose'].replace(',', '')),
                    'pChange': float(quote['percChange'].replace(',', ''))
                })
            else:
                print(f"Quote format not valid for {index}: {quote}")
        except Exception as e:
            print(f"Error fetching {index}: {e}")

    # BSE index via Yahoo Finance
    for index, ticker in BSE_INDEX_TICKERS.items():
        try:
            data = yf.download(ticker, period="1d", interval="1m")
            if not data.empty:
                latest = data.iloc[-1]
                previous = data.iloc[-2] if len(data) > 1 else latest
                records.append({
                    'datetime': datetime.datetime.now(),
                    'index': index,
                    'last_price': round(latest['Close'], 2),
                    'change': round(latest['Close'] - previous['Close'], 2),
                    'pChange': round(((latest['Close'] - previous['Close']) / previous['Close']) * 100, 2)
                })
        except Exception as e:
            print(f"Error fetching BSE index {index}: {e}")

    return records

def append_data_to_csv():
    file_path = get_today_file()
    os.makedirs(DATA_DIR, exist_ok=True)

    while True:
        if is_market_open():
            data = fetch_index_data()
            if data:
                df = pd.DataFrame(data)
                if os.path.exists(file_path):
                    df.to_csv(file_path, mode='a', header=False, index=False)
                else:
                    df.to_csv(file_path, index=False)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Data appended.")
            time.sleep(60)
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Market closed or holiday. Waiting...")
            time.sleep(300)

if __name__ == '__main__':
    append_data_to_csv()



