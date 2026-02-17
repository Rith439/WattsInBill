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
