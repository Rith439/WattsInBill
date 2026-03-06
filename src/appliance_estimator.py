<<<<<<< HEAD
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
=======
import pandas as pd

DAYS = 30

def load_power_data():
    """
    Load appliance power data from CSV into a dictionary.
    Keys: appliance names in lowercase
    Values: power in kW
    """
    df = pd.read_csv("data/appliance_power.csv")
    # Convert appliance names to lowercase for safe matching
    return dict(zip(df["appliance"].str.lower(), df["power_kw"]))


def estimate_appliance_energy(user_input):
    """
    Estimate total monthly energy consumption (kWh) from user input.
    
    user_input: list of dictionaries, each with:
        - "name": appliance name (string)
        - "hours": hours used per day (number)
        - "power_kw" (optional): power in kW for custom appliances
    
    Returns:
        total_energy (float): estimated monthly energy in kWh
    """
    power_data = load_power_data()
    total_energy = 0

    for item in user_input:
        appliance_name = item["name"].lower()
        hours_used = float(item["hours"])

        # Determine power:
        # - Use CSV power if appliance exists
        # - Else, use user-provided power_kw (optional)
        if appliance_name in power_data:
            power = power_data[appliance_name]
        else:
            power = float(item.get("power_kw", 0))  # defaults to 0 if not provided

        # Calculate monthly energy for this appliance
        energy = power * hours_used * DAYS
        total_energy += energy

    return total_energy
>>>>>>> fc00c93c2c23148d5fe5c1cef7ffb80187a05308
