import pandas as pd
from luxalgo_pine_equivalent import detect_pivots, calculate_volume_oscillator, detect_breaks

df = pd.read_csv("NIF_deep_analysis_2025-06-30.csv")
df['datetime'] = pd.to_datetime(df['datetime'])

high_pivot, low_pivot = detect_pivots(df, left=15, right=15)
osc = calculate_volume_oscillator(df)

# Shift by 1 to mimic PineScript's [1]
results = detect_breaks(df, high_pivot.shift(1), low_pivot.shift(1), osc, volume_thresh=20)
print(results.tail(100))