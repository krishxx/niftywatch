# program_1: nse_data_collector.py

import time
import datetime
import pandas as pd
import os
import requests
from nselib import capital_market as cm
from nsepython import nse_get_index_quote, nse_get_index_list
import datetime

DATA_DIR = "data"
INDEX_LIST = ["NIFTY BANK", "SENSEX"]

# Install with: pip install nselib

SAVE_DIR = "data"
INDEX_LIST = ["NIFTY BANK", "SENSEX"]  # You can add option data if APIs allow

os.makedirs(SAVE_DIR, exist_ok=True)


def is_market_open():
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    market_open = datetime.time(9, 15)
    market_close = datetime.time(15, 30)
    return market_open <= now.time() <= market_close


def fetch_index_data():
    records = []
    available_indices = nse_get_index_list()
    
    for index in INDEX_LIST:
        if index not in available_indices:
            print(f"Index {index} not found in NSE index list. Skipping.")
            continue

        try:
            quote = nse_get_index_quote(index)
            if quote and 'data' in quote and quote['data']:
                item = quote['data'][0]
                records.append({
                    'datetime': datetime.datetime.now(),
                    'index': index,
                    'last_price': item['lastPrice'],
                    'change': item['change'],
                    'pChange': item['pChange']
                })
            else:
                print(f"Quote format not valid for {index}: {quote}")
        except Exception as e:
            print(f"Error fetching {index}: {e}")

    return records

def main():
    print("\n[Started NSE Data Collector - minute-wise]")
    while True:
        if is_market_open():
            data = fetch_index_data()
            if data:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                file_path = os.path.join(SAVE_DIR, f"nse_data_{today}.csv")
                df = pd.DataFrame(data)
                if os.path.exists(file_path):
                    df.to_csv(file_path, mode='a', header=False, index=False)
                else:
                    df.to_csv(file_path, index=False)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Data saved.")
            time.sleep(60)
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Market closed. Sleeping...")
            time.sleep(300)


if __name__ == '__main__':
    main()
