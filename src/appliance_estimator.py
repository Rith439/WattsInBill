# src/appliance_estimator.py
# Estimates monthly energy consumption from user appliance input

import pandas as pd


APPLIANCE_DATA_PATH = "data/processed/appliance_power.csv"


def load_power_data() -> dict:
    df = pd.read_csv(APPLIANCE_DATA_PATH)
    return dict(zip(df["appliance"].str.lower(), df["power_kw"]))


def estimate_appliance_energy(user_input: list, days: int = 30) -> dict:
    power_data  = load_power_data()
    total_kwh   = 0.0
    breakdown   = []
    skipped     = []

    for item in user_input:
        name     = item["name"].lower().strip()
        hours    = float(item.get("hours",    1))
        quantity = int(item.get("quantity",   1))

        if name in power_data:
            power = float(power_data[name])
        elif "power_kw" in item and float(item["power_kw"]) > 0:
            power = float(item["power_kw"])
        else:
            print(f"  Warning: '{name}' not found — skipped")
            skipped.append(name)
            continue

        monthly_kwh = power * hours * quantity * days

        breakdown.append({
            "appliance"  : name,
            "power_kw"   : power,
            "hours_day"  : hours,
            "quantity"   : quantity,
            "monthly_kwh": round(monthly_kwh, 3),
        })

        total_kwh += monthly_kwh

    return {
        "total_kwh" : round(total_kwh, 3),
        "breakdown" : breakdown,
        "skipped"   : skipped,
    }


if __name__ == "__main__":
    sample_input = [
        {"name": "ac",              "hours": 8,  "quantity": 1},
        {"name": "fan",             "hours": 10, "quantity": 4},
        {"name": "refrigerator",    "hours": 24, "quantity": 1},
        {"name": "television",      "hours": 5,  "quantity": 1},
        {"name": "lightbulb_led",   "hours": 6,  "quantity": 6},
        {"name": "washing_machine", "hours": 1,  "quantity": 1},
        {"name": "laptop",          "hours": 8,  "quantity": 1},
    ]

    result = estimate_appliance_energy(sample_input, days=30)

    print(f"Total: {result['total_kwh']} kWh")
    for item in result["breakdown"]:
        print(f"  {item['appliance']}: {item['monthly_kwh']} kWh")
    if result["skipped"]:
        print(f"Skipped: {result['skipped']}")