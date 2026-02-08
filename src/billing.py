def calculate_bill(units_kwh):
    """
    Calculates electricity bill using slab-based tariff.

    Parameters:
    units_kwh (float): Monthly energy consumption in kWh

    Returns:
    dict: total bill, slab-wise breakdown, slab alert
    """

    slabs = [
        (100, 3),   # first 100 units at ₹3
        (100, 5),   # next 100 units at ₹5
        (100, 7),   # next 100 units at ₹7
        (float('inf'), 9)  # remaining units at ₹9
    ]

    remaining_units = units_kwh
    total_cost = 0
    breakdown = []

    for slab_limit, rate in slabs:
        if remaining_units <= 0:
            break

        units_in_slab = min(remaining_units, slab_limit)
        cost = units_in_slab * rate

        breakdown.append({
            "units": units_in_slab,
            "rate": rate,
            "cost": cost
        })

        total_cost += cost
        remaining_units -= units_in_slab

    alert = get_slab_alert(units_kwh)

    return {
        "units_consumed": units_kwh,
        "total_bill": round(total_cost, 2),
        "breakdown": breakdown,
        "alert": alert
    }


def get_slab_alert(units_kwh):
    """
    Generates slab alert if user is near next slab.
    """
    if units_kwh < 100:
        return "You are in the lowest slab."
    elif units_kwh < 200:
        return "Approaching higher slab at 200 units."
    elif units_kwh < 300:
        return "Warning: Next slab starts at 300 units."
    else:
        return "High consumption slab. Consider reducing usage."


# Simple test
if __name__ == "__main__":
    sample = calculate_bill(245)
    print(sample)
