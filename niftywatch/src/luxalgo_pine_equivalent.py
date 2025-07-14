
import pandas as pd
import numpy as np

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def detect_pivots(df, left=15, right=15):
    highs = df['High']
    lows = df['Low']
    high_pivot = [np.nan] * len(df)
    low_pivot = [np.nan] * len(df)

    for i in range(left, len(df) - right):
        window_high = highs[i - left:i + right + 1]
        window_low = lows[i - left:i + right + 1]
        if highs[i] == max(window_high):
            high_pivot[i] = highs[i]
        if lows[i] == min(window_low):
            low_pivot[i] = lows[i]

    return pd.Series(high_pivot), pd.Series(low_pivot)

def calculate_volume_oscillator(df):
    short_ema = ema(df['volume'], 5)
    long_ema = ema(df['volume'], 10)
    osc = 100 * (short_ema - long_ema) / long_ema
    return osc

def detect_breaks(df, high_pivot, low_pivot, osc, volume_thresh):
    df['Break_Support'] = (
        (df['Close'] < low_pivot) &
        ~((df['Open'] - df['Close']) < (df['High'] - df['Open'])) &
        (osc > volume_thresh)
    )

    df['Break_Resistance'] = (
        (df['Close'] > high_pivot) &
        ~((df['Open'] - df['Low']) > (df['Close'] - df['Open'])) &
        (osc > volume_thresh)
    )

    df['Bull_Wick'] = (
        (df['Close'] > high_pivot) &
        ((df['Open'] - df['Low']) > (df['Close'] - df['Open']))
    )

    df['Bear_Wick'] = (
        (df['Close'] < low_pivot) &
        ((df['Open'] - df['Close']) < (df['High'] - df['Open']))
    )

    return df[['datetime', 'Close', 'Break_Support', 'Break_Resistance', 'Bull_Wick', 'Bear_Wick']]

# Example usage:
# df = pd.read_csv("NIF_deep_analysis_2025-06-17.csv")
# df['datetime'] = pd.to_datetime(df['datetime'])
# high_pivot, low_pivot = detect_pivots(df, left=15, right=15)
# osc = calculate_volume_oscillator(df)
# df_luxalgo = detect_breaks(df, high_pivot.shift(1), low_pivot.shift(1), osc, volume_thresh=20)
