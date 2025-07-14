import pandas as pd
from datetime import datetime
import time
import os

DATA_FILE = "NIF_deep_analysis_2025-07-07.csv"
FVG_LOG_FILE = "fvg_live_signals_2025-07-07.csv"

def load_data():
    df = pd.read_csv(DATA_FILE)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values(by='datetime').reset_index(drop=True)
    return df

def detect_fvg(df):
    # Bullish FVG: low[n-2] > high[n]
    df['bullish_fvg'] = (df['Low'].shift(2) > df['High'])
    df['bullish_fvg_zone'] = df.apply(
        lambda row: (row['High'], df['Low'].shift(2)[row.name]) if row['bullish_fvg'] else None, axis=1
    )

    # Bearish FVG: high[n-2] < low[n]
    df['bearish_fvg'] = (df['High'].shift(2) < df['Low'])
    df['bearish_fvg_zone'] = df.apply(
        lambda row: (df['High'].shift(2)[row.name], row['Low']) if row['bearish_fvg'] else None, axis=1
    )

    # FVG size
    df['bullish_fvg_size'] = df.apply(
        lambda row: row['bullish_fvg_zone'][1] - row['bullish_fvg_zone'][0]
        if row['bullish_fvg_zone'] else 0, axis=1
    )
    df['bearish_fvg_size'] = df.apply(
        lambda row: row['bearish_fvg_zone'][1] - row['bearish_fvg_zone'][0]
        if row['bearish_fvg_zone'] else 0, axis=1
    )

    # Volume spike and momentum
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['vol_spike'] = df['volume'] / df['volume'].rolling(5).mean()
    df['vol_spike'] = df['vol_spike'].fillna(0)
    df['momentum_after'] = df['Close'].shift(-3) - df['Close']
    df['momentum_after'] = df['momentum_after'].fillna(0)    

    # Strength
    df['bullish_fvg_strength'] = df['bullish_fvg'].astype(int) * (
        df['bullish_fvg_size'].abs() + df['vol_spike'] + df['momentum_after']
    )
    df['bearish_fvg_strength'] = df['bearish_fvg'].astype(int) * (
        df['bearish_fvg_size'].abs() + df['vol_spike'] - df['momentum_after']
    )

    return df

def log_new_signals(df):
    signals = df[df['bullish_fvg'] | df['bearish_fvg']][[
        'datetime', 'High', 'Low', 'bullish_fvg', 'bullish_fvg_zone', 'bullish_fvg_strength',
        'bearish_fvg', 'bearish_fvg_zone', 'bearish_fvg_strength'
    ]]
    if not signals.empty:
        if os.path.exists(FVG_LOG_FILE):
            existing = pd.read_csv(FVG_LOG_FILE)
            signals['datetime'] = pd.to_datetime(signals['datetime'])
            existing['datetime'] = pd.to_datetime(existing['datetime'])

            signals = signals[~signals['datetime'].isin(existing['datetime'])]
            final = pd.concat([existing, signals], ignore_index=True)            
        else:
            final = signals
        final.to_csv(FVG_LOG_FILE, index=False)
        print(signals.tail(1).to_string(index=False))

def run_monitor():
    print("🔁 Live FVG Monitoring Started...")
    last_rows = 0
    while True:
        df = load_data()
        if len(df) > last_rows:
            new_df = detect_fvg(df)
            log_new_signals(new_df)
            last_rows = len(df)
        time.sleep(30)  # Check every 30 seconds

def run_once():
    print("🔁 Live FVG Monitoring...")
    df = load_data()
    new_df = detect_fvg(df)
    log_new_signals(new_df)
    
# Run monitor
# run_monitor()
run_once()
