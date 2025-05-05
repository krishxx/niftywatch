from preprocess import load_and_preprocess_data, create_lstm_sequences
from model_xgb import train_xgb_model
from model_lstm import train_lstm_model

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

if __name__ == "__main__":
    data_folder = "D:\\Palmtree\\niftywatch\\data\\deep"  # Make sure this path contains your 70 CSV files
    df = load_and_preprocess_data(data_folder)

    print("\n--- XGBoost Model Training ---")
    train_xgb_model(df)

    print("\n--- LSTM Model Training ---")
    train_lstm_model(df)