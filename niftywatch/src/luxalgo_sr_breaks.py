
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def detect_swing_highs_lows(df, left=2, right=2):
    highs = df['High']
    lows = df['Low']

    swing_highs = []
    swing_lows = []

    for i in range(left, len(df) - right):
        if highs[i] > max(highs[i - left:i]) and highs[i] > max(highs[i + 1:i + 1 + right]):
            swing_highs.append(i)
        if lows[i] < min(lows[i - left:i]) and lows[i] < min(lows[i + 1:i + 1 + right]):
            swing_lows.append(i)

    return swing_highs, swing_lows

def calculate_sr_levels(df, swing_highs, swing_lows, tolerance=0.2):
    levels = []

    for idx in swing_highs:
        level = df['High'][idx]
        levels.append({'index': idx, 'level': level, 'type': 'resistance'})

    for idx in swing_lows:
        level = df['Low'][idx]
        levels.append({'index': idx, 'level': level, 'type': 'support'})

    return pd.DataFrame(levels)

def check_breaks(df, sr_levels, lookahead=3, tolerance=0.1):
    result = sr_levels.copy()
    result['broken'] = False
    result['break_type'] = None

    for i, row in sr_levels.iterrows():
        level = row['level']
        idx = row['index']
        sr_type = row['type']

        future_highs = df['High'][idx+1:idx+1+lookahead]
        future_lows = df['Low'][idx+1:idx+1+lookahead]

        if sr_type == 'resistance':
            if any(future_highs > level * (1 + tolerance)):
                result.at[i, 'broken'] = True
                result.at[i, 'break_type'] = 'break_above'
        elif sr_type == 'support':
            if any(future_lows < level * (1 - tolerance)):
                result.at[i, 'broken'] = True
                result.at[i, 'break_type'] = 'break_below'

    return result

def plot_levels(df, sr_with_breaks, last_n=100):
    plt.figure(figsize=(15, 6))
    plt.plot(df['datetime'][-last_n:], df['Close'][-last_n:], label='Close Price')

    for _, row in sr_with_breaks.iterrows():
        if row['index'] >= len(df) - last_n:
            color = 'green' if row['type'] == 'support' else 'red'
            if row['broken']:
                color = 'orange'
            plt.hlines(row['level'], xmin=df['datetime'][row['index']], xmax=df['datetime'].iloc[-1],
                       colors=color, linestyles='dashed', linewidth=1)

    plt.title("Support and Resistance Levels with Breaks (LuxAlgo Style)")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Example Usage ---
# df = pd.read_csv("NIF_deep_analysis_2025-06-17.csv")
# df['datetime'] = pd.to_datetime(df['datetime'])

# swing_highs, swing_lows = detect_swing_highs_lows(df)
# sr_levels = calculate_sr_levels(df, swing_highs, swing_lows)
# sr_with_breaks = check_breaks(df, sr_levels)
# plot_levels(df, sr_with_breaks)
