# program_2: read_latest_nse_data.py

import os
import pandas as pd
import datetime
import time
from pathlib import Path
from nselib import capital_market as cm
from nsepython import nse_get_index_quote, nse_get_index_list
import datetime

DATA_DIR = "data"
INDEX_LIST = ["NIFTY BANK", "NIFTY 50", "FINNIFTY", "NIFTY NEXT 50"]  # You can update this list

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
    available_indices = nse_get_index_list()

    for index in INDEX_LIST:
        if index not in available_indices:
            print(f"Index {index} not found in NSE index list. Skipping.")
            continue

        try:
            quote = nse_get_index_quote(index)
            if quote and 'last' in quote:
                records.append({
                    'datetime': datetime.datetime.now(),
                    'index': index,
                    'last_price': float(quote['last'].replace(',', '')),
                    'high': float(quote['high'].replace(',', '')),
                    'low': float(quote['low'].replace(',', '')),
                    'change': float(quote['last'].replace(',', '')) - float(quote['previousClose'].replace(',', '')),
                    'pChange': float(quote['percChange'].replace(',', ''))
                })
            else:
                print(f"Quote format not valid for {index}: {quote}")
        except Exception as e:
            print(f"Error fetching {index}: {e}")

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
                # After appending new row in DataFrame

                # Calculate idx_chg
                df["idx_chg"] = df["close_x"].diff().fillna(0)

                # Rolling lowest/highest prices
                df["till_low_x"] = df["low_x"].cummin()
                df["till_high_x"] = df["high_x"].cummax()

                # Trending OI
                df["trn_oi"] = df["put_oi"] - df["call_oi"]
                df["till_low_y"] = df["trn_oi"].cummin()
                df["till_high_y"] = df["trn_oi"].cummax()

                # Spurt in OI
                df["spurt"] = df["trn_oi"].pct_change().fillna(0)
                df["exceeds_spurt_threshold"] = df["spurt"].abs() > 0.099  # 9.9% spurt

                # Range and candlestick body
                df["range"] = df["high_x"] - df["low_x"]
                df["body_pct"] = (df["close_x"] - df["yf_open"]).abs()
                df["up_wick_pct"] = df["high_x"] - df[["close_x", "yf_open"]].max(axis=1)
                df["down_wick_pct"] = df[["close_x", "yf_open"]].min(axis=1) - df["low_x"]

                # Day high/low for trn_oi
                df["day_high"] = df["trn_oi"] == df["trn_oi"].max()
                df["day_low"] = df["trn_oi"] == df["trn_oi"].min()               
                
            time.sleep(60)
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Market closed or holiday. Waiting...")
            time.sleep(300)

if __name__ == '__main__':
    append_data_to_csv()
