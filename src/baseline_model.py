# src/baseline_model.py
# 3-month moving average baseline prediction with MAE evaluation

import pandas as pd
import numpy as np


DATA_PATH = "data/processed/uci_monthly.csv"


def baseline_monthly_energy() -> float:
    """
    Baseline model:
    Predicts next month's energy consumption
    using average of last 3 months (moving average).

    Returns:
        float: predicted energy consumption in kWh
    """
    df = load_data()

    # Take last 3 months
    last_3 = df["energy_kwh"].iloc[-3:]
    baseline_prediction = last_3.mean()

    return float(baseline_prediction)


def evaluate_baseline() -> dict:
    """
    Evaluates the 3-month moving average baseline
    using a rolling walk-forward evaluation.

    For each month (starting from month 4), predicts using
    the previous 3 months and compares to actual value.

    Returns:
        dict: MAE, RMSE, MAPE of the baseline model
    """
    df = load_data()
    actuals    = []
    predictions = []

    # Walk-forward: predict each month using previous 3
    for i in range(3, len(df)):
        pred   = df["energy_kwh"].iloc[i - 3:i].mean()
        actual = df["energy_kwh"].iloc[i]
        predictions.append(pred)
        actuals.append(actual)

    actuals     = np.array(actuals)
    predictions = np.array(predictions)

    mae  = np.mean(np.abs(actuals - predictions))
    rmse = np.sqrt(np.mean((actuals - predictions) ** 2))

    return {
        "MAE"  : round(mae,  3),
        "RMSE" : round(rmse, 3),
    }


def load_data() -> pd.DataFrame:
    """Loads and sorts the processed monthly dataset."""
    df = pd.read_csv(DATA_PATH)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)
    return df


if __name__ == "__main__":
    prediction = baseline_monthly_energy()
    metrics    = evaluate_baseline()

    print("=" * 45)
    print("  Baseline Model — 3-Month Moving Average")
    print("=" * 45)
    print(f"  Predicted next month : {prediction:.2f} kWh")
    print(f"  MAE                  : {metrics['MAE']} kWh")
    print(f"  RMSE                 : {metrics['RMSE']} kWh")
    print("=" * 45)
    print("  (ML model must beat these numbers to be useful)")
