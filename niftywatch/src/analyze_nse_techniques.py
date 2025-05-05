# program_3: analyze_nse_techniques.py

import pandas as pd
import os
import datetime

DATA_DIR = "data"

# Technique 1: Identify >27 points spike

def technique_price_spike(df, threshold=27):
    alerts = []
    for index in df['index'].unique():
        index_df = df[df['index'] == index].copy()
        index_df.sort_values('datetime', inplace=True)
        index_df['last_price_diff'] = index_df['last_price'].diff()
        spiked = index_df[index_df['last_price_diff'] > threshold]
        for _, row in spiked.iterrows():
            alerts.append(f"ALERT: {index} spiked by {row['last_price_diff']:.2f} points at {row['datetime']}")
    return alerts


def run_all_techniques(df):
    results = []
    results.extend(technique_price_spike(df))
    # Future techniques can be added here with results.extend(...)
    return results


def read_today_data():
    today = datetime.date.today()
    filename = f"nse_data_{today}.csv"
    file_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(file_path):
        print("Data file not found.")
        return

    df = pd.read_csv(file_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df


def main():
    df = read_today_data()
    if df is not None:
        print("\n[Running analysis techniques...]")
        alerts = run_all_techniques(df)
        if alerts:
            for alert in alerts:
                print(alert)
        else:
            print("No alerts generated today.")


if __name__ == '__main__':
    main()
