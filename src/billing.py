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
    """
    Calculates electricity bill using slab-based tariff.

    Args:
        units_kwh (float): Monthly energy consumption in kWh

    Returns:
        dict:
          - units_consumed : input units
          - energy_charge  : charge from slabs only
          - fixed_charge   : fixed monthly charge
          - meter_rent     : meter rental fee
          - total_bill     : final amount payable
          - breakdown      : slab-wise unit and cost details
          - alert          : slab position message
    """
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

    # FIX #1 — add fixed charge + meter rent on top of energy charge
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
    """
    Generates a slab position alert for the user.

    FIX #2 — corrected boundary conditions (≤ instead of <)
              so users at exactly 100, 200, 300 units get
              the right message.
    """
    if units_kwh <= 100:
        return "You are in the lowest slab (0–100 units at ₹3/kWh)."
    elif units_kwh <= 200:
        return "Approaching higher slab — next slab starts at 200 units (₹7/kWh)."
    elif units_kwh <= 300:
        return "Warning: You are in the third slab. Next slab at 300 units (₹9/kWh)."
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