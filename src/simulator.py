# src/simulator.py
# Core hybrid simulation engine
# Connects prediction.py + appliance_estimator.py + billing.py

import sys
import os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

from prediction          import predict_monthly_energy
from appliance_estimator import estimate_appliance_energy
from billing             import calculate_bill

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

DATASET_AVG = pd.read_csv("data/processed/uci_monthly.csv")["energy_kwh"].mean()

# Blend weight — how much the ML prediction influences the final result.
# When appliance input is very small vs DATASET_AVG, the appliance
# estimate should dominate (weight → 0). When appliance input is close
# to or exceeds DATASET_AVG the ML model is more relevant (weight → 0.4).
MAX_ML_WEIGHT = 0.4   # ML contributes at most 40% of the final value
MAX_FACTOR    = 2.0   # final can't exceed 200% of ML prediction


# ─────────────────────────────────────────────────────────────
# ADJUSTMENT LOGIC
# ─────────────────────────────────────────────────────────────
def compute_adjusted_prediction(ml_kwh: float, appliance_kwh: float) -> dict:
    """
    Blends the appliance estimate with the ML prediction.

    Formula:
        ml_weight     = min(appliance_kwh / DATASET_AVG, 1.0) * MAX_ML_WEIGHT
        appliance_weight = 1 - ml_weight
        final_kwh     = appliance_weight * appliance_kwh
                      + ml_weight       * ml_kwh

    This ensures:
      - Small appliance input  → result stays close to appliance estimate
      - Full household input   → ML model contributes up to 40%
      - No hard floor that inflates bills for minimal usage

    Args:
        ml_kwh        : ML predicted consumption (kWh)
        appliance_kwh : Appliance-based estimated consumption (kWh)

    Returns:
        dict with factor, final_kwh, and deviation flag
    """
    # How "complete" is the appliance list relative to a typical household?
    completeness  = min(appliance_kwh / DATASET_AVG, 1.0)

    # ML weight scales from 0 (just 1 appliance) → MAX_ML_WEIGHT (full house)
    ml_weight         = completeness * MAX_ML_WEIGHT
    appliance_weight  = 1.0 - ml_weight

    final_kwh = appliance_weight * appliance_kwh + ml_weight * ml_kwh

    # Safety cap — never exceed 200% of ML prediction
    final_kwh = min(final_kwh, ml_kwh * MAX_FACTOR)

    # Adjustment factor for display purposes
    factor = final_kwh / ml_kwh if ml_kwh > 0 else 1.0

    # Deviation flag
    deviation_pct = ((appliance_kwh - DATASET_AVG) / DATASET_AVG) * 100

    if deviation_pct > 30:
        flag = "high_usage"
    elif deviation_pct < -30:
        flag = "low_usage"
    else:
        flag = "normal"

    return {
        "adjustment_factor" : round(factor,        4),
        "final_kwh"         : round(final_kwh,     2),
        "deviation_pct"     : round(deviation_pct, 1),
        "usage_flag"        : flag,
    }


# ─────────────────────────────────────────────────────────────
# MAIN SIMULATOR
# ─────────────────────────────────────────────────────────────
def run_simulation(appliance_inputs: list, days: int = 30) -> dict:
    """
    Runs the full SmartBill AI simulation pipeline.

    Pipeline:
        1. ML prediction        → predict_monthly_energy()
        2. Appliance estimate   → estimate_appliance_energy()
        3. Hybrid blend         → compute_adjusted_prediction()
        4. Bill calculation     → calculate_bill()
    """

    # ── Step 1: ML Prediction ──────────────────────────────
    ml_kwh = predict_monthly_energy()

    # ── Step 2: Appliance Estimation ──────────────────────
    appliance_result = estimate_appliance_energy(appliance_inputs, days)
    appliance_kwh    = appliance_result["total_kwh"]

    # ── Step 3: Hybrid Blend ───────────────────────────────
    adjustment = compute_adjusted_prediction(ml_kwh, appliance_kwh)
    final_kwh  = adjustment["final_kwh"]

    # ── Step 4: Bill Calculation ──────────────────────────
    bill = calculate_bill(final_kwh)

    return {
        "ml_predicted_kwh"   : round(ml_kwh, 2),
        "appliance_kwh"      : appliance_kwh,
        "appliance_breakdown": appliance_result["breakdown"],
        "skipped_appliances" : appliance_result["skipped"],
        "adjustment_factor"  : adjustment["adjustment_factor"],
        "deviation_pct"      : adjustment["deviation_pct"],
        "usage_flag"         : adjustment["usage_flag"],
        "final_kwh"          : final_kwh,
        "energy_charge"      : bill["energy_charge"],
        "fixed_charge"       : bill["fixed_charge"],
        "meter_rent"         : bill["meter_rent"],
        "total_bill"         : bill["total_bill"],
        "bill_breakdown"     : bill["breakdown"],
        "slab_alert"         : bill["alert"],
    }


# ─────────────────────────────────────────────────────────────
# MAIN — quick test
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test 1: just 1 AC for 1 hour — should give a small bill
    single = [{"name": "ac", "hours": 1, "quantity": 1}]
    r = run_simulation(single, days=30)
    print(f"1hr AC/day → {r['appliance_kwh']} kWh appliance | {r['final_kwh']} kWh final | ₹{r['total_bill']}")

    # Test 2: full household
    full = [
        {"name": "ac",              "hours": 8,  "quantity": 1},
        {"name": "fan",             "hours": 10, "quantity": 4},
        {"name": "refrigerator",    "hours": 24, "quantity": 1},
        {"name": "television",      "hours": 5,  "quantity": 1},
        {"name": "lightbulb_led",   "hours": 6,  "quantity": 6},
        {"name": "washing_machine", "hours": 1,  "quantity": 1},
        {"name": "laptop",          "hours": 8,  "quantity": 1},
    ]
    r2 = run_simulation(full, days=30)
    print(f"Full house → {r2['appliance_kwh']} kWh appliance | {r2['final_kwh']} kWh final | ₹{r2['total_bill']}")