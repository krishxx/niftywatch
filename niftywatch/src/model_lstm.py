# model_lstm.py
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.losses import MeanSquaredError
import numpy as np
import pandas as pd
import joblib
from preprocess import create_lstm_sequences  # make sure it accepts a scaler and df

def train_lstm_model(df, target_col="direction", lookback=10):
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=['float64', 'int64'])

    # Fit scaler
    scaler = MinMaxScaler()
    scaled_array = scaler.fit_transform(numeric_df)
    scaled_df = pd.DataFrame(scaled_array, columns=numeric_df.columns)

    # Add the target column back (not scaled)
    scaled_df[target_col] = df[target_col].values

    # Save the scaler
    joblib.dump(scaler, "lstm_scaler.pkl")

    # Create sequences on scaled data
    X_seq, y_seq = create_lstm_sequences(scaled_df, target_col=target_col, lookback=lookback)

    X_train, X_test, y_train, y_test = train_test_split(X_seq, y_seq, shuffle=False)

    X_train = np.nan_to_num(X_train, nan=0.0)
    X_test = np.nan_to_num(X_test, nan=0.0)

    model = Sequential()
    model.add(LSTM(64, input_shape=(X_seq.shape[1], X_seq.shape[2])))
    model.add(Dense(1, activation='tanh'))

    model.compile(optimizer='adam', loss=MeanSquaredError())

    model.fit(X_train, y_train, epochs=1000, batch_size=32, verbose=1)

    loss = model.evaluate(X_test, y_test)
    print("LSTM Test Loss:", loss)

    model.save("lstm_model.keras", include_optimizer=False)


def predict_lstm_input(input_df):
    """
    Predict using saved LSTM model.
    input_df must be preprocessed and compatible with sequence creation.
    """
    from preprocess import create_lstm_sequences  # ensure identical preprocessing

    # Load model and metadata
    model = load_model("lstm_model.h5")
    time_steps, num_features = joblib.load("lstm_input_shape.pkl")

    # Create sequence from input_df
    X_input, _ = create_lstm_sequences(input_df)

    # Check shape
    if X_input.shape[1:] != (time_steps, num_features):
        raise ValueError(f"Input shape mismatch. Expected {(time_steps, num_features)}, got {X_input.shape[1:]}")

    # Clean data
    X_input = np.nan_to_num(X_input, nan=0.0, posinf=0.0, neginf=0.0)

    # Predict
    predictions = model.predict(X_input)
    return predictions
