import pandas as pd
import os


RAW_DATA_PATH = "data/raw/household_power_consumption.txt"     #E:\Rithvik\Projects\mini_project\SmartBill_AI\data\raw\household_power_consumption.txt
PROCESSED_DATA_DIR = "data/processed"
PROCESSED_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "uci_monthly.csv")


def load_raw_data():
    """
    Loads the raw UCI household power consumption dataset.
    """
    df = pd.read_csv(
        RAW_DATA_PATH,
        sep=';',
        parse_dates={'datetime': ['Date', 'Time']},
        na_values='?',
        low_memory=False
    )
    return df


def clean_data(df):
    """
    Cleans the dataset by removing missing values
    and converting data types.
    """
    df.dropna(inplace=True)

    df['Global_active_power'] = df['Global_active_power'].astype(float)

    return df


def convert_power_to_energy(df):
    """
    Converts power (kW) to energy consumption (kWh per minute).
    """
    df['energy_kwh'] = df['Global_active_power'] / 60
    return df


def aggregate_monthly(df):
    """
    Aggregates energy consumption on a monthly basis.
    """
    df['month'] = df['datetime'].dt.to_period('M')
    monthly_df = df.groupby('month')['energy_kwh'].sum().reset_index()
    monthly_df['month'] = monthly_df['month'].astype(str)
    return monthly_df


def save_processed_data(df):
    """
    Saves the processed monthly data to disk.
    """
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    df.to_csv(PROCESSED_FILE_PATH, index=False)


def run_preprocessing():
    """
    Runs the full preprocessing pipeline.
    """
    print("Loading raw data...")
    df = load_raw_data()

    print("Cleaning data...")
    df = clean_data(df)

    print("Converting power to energy...")
    df = convert_power_to_energy(df)

    print("Aggregating monthly usage...")
    monthly_df = aggregate_monthly(df)

    print("Saving processed data...")
    save_processed_data(monthly_df)

    process_bill_dataset()

    print("✅All  data preprocessing completed successfully!")




BILL_DATA_PATH = "data/raw/electricity_bill_dataset.csv"                #data\raw\electricity_bill_dataset.csv
TARIFF_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "tariff_reference.csv")


def process_bill_dataset():
    """
    Processes electricity bill dataset to extract tariff reference.
    """
    print("Loading electricity bill dataset...")
    df = pd.read_csv(BILL_DATA_PATH)

    # Normalize column names
    df.columns = [c.lower().strip() for c in df.columns]

    # Rename tariff column for consistency
    df.rename(columns={'tariffrate': 'tariff_rate'}, inplace=True)

    if 'tariff_rate' not in df.columns:
        raise ValueError(
            f"TariffRate column not found. Columns: {list(df.columns)}"
        )

    # Create slab reference based on tariff rate distribution
    tariff_df = (
        df[['tariff_rate']]
        .dropna()
        .assign(
            slab=pd.cut(
                df['tariff_rate'],
                bins=[0, 3, 5, 7, 10, float('inf')],
                labels=["low", "medium", "high", "very_high", "extreme"]
            )
        )
        .groupby('slab')['tariff_rate']
        .mean()
        .reset_index()
    )

    tariff_df.to_csv(TARIFF_FILE_PATH, index=False)

    print("✅ Tariff reference extracted successfully!")



if __name__ == "__main__":
    run_preprocessing()

