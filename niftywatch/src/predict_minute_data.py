import pandas as pd
import numpy as np
import joblib
import xgboost as xgb

# Load saved artifacts
model = joblib.load(xgb_model.pkl)
scaler = joblib.load(xgb_scaler.pkl)  # If you used one, else set this to None
feature_columns = joblib.load(xgb_features.pkl)  # List of feature column names

# You can replace this with dynamic input from stream, CSV, etc.
def get_new_minute_data()
    data = {
        'yf_open' [22500.0],
        'high_x' [22520.0],
        'low_x' [22490.0],
        'close_x' [22510.0],
        'volume_x' [1520],
        'datetime' ['2025-05-04 091600'],
        'idx_chg' [10],
        'till_low_x' [22400],
        'till_high_x' [22600],
        'symbol' ['BANKNIFTY'],
        'trn_oi' [320000],
        'till_low_y' [300000],
        'till_high_y' [400000],
        'up_pct' [0.8],
        'down_pct' [0.2],
        'spurt' [1],
        'day_high' [0],
        'day_low' [0],
        'range' [30],
        'body_pct' [0.5],
        'up_wick_pct' [10],
        'down_wick_pct' [5],
        'exceeds_spurt_threshold' [0],
        'sent' [0.6],
        'atm_sent' [0.7],
        'atm_ce_sum' [120000],
        'atm_pe_sum' [80000],
        'otm_sent' [0.5],
        'otm_ce_sum' [100000],
        'otm_pe_sum' [95000],
        'atm_wgt_pct' [0.55],
        'otm_wgt_pct' [0.45],
        'is_atm_heavy' [1],
        'call_wgt_sent' [0.6],
        'put_wgt_sent' [0.4],
        'itm_call_sent' [0.65],
        'itm_put_sent' [0.35],
        'safety_strk' [22500],
        'trial_strk' [22600],
        'safety_entry' [180],
        'safety_DL' [160],
        'trial_entry' [90],
        'trial_DL' [70],
        'trust_value' [80],
    }
    return pd.DataFrame(data)

def preprocess_input(df)
    # Handle 'symbol' column
    if 'symbol' in df.columns
        df['symbol'] = df['symbol'].astype('category').cat.codes

    # Drop non-numeric and unused columns
    for col in df.columns
        if df[col].dtype == 'object'
            df.drop(columns=[col], inplace=True)

    # Reorder columns to match training
    df = df.reindex(columns=feature_columns)

    # Replace inf and drop NaNs
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    # Apply scaling if scaler was used
    if scaler
        df_scaled = scaler.transform(df)
        return df_scaled
    else
        return df.values

def main()
    df_new = get_new_minute_data()
    X_input = preprocess_input(df_new)

    if X_input.shape[0] == 0
        print(Input data is empty after preprocessing.)
        return

    pred = model.predict(X_input)
    pred_label = {0 Down, 1 No Trade, 2 Up}
    print(Predicted direction, pred_label[int(pred[0])])

if __name__ == __main__
    main()
