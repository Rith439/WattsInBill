# src/prediction.py
#Base line prediction
import pandas as pd
import numpy as np
from xgboost import XGBRegressor


def predict_monthly_energy():
    """
    Predicts next month's energy consumption (kWh)
    using time-series features and XGBoost.
    Returns:
        float: predicted energy consumption in kWh
    """

    # Load processed monthly dataset
    df = pd.read_csv("data/processed/uci_monthly.csv")

    # Sort by time (important for time-series)
    df = df.sort_values("month").reset_index(drop=True)

    # Trend feature
    df["month_index"] = np.arange(len(df))

    # Lag features
    df["lag_1"] = df["energy_kwh"].shift(1)
    df["lag_2"] = df["energy_kwh"].shift(2)

    # Rolling averages
    df["roll_3_mean"] = df["energy_kwh"].rolling(window=3).mean()
    df["roll_6_mean"] = df["energy_kwh"].rolling(window=6).mean()

    # Drop rows with NaN values caused by lag/rolling features
    df = df.dropna().reset_index(drop=True)

    # Feature matrix and target
    feature_cols = [
        "month_index",
        "lag_1",
        "lag_2",
        "roll_3_mean",
        "roll_6_mean"
    ]

    X = df[feature_cols]
    y = df["energy_kwh"]

    # Train XGBoost regression model
    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )

    model.fit(X, y)

    # Prepare input for next month prediction
    last_row = df.iloc[-1]

    next_month_data = pd.DataFrame([{
        "month_index": last_row["month_index"] + 1,
        "lag_1": last_row["energy_kwh"],
        "lag_2": df.iloc[-2]["energy_kwh"],
        "roll_3_mean": df["energy_kwh"].iloc[-3:].mean(),
        "roll_6_mean": df["energy_kwh"].iloc[-6:].mean()
    }])

    # Predict next month's energy consumption
    predicted_kwh = model.predict(next_month_data)[0]

    return float(predicted_kwh)
if __name__ == "__main__":
    df = pd.read_csv("data/processed/uci_monthly.csv")

    actual_last = df["energy_kwh"].iloc[-1]
    predicted_next = predict_monthly_energy()

    print("Last known month actual kWh:", actual_last)
    print("Next month predicted kWh:", predicted_next)


