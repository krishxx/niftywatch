import numpy as np
import pandas as pd
import pickle
from tensorflow.keras.models import load_model
import time
import random  # Simulating live data feed

# Load trained LSTM model and scaler
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError

model = load_model("lstm_model.keras", custom_objects={'MeanSquaredError': MeanSquaredError})


#lstm_model = load_model("lstm_model.h5")
import joblib

scaler = joblib.load("lstm_scaler.pkl")  # This must be a MinMaxScaler object

#with open("lstm_scaler.pkl", "rb") as f:
#    scaler = pickle.load(f)

SEQUENCE_LENGTH = 20  # Adjust according to the training sequence length

# Initialize an empty dataframe to hold live feed data
live_data_df = pd.DataFrame(columns=["yf_open", "high_x", "low_x", "close_x", "volume_x", "datetime", 
                                     "idx_chg", "till_low_x", "till_high_x", "symbol", "trn_oi", 
                                     "till_low_y", "till_high_y", "up_pct", "down_pct", "spurt", 
                                     "day_high", "day_low", "range", "body_pct", "up_wick_pct", 
                                     "down_wick_pct", "exceeds_spurt_threshold", "sent", "atm_sent", 
                                     "atm_ce_sum", "atm_pe_sum", "otm_sent", "otm_ce_sum", 
                                     "otm_pe_sum", "atm_wgt_pct", "otm_wgt_pct", "is_atm_heavy", 
                                     "call_wgt_sent", "put_wgt_sent", "itm_call_sent", "itm_put_sent", 
                                     "safety_strk", "trial_strk", "safety_entry", "safety_DL", 
                                     "trial_entry", "trial_DL", "trust_value", "direction"])

# Simulate incoming data (replace with your live data collection logic)
def get_live_data():
    # Simulate random data for example (replace with actual live feed)
    data = {
        "yf_open": random.random() * 100,
        "high_x": random.random() * 100,
        "low_x": random.random() * 100,
        "close_x": random.random() * 100,
        "volume_x": random.randint(1, 1000),
        "datetime": pd.to_datetime("now"),
        "idx_chg": random.random() * 10,
        "till_low_x": random.random() * 100,
        "till_high_x": random.random() * 100,
        "symbol": "TICKER",  # Replace with actual ticker
        "trn_oi": random.random() * 100,
        "till_low_y": random.random() * 100,
        "till_high_y": random.random() * 100,
        "up_pct": random.random(),
        "down_pct": random.random(),
        "spurt": random.random() > 0.8,  # Simulating spurt
        "day_high": random.random() > 0.9,  # Simulating day high
        "day_low": random.random() < 0.1,  # Simulating day low
        "range": random.random() * 10,
        "body_pct": random.random(),
        "up_wick_pct": random.random(),
        "down_wick_pct": random.random(),
        "exceeds_spurt_threshold": random.random() > 0.7,  # Simulating condition
        "sent": random.random(),
        "atm_sent": random.random(),
        "atm_ce_sum": random.random(),
        "atm_pe_sum": random.random(),
        "otm_sent": random.random(),
        "otm_ce_sum": random.random(),
        "otm_pe_sum": random.random(),
        "atm_wgt_pct": random.random(),
        "otm_wgt_pct": random.random(),
        "is_atm_heavy": random.random() > 0.5,  # Simulating ATM heaviness
        "call_wgt_sent": random.random(),
        "put_wgt_sent": random.random(),
        "itm_call_sent": random.random(),
        "itm_put_sent": random.random(),
        "safety_strk": random.random() * 100,
        "trial_strk": random.random() * 100,
        "safety_entry": random.random() * 100,
        "safety_DL": random.random() * 100,
        "trial_entry": random.random() * 100,
        "trial_DL": random.random() * 100,
        "trust_value": random.random() * 100,
        "direction": random.choice([0, 1, -1])  # Direction for training purposes
    }
    return pd.DataFrame([data])

def update_live_data(new_row_df):
    global live_data_df
    live_data_df = pd.concat([live_data_df, new_row_df], ignore_index=True)
    if len(live_data_df) > SEQUENCE_LENGTH:  # Keep only the last SEQUENCE_LENGTH rows
        live_data_df = live_data_df.tail(SEQUENCE_LENGTH)
    return live_data_df

def predict_next_minute(live_data_df):
    """
    Predict the next minute based on the most recent data.
    """
    # Scale the new data
    # scaled_data = pd.DataFrame(scaler.transform(live_data_df), columns=live_data_df.columns)
    scaled_data = pd.DataFrame(scaler.transform(live_data_df), columns=live_data_df.columns)

    # Extract last SEQUENCE_LENGTH rows
    if len(scaled_data) < SEQUENCE_LENGTH:
        print("Not enough data to form a sequence.")
        return None

    seq = scaled_data.iloc[-SEQUENCE_LENGTH:].values
    seq = np.expand_dims(seq, axis=0)  # (1, timesteps, features)

    prediction = lstm_model.predict(seq)
    print("Predicted next minute direction (raw tanh):", prediction[0][0])
    return prediction[0][0]

def main():
    while True:
        # Simulate receiving new data
        new_data = get_live_data()
        updated_data = update_live_data(new_data)

        # Make prediction with the most recent data
        pred = predict_next_minute(updated_data)
        if pred is not None:
            if pred > 0.3:
                print("Prediction: UP")
            elif pred < -0.3:
                print("Prediction: DOWN")
            else:
                print("Prediction: NO TRADE")

        # Wait before processing the next data (e.g., 1 minute)
        time.sleep(60)  # Adjust the sleep time to match your data feed frequency

if __name__ == "__main__":
    main()
