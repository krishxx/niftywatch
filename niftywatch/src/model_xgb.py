import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import MinMaxScaler
import joblib

def train_xgb_model(df):
    # Drop target
    X = df.drop(columns=["direction"])
    y = df["direction"].map({-1: 0, 0: 1, 1: 2})  # Map to 0/1/2 for XGBClassifier

    # Save feature columns
    feature_columns = X.columns.tolist()
    joblib.dump(feature_columns, "xgb_features.pkl")

    # Apply MinMaxScaler
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, "xgb_scaler.pkl")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, shuffle=False)

    # Train model
    model = xgb.XGBClassifier(enable_categorical=False)
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    print("XGB Accuracy:", accuracy_score(y_test, preds))

    # Save model
    joblib.dump(model, "xgb_model.pkl")
