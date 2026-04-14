⚡ WattsInBill AI

AI-powered electricity bill predictor — combines machine learning time-series forecasting with appliance-level estimation to predict your next month's energy consumption and bill.


📌 Overview
WattsInBill AI is a hybrid energy prediction system that:

Trains and compares 3 ML models (RandomForest, XGBoost, Ridge) on real household power consumption data
Accepts user-defined appliance usage as a personalization layer
Applies a hybrid adjustment formula to blend both signals
Calculates a slab-based electricity bill with itemized breakdown
Explains predictions using SHAP (XAI) — showing which features drove the forecast


🏗️ Project Structure
WattsInBill_AI/
│
├── data/
│   ├── raw/
│   │   ├── household_power_consumption.txt   # UCI dataset
│   │   └── electricity_bill_dataset.csv      # 45K bill records
│   └── processed/
│       ├── uci_monthly.csv                   # Aggregated monthly usage
│       ├── tariff_reference.csv              # Slab tariff reference
│       └── appliance_power.csv               # Appliance power ratings (kW)
│
├── src/
│   ├── data_preprocessing.py                 # Data pipeline
│   ├── prediction.py                         # ML models + SHAP
│   ├── appliance_estimator.py                # Appliance energy estimator
│   ├── simulator.py                          # Core hybrid engine
│   ├── billing.py                            # Slab-based bill calculator
│   └── baseline_model.py                     # (Reserved)
│
└── README.md

⚙️ How It Works
┌─────────────────────┐     ┌──────────────────────┐
│  UCI Power Dataset  │     │  User Appliance Input │
│  (48 months)        │     │  (name, hours, qty)   │
└────────┬────────────┘     └──────────┬───────────┘
         │                             │
         ▼                             ▼
┌─────────────────────┐     ┌──────────────────────┐
│  ML Prediction      │     │  Appliance Estimator  │
│  RF / XGB / Ridge   │     │  power × hours × days │
│  → Best by MAE      │     │  → monthly kWh        │
└────────┬────────────┘     └──────────┬───────────┘
         │                             │
         └──────────┬──────────────────┘
                    ▼
         ┌──────────────────────┐
         │  Hybrid Adjustment   │
         │  factor = app_kwh /  │
         │           dataset_avg│
         │  final = ml × factor │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │  Slab Bill Calculator│
         │  ₹3 / ₹5 / ₹7 / ₹9  │
         │  + Fixed + Meter Rent│
         └──────────────────────┘

🤖 ML Models & Features
Models Compared (Chronological 80/20 Split)
ModelNotesRandomForest200 estimators, max_depth=6XGBoost200 estimators, lr=0.05, max_depth=3RidgeStandardScaler + alpha=1.0
Best model selected automatically by lowest MAE.
Features Engineered
FeatureDescriptionmonth_indexLinear trend positionmonth_numCalendar month (1–12)sin_month, cos_monthCyclical seasonal encodinglag_1, lag_2, lag_3Previous 1–3 months usageroll_3_mean, roll_6_mean3 & 6-month rolling averagesroll_3_std3-month rolling volatility
SHAP Explainability
XGBoost is always used for SHAP explanations via TreeExplainer, showing which features pushed the prediction up (↑) or down (↓).

🔌 Supported Appliances
AppliancePower (kW)Air Conditioner1.500Induction Stove1.800Geyser2.000Microwave1.200Iron Box1.200Washing Machine0.500Refrigerator0.150Television0.100Fan0.070Laptop0.065Water Purifier0.025LED Bulb0.012

Custom appliances can be added to appliance_power.csv.


💡 Billing Tariff
SlabUnitsRateSlab 10 – 100 kWh₹3 / kWhSlab 2101 – 200 kWh₹5 / kWhSlab 3201 – 300 kWh₹7 / kWhSlab 4300+ kWh₹9 / kWh
Fixed Charge: ₹50/month | Meter Rent: ₹10/month

🚀 Getting Started
1. Clone the Repository
bashgit clone https://github.com/your-username/SmartBill_AI.git
cd SmartBill_AI
2. Install Dependencies
bashpip install pandas numpy scikit-learn xgboost shap
3. Preprocess Data
bashpython src/data_preprocessing.py
4. Run Prediction Engine
bashpython src/prediction.py
5. Run Full Simulation
bashpython src/simulator.py

📊 Sample Output
==================================================
  SmartBill AI — Simulation Results
==================================================
  ML Predicted       : 312.45 kWh
  Appliance Estimate : 387.60 kWh
  Adjustment Factor  : 1.24
  Deviation          : +23.8%
  Usage Flag         : normal
  Final Prediction   : 387.44 kWh

  ────────────────────────────────────────
  Energy Charge      : ₹2,312.96
  Fixed Charge       : ₹50.00
  Meter Rent         : ₹10.00
  ────────────────────────────────────────
  Total Bill         : ₹2,372.96

  Alert: High consumption slab (₹9/kWh). Consider reducing usage.
==================================================

📦 Datasets
DatasetSourceRecordsUCI Household Power ConsumptionUCI ML Repository~2M minute-level readingsElectricity Bill DatasetKaggle45,345 records

🛠️ Tech Stack

Python 3.8+
pandas, numpy — Data processing
scikit-learn — RandomForest, Ridge, preprocessing
XGBoost — Gradient boosted trees
SHAP — Explainable AI / feature attribution

