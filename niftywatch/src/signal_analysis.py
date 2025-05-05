# signal_analysis.py

import pandas as pd
import time
from datetime import datetime

# CSV_PATH = "data/nse_data_{}.csv".format(datetime.today().date())
CSV_PATH = "data/nse_data_2025-05-02.csv"

# Define logic for signal generation techniques
def detect_large_price_move(df, threshold=27):
    df["signal_price_jump"] = df["idx_chg"] > threshold
    return df

def detect_sentiment_signals(df):
    df["signal_buy"] = (df["sent"] > 0) & (df["pChange"] > 1)
    df["signal_sell"] = (df["sent"] < 0) & (df["pChange"] < -1)
    return df

def detect_trustworthy_signal(df, trust_threshold=70):
    df["signal_trusted"] = df["trust_value"] > trust_threshold
    return df

def detect_fvg(df):
    df["fvg"] = (df["low_x"].shift(-1) > df["high_x"]) | (df["high_x"].shift(-1) < df["low_x"])
    return df

# Apply all strategies
def apply_all_strategies(df):
    if "idx_chg" in df.columns:
        df = detect_large_price_move(df)
    else:
        print("Warning: 'idx_chg' column missing. Skipping price jump detection.")

    if "sent" in df.columns and "pChange" in df.columns:
        df = detect_sentiment_signals(df)
    else:
        print("Warning: 'sent' or 'pChange' column missing. Skipping sentiment detection.")

    if "trust_value" in df.columns:
        df = detect_trustworthy_signal(df)
    else:
        print("Warning: 'trust_value' column missing. Skipping trust signal.")

    if "high_x" in df.columns and "low_x" in df.columns:
        df = detect_fvg(df)
    else:
        print("Warning: 'high_x' or 'low_x' column missing. Skipping FVG detection.")

    return df

def live_monitor(csv_file):
    last_row_count = 0
    while True:
        try:
            df = pd.read_csv(csv_file)
            if len(df) > last_row_count:
                df = apply_all_strategies(df)

                latest = df.iloc[-1]
                print("\n--- Live Signal Update ---")
                print("Time:", latest["datetime"])
                print("Symbol:", latest["symbol"])
                print("Price:", latest["close_x"])
                print("Sentiment:", latest["sent"])
                print("pChange:", latest["pChange"])
                print("Signal: ", end="")
                if latest.get("signal_buy"):
                    print("BUY")
                elif latest.get("signal_sell"):
                    print("SELL")
                else:
                    print("HOLD")

                if latest.get("fvg"):
                    print("FVG Detected: True")
                if latest.get("signal_trusted"):
                    print(f"Trusted Signal (Trust: {latest['trust_value']}%)")

                last_row_count = len(df)
            time.sleep(60)
        except Exception as e:
            print("Error processing file:", e)
            time.sleep(60)

if __name__ == "__main__":
    live_monitor(CSV_PATH)
