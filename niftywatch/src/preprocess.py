# preprocess.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from config import LOOKBACK, TARGET_COL

import os
import pandas as pd

def load_and_preprocess_data(data_folder):
    all_dfs = []

    for file in sorted(os.listdir(data_folder)):
        if file.endswith(".csv"):
            file_path = os.path.join(data_folder, file)
            try:
                df = pd.read_csv(file_path)
                df.dropna(inplace=True)

                # --- Handle datetime column ---
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                    df['hour'] = df['datetime'].dt.hour
                    df['minute'] = df['datetime'].dt.minute
                    df.drop('datetime', axis=1, inplace=True)

                # --- Drop time column if exists ---
                if 'time' in df.columns:
                    df.drop('time', axis=1, inplace=True)

                # --- Ensure 'symbol' is encoded as category ---
                if 'symbol' in df.columns:
                    df['symbol'] = df['symbol'].astype('category').cat.codes

                # --- Encode all remaining object-type categorical columns ---
                for col in df.select_dtypes(include='object').columns:
                    df[col] = df[col].astype('category').cat.codes
                    
                df.replace([np.inf, -np.inf], np.nan, inplace=True)
                df.dropna(inplace=True)

                all_dfs.append(df)

            except Exception as e:
                print(f"Skipping {file} due to error: {e}")

    if not all_dfs:
        raise ValueError("No valid CSV files found or all failed to load.")

    full_df = pd.concat(all_dfs, ignore_index=True)
    return full_df


def create_lstm_sequences(df, target_col="direction", lookback=10):
    X_seq, y_seq = [], []
    for i in range(lookback, len(df)):
        X_seq.append(df.drop(columns=[target_col]).iloc[i - lookback:i].values)
        y_seq.append(df[target_col].iloc[i])
    return np.array(X_seq), np.array(y_seq)
    
    
def preprocess_lstm_input(df_row: pd.DataFrame):
    """
    - Accepts raw DataFrame with same structure as training data.
    - Normalizes/transforms it accordingly.
    - Creates sequence shape (e.g. shape=(1, 60, n_features)) for LSTM prediction.
    """
    # Apply same transformation as training
    df_row = df_row.copy()
    df_row.fillna(0, inplace=True)
    df_row = df_row.select_dtypes(include=[np.number])
    
    # Convert to shape (1, sequence_len, num_features)
    return np.expand_dims(df_row.values, axis=0)
    