import pandas as pd

# Step 1: Load the CSV
df = pd.read_csv("..//data//NIF_deep_analysis_2025-05-16.csv")  # Replace with your actual file path

# Step 2: Ensure datetime is sorted
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values(by='datetime').reset_index(drop=True)

# Step 3: Extract OHLC
high = df['high_x']
low = df['low_x']
close = df['close_x']

# Step 4: Detect Bullish FVG (low[n-2] > high[n])
df['bullish_fvg'] = (low.shift(2) > high)
df['bullish_fvg_zone'] = df.apply(
    lambda row: (high[row.name], low.shift(2)[row.name]) if row['bullish_fvg'] else None,
    axis=1
)

# Step 5: Detect Bearish FVG (high[n-2] < low[n])
df['bearish_fvg'] = (high.shift(2) < low)
df['bearish_fvg_zone'] = df.apply(
    lambda row: (high.shift(2)[row.name], low[row.name]) if row['bearish_fvg'] else None,
    axis=1
)

# Step 6: Calculate FVG size
df['bullish_fvg_size'] = df.apply(
    lambda row: row['bullish_fvg_zone'][1] - row['bullish_fvg_zone'][0]
    if row['bullish_fvg_zone'] else 0,
    axis=1
)
df['bearish_fvg_size'] = df.apply(
    lambda row: row['bearish_fvg_zone'][1] - row['bearish_fvg_zone'][0]
    if row['bearish_fvg_zone'] else 0,
    axis=1
)

# Step 7: Calculate volume spike
df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
df['vol_spike'] = df['Volume'] / df['Volume'].rolling(5).mean()
df['vol_spike'].fillna(0, inplace=True)

# Step 8: Calculate momentum
df['momentum_after'] = close.shift(-3) - close
df['momentum_after'].fillna(0, inplace=True)

# Step 9: Strength calculation
df['bullish_fvg_strength'] = df['bullish_fvg'].astype(int) * (
    df['bullish_fvg_size'].abs() + df['vol_spike'] + df['momentum_after']
)

df['bearish_fvg_strength'] = df['bearish_fvg'].astype(int) * (
    df['bearish_fvg_size'].abs() + df['vol_spike'] - df['momentum_after']
)

# Step 10: Output only rows with FVGs
df_fvg = df[df['bullish_fvg'] | df['bearish_fvg']][[
    'datetime', 'high_x', 'low_x',
    'bullish_fvg', 'bullish_fvg_zone', 'bullish_fvg_strength',
    'bearish_fvg', 'bearish_fvg_zone', 'bearish_fvg_strength'
]]

# Step 11: Save to CSV
df_fvg.to_csv("fvg_analysis_with_strength.csv", index=False)

# Optional preview
print(df_fvg.head(10))
