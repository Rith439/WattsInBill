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

# Average monthly consumption computed directly from UCI dataset
# Auto-updates if the dataset changes — no hardcoding
DATASET_AVG = pd.read_csv("data/processed/uci_monthly.csv")["energy_kwh"].mean()

# Clamp bounds for adjustment factor
# Prevents unrealistic predictions if appliance input is extreme
MIN_FACTOR = 0.5   # final can't go below 50% of ML prediction
MAX_FACTOR = 2.0   # final can't go above 200% of ML prediction


# ─────────────────────────────────────────────────────────────
# ADJUSTMENT LOGIC
# ─────────────────────────────────────────────────────────────
def compute_adjusted_prediction(ml_kwh: float, appliance_kwh: float) -> dict:
    """
    Scales the ML prediction using the appliance estimate.

    Formula:
        AdjustmentFactor = appliance_kwh / DATASET_AVG
        FinalEnergy      = ml_kwh × AdjustmentFactor

    The factor is clamped between 0.5 and 2.0 to prevent
    unrealistic outputs from extreme appliance inputs.

    Args:
        ml_kwh        : ML predicted consumption (kWh)
        appliance_kwh : Appliance-based estimated consumption (kWh)

    Returns:
        dict with factor, final_kwh, and deviation flag
    """
    factor  = appliance_kwh / DATASET_AVG
    factor  = max(MIN_FACTOR, min(factor, MAX_FACTOR))  # clamp

    final_kwh = ml_kwh * factor

    # Deviation flag — how far appliance estimate is from dataset avg
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
        3. Hybrid adjustment    → compute_adjusted_prediction()
        4. Bill calculation     → calculate_bill()

    Args:
        appliance_inputs : list of dicts, each with:
                             - "name"     : appliance name (str)
                             - "hours"    : hours used per day (float)
                             - "quantity" : number of units (int)
        days             : number of days in billing month (default 30)

    Returns:
        dict with full simulation results for app.py to display
    """

    # ── Step 1: ML Prediction ──────────────────────────────
    ml_kwh = predict_monthly_energy()

    # ── Step 2: Appliance Estimation ──────────────────────
    appliance_result = estimate_appliance_energy(appliance_inputs, days)
    appliance_kwh    = appliance_result["total_kwh"]

    # ── Step 3: Hybrid Adjustment ─────────────────────────
    adjustment = compute_adjusted_prediction(ml_kwh, appliance_kwh)
    final_kwh  = adjustment["final_kwh"]

    # ── Step 4: Bill Calculation ──────────────────────────
    bill = calculate_bill(final_kwh)

    return {
        # ML layer
        "ml_predicted_kwh"   : round(ml_kwh, 2),

        # Appliance layer
        "appliance_kwh"      : appliance_kwh,
        "appliance_breakdown": appliance_result["breakdown"],
        "skipped_appliances" : appliance_result["skipped"],

        # Adjustment layer
        "adjustment_factor"  : adjustment["adjustment_factor"],
        "deviation_pct"      : adjustment["deviation_pct"],
        "usage_flag"         : adjustment["usage_flag"],

        # Final prediction
        "final_kwh"          : final_kwh,

        # Billing layer
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
    sample_appliances = [
        {"name": "ac",              "hours": 8,  "quantity": 1},
        {"name": "fan",             "hours": 10, "quantity": 4},
        {"name": "refrigerator",    "hours": 24, "quantity": 1},
        {"name": "television",      "hours": 5,  "quantity": 1},
        {"name": "lightbulb_led",   "hours": 6,  "quantity": 6},
        {"name": "washing_machine", "hours": 1,  "quantity": 1},
        {"name": "laptop",          "hours": 8,  "quantity": 1},
    ]

    result = run_simulation(sample_appliances, days=30)

    print("\n" + "="*50)
    print("  SmartBill AI — Simulation Results")
    print("="*50)
    print(f"  ML Predicted       : {result['ml_predicted_kwh']} kWh")
    print(f"  Appliance Estimate : {result['appliance_kwh']} kWh")
    print(f"  Adjustment Factor  : {result['adjustment_factor']}")
    print(f"  Deviation          : {result['deviation_pct']}%")
    print(f"  Usage Flag         : {result['usage_flag']}")
    print(f"  Final Prediction   : {result['final_kwh']} kWh")
    print(f"\n  {'─'*40}")
    print(f"  Energy Charge      : ₹{result['energy_charge']}")
    print(f"  Fixed Charge       : ₹{result['fixed_charge']}")
    print(f"  Meter Rent         : ₹{result['meter_rent']}")
    print(f"  {'─'*40}")
    print(f"  Total Bill         : ₹{result['total_bill']}")
    print(f"\n  Alert              : {result['slab_alert']}")
    print("="*50)

    if result["skipped_appliances"]:
        print(f"\n  ⚠️  Skipped: {result['skipped_appliances']}")