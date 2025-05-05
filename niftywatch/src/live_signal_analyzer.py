import pandas as pd
import time
import datetime
import os

DATA_DIR = "data"

def get_today_file():
    today = datetime.date.today()
    return os.path.join(DATA_DIR, f"nse_data_{today}.csv")

def detect_fvg(df):
    """
    Add 'fvg' column to each row with values: 'Bullish', 'Bearish', or None
    """
    df = df.sort_values("datetime")
    df["fvg"] = None
    for idx in range(1, len(df)):
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]

        if prev["high"] < curr["low"]:
            df.at[idx, "fvg"] = "Bullish"
        elif prev["low"] > curr["high"]:
            df.at[idx, "fvg"] = "Bearish"
    return df

def analyze_signals(df):
    
    if 'high' not in df.columns or 'low' not in df.columns:
        print("High/Low data missing, skipping FVG logic.")
        df["fvg"] = None
    else:
        df = detect_fvg(df)
    latest_df = df.sort_values("datetime").groupby("index").tail(1)
    results = []

    for _, row in latest_df.iterrows():
        signal = "HOLD"
        if row["pChange"] > 1:
            signal = "BUY"
            if row.get("fvg") == "Bullish":
                signal = "STRONG BUY"
        elif row["pChange"] < -1:
            signal = "SELL"
            if row.get("fvg") == "Bearish":
                signal = "STRONG SELL"

        results.append({
            "index": row["index"],
            "last_price": row["last_price"],
            "pChange": round(row["pChange"], 2),
            "fvg": row.get("fvg", "-"),
            "signal": signal
        })
    return results

def print_signals(signals):
    os.system("cls" if os.name == "nt" else "clear")  # Clears the terminal
    print(f"Updated at {datetime.datetime.now().strftime('%H:%M:%S')}\n")
    print(f"{'Index':<15}{'Last Price':<15}{'% Change':<10}{'Signal'}")
    print("-" * 50)
    for s in signals:
        print(f"{s['index']:<15}{s['last_price']:<15}{s['pChange']:<10}{s['signal']}")

def live_monitor():
    while True:
        try:
            file_path = get_today_file()
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, parse_dates=['datetime'])
                signals = analyze_signals(df)
                print_signals(signals)
            else:
                print("Waiting for CSV data to appear...")
        except Exception as e:
            print(f"Error processing file: {e}")
        
        time.sleep(60)  # Refresh every 1 minute

if __name__ == "__main__":
    live_monitor()
