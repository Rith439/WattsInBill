# src/billing.py
# Slab-based electricity bill calculator

FIXED_CHARGE = 50.0   # ₹/month — charged regardless of consumption
METER_RENT   = 10.0   # ₹/month — standard meter rental fee

SLABS = [
    (100, 3),           # first 100 units at ₹3/kWh
    (100, 5),           # next  100 units at ₹5/kWh
    (100, 7),           # next  100 units at ₹7/kWh
    (float('inf'), 9),  # remaining units at ₹9/kWh
]


def calculate_bill(units_kwh: float) -> dict:
    remaining = units_kwh
    energy_charge = 0.0
    breakdown = []

    for slab_limit, rate in SLABS:
        if remaining <= 0:
            break

        units_in_slab = min(remaining, slab_limit)
        cost          = units_in_slab * rate

        breakdown.append({
            "units": round(units_in_slab, 2),
            "rate" : rate,
            "cost" : round(cost, 2),
        })

        energy_charge += cost
        remaining     -= units_in_slab

    total_bill = energy_charge + FIXED_CHARGE + METER_RENT

    return {
        "units_consumed": units_kwh,
        "energy_charge" : round(energy_charge, 2),
        "fixed_charge"  : FIXED_CHARGE,
        "meter_rent"    : METER_RENT,
        "total_bill"    : round(total_bill, 2),
        "breakdown"     : breakdown,
        "alert"         : get_slab_alert(units_kwh),
    }


def get_slab_alert(units_kwh: float) -> str:
    if units_kwh <= 100:
        return "You are in the lowest slab (0–100 units at ₹3/kWh)."
    elif units_kwh <= 200:
        return "You are in slab 2 (101–200 units at ₹5/kWh). Next slab at 200 units (₹7/kWh)."
    elif units_kwh <= 300:
        return "Warning: You are in slab 3 (201–300 units at ₹7/kWh). Next slab at 300 units (₹9/kWh)."
    else:
        return "High consumption slab (₹9/kWh). Consider reducing usage."


if __name__ == "__main__":
    test_units = [80, 100, 150, 245, 320, 500]

    for units in test_units:
        bill = calculate_bill(units)
        print(f"\n  Units: {units} kWh")
        print(f"  Energy Charge : ₹{bill['energy_charge']}")
        print(f"  Fixed Charge  : ₹{bill['fixed_charge']}")
        print(f"  Meter Rent    : ₹{bill['meter_rent']}")
        print(f"  Total Bill    : ₹{bill['total_bill']}")
        print(f"  Alert         : {bill['alert']}")