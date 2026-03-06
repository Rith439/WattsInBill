# src/prediction.py
<<<<<<< HEAD
# ML-based next-month energy prediction
# Models : RandomForest vs XGBoost vs Ridge — compared by MAE
# XAI    : SHAP explanation always on XGBoost for explainability

import pandas as pd
import numpy as np
import shap
from sklearn.ensemble      import RandomForestRegressor
from sklearn.linear_model  import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics       import mean_absolute_error, mean_squared_error
from xgboost               import XGBRegressor


DATA_PATH = "data/processed/uci_monthly.csv"


# ─────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates time-series features from monthly energy data.

    Features:
      - month_index  : linear trend (position in series)
      - month_num    : calendar month (1–12)
      - sin_month    : cyclical sine encoding of month
      - cos_month    : cyclical cosine encoding of month
      - lag_1/2/3    : previous 1, 2, 3 months consumption
      - roll_3_mean  : 3-month rolling average
      - roll_6_mean  : 6-month rolling average
      - roll_3_std   : 3-month rolling std (volatility)
    """
    df = df.copy()

    df["month_index"] = np.arange(len(df))
    df["month_num"]   = df["month"].dt.month

    # Cyclical encoding so Dec(12) and Jan(1) are treated as adjacent
    df["sin_month"]   = np.sin(2 * np.pi * df["month_num"] / 12)
    df["cos_month"]   = np.cos(2 * np.pi * df["month_num"] / 12)

    # Lag features
    df["lag_1"]       = df["energy_kwh"].shift(1)
    df["lag_2"]       = df["energy_kwh"].shift(2)
    df["lag_3"]       = df["energy_kwh"].shift(3)

    # Rolling features (shift(1) prevents data leakage)
    df["roll_3_mean"] = df["energy_kwh"].shift(1).rolling(3).mean()
    df["roll_6_mean"] = df["energy_kwh"].shift(1).rolling(6).mean()
    df["roll_3_std"]  = df["energy_kwh"].shift(1).rolling(3).std()

    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


FEATURE_COLS = [
    "month_index",
    "month_num",
    "sin_month",
    "cos_month",
    "lag_1",
    "lag_2",
    "lag_3",
    "roll_3_mean",
    "roll_6_mean",
    "roll_3_std",
]

# Human-readable labels for SHAP chart
FEATURE_LABELS = {
    "month_index" : "Long-term Trend",
    "month_num"   : "Calendar Month",
    "sin_month"   : "Seasonal Cycle (sin)",
    "cos_month"   : "Seasonal Cycle (cos)",
    "lag_1"       : "Last Month Usage",
    "lag_2"       : "2 Months Ago Usage",
    "lag_3"       : "3 Months Ago Usage",
    "roll_3_mean" : "3-Month Avg Usage",
    "roll_6_mean" : "6-Month Avg Usage",
    "roll_3_std"  : "3-Month Volatility",
}


# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    """Loads and sorts the processed monthly dataset."""
    df = pd.read_csv(DATA_PATH)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values("month").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────
# TRAIN & EVALUATE  (all 3 models)
# ─────────────────────────────────────────────────────────────
def train_and_evaluate() -> dict:
    """
    Trains RandomForest, XGBoost, and Ridge on a chronological
    80/20 train-test split and returns metrics for all three.

    Returns:
        dict with model objects, metrics, scaler, feature cols
    """
    df = load_data()
    df = build_features(df)

    X = df[FEATURE_COLS]
    y = df["energy_kwh"]

    # Chronological 80/20 split — no shuffling (time-series rule)
    split           = int(len(df) * 0.80)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    # Scaler only needed for Ridge
    scaler     = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    candidates = {
        "RandomForest": RandomForestRegressor(
            n_estimators=200, max_depth=6,
            min_samples_leaf=2, random_state=42
        ),
        "XGBoost": XGBRegressor(
            n_estimators=200, learning_rate=0.05,
            max_depth=3, random_state=42,
            verbosity=0
        ),
        "Ridge": Ridge(alpha=1.0),
    }

    results   = {}
    best_mae  = np.inf
    best_name = ""

    for name, model in candidates.items():
        if name == "Ridge":
            model.fit(X_train_sc, y_train)
            preds = model.predict(X_test_sc)
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

        mae  = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        results[name] = {
            "MAE" : round(mae,  3),
            "RMSE": round(rmse, 3),
        }

        if mae < best_mae:
            best_mae  = mae
            best_name = name

    return {
        "best_model_name" : best_name,
        "best_mae"        : round(best_mae, 3),
        "results"         : results,
        "models"          : candidates,
        "scaler"          : scaler,
        "df"              : df,
    }


# ─────────────────────────────────────────────────────────────
# BUILD NEXT MONTH FEATURE ROW
# ─────────────────────────────────────────────────────────────
def build_next_row(df: pd.DataFrame) -> pd.DataFrame:
    """Builds the feature row for next month prediction."""
    last           = df.iloc[-1]
    next_month_num = (last["month_num"] % 12) + 1

    return pd.DataFrame([{
        "month_index" : last["month_index"] + 1,
        "month_num"   : next_month_num,
        "sin_month"   : np.sin(2 * np.pi * next_month_num / 12),
        "cos_month"   : np.cos(2 * np.pi * next_month_num / 12),
        "lag_1"       : last["energy_kwh"],
        "lag_2"       : df.iloc[-2]["energy_kwh"],
        "lag_3"       : df.iloc[-3]["energy_kwh"],
        "roll_3_mean" : df["energy_kwh"].iloc[-3:].mean(),
        "roll_6_mean" : df["energy_kwh"].iloc[-6:].mean(),
        "roll_3_std"  : df["energy_kwh"].iloc[-3:].std(),
    }])


# ─────────────────────────────────────────────────────────────
# PREDICT NEXT MONTH  (best model by MAE)
# ─────────────────────────────────────────────────────────────
def predict_monthly_energy() -> float:
    """
    Trains all 3 models, selects best by MAE, predicts next month.

    Returns:
        float: predicted energy consumption in kWh
    """
    result   = train_and_evaluate()
    df       = result["df"]
    model    = result["models"][result["best_model_name"]]
    scaler   = result["scaler"]
    next_row = build_next_row(df)

    if result["best_model_name"] == "Ridge":
        predicted = model.predict(scaler.transform(next_row))[0]
    else:
        predicted = model.predict(next_row)[0]

    return float(max(predicted, 0.0))


# ─────────────────────────────────────────────────────────────
# SHAP EXPLAINABILITY  (always XGBoost)
# ─────────────────────────────────────────────────────────────
def explain_prediction() -> dict:
    """
    Uses SHAP TreeExplainer on XGBoost to explain next month's
    prediction — showing which features pushed it up or down.

    Always uses XGBoost regardless of MAE winner because:
      - XGBoost has native TreeExplainer support (fastest + most accurate SHAP)
      - Most interpretable for time-series features
      - Standard in XAI literature

    Returns:
        dict with:
          - predicted_kwh  : XGBoost prediction for next month
          - base_value     : dataset average (SHAP baseline)
          - contributions  : list of dicts sorted by impact
          - feature_labels : human readable names (for chart)
          - shap_values    : raw SHAP values (for chart)
    """
    df = load_data()
    df = build_features(df)

    X = df[FEATURE_COLS]
    y = df["energy_kwh"]

    # Train XGBoost on full dataset
    xgb_model = XGBRegressor(
        n_estimators=200, learning_rate=0.05,
        max_depth=3, random_state=42,
        verbosity=0
    )
    xgb_model.fit(X, y)

    # Build next month feature row
    next_row  = build_next_row(df)
    predicted = float(xgb_model.predict(next_row)[0])

    # ── SHAP explanation ──────────────────────────────────
    explainer  = shap.TreeExplainer(xgb_model)
    shap_vals  = explainer.shap_values(next_row)

    # shap_vals shape is (1, n_features) — get first row
    shap_list  = shap_vals[0].tolist()
    base_value = float(explainer.expected_value)

    # Build contributions list with human-readable labels
    contributions = []
    for feat, shap_val in zip(FEATURE_COLS, shap_list):
        contributions.append({
            "feature"    : feat,
            "label"      : FEATURE_LABELS[feat],
            "shap_value" : round(shap_val, 3),
            "direction"  : "↑" if shap_val > 0 else "↓",
        })

    # Sort by absolute SHAP value — most impactful first
    contributions = sorted(
        contributions,
        key=lambda x: abs(x["shap_value"]),
        reverse=True
    )

    return {
        "predicted_kwh" : round(predicted,  2),
        "base_value"    : round(base_value, 2),
        "contributions" : contributions,
        # Separated lists — ready for direct use in st.pyplot()
        "feature_labels": [c["label"]      for c in contributions],
        "shap_values"   : [c["shap_value"] for c in contributions],
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  SmartBill AI — ML Prediction Engine")
    print("="*55)

    # Model comparison
    result = train_and_evaluate()
    print(f"\n  Model Comparison (Chronological 80/20 Split):")
    print(f"  {'Model':<16} {'MAE':>8} {'RMSE':>8}")
    print(f"  {'-'*36}")
    for name, metrics in result["results"].items():
        flag = " ✅" if name == result["best_model_name"] else ""
        print(f"  {name:<16} {metrics['MAE']:>8} {metrics['RMSE']:>8}{flag}")

    # Best model prediction
    prediction = predict_monthly_energy()
    print(f"\n  Best model  : {result['best_model_name']} (MAE={result['best_mae']} kWh)")
    print(f"  Prediction  : {prediction:.2f} kWh (next month)")

    # SHAP explanation
    print(f"\n  {'─'*50}")
    print(f"  SHAP Explanation (XGBoost)")
    print(f"  {'─'*50}")
    shap_result = explain_prediction()
    print(f"  Base value (dataset avg) : {shap_result['base_value']} kWh")
    print(f"  XGBoost predicted        : {shap_result['predicted_kwh']} kWh")
    print(f"\n  {'Feature':<25} {'SHAP Value':>12} {'Impact':>6}")
    print(f"  {'-'*46}")
    for c in shap_result["contributions"]:
        bar = "█" * max(1, int(abs(c["shap_value"]) / 10))
        print(f"  {c['label']:<25} {c['shap_value']:>+10.3f}   {c['direction']}  {bar}")
    print("="*55)
=======
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


>>>>>>> fc00c93c2c23148d5fe5c1cef7ffb80187a05308
