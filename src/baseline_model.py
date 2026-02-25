# src/baseline_model.py
#3 month moving average baseline precdiction
import pandas as pd


def baseline_monthly_energy():
    """
    Baseline model:
    Predict next month's energy consumption
    using average of last 3 months.

    Returns:
        float: predicted energy consumption in kWh
    """

    df = pd.read_csv("data/processed/uci_monthly.csv")

    # Sort by month
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)

    # Take last 3 months energy values
    last_3 = df["energy_kwh"].iloc[-3:]

    # Compute average
    baseline_prediction = last_3.mean()

    return float(baseline_prediction)


if __name__ == "__main__":
    prediction = baseline_monthly_energy()
    print("Baseline (3-month avg) predicted kWh:", prediction)