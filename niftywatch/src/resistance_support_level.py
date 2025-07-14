import pandas as pd

df = pd.read_csv("NIF_deep_analysis_2025-06-26.csv")
df['datetime'] = pd.to_datetime(df['datetime'])


from luxalgo_sr_breaks import detect_swing_highs_lows, calculate_sr_levels, check_breaks, plot_levels

swing_highs, swing_lows = detect_swing_highs_lows(df)
sr_levels = calculate_sr_levels(df, swing_highs, swing_lows)
sr_with_breaks = check_breaks(df, sr_levels)
plot_levels(df, sr_with_breaks)


